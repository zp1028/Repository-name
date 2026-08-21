# -*- coding: utf-8 -*-
"""
彩票 AI 数据分析助手 - Streamlit 多彩种版
支持：双色球 · 快乐8 · 极速飞艇(PK10风格)
仅供学习与娱乐，开奖完全随机，历史无法预测未来。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="彩票数据分析助手",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header { font-size: 2.0rem; font-weight: 700; color: #e63946; text-align: center; }
    .sub-header { text-align: center; color: #666; margin-bottom: 1rem; }
    .disclaimer {
        background-color: #fff3cd; border-left: 5px solid #ffc107;
        padding: 10px 14px; margin: 10px 0; border-radius: 4px; font-size: 0.92rem;
    }
</style>
""", unsafe_allow_html=True)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ==================== 通用工具 ====================
def safe_get(url: str, timeout: int = 25) -> Optional[str]:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.content.decode("utf-8", errors="ignore")
    except Exception as e:
        st.warning(f"网络请求失败: {e}")
        return None


# ==================== 双色球 ====================
@st.cache_data(ttl=3600 * 6, show_spinner="加载双色球数据...")
def load_ssq(force: bool = False) -> pd.DataFrame:
    cache = DATA_DIR / "ssq_history.csv"
    if cache.exists() and not force:
        df = pd.read_csv(cache, dtype={"期号": str})
        df["开奖日期"] = pd.to_datetime(df["开奖日期"])
        return df.sort_values("期号").reset_index(drop=True)

    text = safe_get("https://data.17500.cn/ssq_asc.txt")
    if not text:
        if cache.exists():
            return pd.read_csv(cache, dtype={"期号": str})
        return pd.DataFrame()

    rows = []
    for line in text.strip().splitlines():
        p = line.split()
        if len(p) < 9:
            continue
        try:
            rows.append({
                "期号": p[0], "开奖日期": p[1],
                "红球1": int(p[2]), "红球2": int(p[3]), "红球3": int(p[4]),
                "红球4": int(p[5]), "红球5": int(p[6]), "红球6": int(p[7]),
                "蓝球": int(p[8]),
            })
        except ValueError:
            continue
    df = pd.DataFrame(rows)
    df["开奖日期"] = pd.to_datetime(df["开奖日期"])
    df = df.sort_values("期号").reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


def ssq_freq(df: pd.DataFrame, n: int):
    d = df.tail(n)
    reds = d[[f"红球{i}" for i in range(1, 7)]].values.flatten()
    return pd.Series(reds).value_counts().sort_index(), d["蓝球"].value_counts().sort_index()


def ssq_missing(df: pd.DataFrame):
    red_cols = [f"红球{i}" for i in range(1, 7)]
    red_m, blue_m = {}, {}
    for num in range(1, 34):
        mask = (df[red_cols] == num).any(axis=1)
        red_m[num] = (len(df) - 1 - mask[::-1].idxmax()) if mask.any() else len(df)
    for num in range(1, 17):
        mask = df["蓝球"] == num
        blue_m[num] = (len(df) - 1 - mask[::-1].idxmax()) if mask.any() else len(df)
    return pd.Series(red_m), pd.Series(blue_m)


# ==================== 快乐8（官方日开，20/80） ====================
@st.cache_data(ttl=3600 * 6, show_spinner="加载快乐8数据...")
def load_kl8(force: bool = False) -> pd.DataFrame:
    cache = DATA_DIR / "kl8_history.csv"
    if cache.exists() and not force:
        df = pd.read_csv(cache, dtype={"期号": str})
        df["开奖日期"] = pd.to_datetime(df["开奖日期"])
        return df.sort_values("期号").reset_index(drop=True)

    text = safe_get("https://data.17500.cn/kl8_asc.txt")
    if not text:
        if cache.exists():
            return pd.read_csv(cache, dtype={"期号": str})
        return pd.DataFrame()

    rows = []
    for line in text.strip().splitlines():
        p = line.split()
        if len(p) < 22:
            continue
        try:
            nums = [int(x) for x in p[2:22]]
            if len(nums) != 20:
                continue
            row = {"期号": p[0], "开奖日期": p[1]}
            for i, n in enumerate(nums, 1):
                row[f"号{i}"] = n
            rows.append(row)
        except ValueError:
            continue
    df = pd.DataFrame(rows)
    df["开奖日期"] = pd.to_datetime(df["开奖日期"])
    df = df.sort_values("期号").reset_index(drop=True)
    df.to_csv(cache, index=False)
    return df


