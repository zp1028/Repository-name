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
@st.cache_data(ttl=1800, show_spinner="加载极速飞艇最近数据...")
def load_feiting(days: int = 3) -> pd.DataFrame:
    """拉取最近几天的极速飞艇(PK10)数据。lotCode=10037 为常见极速飞艇代码。"""
    all_rows = []
    today = datetime.now().date()
    for i in range(days):
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        url = f"https://api.api68.com/pks/getPksHistoryList.do?lotCode=10037&date={day}"
        try:
            r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            data = r.json()
            items = data.get("result", {}).get("data", [])
            for it in items:
                code = str(it.get("preDrawCode", ""))
                nums = [int(x) for x in code.split(",") if x.strip().isdigit()]
                if len(nums) != 10:
                    continue
                row = {
                    "期号": str(it.get("preDrawIssue", "")),
                    "开奖时间": it.get("preDrawTime", ""),
                    "冠军": nums[0], "亚军": nums[1], "第三": nums[2],
                    "第四": nums[3], "第五": nums[4], "第六": nums[5],
                    "第七": nums[6], "第八": nums[7], "第九": nums[8], "第十": nums[9],
                    "冠亚和": nums[0] + nums[1],
                }
                all_rows.append(row)
        except Exception:
            continue
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    df = df.drop_duplicates(subset=["期号"]).sort_values("期号").reset_index(drop=True)
    return df


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
        ["双色球", "快乐8（官方）", "极速飞艇（PK10）"],
        index=0,
    )
    force_refresh = st.button("🔄 强制刷新数据")
    n_recent = st.slider("分析最近期数", 30, 500, 100, 10)
    if lottery == "极速飞艇（PK10）":
        ft_days = st.slider("拉取最近几天数据", 1, 7, 3)
    st.markdown("---")
    st.caption("双色球/快乐8 数据源：data.17500.cn")
    st.caption("极速飞艇 数据源：api.api68.com（第三方）")

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

    tab1, tab2, tab3, tab4 = st.tabs(["📊 频率", "📉 遗漏", "📈 走势", "📋 历史"])

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

    tab1, tab2, tab3, tab4 = st.tabs(["📊 频率热冷", "📉 遗漏", "📈 和值/奇偶/大小", "📋 历史"])

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
        show_cols = ["期号", "开奖日期"] + [f"号{i}" for i in range(1, 21)]
        st.dataframe(df.tail(20)[show_cols].iloc[::-1], use_container_width=True, height=400)
        st.download_button("下载全部CSV", df.to_csv(index=False).encode("utf-8-sig"),
                           f"kl8_{datetime.now():%Y%m%d}.csv", "text/csv")

# ---------- 极速飞艇 ----------
else:
    df = load_feiting(ft_days)
    if df.empty:
        st.error("极速飞艇数据加载失败，请稍后重试或检查网络")
        st.stop()

    c1, c2, c3 = st.columns(3)
    latest = df.iloc[-1]
    c1.metric("已加载期数", f"{len(df):,}")
    c2.metric("最新期号", latest["期号"])
    c3.metric("开奖时间", str(latest["开奖时间"])[:16])
    nums = " ".join(f"{latest[p]:02d}" for p in ["冠军", "亚军", "第三", "第四", "第五", "第六", "第七", "第八", "第九", "第十"])
    st.info(f"最新开奖：{nums}  |  冠亚和 = {latest['冠亚和']}")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 各名次频率", "🏆 冠军 & 冠亚和", "🐉 龙虎/基本形态", "📋 历史"])

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
        champ, gy = feiting_champion_stats(df, min(n_recent, len(df)))
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(x=champ.index, y=champ.values, title="冠军号码频率",
                         labels={"x": "号码", "y": "次数"}, color=champ.values, color_continuous_scale="Reds")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.bar(x=gy.index, y=gy.values, title="冠亚和分布",
                         labels={"x": "冠亚和", "y": "次数"}, color=gy.values, color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)
        st.write("冠军热号:", " ".join(f"`{i}`" for i in champ.nlargest(3).index))
        st.write("冠亚和热值:", " ".join(f"`{i}`" for i in gy.nlargest(5).index))

    with tab3:
        d = df.tail(min(n_recent, len(df))).copy()
        # 简单龙虎：冠军 vs 第十
        d["龙虎"] = np.where(d["冠军"] > d["第十"], "龙", "虎")
        lt = d["龙虎"].value_counts()
        c1, c2 = st.columns(2)
        with c1:
            fig = px.pie(values=lt.values, names=lt.index, title="冠军 vs 第十（龙虎）")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            # 冠亚和大小（通常 >11 为大）
            d["冠亚大小"] = np.where(d["冠亚和"] > 11, "大", "小")
            bs = d["冠亚大小"].value_counts()
            fig = px.pie(values=bs.values, names=bs.index, title="冠亚和大小（>11为大）")
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        show_cols = ["期号", "开奖时间", "冠军", "亚军", "第三", "第四", "第五",
                     "第六", "第七", "第八", "第九", "第十", "冠亚和"]
        st.dataframe(df.tail(50)[show_cols].iloc[::-1], use_container_width=True, height=400)
        st.download_button("下载当前数据CSV", df.to_csv(index=False).encode("utf-8-sig"),
                           f"feiting_{datetime.now():%Y%m%d}.csv", "text/csv")

st.markdown("---")
st.caption("仅供学习与数据分析练习 | 请理性购彩，远离赌博心态")
