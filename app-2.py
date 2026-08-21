# -*- coding: utf-8 -*-
"""
彩票 AI 数据分析助手 - 极速系列（api.api16868.com）
仅供学习娱乐，开奖随机，历史无法预测未来。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
import time

st.set_page_config(page_title="极速彩数据分析", page_icon="🎱", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
  .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1200px; }
  [data-testid="stSidebar"] { background: linear-gradient(180deg, #1d3557 0%, #0d1b2a 100%); }
  [data-testid="stSidebar"] * { color: #f1faee !important; }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stSlider label,
  [data-testid="stSidebar"] .stCheckbox label { color: #f1faee !important; }
  [data-testid="stSidebar"] [data-baseweb="select"] > div { background: #1b263b; color: #fff; }
  .main-header {
    font-size: 1.85rem; font-weight: 800; text-align: center;
    background: linear-gradient(90deg, #e63946, #f4a261);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 0.15rem;
  }
  .sub-header { text-align: center; color: #6c757d; font-size: 0.95rem; margin-bottom: 0.8rem; }
  .disclaimer {
    background: linear-gradient(90deg, #fff3cd, #ffe8a1);
    border-left: 5px solid #e9a825;
    padding: 12px 16px; margin: 8px 0 16px; border-radius: 8px;
    font-size: 0.9rem; color: #5c4a00; line-height: 1.5;
  }
  .num-ball {
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 2rem; height: 2rem; padding: 0 0.35rem; margin: 0 3px 4px;
    border-radius: 50%; font-weight: 700; font-size: 0.85rem;
    color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.15);
  }
  .num-ball.gold { background: linear-gradient(145deg, #f4a261, #e76f51); }
  .num-ball.green { background: linear-gradient(145deg, #2a9d8f, #1b7a6e); }
  .draw-line {
    background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 12px;
    padding: 12px 14px; margin: 8px 0 12px; text-align: center; line-height: 2.2;
  }
  .tag-combo {
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    font-weight: 700; font-size: 0.9rem; color: #fff;
    background: linear-gradient(90deg, #e63946, #f4a261);
  }
  [data-testid="stMetric"] {
    background: #f8f9fa; border-radius: 10px; padding: 10px 12px; border: 1px solid #eef1f4;
  }
  .stTabs [data-baseweb="tab-list"] { gap: 6px; background: #f1f3f5; padding: 6px; border-radius: 10px; }
  .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 14px; font-weight: 600; }
  .stTabs [aria-selected="true"] { background: #fff !important; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  @media (max-width: 768px) {
    .main-header { font-size: 1.45rem; }
    .num-ball { min-width: 1.75rem; height: 1.75rem; font-size: 0.78rem; }
  }
  .footer-note {
    text-align: center; color: #adb5bd; font-size: 0.82rem;
    margin-top: 1.5rem; padding-top: 0.8rem; border-top: 1px solid #e9ecef;
  }
</style>
""", unsafe_allow_html=True)

# ==================== 彩种目录（API 实测可用） ====================
# type: pks = 10名次赛车/飞艇 | luck20 = 20码快乐8风格
LOTTERY_CATALOG = [
    {"key": "10037", "name": "极速飞艇", "type": "pks", "code": 10037},
    {"key": "10035", "name": "极速赛车", "type": "pks", "code": 10035},
    {"key": "10012", "name": "幸运飞艇", "type": "pks", "code": 10012},
    {"key": "10058", "name": "PK拾(10058)", "type": "pks", "code": 10058},
    {"key": "10057", "name": "澳洲幸运10", "type": "pks", "code": 10057},
    {"key": "10047", "name": "极速快乐8", "type": "luck20", "code": 10047},
    {"key": "10054", "name": "幸运20", "type": "luck20", "code": 10054},
]

API_BASE = "https://api.api16868.com"
API_BASE_ALT = "https://api.api68.com"
POS_COLS = ["冠军", "亚军", "第三", "第四", "第五", "第六", "第七", "第八", "第九", "第十"]


def balls_html(nums, color="gold"):
    return "".join(f'<span class="num-ball {color}">{int(n):02d}</span>' for n in nums)


def draw_box(html_inner: str):
    st.markdown(f'<div class="draw-line">{html_inner}</div>', unsafe_allow_html=True)


