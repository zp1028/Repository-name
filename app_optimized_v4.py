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
from datetime import datetime, timedelta
from collections import Counter
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

st.set_page_config(page_title="极速彩数据分析", page_icon="🎱", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;600;700;900&display=swap');
  html, body, [class*="css"] { font-family: 'Noto Sans SC', sans-serif; }
  .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1100px; }
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #8b0000 0%, #4a0000 55%, #1a0000 100%);
  }
  [data-testid="stSidebar"] * { color: #ffe8a1 !important; }
  [data-testid="stSidebar"] [data-baseweb="select"] > div { background: #5c0000; color: #fff; }

  .main-header {
    font-size: 1.9rem; font-weight: 900; text-align: center; color: #c41e3a;
    text-shadow: 0 1px 0 #fff, 0 2px 8px rgba(196,30,58,0.25);
    letter-spacing: 0.08em; margin-bottom: 0.1rem;
  }
  .sub-header { text-align: center; color: #8a6d3b; font-size: 0.9rem; margin-bottom: 0.6rem; }
  .disclaimer {
    background: #fff8e7; border: 1px solid #e8d5a3; border-left: 5px solid #c41e3a;
    padding: 10px 14px; margin: 6px 0 12px; border-radius: 6px;
    font-size: 0.88rem; color: #5c4a00; line-height: 1.45;
  }

  /* 开奖看板 */
  .live-board {
    background: linear-gradient(145deg, #1a0505 0%, #3d0a0a 40%, #1a0505 100%);
    border: 2px solid #c9a227; border-radius: 14px;
    padding: 16px 18px 14px; margin: 8px 0 14px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,215,0,0.2);
  }
  .live-board .title {
    color: #ffd700; font-weight: 800; font-size: 1.05rem; text-align: center;
    letter-spacing: 0.12em; margin-bottom: 10px;
  }
  .live-board .meta {
    color: #e8c96a; font-size: 0.85rem; text-align: center; margin-bottom: 10px;
  }
  .num-ball {
    display: inline-flex; align-items: center; justify-content: center;
    width: 2.15rem; height: 2.15rem; margin: 0 4px 6px;
    border-radius: 50%; font-weight: 800; font-size: 0.88rem; color: #fff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.35), inset 0 -2px 3px rgba(0,0,0,0.2);
  }
  .num-ball.red { background: radial-gradient(circle at 30% 30%, #ff6b6b, #c41e3a 70%); }
  .num-ball.gold { background: radial-gradient(circle at 30% 30%, #ffe566, #d4a017 70%); color: #3d2a00; }
  .num-ball.green { background: radial-gradient(circle at 30% 30%, #5eead4, #0f766e 70%); }
  .num-ball.blue { background: radial-gradient(circle at 30% 30%, #7dd3fc, #0369a1 70%); }
  .balls-row { text-align: center; line-height: 2.4; }
  .tag-combo {
    display: inline-block; margin-top: 8px; padding: 4px 14px; border-radius: 999px;
    font-weight: 800; font-size: 0.95rem; color: #1a0505;
    background: linear-gradient(90deg, #ffd700, #f0c14e);
  }
  .countdown-box {
    background: linear-gradient(90deg, #7f1d1d, #b91c1c);
    border: 1px solid #fbbf24; border-radius: 12px;
    padding: 12px 16px; text-align: center; margin: 8px 0 12px; color: #fff;
  }
  .countdown-box .time {
    font-size: 1.85rem; font-weight: 900; letter-spacing: 3px; color: #fde68a;
    font-variant-numeric: tabular-nums;
  }

  /* 预测卡片 */
  .pred-card {
    background: #fffef8; border: 1px solid #e8d5a3; border-radius: 12px;
    padding: 12px 14px; margin-bottom: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  }
  .pred-card h4 { margin: 0 0 6px; color: #7f1d1d; font-size: 0.95rem; }
  .hit-ok { color: #15803d; font-weight: 800; }
  .hit-bad { color: #b91c1c; font-weight: 800; }
  .hit-wait { color: #a16207; font-weight: 700; }

  [data-testid="stMetric"] {
    background: #fffef8; border-radius: 10px; padding: 10px 12px;
    border: 1px solid #f0e6c8;
  }
  [data-testid="stMetricValue"] { color: #7f1d1d; font-weight: 800; }
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: #f5e6c8; padding: 5px; border-radius: 10px;
  }
  .stTabs [data-baseweb="tab"] { border-radius: 8px; font-weight: 700; color: #5c4a00; }
  .stTabs [aria-selected="true"] {
    background: #c41e3a !important; color: #fff !important;
  }
  @media (max-width: 768px) {
    .main-header { font-size: 1.4rem; }
    .num-ball { width: 1.8rem; height: 1.8rem; font-size: 0.75rem; margin: 0 2px 4px; }
    .countdown-box .time { font-size: 1.45rem; }
  }
  .footer-note {
    text-align: center; color: #a89878; font-size: 0.8rem;
    margin-top: 1.2rem; padding-top: 0.7rem; border-top: 1px solid #e8d5a3;
  }
</style>
""", unsafe_allow_html=True)

# ==================== 配置 / 数据层 / UI 层 ====================
# 彩种目录集中维护；数据请求、解析、统计、渲染彼此解耦，便于后续扩展新彩种。

# ==================== 彩种目录（API 实测可用） ====================
# type: pks = 10名次赛车/飞艇 | luck20 = 20码快乐8风格
LOTTERY_CATALOG = [
    {"key": "10037", "name": "极速飞艇", "type": "pks", "code": 10037},
    {"key": "10035", "name": "极速赛车", "type": "pks", "code": 10035},
    {"key": "10012", "name": "幸运飞艇", "type": "pks", "code": 10012},
    {"key": "10058", "name": "PK拾(10058)", "type": "pks", "code": 10058},
    {"key": "10057", "name": "澳洲幸运10", "type": "pks", "code": 10057},
    # 注意：接口 preDrawCode 含 21 个号，前 20 为开奖号，第 21 为附加号（不计入和值）
    {"key": "10054", "name": "极速快乐8", "type": "luck20", "code": 10054},  # 约 75 秒/期
    {"key": "10047", "name": "幸运20(10047)", "type": "luck20", "code": 10047},  # 约 5 分钟/期
]

API_BASE = "https://api.api16868.com"
API_BASE_ALT = "https://api.api68.com"
POS_COLS = ["冠军", "亚军", "第三", "第四", "第五", "第六", "第七", "第八", "第九", "第十"]


def balls_html(nums, color="gold"):
    return "".join(f'<span class="num-ball {color}">{int(n):02d}</span>' for n in nums)


def draw_box(html_inner: str):
    st.markdown('<div class="live-board">%s</div>' % html_inner, unsafe_allow_html=True)


HTTP_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


_thread_local = threading.local()


def get_http_session():
    """每个线程复用自己的 Session，兼顾连接复用与线程安全。"""
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(HTTP_HEADERS)
        _thread_local.session = session
    return session


def safe_json_get(url, timeout=(5, 10), retries=2):
    """带短连接超时和指数退避的 JSON 请求。失败只返回 None，不阻塞页面。"""
    session = get_http_session()
    for attempt in range(retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            if attempt >= retries:
                return None
            time.sleep(0.35 * (2 ** attempt))
    return None


def _history_items(base_urls, endpoint, lot_code, day):
    """从主/备用 API 获取某一天的数据。"""
    for base in base_urls:
        data = safe_json_get(f"{base}/{endpoint}?lotCode={lot_code}&date={day}")
        if data:
            items = data.get("result", {}).get("data", []) or []
            if items:
                return items
    return []


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


def parse_api_time(s):
    """解析接口时间：支持 'YYYY-MM-DD HH:MM:SS' 或 unix 秒/毫秒"""
    if s is None or s == "":
        return None
    if isinstance(s, (int, float)):
        ts = float(s)
        if ts > 1e12:
            ts /= 1000.0
        try:
            return datetime.fromtimestamp(ts)
        except Exception:
            return None
    text = str(s).strip()
    if text.isdigit():
        ts = float(text)
        if ts > 1e12:
            ts /= 1000.0
        try:
            return datetime.fromtimestamp(ts)
        except Exception:
            return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt)
        except Exception:
            continue
    return None


def render_countdown(rt, label="下期开奖"):
    """根据 serverTime / drawTime 显示倒计时"""
    if not rt:
        return
    server = parse_api_time(rt.get("服务器时间") or rt.get("serverTime"))
    draw = parse_api_time(rt.get("下期时间") or rt.get("drawTime"))
    next_issue = rt.get("下期期号") or rt.get("drawIssue") or ""
    if not draw:
        st.caption(label + "：时间未知")
        return
    now = server or datetime.now()
    remain = (draw - now).total_seconds()
    if remain < -30:
        st.warning("可能已开奖，请刷新 · 下期 " + str(next_issue))
        return
    if remain < 0:
        remain = 0
    m, sec = divmod(int(remain), 60)
    h, m = divmod(m, 60)
    tstr = ("%02d:%02d:%02d" % (h, m, sec)) if h > 0 else ("%02d:%02d" % (m, sec))
    draw_s = draw.strftime("%H:%M:%S")
    now_s = now.strftime("%H:%M:%S") if server else "本地"
    html = (
        '<div class="countdown-box">'
        "⏳ <b>%s</b>　第 <b>%s</b> 期<br/>"
        '<span class="time">%s</span>'
        '<div style="font-size:0.8rem;opacity:0.9;margin-top:4px;">预计 %s　校对时间 %s</div></div>'
    ) % (label, next_issue, tstr, draw_s, now_s)
    st.markdown(html, unsafe_allow_html=True)


def luzhu_with_fallback(seq, prefer_len=5, min_samples=5):
    """优先用 prefer_len 期形态；若样本不足则自动缩短到 4、3 期。"""
    if len(seq) < 3:
        return None, {}, 0
    for L in [prefer_len, 4, 3]:
        if len(seq) < L:
            continue
        pat = seq[-L:]
        r = luzhu_after_pattern(seq, pat)
        if r["total"] >= min_samples or L == 3:
            return pat, r, L
    pat = seq[-3:] if len(seq) >= 3 else seq
    return pat, luzhu_after_pattern(seq, pat), len(pat)




# ==================== PK10 / 飞艇 ====================
@st.cache_data(ttl=20, show_spinner=False)
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
    """并行拉取历史数据；结果缓存 90 秒，避免 Streamlit rerun 重复请求。"""
    today = datetime.now().date()
    days_list = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    rows = []

    with ThreadPoolExecutor(max_workers=min(4, max(1, days))) as pool:
        futures = {
            pool.submit(_history_items, (API_BASE, API_BASE_ALT), "pks/getPksHistoryList.do", lot_code, day): day
            for day in days_list
        }
        for future in as_completed(futures):
            for it in future.result():
                code = str(it.get("preDrawCode", ""))
                nums = [int(x) for x in code.split(",") if x.strip().isdigit()]
                if len(nums) != 10:
                    continue
                row = {
                    "期号": str(it.get("preDrawIssue", "")),
                    "开奖时间": it.get("preDrawTime", ""),
                    "冠亚和": nums[0] + nums[1],
                }
                row.update(dict(zip(POS_COLS, nums)))
                rows.append(row)

    latest = fetch_pks_latest(lot_code)
    if latest:
        rows.append({k: latest[k] for k in ["期号", "开奖时间", "冠亚和"] + POS_COLS if k in latest})
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).drop_duplicates(subset=["期号"])
    return df.sort_values("期号", kind="stable").reset_index(drop=True)


def pks_dx_seq(df):
    return ["大" if int(x) > 11 else "小" for x in df["冠亚和"].tolist()]


def pks_ds_seq(df):
    return ["单" if int(x) % 2 == 1 else "双" for x in df["冠亚和"].tolist()]


# ==================== Luck20 ====================
def classify_sum(s, api_big_small=None, api_single_double=None):
    """和值大小单双。优先采用接口 sumBigSmall / sumSingleDouble，避免与数据源不一致。
    接口约定：sumBigSmall: 1=大, -1=小；sumSingleDouble: 1=单, -1=双。
    本地兜底：>=810 为大，奇数为单。
    """
    if api_big_small is not None and str(api_big_small) != "":
        try:
            dx = "大" if int(api_big_small) == 1 else "小"
        except Exception:
            dx = "大" if s >= 810 else "小"
    else:
        dx = "大" if s >= 810 else "小"
    if api_single_double is not None and str(api_single_double) != "":
        try:
            ds = "单" if int(api_single_double) == 1 else "双"
        except Exception:
            ds = "单" if s % 2 == 1 else "双"
    else:
        ds = "单" if s % 2 == 1 else "双"
    return dx, ds, dx + ds


def _parse_luck20(it):
    """解析幸运20/快乐8。
    重要：preDrawCode 常为 21 个数字——前 20 个是开奖号码，第 21 个是附加号（不计入和值）。
    和值以接口 sumNum 为准（= 前 20 个之和）。
    """
    code = str(it.get("preDrawCode", ""))
    all_nums = [int(x) for x in code.split(",") if x.strip().isdigit()]
    if len(all_nums) < 20:
        return None
    nums = all_nums[:20]  # 只取开奖 20 码
    extra = all_nums[20] if len(all_nums) > 20 else None
    # 优先用接口 sumNum
    try:
        s = int(it.get("sumNum"))
    except Exception:
        s = sum(nums)
    dx, ds, combo = classify_sum(
        s,
        api_big_small=it.get("sumBigSmall"),
        api_single_double=it.get("sumSingleDouble"),
    )
    row = {
        "期号": str(it.get("preDrawIssue", "")),
        "开奖时间": str(it.get("preDrawTime", "")),
        "号码": nums,
        "附加号": extra,
        "和值": s,
        "大小": dx,
        "单双": ds,
        "组合": combo,
    }
    for i in range(20):
        row[f"号{i+1}"] = nums[i]
    return row


@st.cache_data(ttl=20, show_spinner=False)
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
    """并行拉取 Luck20 历史数据；解析集中在 _parse_luck20，减少重复逻辑。"""
    today = datetime.now().date()
    days_list = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    rows = []

    with ThreadPoolExecutor(max_workers=min(4, max(1, days))) as pool:
        futures = {
            pool.submit(_history_items, (API_BASE, API_BASE_ALT), "LuckTwenty/getBaseLuckTwentyList.do", lot_code, day): day
            for day in days_list
        }
        for future in as_completed(futures):
            for it in future.result():
                row = _parse_luck20(it)
                if row:
                    rows.append(row)

    latest = fetch_luck20_latest(lot_code)
    if latest:
        keys = ["期号", "开奖时间", "号码", "附加号", "和值", "大小", "单双", "组合"] + [f"号{i}" for i in range(1, 21)]
        rows.append({k: latest[k] for k in keys if k in latest})
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).drop_duplicates(subset=["期号"])
    return df.sort_values("期号", kind="stable").reset_index(drop=True)


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


def derive_combo_probabilities(r_dx, r_ds):
    """根据大小/单双两个边际结果推导四组合概率。

    这里不再单独对“组合路珠”做预测，而是直接使用大小、单双两项结果：
    P(大单)=P(大)*P(单)，其余同理。
    这是一种“边际独立”近似，仅用于展示统计倾向，不代表真实概率。
    """
    dx = {"大": float(r_dx.get("大%", 0) or 0), "小": float(r_dx.get("小%", 0) or 0)}
    ds = {"单": float(r_ds.get("单%", 0) or 0), "双": float(r_ds.get("双%", 0) or 0)}
    combos = {
        "大单": dx["大"] * ds["单"] / 100,
        "大双": dx["大"] * ds["双"] / 100,
        "小单": dx["小"] * ds["单"] / 100,
        "小双": dx["小"] * ds["双"] / 100,
    }
    # 四项理论上已经合计100；再次归一化可抵抗接口四舍五入误差。
    total = sum(combos.values())
    if total > 0:
        combos = {k: round(v * 100 / total, 2) for k, v in combos.items()}
    return combos


def render_auto_dx_ds(seq_dx, seq_ds, pred_key=None, latest_issue=None):
    """大小、单双分别统计；四组合由两项边际结果直接推导，不再单独统计组合路珠。"""
    if len(seq_dx) < 3:
        st.info("历史仅 %d 期，至少需 3 期才能对照。请加大「拉取最近几天数据」。" % len(seq_dx))
        return

    pat_dx, r_dx, Ldx = luzhu_with_fallback(seq_dx, 5, 3)
    pat_ds, r_ds, Lds = luzhu_with_fallback(seq_ds, 5, 3)
    st.markdown("#### 📊 自动对照 · 下期倾向")
    st.caption("大小、单双分别计算；组合概率由两项结果推导。≠ 真实概率。")

    cols = st.columns(3)
    with cols[0]:
        lean_dx, _, pct_dx = lean_from_result(r_dx, ("大", "小"))
        st.markdown('<div class="pred-card"><h4>大小（%d期） %s</h4>' % (Ldx, "".join(pat_dx) if pat_dx else ""), unsafe_allow_html=True)
        if r_dx.get("total", 0) > 0:
            st.metric("样本", r_dx["total"])
            a, b = st.columns(2)
            a.metric("大", "%s%%" % r_dx.get("大%", 0))
            b.metric("小", "%s%%" % r_dx.get("小%", 0))
            if lean_dx:
                st.markdown("倾向：**%s**（%s%%）" % (lean_dx, pct_dx))
                if pred_key and latest_issue:
                    push_prediction(pred_key, latest_issue, "大小", "".join(pat_dx), lean_dx, r_dx["total"], pct_dx)
        else:
            st.info("样本不足")
        st.markdown("</div>", unsafe_allow_html=True)

    with cols[1]:
        lean_ds, _, pct_ds = lean_from_result(r_ds, ("单", "双"))
        st.markdown('<div class="pred-card"><h4>单双（%d期） %s</h4>' % (Lds, "".join(pat_ds) if pat_ds else ""), unsafe_allow_html=True)
        if r_ds.get("total", 0) > 0:
            st.metric("样本", r_ds["total"])
            a, b = st.columns(2)
            a.metric("单", "%s%%" % r_ds.get("单%", 0))
            b.metric("双", "%s%%" % r_ds.get("双%", 0))
            if lean_ds:
                st.markdown("倾向：**%s**（%s%%）" % (lean_ds, pct_ds))
                if pred_key and latest_issue:
                    push_prediction(pred_key, latest_issue, "单双", "".join(pat_ds), lean_ds, r_ds["total"], pct_ds)
        else:
            st.info("样本不足")
        st.markdown("</div>", unsafe_allow_html=True)

    # 组合直接由大小×单双生成
    with cols[2]:
        combo = derive_combo_probabilities(r_dx, r_ds)
        combo_lean = max(combo, key=combo.get) if combo else None
        combo_pct = combo.get(combo_lean, 0) if combo_lean else 0
        st.markdown('<div class="pred-card"><h4>组合 · 由大小×单双推导</h4>', unsafe_allow_html=True)
        if combo:
            for lb in ("大单", "大双", "小单", "小双"):
                st.caption("%s　%s%%" % (lb, combo.get(lb, 0)))
            st.markdown("倾向：**%s**（%s%%）" % (combo_lean, combo_pct))
            if pred_key and latest_issue:
                push_prediction(pred_key, latest_issue, "组合", "大小×单双", combo_lean, min(r_dx.get("total", 0), r_ds.get("total", 0)), combo_pct)
        else:
            st.info("大小/单双样本不足，无法推导组合")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")


# ==================== 实时看板（局部刷新，不触发历史数据重载） ====================
def _render_live_common(rt, lottery_name, lot_type):
    if not rt:
        st.warning("实时接口暂不可用")
        return
    if lot_type == "pks":
        nums = [rt[p] for p in POS_COLS]
        gy = int(rt["冠亚和"])
        draw_box('<div class="title">🔴 %s · 实时开奖</div><div class="meta">第 %s 期　%s</div><div class="balls-row">%s</div>' % (
            lottery_name, rt["期号"], str(rt["开奖时间"])[:19], balls_html(nums, "gold")))
        st.caption("冠亚和 %d · %s%s" % (gy, "大" if gy > 11 else "小", " · " + ("单" if gy % 2 else "双")))
    else:
        nums = rt["号码"]
        extra = rt.get("附加号")
        extra_html = f'　附加号 <span class="num-ball gold">{int(extra):02d}</span>' if extra is not None else ""
        draw_box('<div class="title">🟢 %s · 实时开奖</div><div class="meta">第 %s 期　%s</div><div class="balls-row">%s%s</div>'
                 '<div style="text-align:center"><span class="tag-combo">和值 %s · %s · %s · %s</span></div>' % (
                     lottery_name, rt["期号"], str(rt["开奖时间"])[:19], balls_html(nums, "green"), extra_html,
                     int(rt["和值"]), rt["大小"], rt["单双"], rt["大小"] + rt["单双"]))
        st.caption("前20个为开奖号码；附加号不计入和值。")
    render_countdown(rt, "下期开奖")
    st.caption("服务器时间 %s" % rt.get("服务器时间", ""))


@st.fragment(run_every=5)
def render_live_panel(lot_code, lottery_name, lot_type):
    """只刷新实时接口；不会重新拉历史数据，也不会重绘主分析区。"""
    if st.button("🔄 立即刷新实时", key=f"live_refresh_{lot_type}_{lot_code}"):
        if lot_type == "pks":
            fetch_pks_latest.clear(lot_code)
            rt = fetch_pks_latest(lot_code)
        else:
            fetch_luck20_latest.clear(lot_code)
            rt = fetch_luck20_latest(lot_code)
    else:
        rt = fetch_pks_latest(lot_code) if lot_type == "pks" else fetch_luck20_latest(lot_code)
    _render_live_common(rt, lottery_name, lot_type)


# ==================== 预测面板（独立局部刷新） ====================
@st.fragment(run_every=5)
def render_prediction_panel(lot_code, lot_type, pred_key, seq_dx, seq_ds):
    """预测独立于主页面刷新：只轮询最新一期，发现新期后自动结算并重新生成预测。"""
    rt = fetch_pks_latest(lot_code) if lot_type == "pks" else fetch_luck20_latest(lot_code)
    if not rt:
        st.warning("预测实时接口暂不可用")
        return

    issue = str(rt.get("期号", ""))
    if lot_type == "pks":
        gy = int(rt.get("冠亚和", 0))
        actual_map = {"大小": "大" if gy > 11 else "小",
                      "单双": "单" if gy % 2 else "双"}
    else:
        actual_map = {"大小": rt.get("大小"), "单双": rt.get("单双")}
        # 组合不再依赖独立组合路珠；结算组合时由实际大小单双组合生成
        if actual_map.get("大小") and actual_map.get("单双"):
            actual_map["组合"] = actual_map["大小"] + actual_map["单双"]

    # 只有发现新期号时才结算上一期，避免5秒轮询重复操作。
    last_seen_key = f"pred_seen_{pred_key}"
    last_seen = st.session_state.get(last_seen_key)
    if issue and issue != last_seen:
        settle_predictions(pred_key, issue, actual_map)
        st.session_state[last_seen_key] = issue

    st.markdown("#### 📊 自动预测 · 独立实时刷新")
    st.caption(f"实时期号：{issue} · 每 5 秒检查一次；历史数据不会重新加载。")
    render_auto_dx_ds(seq_dx, seq_ds, pred_key=pred_key, latest_issue=issue)


# ==================== 主界面 ====================
st.markdown('<div class="main-header">🎱 极速彩数据分析助手</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">api.api16868.com · 仅供学习娱乐</div>', unsafe_allow_html=True)
st.markdown("""
<div class="disclaimer">
⚠️ <b>重要声明</b>：开奖为随机事件，历史无法预测未来。本工具只做统计可视化，不提供中奖保证。请理性对待。
</div>
""", unsafe_allow_html=True)


def lean_from_result(result, labels):
    """从路珠结果中取样本最多的一侧作为「倾向」"""
    if not result or result.get("total", 0) <= 0:
        return None, 0, 0
    best, best_n = None, -1
    for lb in labels:
        n = result.get(lb, 0)
        if n > best_n:
            best, best_n = lb, n
    pct = result.get("%s%%" % best, 0) if best else 0
    return best, best_n, pct


def push_prediction(key, issue, category, pattern, lean, sample, pct):
    """写入待验证预测（同一期同类别只保留一条）"""
    if "pred_hist" not in st.session_state:
        st.session_state.pred_hist = []
    hist = st.session_state.pred_hist
    # 去掉同 key+issue+category 的旧待验证记录
    hist = [x for x in hist if not (x.get("key") == key and x.get("issue") == str(issue) and x.get("cat") == category and x.get("result") == "待开")]
    hist.insert(0, {
        "key": key,
        "issue": str(issue),
        "cat": category,
        "pattern": pattern,
        "lean": lean,
        "sample": sample,
        "pct": pct,
        "actual": "",
        "result": "待开",
        "time": datetime.now().strftime("%H:%M:%S"),
    })
    st.session_state.pred_hist = hist[:200]


def settle_predictions(key, new_issue, actual_map):
    """用最新一期实际结果结算上一期预测。actual_map: {类别: 实际值}"""
    if "pred_hist" not in st.session_state:
        return
    hist = st.session_state.pred_hist
    for row in hist:
        if row.get("key") != key or row.get("result") != "待开":
            continue
        # 预测针对的是「形态之后的下一期」，记录时 issue 为当时最新期，实际应对 new_issue
        if str(row.get("issue")) == str(new_issue):
            continue  # 还是当期，未到下一期
        cat = row.get("cat")
        if cat not in actual_map:
            continue
        # 只结算「紧邻」的：issue < new_issue（字符串数字比较）
        try:
            if int(str(row["issue"])) >= int(str(new_issue)):
                continue
        except Exception:
            if str(row["issue"]) >= str(new_issue):
                continue
        actual = actual_map[cat]
        row["actual"] = actual
        row["result"] = "对" if actual == row.get("lean") else "错"
        row["settle_issue"] = str(new_issue)
    st.session_state.pred_hist = hist


def render_pred_history(key):
    """分类展示预测历史：支持按预测类型和验证结果筛选。"""
    hist = [x for x in st.session_state.get("pred_hist", []) if x.get("key") == key]
    if not hist:
        st.caption("暂无预测记录。每次开奖后的自动对照会记入「倾向」，下期揭晓后统计对错。")
        return

    categories = []
    for x in hist:
        cat = x.get("cat", "")
        if cat and cat not in categories:
            categories.append(cat)

    # 分类查看：全部 / 大小 / 单双 / 组合
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        category_options = ["全部"] + categories
        selected_cat = st.selectbox(
            "预测类型",
            category_options,
            key=f"pred_cat_filter_{key}",
        )
    with filter_col2:
        result_options = ["全部", "对", "错", "待开"]
        selected_result = st.selectbox(
            "验证结果",
            result_options,
            key=f"pred_result_filter_{key}",
        )

    filtered = hist
    if selected_cat != "全部":
        filtered = [x for x in filtered if x.get("cat") == selected_cat]
    if selected_result != "全部":
        filtered = [x for x in filtered if x.get("result") == selected_result]

    # 当前分类的统计
    settled = [x for x in filtered if x.get("result") in ("对", "错")]
    ok = sum(1 for x in settled if x.get("result") == "对")
    bad = sum(1 for x in settled if x.get("result") == "错")
    pending = sum(1 for x in filtered if x.get("result") == "待开")
    rate = (ok / len(settled) * 100) if settled else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("当前记录", len(filtered))
    c2.metric("已验证", len(settled))
    c3.metric("对", ok)
    c4.metric("错", bad)
    c5.metric("正确率", "%.1f%%" % rate)

    if pending:
        st.caption(f"当前筛选还有 {pending} 条待开奖记录。")
    else:
        st.caption("正确率仅反映历史条件统计的「运气」，不代表以后会准。")

    # 类型汇总：方便一眼比较大小、单双、组合各自表现
    if selected_cat == "全部":
        summary_rows = []
        for cat in categories:
            cat_hist = [x for x in hist if x.get("cat") == cat]
            cat_settled = [x for x in cat_hist if x.get("result") in ("对", "错")]
            cat_ok = sum(1 for x in cat_settled if x.get("result") == "对")
            cat_bad = len(cat_settled) - cat_ok
            cat_rate = cat_ok / len(cat_settled) * 100 if cat_settled else 0
            summary_rows.append({
                "预测类型": cat,
                "记录": len(cat_hist),
                "已验证": len(cat_settled),
                "对": cat_ok,
                "错": cat_bad,
                "待开": sum(1 for x in cat_hist if x.get("result") == "待开"),
                "正确率": f"{cat_rate:.1f}%",
            })
        if summary_rows:
            st.markdown("#### 📊 各类型验证汇总")
            st.dataframe(
                pd.DataFrame(summary_rows),
                use_container_width=True,
                hide_index=True,
            )

    rows = []
    for x in filtered[:80]:
        res = x.get("result", "")
        if res == "对":
            mark = "✅ 对"
        elif res == "错":
            mark = "❌ 错"
        else:
            mark = "⏳ 待开"

        rows.append({
            "记录期号": x.get("issue"),
            "结算期": x.get("settle_issue", "-"),
            "类型": x.get("cat"),
            "形态": x.get("pattern"),
            "倾向": x.get("lean"),
            "样本": x.get("sample"),
            "比例%": x.get("pct"),
            "实际": x.get("actual") or "-",
            "结果": mark,
            "时间": x.get("time"),
        })

    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            height=360,
            hide_index=True,
        )
    else:
        st.info("当前筛选条件下暂无预测记录。")


name_to_item = {x["name"]: x for x in LOTTERY_CATALOG}

with st.sidebar:
    st.header("⚙️ 设置")
    lottery_name = st.selectbox("选择彩种", [x["name"] for x in LOTTERY_CATALOG], index=0)
    item = name_to_item[lottery_name]
    lot_code = item["code"]
    lot_type = item["type"]
    force_refresh = st.button("🔄 强制刷新数据")
    n_recent = st.slider("分析最近期数", 30, 500, 100, 10)
    ft_days = st.slider("拉取最近几天数据", 1, 14, 7)
    st.caption("接口每天最多约50条，天数越多路珠样本越足")
    auto_refresh = st.checkbox("⏱ 实时看板自动刷新（5 秒）", value=True)
    if auto_refresh:
        st.caption("实时开奖结果 + 预测结果独立局部刷新，历史数据不会跟着重载")
    st.markdown("---")
    st.caption(f"当前 lotCode = {lot_code}")
    st.caption("数据源：api.api16868.com")
    with st.expander("全部彩种列表"):
        for x in LOTTERY_CATALOG:
            st.write(f"· {x['name']}（{x['code']} / {x['type']}）")


# ---------- PK10 家族 ----------
if lot_type == "pks":
    if force_refresh:
        load_pks.clear()
    df = load_pks(lot_code, ft_days)
    if df.empty:
        st.error("数据加载失败，请稍后重试")
        st.stop()
    latest = df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("已加载期数", f"{len(df):,}")
    c2.metric("历史最新期号", latest["期号"])
    c3.metric("历史开奖时间", str(latest["开奖时间"])[:19])
    render_live_panel(lot_code, lottery_name, "pks")

    seq_dx, seq_ds = pks_dx_seq(df), pks_ds_seq(df)
    pred_key = "pks_%s" % lot_code
    render_prediction_panel(lot_code, "pks", pred_key, seq_dx, seq_ds)

    recent_df = df.tail(min(n_recent, len(df)))
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 名次频率", "🏆 冠军&冠亚和", "🐉 龙虎", "🔴 路珠", "📋 历史", "✅ 预测对错"])
    with tab1:
        d = recent_df
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
        d = recent_df
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
        d = recent_df.copy()
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
        show["大小"] = np.where(show["冠亚和"].astype(int) > 11, "大", "小")
        show["单双"] = np.where(show["冠亚和"].astype(int) % 2 == 1, "单", "双")
        st.dataframe(show.iloc[::-1], use_container_width=True, height=400)
        st.download_button("下载CSV", df.to_csv(index=False).encode("utf-8-sig"),
                           f"pks_{lot_code}_{datetime.now():%Y%m%d}.csv", "text/csv")
    with tab6:
        st.subheader("预测历史 · 对错统计")
        st.caption("根据自动对照的「倾向」与下期实际开奖比对。仅供复盘，不代表可稳定盈利。")
        render_pred_history("pks_%s" % lot_code)
        if st.button("清空本彩种预测记录", key="clr_pks_%s" % lot_code):
            st.session_state.pred_hist = [x for x in st.session_state.get("pred_hist", []) if x.get("key") != "pks_%s" % lot_code]
            st.rerun()

# ---------- Luck20 家族 ----------
else:
    if force_refresh:
        load_luck20.clear()
    df = load_luck20(lot_code, ft_days)
    if df.empty:
        st.error("数据加载失败，请稍后重试")
        st.stop()
    latest = df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("已加载期数", f"{len(df):,}")
    c2.metric("历史最新期号", str(latest["期号"]))
    c3.metric("历史开奖时间", str(latest["开奖时间"])[:19])
    render_live_panel(lot_code, lottery_name, "luck20")

    seq_dx = df["大小"].tolist()
    seq_ds = df["单双"].tolist()
    seq_combo = df["组合"].tolist()
    st.caption("历史样本：已加载 **%d** 期（接口每天约返回最近50条，多选天数可累积）" % len(df))
    pred_key = "l20_%s" % lot_code
    render_prediction_panel(lot_code, "luck20", pred_key, seq_dx, seq_ds)

    recent_df = df.tail(min(n_recent, len(df)))
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 号码频率", "📈 和值", "🎲 大小单双", "🔴 路珠", "📋 历史", "✅ 预测对错"])
    with tab1:
        cols = [c for c in df.columns if c.startswith("号") and c[1:].isdigit()]
        d = recent_df
        freq = pd.Series(d[cols].values.flatten()).value_counts().reindex(range(1, 81), fill_value=0)
        fig = px.bar(x=freq.index, y=freq.values, title=f"1-80 频率（近{min(n_recent,len(df))}期）",
                     color=freq.values, color_continuous_scale="Viridis")
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
        c1, c2 = st.columns(2)
        c1.write("**热号** " + " ".join(f"`{i:02d}`" for i in freq.nlargest(10).index))
        c2.write("**冷号** " + " ".join(f"`{i:02d}`" for i in freq.nsmallest(10).index))
    with tab2:
        recent = recent_df
        fig = px.line(recent, x="期号", y="和值", title="和值走势", markers=True)
        fig.add_hline(y=recent["和值"].mean(), line_dash="dash")
        fig.add_hline(y=810, line_dash="dot", annotation_text="810 分界")
        st.plotly_chart(fig, use_container_width=True)
    with tab3:
        d = recent_df
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
        cols_show = ["期号", "开奖时间", "和值", "大小", "单双", "组合"]
        if "附加号" in df.columns:
            cols_show.insert(3, "附加号")
        show = df.tail(50)[[c for c in cols_show if c in df.columns]].copy()
        st.dataframe(show.iloc[::-1], use_container_width=True, height=400)
        st.download_button("下载CSV", df.drop(columns=["号码"], errors="ignore").to_csv(index=False).encode("utf-8-sig"),
                           f"luck20_{lot_code}_{datetime.now():%Y%m%d}.csv", "text/csv")
    with tab6:
        st.subheader("预测历史 · 对错统计")
        st.caption("根据自动对照的「倾向」与下期实际开奖比对。仅供复盘。")
        render_pred_history("l20_%s" % lot_code)
        if st.button("清空本彩种预测记录", key="clr_l20_%s" % lot_code):
            st.session_state.pred_hist = [x for x in st.session_state.get("pred_hist", []) if x.get("key") != "l20_%s" % lot_code]
            st.rerun()

st.markdown('<div class="footer-note">仅供学习 · 请理性购彩，远离赌博心态</div>', unsafe_allow_html=True)