def kl8_freq(df: pd.DataFrame, n: int) -> pd.Series:
    d = df.tail(n)
    cols = [c for c in d.columns if c.startswith("号")]
    all_nums = d[cols].values.flatten()
    return pd.Series(all_nums).value_counts().reindex(range(1, 81), fill_value=0)


def kl8_missing(df: pd.DataFrame) -> pd.Series:
    cols = [c for c in df.columns if c.startswith("号")]
    miss = {}
    for num in range(1, 81):
        mask = (df[cols] == num).any(axis=1)
        miss[num] = (len(df) - 1 - mask[::-1].idxmax()) if mask.any() else len(df)
    return pd.Series(miss)


def kl8_sum_stats(df: pd.DataFrame, n: int) -> pd.DataFrame:
    d = df.tail(n).copy()
    cols = [c for c in d.columns if c.startswith("号")]
    d["和值"] = d[cols].sum(axis=1)
    d["奇数个数"] = (d[cols] % 2 == 1).sum(axis=1)
    d["大号个数"] = (d[cols] > 40).sum(axis=1)  # 41-80 为大
    return d


# ==================== 极速飞艇 / PK10 风格 ====================
# 实时最新: https://api.api16868.com/pks/getLotteryPksInfo.do?lotCode=10037
# 历史列表: .../pks/getPksHistoryList.do?lotCode=10037&date=YYYY-MM-DD
FEITING_LOT_CODE = 10037

def fetch_feiting_latest() -> dict | None:
    """实时接口拉取最新一期"""
    url = f"https://api.api16868.com/pks/getLotteryPksInfo.do?lotCode={FEITING_LOT_CODE}"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        data = r.json()
        if data.get("errorCode") != 0:
            return None
        d = data.get("result", {}).get("data") or {}
        code = str(d.get("preDrawCode", ""))
        nums = [int(x) for x in code.split(",") if x.strip().isdigit()]
        if len(nums) != 10:
            return None
        return {
            "期号": str(d.get("preDrawIssue", "")),
            "开奖时间": str(d.get("drawTime") or d.get("preDrawTime", "")),
            "下期期号": str(d.get("drawIssue", "")),
            "下期时间": str(d.get("drawTime", "")),
            "冠军": nums[0], "亚军": nums[1], "第三": nums[2],
            "第四": nums[3], "第五": nums[4], "第六": nums[5],
            "第七": nums[6], "第八": nums[7], "第九": nums[8], "第十": nums[9],
            "冠亚和": nums[0] + nums[1],
            "服务器时间": str(d.get("serverTime", "")),
        }
    except Exception:
        return None


@st.cache_data(ttl=90, show_spinner="加载极速飞艇最近数据...")
def load_feiting(days: int = 3) -> pd.DataFrame:
    """历史按天拉取 + 合并实时最新一期。"""
    all_rows = []
    today = datetime.now().date()
    for i in range(days):
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        ok = False
        for base in ("https://api.api16868.com", "https://api.api68.com"):
            url = f"{base}/pks/getPksHistoryList.do?lotCode={FEITING_LOT_CODE}&date={day}"
            try:
                r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
                data = r.json()
                items = data.get("result", {}).get("data", [])
                if not items:
                    continue
                for it in items:
                    code = str(it.get("preDrawCode", ""))
                    nums = [int(x) for x in code.split(",") if x.strip().isdigit()]
                    if len(nums) != 10:
                        continue
                    all_rows.append({
                        "期号": str(it.get("preDrawIssue", "")),
                        "开奖时间": it.get("preDrawTime", ""),
                        "冠军": nums[0], "亚军": nums[1], "第三": nums[2],
                        "第四": nums[3], "第五": nums[4], "第六": nums[5],
                        "第七": nums[6], "第八": nums[7], "第九": nums[8], "第十": nums[9],
                        "冠亚和": nums[0] + nums[1],
                    })
                ok = True
                break
            except Exception:
                continue
        if not ok:
            continue
    latest = fetch_feiting_latest()
    if latest:
        all_rows.append({
            "期号": latest["期号"], "开奖时间": latest["开奖时间"],
            "冠军": latest["冠军"], "亚军": latest["亚军"], "第三": latest["第三"],
            "第四": latest["第四"], "第五": latest["第五"], "第六": latest["第六"],
            "第七": latest["第七"], "第八": latest["第八"], "第九": latest["第九"],
            "第十": latest["第十"], "冠亚和": latest["冠亚和"],
        })
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    df = df.drop_duplicates(subset=["期号"]).sort_values("期号").reset_index(drop=True)
    return df