def safe_json_get(url, timeout=15, retries=2):
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == retries:
                return None
            time.sleep(0.8)
    return None


def parse_pattern(text, allowed_chars):
    t = text.strip().replace("，", "").replace(",", "").replace(" ", "").replace("　", "")
    if not t or any(c not in allowed_chars for c in t):
        return None
    return list(t)


def luzhu_after_pattern(seq, pattern):
    n = len(pattern)
    nexts = []
    for i in range(len(seq) - n):
        if seq[i:i + n] == pattern:
            nexts.append(seq[i + n])
    c = Counter(nexts)
    total = sum(c.values())
    out = {"total": total, "counter": dict(c)}
    for k, v in c.items():
        out[k] = v
        out[f"{k}%"] = round(v / total * 100, 2) if total else 0
    return out


# ==================== PK10 / 飞艇 ====================
def fetch_pks_latest(lot_code: int):
    url = f"{API_BASE}/pks/getLotteryPksInfo.do?lotCode={lot_code}"
    data = safe_json_get(url)
    if not data or data.get("errorCode") != 0:
        return None
    d = data.get("result", {}).get("data") or {}
    code = str(d.get("preDrawCode", ""))
    nums = [int(x) for x in code.split(",") if x.strip().isdigit()]
    if len(nums) != 10:
        return None
    row = {
        "期号": str(d.get("preDrawIssue", "")),
        "开奖时间": str(d.get("drawTime") or d.get("preDrawTime", "")),
        "下期期号": str(d.get("drawIssue", "")),
        "下期时间": str(d.get("drawTime", "")),
        "服务器时间": str(d.get("serverTime", "")),
        "冠亚和": nums[0] + nums[1],
    }
    for i, name in enumerate(POS_COLS):
        row[name] = nums[i]
    return row


@st.cache_data(ttl=90, show_spinner="加载历史数据...")
def load_pks(lot_code: int, days: int = 3) -> pd.DataFrame:
    all_rows = []
    today = datetime.now().date()
    for i in range(days):
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for base in (API_BASE, API_BASE_ALT):
            url = f"{base}/pks/getPksHistoryList.do?lotCode={lot_code}&date={day}"
            data = safe_json_get(url)
            if not data:
                continue
            items = data.get("result", {}).get("data", [])
            if not items:
                continue
            for it in items:
                code = str(it.get("preDrawCode", ""))
                nums = [int(x) for x in code.split(",") if x.strip().isdigit()]
                if len(nums) != 10:
                    continue
                row = {
                    "期号": str(it.get("preDrawIssue", "")),
                    "开奖时间": it.get("preDrawTime", ""),
                    "冠亚和": nums[0] + nums[1],
                }
                for j, name in enumerate(POS_COLS):
                    row[name] = nums[j]
                all_rows.append(row)
            break
    latest = fetch_pks_latest(lot_code)
    if latest:
        all_rows.append({k: latest[k] for k in ["期号", "开奖时间", "冠亚和"] + POS_COLS if k in latest})
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    return df.drop_duplicates(subset=["期号"]).sort_values("期号").reset_index(drop=True)


def pks_dx_seq(df):
    return ["大" if int(x) > 11 else "小" for x in df["冠亚和"].tolist()]


def pks_ds_seq(df):
    return ["单" if int(x) % 2 == 1 else "双" for x in df["冠亚和"].tolist()]


# ==================== Luck20 ====================
def classify_sum(s):
    dx = "大" if s >= 810 else "小"
    ds = "单" if s % 2 == 1 else "双"
    return dx, ds, dx + ds


def _parse_luck20(it):
    code = str(it.get("preDrawCode", ""))
    nums = [int(x) for x in code.split(",") if x.strip().isdigit()][:20]
    if len(nums) < 20:
        return None
    s = int(it.get("sumNum") or sum(nums))
    dx, ds, combo = classify_sum(s)
    row = {
        "期号": str(it.get("preDrawIssue", "")),
        "开奖时间": str(it.get("preDrawTime", "")),
        "号码": nums,
        "和值": s,
        "大小": dx,
        "单双": ds,
        "组合": combo,
    }
    for i in range(20):
        row[f"号{i+1}"] = nums[i]
    return row