# ==================== 极速快乐8 / Luck Twenty ====================
# 实时: https://api.api16868.com/LuckTwenty/getBaseLuckTewnty.do?lotCode=10047
KL8_SPEED_CODE = 10047

def fetch_kl8_speed_latest() -> dict | None:
    url = f"https://api.api16868.com/LuckTwenty/getBaseLuckTewnty.do?lotCode={KL8_SPEED_CODE}"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        data = r.json()
        if data.get("errorCode") != 0:
            return None
        d = data.get("result", {}).get("data") or {}
        code = str(d.get("preDrawCode", ""))
        nums = [int(x) for x in code.split(",") if x.strip().isdigit()][:20]
        if len(nums) < 20:
            return None
        return {
            "期号": str(d.get("preDrawIssue", "")),
            "开奖时间": str(d.get("preDrawTime", "")),
            "下期期号": str(d.get("drawIssue", "")),
            "下期时间": str(d.get("drawTime", "")),
            "号码": nums,
            "和值": int(d.get("sumNum") or sum(nums)),
            "服务器时间": str(d.get("serverTime", "")),
        }
    except Exception:
        return None


def feiting_pos_freq(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """各名次号码出现频率"""
    d = df.tail(n)
    pos_cols = ["冠军", "亚军", "第三", "第四", "第五", "第六", "第七", "第八", "第九", "第十"]
    records = []
    for pos in pos_cols:
        vc = d[pos].value_counts().reindex(range(1, 11), fill_value=0)
        for num, cnt in vc.items():
            records.append({"名次": pos, "号码": num, "次数": cnt})
    return pd.DataFrame(records)


def feiting_champion_stats(df: pd.DataFrame, n: int):
    d = df.tail(n)
    champ_freq = d["冠军"].value_counts().sort_index()
    gy_sum = d["冠亚和"].value_counts().sort_index()
    return champ_freq, gy_sum


def feiting_dx_sequence(df: pd.DataFrame) -> list[str]:
    """冠亚和大小序列：大=冠亚和>11，小=≤11"""
    return ["大" if int(x) > 11 else "小" for x in df["冠亚和"].tolist()]


def luzhu_after_pattern(seq: list[str], pattern: list[str]) -> dict:
    """路珠：某形态之后下一期是大/小的次数"""
    n = len(pattern)
    from collections import Counter
    nexts = []
    for i in range(len(seq) - n):
        if seq[i : i + n] == pattern:
            nexts.append(seq[i + n])
    c = Counter(nexts)
    total = sum(c.values())
    return {
        "大": c.get("大", 0),
        "小": c.get("小", 0),
        "total": total,
        "大%": round(c.get("大", 0) / total * 100, 2) if total else 0,
        "小%": round(c.get("小", 0) / total * 100, 2) if total else 0,
    }


def parse_dx_pattern(text: str) -> list[str] | None:
    """解析用户输入的大小形态，如 大大大小小 或 大,大,大,小,小"""
    t = text.strip().replace("，", "").replace(",", "").replace(" ", "").replace("　", "")
    if not t or any(c not in "大小" for c in t):
        return None
    return list(t)


# ==================== 五码组合历史对照 ====================
def count_combo_hits_kl8(df: pd.DataFrame, nums: list[int], n: int | None = None) -> tuple[int, int, list]:
    """统计快乐8中，指定5个号码全部出现在开奖20码中的期数。返回 (命中期数, 总期数, 命中期号列表)"""
    if n:
        df = df.tail(n)
    cols = [c for c in df.columns if c.startswith("号")]
    target = set(nums)
    hits = []
    for _, row in df.iterrows():
        drawn = set(int(row[c]) for c in cols)
        if target.issubset(drawn):
            hits.append(str(row["期号"]))
    return len(hits), len(df), hits


def count_combo_hits_ssq(df: pd.DataFrame, nums: list[int], n: int | None = None) -> tuple[int, int, list]:
    """统计双色球中，指定5个红球号码全部出现在当期6个红球中的期数。"""
    if n:
        df = df.tail(n)
    red_cols = [f"红球{i}" for i in range(1, 7)]
    target = set(nums)
    hits = []
    for _, row in df.iterrows():
        drawn = set(int(row[c]) for c in red_cols)
        if target.issubset(drawn):
            hits.append(str(row["期号"]))
    return len(hits), len(df), hits


def suggest_combos_by_freq(freq: pd.Series, k: int = 5, n_groups: int = 10) -> list[list[int]]:
    """根据单号频率加权，随机生成若干组 k 个号码（仅供对照参考）。"""
    nums = freq.index.tolist()
    weights = freq.values.astype(float)
    weights = weights / weights.sum()
    rng = np.random.default_rng()
    groups = []
    for _ in range(n_groups * 3):  # 多抽一些去重
        chosen = sorted(rng.choice(nums, size=k, replace=False, p=weights).tolist())
        if chosen not in groups:
            groups.append(chosen)
        if len(groups) >= n_groups:
            break
    return groups


# ==================== 主界面 ====================
st.markdown('<div class="main-header">🎱 彩票 AI 数据分析助手</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">双色球 · 快乐8 · 极速飞艇 | 仅供学习娱乐</div>', unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer">
⚠️ <b>重要声明</b>：所有彩票开奖均为随机事件，历史数据无法预测未来。
本工具只做统计与可视化，不提供任何“中奖保证”。请理性对待，量力而行。
极速类高频彩种数据来自第三方接口，仅供参考。
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 设置")
    lottery = st.selectbox(
        "选择彩种",
        ["双色球", "快乐8（官方）", "极速飞艇（PK10）", "极速快乐8"],
        index=0,
    )
    force_refresh = st.button("🔄 强制刷新数据")
    n_recent = st.slider("分析最近期数", 30, 500, 100, 10)
    if lottery in ("极速飞艇（PK10）", "极速快乐8"):
        ft_days = st.slider("拉取最近几天数据", 1, 7, 5) if lottery == "极速飞艇（PK10）" else 1
        auto_refresh = st.checkbox("⏱ 自动刷新开奖（约每 45 秒）", value=False)
        if auto_refresh:
            st.caption("开启后页面会定时重新拉取最新开奖")
    else:
        auto_refresh = False
        ft_days = 3
    st.markdown("---")
    st.caption("双色球/官方快乐8：data.17500.cn")
    st.caption("极速飞艇：api.api16868.com/pks")
    st.caption("极速快乐8：api.api16868.com/LuckTwenty")

# ---------- 双色球 ----------
if lottery == "双色球":
    df = load_ssq(force_refresh)
    if df.empty:
        st.error("双色球数据加载失败")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    latest = df.iloc[-1]
    c1.metric("总期数", f"{len(df):,}")
    c2.metric("最新期号", latest["期号"])
    c3.metric("开奖日", latest["开奖日期"].strftime("%Y-%m-%d"))
    reds = " ".join(f"{latest[f'红球{i}']:02d}" for i in range(1, 7))
    c4.metric("开奖号码", f"{reds} + {latest['蓝球']:02d}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 频率", "📉 遗漏", "📈 走势", "🎯 五码对照", "📋 历史"])

    with tab1:
        rf, bf = ssq_freq(df, n_recent)
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(x=rf.index, y=rf.values, title=f"红球频率（近{n_recent}期）",
                         labels={"x": "号码", "y": "次数"}, color=rf.values, color_continuous_scale="Reds")
            st.plotly_chart(fig, use_container_width=True)
            st.write("热号:", " ".join(f"`{i:02d}`" for i in rf.nlargest(6).index))
            st.write("冷号:", " ".join(f"`{i:02d}`" for i in rf.nsmallest(6).index))
        with col2:
            fig = px.bar(x=bf.index, y=bf.values, title="蓝球频率",
                         labels={"x": "号码", "y": "次数"}, color=bf.values, color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        rm, bm = ssq_missing(df)
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(x=rm.index, y=rm.values, title="红球当前遗漏", color=rm.values, color_continuous_scale="OrRd")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(x=bm.index, y=bm.values, title="蓝球当前遗漏", color=bm.values, color_continuous_scale="PuBu")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        red_cols = [f"红球{i}" for i in range(1, 7)]
        recent = df.tail(n_recent).copy()
        recent["和值"] = recent[red_cols].sum(axis=1)
        fig = px.line(recent, x="期号", y="和值", title="红球和值走势", markers=True)
        fig.add_hline(y=recent["和值"].mean(), line_dash="dash")
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("五码组合 · 历史对照")
        st.warning("以下为历史出现次数统计，**不是**未来中奖概率。每期开奖独立，请勿当作预测依据。")
        st.caption("统计：你选的 5 个红球，在历史（或近 N 期）中，有多少期「这 5 个全部出现在当期 6 个红球里」。")

        scope = st.radio("统计范围", ["全部历史", f"近 {n_recent} 期"], horizontal=True, key="ssq_combo_scope")
        use_n = None if scope == "全部历史" else n_recent

        user_input = st.text_input("输入 5 个红球号码（空格或逗号分隔，如 03 08 15 22 29）", key="ssq_combo_input")
        if st.button("查询历史命中", key="ssq_combo_btn") and user_input.strip():
            try:
                parts = user_input.replace("，", ",").replace(" ", ",").split(",")
                nums = sorted(set(int(x.strip()) for x in parts if x.strip()))
                if len(nums) != 5 or any(n < 1 or n > 33 for n in nums):
                    st.error("请输入恰好 5 个不重复的红球号码（1-33）")
                else:
                    hits, total, hit_list = count_combo_hits_ssq(df, nums, use_n)
                    rate = hits / total * 100 if total else 0
                    st.success(f"号码 {' '.join(f'{n:02d}' for n in nums)}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("历史命中期数", hits)
                    c2.metric("统计总期数", total)
                    c3.metric("历史出现率", f"{rate:.4f}%")
                    st.caption("理论随机期望：C(28,1)/C(33,6) ≈ 约 1.8%（每期这 5 个全中的概率）")
                    if hit_list:
                        st.write("命中期号（最多显示 20 个）：", "、".join(hit_list[-20:]))
            except ValueError:
                st.error("号码格式不正确")

        st.markdown("---")
        st.write("**基于近期频率的参考五码组合**（按单号出现次数加权随机生成，仅供对照）")
        if st.button("生成参考组合", key="ssq_suggest"):
            rf, _ = ssq_freq(df, n_recent)
            groups = suggest_combos_by_freq(rf, k=5, n_groups=8)
            rows = []
            for g in groups:
                h, t, _ = count_combo_hits_ssq(df, g, n_recent)
                rows.append({
                    "五码组合": " ".join(f"{x:02d}" for x in g),
                    "近N期命中": h,
                    "近N期出现率%": round(h / t * 100, 4) if t else 0,
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with tab5:
        st.dataframe(df.tail(30).iloc[::-1], use_container_width=True, height=400)
        st.download_button("下载全部CSV", df.to_csv(index=False).encode("utf-8-sig"),
                           f"ssq_{datetime.now():%Y%m%d}.csv", "text/csv")

# ---------- 快乐8 ----------
elif lottery == "快乐8（官方）":
    df = load_kl8(force_refresh)
    if df.empty:
        st.error("快乐8数据加载失败")
        st.stop()

    c1, c2, c3 = st.columns(3)
    latest = df.iloc[-1]
    c1.metric("总期数", f"{len(df):,}")
    c2.metric("最新期号", latest["期号"])
    c3.metric("开奖日", latest["开奖日期"].strftime("%Y-%m-%d"))
    nums = " ".join(f"{latest[f'号{i}']:02d}" for i in range(1, 21))
    st.info(f"最新开奖号码（20个）：{nums}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 频率热冷", "📉 遗漏", "📈 和值/奇偶/大小", "🎯 五码对照", "📋 历史"])

    with tab1:
        freq = kl8_freq(df, n_recent)
        fig = px.bar(x=freq.index, y=freq.values, title=f"1-80 号码频率（近{n_recent}期）",
                     labels={"x": "号码", "y": "出现次数"}, color=freq.values, color_continuous_scale="Viridis")
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            st.write("**热号 Top10**", "  ".join(f"`{i:02d}`({c})" for i, c in freq.nlargest(10).items()))
        with col2:
            st.write("**冷号 Top10**", "  ".join(f"`{i:02d}`({c})" for i, c in freq.nsmallest(10).items()))

    with tab2:
        miss = kl8_missing(df)
        fig = px.bar(x=miss.index, y=miss.values, title="当前遗漏期数", color=miss.values, color_continuous_scale="YlOrRd")
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
        st.write("**最长遗漏 Top10**", "  ".join(f"`{i:02d}`({m}期)" for i, m in miss.nlargest(10).items()))

    with tab3:
        stats = kl8_sum_stats(df, n_recent)
        fig = px.line(stats, x="期号", y="和值", title="20码和值走势", markers=True)
        fig.add_hline(y=stats["和值"].mean(), line_dash="dash", annotation_text=f"均值{stats['和值'].mean():.0f}")
        st.plotly_chart(fig, use_container_width=True)
        c1, c2 = st.columns(2)
        with c1:
            oe = stats["奇数个数"].value_counts().sort_index()
            fig = px.bar(x=oe.index, y=oe.values, title="奇数个数分布", labels={"x": "奇数个数", "y": "期数"})
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            big = stats["大号个数"].value_counts().sort_index()
            fig = px.bar(x=big.index, y=big.values, title="大号(41-80)个数分布", labels={"x": "大号个数", "y": "期数"})
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("五码组合 · 历史对照（对应快乐8「选五」）")
        st.warning("以下为历史出现次数统计，**不是**未来中奖概率。每期开奖独立，请勿当作预测依据。")
        st.caption("统计：你选的 5 个号码，在历史（或近 N 期）中，有多少期「这 5 个全部出现在当期开出的 20 个号码里」。")

        scope = st.radio("统计范围", ["全部历史", f"近 {n_recent} 期"], horizontal=True, key="kl8_combo_scope")
        use_n = None if scope == "全部历史" else n_recent

        user_input = st.text_input("输入 5 个号码（空格或逗号分隔，如 05 12 28 45 67）", key="kl8_combo_input")
        if st.button("查询历史命中", key="kl8_combo_btn") and user_input.strip():
            try:
                parts = user_input.replace("，", ",").replace(" ", ",").split(",")
                nums = sorted(set(int(x.strip()) for x in parts if x.strip()))
                if len(nums) != 5 or any(n < 1 or n > 80 for n in nums):
                    st.error("请输入恰好 5 个不重复的号码（1-80）")
                else:
                    hits, total, hit_list = count_combo_hits_kl8(df, nums, use_n)
                    rate = hits / total * 100 if total else 0
                    st.success(f"号码 {' '.join(f'{n:02d}' for n in nums)}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("历史命中期数", hits)
                    c2.metric("统计总期数", total)
                    c3.metric("历史出现率", f"{rate:.4f}%")
                    # 理论：C(75,15)/C(80,20) = 选五全中的概率
                    st.caption("理论随机期望（选五全中）：约 0.32% 左右（每期）")
                    if hit_list:
                        st.write("命中期号（最多显示 20 个）：", "、".join(hit_list[-20:]))
            except ValueError:
                st.error("号码格式不正确")

        st.markdown("---")
        st.write("**基于近期频率的参考五码组合**（按单号出现次数加权随机生成，并对照近 N 期命中次数）")
        if st.button("生成参考组合", key="kl8_suggest"):
            freq = kl8_freq(df, n_recent)
            # 只对出现过的号加权
            freq = freq[freq > 0]
            groups = suggest_combos_by_freq(freq, k=5, n_groups=10)
            rows = []
            for g in groups:
                h, t, _ = count_combo_hits_kl8(df, g, n_recent)
                rows.append({
                    "五码组合": " ".join(f"{x:02d}" for x in g),
                    "近N期命中": h,
                    "近N期出现率%": round(h / t * 100, 4) if t else 0,
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            st.caption("出现率高只说明过去凑巧一起出过，不代表下一期更容易出。")

    with tab5:
        show_cols = ["期号", "开奖日期"] + [f"号{i}" for i in range(1, 21)]
        st.dataframe(df.tail(20)[show_cols].iloc[::-1], use_container_width=True, height=400)
        st.download_button("下载全部CSV", df.to_csv(index=False).encode("utf-8-sig"),
                           f"kl8_{datetime.now():%Y%m%d}.csv", "text/csv")

# ---------- 极速飞艇 ----------
elif lottery == "极速飞艇（PK10）":
    # 自动刷新
    if auto_refresh:
        try:
            st_autorefresh = getattr(st, "fragment", None)
            # Streamlit 1.33+ 可用 st.fragment(run_every=...)
            pass
        except Exception:
            pass
        # 兼容写法：使用 meta 刷新 + 清空缓存提示
        st.markdown(
            '<meta http-equiv="refresh" content="45">',
            unsafe_allow_html=True,
        )
        st.info("⏱ 已开启自动刷新（约每 45 秒重新拉取最新开奖）。关闭侧边栏勾选可停止。")
        # 强制不走太久缓存
        load_feiting.clear()

    if force_refresh or auto_refresh:
        try:
            load_feiting.clear()
        except Exception:
            pass
    df = load_feiting(ft_days)
    if df.empty:
        st.error("极速飞艇数据加载失败，请稍后重试或检查网络")
        st.stop()

    rt = fetch_feiting_latest()
    c1, c2, c3, c4 = st.columns(4)
    latest = df.iloc[-1]
    c1.metric("已加载期数", f"{len(df):,}")
    c2.metric("最新期号", latest["期号"])
    c3.metric("开奖时间", str(latest["开奖时间"])[:19])
    gy = int(latest["冠亚和"])
    dx_now = "大" if gy > 11 else "小"
    c4.metric("冠亚和 / 大小", f"{gy} / {dx_now}")
    nums = " ".join(f"{latest[p]:02d}" for p in ["冠军", "亚军", "第三", "第四", "第五", "第六", "第七", "第八", "第九", "第十"])
    st.info(f"最新开奖：{nums}")
    if rt:
        st.caption(f"实时接口 · 下期 {rt.get('下期期号','')} · 服务器时间 {rt.get('服务器时间','')}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 各名次频率", "🏆 冠军 & 冠亚和", "🐉 龙虎/基本形态", "🔴 路珠查询", "📋 历史"
    ])

    with tab1:
        pos_df = feiting_pos_freq(df, min(n_recent, len(df)))
        fig = px.density_heatmap(
            pos_df, x="号码", y="名次", z="次数",
            title=f"各名次号码出现热力（近{min(n_recent, len(df))}期）",
            color_continuous_scale="YlOrRd",
        )
        fig.update_layout(height=480)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        champ, gy_s = feiting_champion_stats(df, min(n_recent, len(df)))
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(x=champ.index, y=champ.values, title="冠军号码频率",
                         labels={"x": "号码", "y": "次数"}, color=champ.values, color_continuous_scale="Reds")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.bar(x=gy_s.index, y=gy_s.values, title="冠亚和分布",
                         labels={"x": "冠亚和", "y": "次数"}, color=gy_s.values, color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)
        st.write("冠军热号:", " ".join(f"`{i}`" for i in champ.nlargest(3).index))
        st.write("冠亚和热值:", " ".join(f"`{i}`" for i in gy_s.nlargest(5).index))

    with tab3:
        d = df.tail(min(n_recent, len(df))).copy()
        d["龙虎"] = np.where(d["冠军"] > d["第十"], "龙", "虎")
        lt = d["龙虎"].value_counts()
        c1, c2 = st.columns(2)
        with c1:
            fig = px.pie(values=lt.values, names=lt.index, title="冠军 vs 第十（龙虎）")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            d["冠亚大小"] = np.where(d["冠亚和"] > 11, "大", "小")
            bs = d["冠亚大小"].value_counts()
            fig = px.pie(values=bs.values, names=bs.index, title="冠亚和大小（>11为大）")
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("冠亚和 · 大小路珠查询")
        st.warning("路珠只是历史形态统计，**不能预测**下一期。每期独立随机，请勿当作投注依据。")
        st.caption("规则：冠亚和 > 11 为「大」，≤ 11 为「小」。")

        seq = feiting_dx_sequence(df)
        base_da = seq.count("大")
        base_xiao = seq.count("小")
        base_total = len(seq)

        # 最近路珠展示
        recent_n = st.slider("显示最近路珠期数", 20, 100, 40, key="luzhu_show_n")
        recent_seq = seq[-recent_n:]
        # 用彩色标签展示
        colored = " ".join(
            f'<span style="color:{"#e63946" if x=="大" else "#457b9d"};font-weight:700">{x}</span>'
            for x in recent_seq
        )
        st.markdown(f"**最近 {recent_n} 期大小：** {colored}", unsafe_allow_html=True)
        st.write(f"当前末尾形态（最近 5 期）：**{''.join(seq[-5:])}**  → 最新一期是 **{seq[-1]}**")

        st.markdown("---")
        st.write("**基础比例（全部已加载数据）**")
        bc1, bc2, bc3 = st.columns(3)
        bc1.metric("大", f"{base_da} 期", f"{base_da/base_total*100:.1f}%")
        bc2.metric("小", f"{base_xiao} 期", f"{base_xiao/base_total*100:.1f}%")
        bc3.metric("总期数", base_total)

        st.markdown("---")
        st.write("**按形态查询：出现某串大小之后，下一期是大/小的历史比例**")
        # 快捷：用当前末尾
        use_tail = st.checkbox("使用当前末尾 5 期作为查询形态", value=True, key="luzhu_use_tail")
        if use_tail and len(seq) >= 5:
            default_pat = "".join(seq[-5:])
        else:
            default_pat = "大大大小小"
        pat_text = st.text_input("输入形态（只含「大」「小」，如 大大大小小）", value=default_pat, key="luzhu_pat")

        if st.button("查询该形态后的下一期比例", key="luzhu_btn"):
            pattern = parse_dx_pattern(pat_text)
            if not pattern:
                st.error("请只输入「大」和「小」组成的字符串")
            else:
                result = luzhu_after_pattern(seq, pattern)
                st.success(f"形态：**{''.join(pattern)}** 在历史中共出现后接一期 **{result['total']}** 次")
                if result["total"] == 0:
                    st.info("该形态在当前数据中未出现过（或出现在最后一期，无下一期）")
                else:
                    r1, r2 = st.columns(2)
                    r1.metric("下一期是「大」", f"{result['大']} 次", f"{result['大%']}%")
                    r2.metric("下一期是「小」", f"{result['小']} 次", f"{result['小%']}%")
                    fig = px.pie(
                        values=[result["大"], result["小"]],
                        names=["大", "小"],
                        title=f"形态「{''.join(pattern)}」之后下一期分布",
                        color_discrete_map={"大": "#e63946", "小": "#457b9d"},
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption(
                        f"对照：全体基础比例 大 {base_da/base_total*100:.1f}% / 小 {base_xiao/base_total*100:.1f}%。"
                        "历史比例接近基础比例是正常的，不代表下一期更可能开某一边。"
                    )

        # 常用短形态一览
        st.markdown("---")
        st.write("**常用短形态速查（最近数据）**")
        quick_pats = ["大", "小", "大大", "小小", "大小", "小大", "大大大", "小小小"]
        qrows = []
        for p in quick_pats:
            r = luzhu_after_pattern(seq, list(p))
            if r["total"] > 0:
                qrows.append({
                    "形态": p,
                    "样本数": r["total"],
                    "下期大%": r["大%"],
                    "下期小%": r["小%"],
                })
        if qrows:
            st.dataframe(pd.DataFrame(qrows), use_container_width=True)

    with tab5:
        show_cols = ["期号", "开奖时间", "冠军", "亚军", "第三", "第四", "第五",
                     "第六", "第七", "第八", "第九", "第十", "冠亚和"]
        show_df = df.tail(50)[show_cols].copy()
        show_df["大小"] = show_df["冠亚和"].apply(lambda x: "大" if int(x) > 11 else "小")
        st.dataframe(show_df.iloc[::-1], use_container_width=True, height=400)
        st.download_button("下载当前数据CSV", df.to_csv(index=False).encode("utf-8-sig"),
                           f"feiting_{datetime.now():%Y%m%d}.csv", "text/csv")

# ---------- 极速快乐8（Luck Twenty 20码） ----------
elif lottery == "极速快乐8":
    if auto_refresh:
        st.markdown('<meta http-equiv="refresh" content="45">', unsafe_allow_html=True)
        st.info("⏱ 已开启自动刷新（约每 45 秒）。关闭侧边栏勾选可停止。")

    latest = fetch_kl8_speed_latest()
    if not latest:
        st.error("极速快乐8 实时数据获取失败，请稍后重试")
        st.stop()

    c1, c2, c3 = st.columns(3)
    c1.metric("最新期号", latest["期号"])
    c2.metric("开奖时间", str(latest["开奖时间"])[:19])
    c3.metric("和值", latest["和值"])
    nums_str = " ".join(f"{n:02d}" for n in latest["号码"])
    st.info(f"最新开奖（20码）：{nums_str}")
    st.caption(f"下期 {latest.get('下期期号','')} · 预计 {latest.get('下期时间','')} · 服务器 {latest.get('服务器时间','')}")

    st.warning("极速快乐8 目前主要提供实时最新一期。完整历史路珠需自行积累或接入历史接口。以下为当期号码分析。")

    nums = latest["号码"]
    # 单期分析
    odd_cnt = sum(1 for x in nums if x % 2 == 1)
    big_cnt = sum(1 for x in nums if x > 40)
    col1, col2, col3 = st.columns(3)
    col1.metric("奇数个数", f"{odd_cnt} / 20")
    col2.metric("大号(41-80)个数", f"{big_cnt} / 20")
    col3.metric("和值", latest["和值"])

    # 简单区间分布
    zones = {"1-20": 0, "21-40": 0, "41-60": 0, "61-80": 0}
    for n in nums:
        if n <= 20:
            zones["1-20"] += 1
        elif n <= 40:
            zones["21-40"] += 1
        elif n <= 60:
            zones["41-60"] += 1
        else:
            zones["61-80"] += 1
    fig = px.bar(x=list(zones.keys()), y=list(zones.values()), title="当期号码区间分布",
                 labels={"x": "区间", "y": "个数"}, color=list(zones.values()), color_continuous_scale="Teal")
    st.plotly_chart(fig, use_container_width=True)

    st.write("**当期号码列表**")
    st.code(nums_str)

    if st.button("立即刷新最新一期"):
        st.rerun()

st.markdown("---")
st.caption("仅供学习与数据分析练习 | 请理性购彩，远离赌博心态")