def fetch_luck20_latest(lot_code: int):
    url = f"{API_BASE}/LuckTwenty/getBaseLuckTewnty.do?lotCode={lot_code}"
    data = safe_json_get(url)
    if not data or data.get("errorCode") != 0:
        return None
    d = data.get("result", {}).get("data") or {}
    row = _parse_luck20(d)
    if not row:
        return None
    row["下期期号"] = str(d.get("drawIssue", ""))
    row["下期时间"] = str(d.get("drawTime", ""))
    row["服务器时间"] = str(d.get("serverTime", ""))
    return row


@st.cache_data(ttl=90, show_spinner="加载历史数据...")
def load_luck20(lot_code: int, days: int = 3) -> pd.DataFrame:
    all_rows = []
    today = datetime.now().date()
    for i in range(days):
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for base in (API_BASE, API_BASE_ALT):
            url = f"{base}/LuckTwenty/getBaseLuckTwentyList.do?lotCode={lot_code}&date={day}"
            data = safe_json_get(url)
            if not data:
                continue
            items = data.get("result", {}).get("data", [])
            if not items:
                continue
            for it in items:
                row = _parse_luck20(it)
                if row:
                    all_rows.append(row)
            break
    latest = fetch_luck20_latest(lot_code)
    if latest:
        keys = ["期号", "开奖时间", "号码", "和值", "大小", "单双", "组合"] + [f"号{i}" for i in range(1, 21)]
        all_rows.append({k: latest[k] for k in keys if k in latest})
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    return df.drop_duplicates(subset=["期号"]).sort_values("期号").reset_index(drop=True)


# ==================== UI：路珠通用 ====================
def render_luzhu_panel(seq, labels, colors, key_prefix, mode_name):
    st.subheader(f"路珠对照 · {mode_name}（默认 5 期）")
    st.warning("历史形态统计 ≠ 预测。请勿据此投注。")
    base_total = len(seq)
    base_counts = {lb: seq.count(lb) for lb in labels}

    recent_n = st.slider("显示最近路珠期数", 20, 120, 50, key=f"{key_prefix}_show")
    recent_seq = seq[-recent_n:]
    if len(labels) <= 2 and colors:
        colored = " ".join(
            f'<span style="color:{colors.get(x,"#333")};font-weight:700">{x}</span>' for x in recent_seq
        )
        st.markdown(f"**最近 {recent_n} 期：** {colored}", unsafe_allow_html=True)
    else:
        st.write("**最近：**", " → ".join(str(x) for x in recent_seq[-40:]))

    pat_len = st.selectbox("形态长度", [3, 4, 5, 6, 7], index=2, key=f"{key_prefix}_len")
    tail = seq[-pat_len:] if len(seq) >= pat_len else seq
    st.write(f"末尾 {pat_len} 期：**{' → '.join(map(str, tail))}** → 最新 **{seq[-1] if seq else '-'}**")

    bc = st.columns(min(len(labels), 4) + 1)
    for i, lb in enumerate(labels):
        if i < len(bc) - 1:
            pct = base_counts[lb] / base_total * 100 if base_total else 0
            bc[i].metric(lb, f"{base_counts[lb]}", f"{pct:.1f}%")
    bc[-1].metric("总期数", base_total)

    use_tail = st.checkbox("使用当前末尾形态", value=True, key=f"{key_prefix}_tail")
    is_combo = any(len(str(lb)) > 1 for lb in labels)
    if is_combo:
        default_pat = "".join(tail) if use_tail else ""
        hint = "每项两字连续写，如 大单小双大单小单大双"
    else:
        default_pat = "".join(tail) if use_tail else (labels[0] * pat_len if labels else "")
        hint = f"只含 {'/'.join(labels)}"
    pat_text = st.text_input(f"输入形态（{hint}）", value=default_pat, key=f"{key_prefix}_pat")

    if st.button("查询下一期比例", key=f"{key_prefix}_btn"):
        if is_combo:
            t = pat_text.strip().replace(" ", "").replace("，", "").replace(",", "")
            pattern = [t[i:i+2] for i in range(0, len(t), 2)] if len(t) % 2 == 0 else None
            if pattern and any(x not in labels for x in pattern):
                pattern = None
        else:
            pattern = parse_pattern(pat_text, "".join(labels))
        if not pattern:
            st.error("形态格式不正确")
        else:
            result = luzhu_after_pattern(seq, pattern)
            st.success(f"形态 {' → '.join(map(str, pattern))}｜样本 {result['total']}")
            if result["total"] == 0:
                st.info("样本不足")
            else:
                cols = st.columns(len(labels))
                for i, lb in enumerate(labels):
                    cols[i].metric(f"下期「{lb}」", f"{result.get(f'{lb}%', 0)}%", f"{result.get(lb, 0)} 次")

    # 速查
    st.markdown("---")
    st.write(f"**{pat_len} 期常见形态（样本≥5）**")
    pc = Counter()
    for i in range(len(seq) - pat_len):
        pc[tuple(seq[i:i+pat_len])] += 1
    rows = []
    for p, _ in pc.most_common(15):
        r = luzhu_after_pattern(seq, list(p))
        if r["total"] < 5:
            continue
        row = {"形态": "→".join(map(str, p)), "样本": r["total"]}
        for lb in labels:
            row[f"下期{lb}%"] = r.get(f"{lb}%", 0)
        rows.append(row)
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)


def render_auto_dx_ds(seq_dx, seq_ds, extra_combo=None):
    """顶部自动对照"""
    n = 5
    if len(seq_dx) < n:
        return
    pat_dx, pat_ds = seq_dx[-n:], seq_ds[-n:]
    r_dx, r_ds = luzhu_after_pattern(seq_dx, pat_dx), luzhu_after_pattern(seq_ds, pat_ds)
    st.markdown("#### 自动对照 · 最近 5 期 → 下期比例")
    st.caption("历史条件比例，**不是**真实概率。")
    cols = st.columns(3 if extra_combo is not None else 2)
    with cols[0]:
        st.markdown(f"**大小** `{''.join(pat_dx)}`")
        if r_dx["total"] > 0:
            st.metric("样本", r_dx["total"])
            a, b = st.columns(2)
            a.metric("大", f"{r_dx.get('大%', 0)}%")
            b.metric("小", f"{r_dx.get('小%', 0)}%")
        else:
            st.info("样本不足")
    with cols[1]:
        st.markdown(f"**单双** `{''.join(pat_ds)}`")
        if r_ds["total"] > 0:
            st.metric("样本", r_ds["total"])
            a, b = st.columns(2)
            a.metric("单", f"{r_ds.get('单%', 0)}%")
            b.metric("双", f"{r_ds.get('双%', 0)}%")
        else:
            st.info("样本不足")
    if extra_combo is not None and len(extra_combo) >= n:
        with cols[2]:
            pat = extra_combo[-n:]
            r = luzhu_after_pattern(extra_combo, pat)
            st.markdown(f"**组合** `{'→'.join(pat)}`")
            if r["total"] > 0:
                st.metric("样本", r["total"])
                for lb in ["大单", "大双", "小单", "小双"]:
                    st.caption(f"{lb} {r.get(f'{lb}%', 0)}%（{r.get(lb, 0)}）")
            else:
                st.info("样本不足")
    st.markdown("---")


# ==================== 主界面 ====================
st.markdown('<div class="main-header">🎱 极速彩数据分析助手</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">api.api16868.com · 仅供学习娱乐</div>', unsafe_allow_html=True)
st.markdown("""
<div class="disclaimer">
⚠️ <b>重要声明</b>：开奖为随机事件，历史无法预测未来。本工具只做统计可视化，不提供中奖保证。请理性对待。
</div>
""", unsafe_allow_html=True)

name_to_item = {x["name"]: x for x in LOTTERY_CATALOG}

with st.sidebar:
    st.header("⚙️ 设置")
    lottery_name = st.selectbox("选择彩种", [x["name"] for x in LOTTERY_CATALOG], index=0)
    item = name_to_item[lottery_name]
    lot_code = item["code"]
    lot_type = item["type"]
    force_refresh = st.button("🔄 强制刷新数据")
    n_recent = st.slider("分析最近期数", 30, 500, 100, 10)
    ft_days = st.slider("拉取最近几天数据", 1, 7, 3)
    auto_refresh = st.checkbox("⏱ 自动刷新（约 45 秒）", value=False)
    if auto_refresh:
        st.caption("开启后页面定时重新拉取")
    st.markdown("---")
    st.caption(f"当前 lotCode = {lot_code}")
    st.caption("数据源：api.api16868.com")
    with st.expander("全部彩种列表"):
        for x in LOTTERY_CATALOG:
            st.write(f"· {x['name']}（{x['code']} / {x['type']}）")

if auto_refresh:
    st.markdown('<meta http-equiv="refresh" content="45">', unsafe_allow_html=True)
    st.info("⏱ 自动刷新已开启")

# ---------- PK10 家族 ----------
if lot_type == "pks":
    if force_refresh:
        load_pks.clear()
    df = load_pks(lot_code, ft_days)
    if df.empty:
        st.error("数据加载失败，请稍后重试")
        st.stop()
    rt = fetch_pks_latest(lot_code)
    latest = df.iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("已加载期数", f"{len(df):,}")
    c2.metric("最新期号", latest["期号"])
    c3.metric("开奖时间", str(latest["开奖时间"])[:19])
    gy = int(latest["冠亚和"])
    c4.metric("冠亚和/大小", f"{gy} / {'大' if gy > 11 else '小'}")
    nums = [latest[p] for p in POS_COLS]
    draw_box(f"<b>{lottery_name} · 最新开奖</b><br/>" + balls_html(nums, "gold"))
    if rt:
        st.caption(f"下期 {rt.get('下期期号','')} · 服务器 {rt.get('服务器时间','')}")

    seq_dx, seq_ds = pks_dx_seq(df), pks_ds_seq(df)
    render_auto_dx_ds(seq_dx, seq_ds)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 名次频率", "🏆 冠军&冠亚和", "🐉 龙虎", "🔴 路珠", "📋 历史"])
    with tab1:
        d = df.tail(min(n_recent, len(df)))
        records = []
        for pos in POS_COLS:
            vc = d[pos].value_counts().reindex(range(1, 11), fill_value=0)
            for num, cnt in vc.items():
                records.append({"名次": pos, "号码": num, "次数": cnt})
        pos_df = pd.DataFrame(records)
        fig = px.density_heatmap(pos_df, x="号码", y="名次", z="次数",
                                title=f"各名次热力（近{min(n_recent,len(df))}期）", color_continuous_scale="YlOrRd")
        fig.update_layout(height=480)
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        d = df.tail(min(n_recent, len(df)))
        champ = d["冠军"].value_counts().sort_index()
        gy_s = d["冠亚和"].value_counts().sort_index()
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(x=champ.index, y=champ.values, title="冠军频率", color=champ.values, color_continuous_scale="Reds")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.bar(x=gy_s.index, y=gy_s.values, title="冠亚和分布", color=gy_s.values, color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)
    with tab3:
        d = df.tail(min(n_recent, len(df))).copy()
        d["龙虎"] = np.where(d["冠军"] > d["第十"], "龙", "虎")
        d["冠亚大小"] = np.where(d["冠亚和"] > 11, "大", "小")
        c1, c2 = st.columns(2)
        with c1:
            lt = d["龙虎"].value_counts()
            st.plotly_chart(px.pie(values=lt.values, names=lt.index, title="龙虎"), use_container_width=True)
        with c2:
            bs = d["冠亚大小"].value_counts()
            st.plotly_chart(px.pie(values=bs.values, names=bs.index, title="冠亚和大小"), use_container_width=True)
    with tab4:
        mode = st.radio("类型", ["大小", "单双"], horizontal=True, key=f"pks_m_{lot_code}")
        if mode == "大小":
            render_luzhu_panel(seq_dx, ("大", "小"), {"大": "#e63946", "小": "#457b9d"}, f"pks_dx_{lot_code}", "大小")
        else:
            render_luzhu_panel(seq_ds, ("单", "双"), {"单": "#e63946", "双": "#2a9d8f"}, f"pks_ds_{lot_code}", "单双")
    with tab5:
        show = df.tail(50)[["期号", "开奖时间"] + POS_COLS + ["冠亚和"]].copy()
        show["大小"] = show["冠亚和"].apply(lambda x: "大" if int(x) > 11 else "小")
        show["单双"] = show["冠亚和"].apply(lambda x: "单" if int(x) % 2 else "双")
        st.dataframe(show.iloc[::-1], use_container_width=True, height=400)
        st.download_button("下载CSV", df.to_csv(index=False).encode("utf-8-sig"),
                           f"pks_{lot_code}_{datetime.now():%Y%m%d}.csv", "text/csv")

# ---------- Luck20 家族 ----------
else:
    if force_refresh:
        load_luck20.clear()
    df = load_luck20(lot_code, ft_days)
    if df.empty:
        st.error("数据加载失败，请稍后重试")
        st.stop()
    rt = fetch_luck20_latest(lot_code)
    latest = df.iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("已加载期数", f"{len(df):,}")
    c2.metric("最新期号", str(latest["期号"]))
    c3.metric("开奖时间", str(latest["开奖时间"])[:19])
    c4.metric("和值/组合", f"{int(latest['和值'])} / {latest['组合']}")
    nums = latest["号码"] if isinstance(latest.get("号码"), list) else [latest.get(f"号{i}") for i in range(1, 21)]
    draw_box(
        f"<b>{lottery_name} · 最新开奖</b><br/>" + balls_html(nums, "green")
        + f'<br/><span class="tag-combo">{latest["大小"]} · {latest["单双"]} · {latest["组合"]}</span>'
    )
    if rt:
        st.caption(f"下期 {rt.get('下期期号','')} · 服务器 {rt.get('服务器时间','')}")

    seq_dx = df["大小"].tolist()
    seq_ds = df["单双"].tolist()
    seq_combo = df["组合"].tolist()
    render_auto_dx_ds(seq_dx, seq_ds, seq_combo)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 号码频率", "📈 和值", "🎲 大小单双", "🔴 路珠", "📋 历史"])
    with tab1:
        cols = [c for c in df.columns if c.startswith("号") and c[1:].isdigit()]
        d = df.tail(min(n_recent, len(df)))
        freq = pd.Series(d[cols].values.flatten()).value_counts().reindex(range(1, 81), fill_value=0)
        fig = px.bar(x=freq.index, y=freq.values, title=f"1-80 频率（近{min(n_recent,len(df))}期）",
                     color=freq.values, color_continuous_scale="Viridis")
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
        c1, c2 = st.columns(2)
        c1.write("**热号** " + " ".join(f"`{i:02d}`" for i in freq.nlargest(10).index))
        c2.write("**冷号** " + " ".join(f"`{i:02d}`" for i in freq.nsmallest(10).index))
    with tab2:
        recent = df.tail(min(n_recent, len(df)))
        fig = px.line(recent, x="期号", y="和值", title="和值走势", markers=True)
        fig.add_hline(y=recent["和值"].mean(), line_dash="dash")
        fig.add_hline(y=810, line_dash="dot", annotation_text="810 分界")
        st.plotly_chart(fig, use_container_width=True)
    with tab3:
        d = df.tail(min(n_recent, len(df)))
        c1, c2, c3 = st.columns(3)
        with c1:
            vc = d["大小"].value_counts()
            st.plotly_chart(px.pie(values=vc.values, names=vc.index, title="大小"), use_container_width=True)
        with c2:
            vc = d["单双"].value_counts()
            st.plotly_chart(px.pie(values=vc.values, names=vc.index, title="单双"), use_container_width=True)
        with c3:
            vc = d["组合"].value_counts()
            st.plotly_chart(px.pie(values=vc.values, names=vc.index, title="四组合"), use_container_width=True)
    with tab4:
        mode = st.radio("类型", ["大小", "单双", "组合(四态)"], horizontal=True, key=f"l20_m_{lot_code}")
        if mode == "大小":
            render_luzhu_panel(seq_dx, ("大", "小"), {"大": "#e63946", "小": "#457b9d"}, f"l20_dx_{lot_code}", "大小")
        elif mode == "单双":
            render_luzhu_panel(seq_ds, ("单", "双"), {"单": "#e63946", "双": "#2a9d8f"}, f"l20_ds_{lot_code}", "单双")
        else:
            render_luzhu_panel(seq_combo, ("大单", "大双", "小单", "小双"), {}, f"l20_cb_{lot_code}", "组合")
    with tab5:
        show = df.tail(50)[["期号", "开奖时间", "和值", "大小", "单双", "组合"]].copy()
        st.dataframe(show.iloc[::-1], use_container_width=True, height=400)
        st.download_button("下载CSV", df.drop(columns=["号码"], errors="ignore").to_csv(index=False).encode("utf-8-sig"),
                           f"luck20_{lot_code}_{datetime.now():%Y%m%d}.csv", "text/csv")

st.markdown('<div class="footer-note">仅供学习 · 请理性购彩，远离赌博心态</div>', unsafe_allow_html=True)
