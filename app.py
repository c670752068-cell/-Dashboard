import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import time
from datetime import datetime, timedelta

# 伪装浏览器绕过 Yahoo Finance 的反爬虫
try:
    from curl_cffi import requests as _cffi_requests
    def _make_yf_session():
        return _cffi_requests.Session(impersonate="chrome")
except ImportError:
    def _make_yf_session():
        return None


def _yf_download_with_retry(tickers, **kwargs):
    """带重试的 yf.download，最多重试 3 次，指数退避。"""
    session = _make_yf_session()
    if session is not None:
        kwargs.setdefault("session", session)
    last_err = None
    for attempt in range(3):
        try:
            df = yf.download(tickers, progress=False, **kwargs)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            last_err = e
        if attempt < 2:
            time.sleep(1.5 ** attempt)
    if last_err is not None:
        raise last_err
    return pd.DataFrame()

# 让 matplotlib 能显示中文（Mac / Windows / Linux 字体回退链）
matplotlib.rcParams["font.sans-serif"] = [
    "Microsoft YaHei", "SimHei", "Microsoft JhengHei",       # Windows
    "PingFang HK", "Hiragino Sans GB", "STHeiti", "Songti SC",  # macOS
    "Noto Sans CJK SC", "WenQuanYi Zen Hei",                 # Linux
    "Arial Unicode MS", "DejaVu Sans",                       # 通用兜底
]
matplotlib.rcParams["axes.unicode_minus"] = False

# ============================================================
# 筛选器用：股票宇宙
# 字段：(代码, 板块, 市值档)  市值档：1=$100B+ / 2=$200B+ / 3=$300B+ / 4=$400B+
# ============================================================
UNIVERSE = [
    # 七大科技 Magnificent 7
    ("AAPL", "消费电子", 4), ("MSFT", "软件/互联网", 4), ("GOOGL", "软件/互联网", 4),
    ("AMZN", "软件/互联网", 4), ("META", "软件/互联网", 4), ("NVDA", "半导体", 4),
    ("TSLA", "汽车/电动车", 4),
    # 半导体
    ("AVGO", "半导体", 4), ("TSM", "半导体", 4), ("ASML", "半导体", 3),
    ("AMD", "半导体", 2), ("QCOM", "半导体", 1), ("INTC", "半导体", 1),
    ("TXN", "半导体", 1), ("AMAT", "半导体", 1), ("LRCX", "半导体", 1),
    ("KLAC", "半导体", 1), ("MU", "半导体", 1), ("ARM", "半导体", 1),
    # 软件/互联网
    ("ORCL", "软件/互联网", 4), ("CRM", "软件/互联网", 3), ("ADBE", "软件/互联网", 2),
    ("NOW", "软件/互联网", 2), ("INTU", "软件/互联网", 1), ("PANW", "软件/互联网", 1),
    ("IBM", "软件/互联网", 2), ("CSCO", "软件/互联网", 2),
    ("SHOP", "软件/互联网", 1), ("UBER", "软件/互联网", 1),
    # 媒体/通信
    ("NFLX", "媒体/通信", 4), ("DIS", "媒体/通信", 2), ("T", "媒体/通信", 2),
    ("VZ", "媒体/通信", 2), ("TMUS", "媒体/通信", 2), ("CMCSA", "媒体/通信", 1),
    # 工业/航空国防
    ("CAT", "工业", 1), ("GE", "工业", 2), ("BA", "工业", 1), ("HON", "工业", 1),
    ("RTX", "工业", 1), ("LMT", "工业", 1), ("DE", "工业", 1),
    ("UNP", "工业", 1), ("UPS", "工业", 1), ("ETN", "工业", 1),
    # 能源
    ("XOM", "能源", 4), ("CVX", "能源", 2), ("COP", "能源", 1),
    ("SLB", "能源", 1), ("EOG", "能源", 1),
    # 基础材料
    ("LIN", "基础材料", 2), ("SHW", "基础材料", 1), ("FCX", "基础材料", 1),
    ("NEM", "基础材料", 1), ("NUE", "基础材料", 1),
    # 医疗
    ("LLY", "医疗", 4), ("UNH", "医疗", 4), ("JNJ", "医疗", 4), ("ABBV", "医疗", 3),
    ("MRK", "医疗", 2), ("PFE", "医疗", 1), ("TMO", "医疗", 2), ("ABT", "医疗", 2),
    ("DHR", "医疗", 1), ("AMGN", "医疗", 1), ("BMY", "医疗", 1), ("GILD", "医疗", 1),
    # 金融
    ("BRK-B", "金融", 4), ("JPM", "金融", 4), ("V", "金融", 4), ("MA", "金融", 4),
    ("BAC", "金融", 3), ("WFC", "金融", 2), ("GS", "金融", 1), ("MS", "金融", 1),
    ("BLK", "金融", 1), ("SPGI", "金融", 1), ("AXP", "金融", 2),
    ("C", "金融", 1), ("SCHW", "金融", 1),
    # 消费/零售
    ("WMT", "消费/零售", 4), ("COST", "消费/零售", 4), ("HD", "消费/零售", 4),
    ("PG", "消费/零售", 4), ("KO", "消费/零售", 3), ("PEP", "消费/零售", 2),
    ("MCD", "消费/零售", 2), ("NKE", "消费/零售", 1), ("SBUX", "消费/零售", 1),
    ("LULU", "消费/零售", 1), ("LOW", "消费/零售", 1), ("TGT", "消费/零售", 1),
    # 公用事业/地产
    ("NEE", "公用事业/地产", 1), ("PLD", "公用事业/地产", 1), ("AMT", "公用事业/地产", 1),
]
MAG7 = {"AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"}

st.set_page_config(page_title="股票趋势仪表盘", layout="wide", page_icon="📊")

st.markdown("""
<style>
div[data-testid="stMetricValue"] { font-size: 32px; font-weight: 700; }
.big-num { font-size: 34px; font-weight: 700; line-height: 1.1; }
.badge { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.badge-green   { background-color: #1f7a3a; color: white; }
.badge-red     { background-color: #c62828; color: white; }
.badge-amber   { background-color: #ef6c00; color: white; }
.badge-neutral { background-color: #d0d0d0; color: #2a2a2a; }
.dot-green { color: #2ecc71; }
.dot-white { color: white; }
.arrow-up   { color: #1f7a3a; font-weight: 700; margin-right: 4px; font-size: 14px; }
.arrow-down { color: #c62828; font-weight: 700; margin-right: 4px; font-size: 14px; }

/* 手机适配：屏幕窄于 640px 时缩小数字和徽章 */
@media (max-width: 640px) {
    .big-num { font-size: 22px; }
    .badge { font-size: 10px; padding: 3px 8px; }
    div[data-testid="stMetricValue"] { font-size: 22px; }
    h1 { font-size: 22px !important; }
    h2 { font-size: 18px !important; }
    h3 { font-size: 16px !important; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("## 📊 股票趋势分析仪表盘 · 200日均线 × 偏离度 × 历史回测")

tab_dash, tab_screen, tab_ratio, tab_guide = st.tabs(
    ["📊 仪表盘", "🔍 筛选器", "📈 相对强度", "📖 使用说明"]
)

# ============================================================
# 📖 使用说明 Tab —— 先渲染，确保 dashboard 即使报错也能看到
# ============================================================
with tab_guide:
    st.markdown("""
### 🎯 这个仪表盘在告诉你什么？

它帮你回答三个问题：
1. **这只股票的长期趋势是涨还是跌？** → 看 **斜率（趋势）**
2. **当前股价相对趋势线是太贵还是太便宜？** → 看 **Z值（偏离度）**
3. **历史上这种状态接下来40天平均怎么走？** → 看下面的 **「未来40天表现」表格**

---

### 1️⃣ 当前股价
就是这只股票现在的收盘价。

---

### 2️⃣ 200日均线
> 过去 200 个交易日（约 10 个月）的平均收盘价。

- 华尔街最常用的**长期趋势线**。
- 股价在它**上方** → 长期偏多头；在它**下方** → 长期偏空头。
- 旁边的百分比 = 当前股价**高于 / 低于** 200 日均线多少 %。
- 实战：很多机构把 200 日均线当**支撑线**——股价回踩到这条线附近，常常是逢低买入的位置。

---

### 3️⃣ Z值（偏离度） · ⭐ 整个仪表盘最核心的数字

**公式**：`Z值 = (当前股价 - 200日均线) ÷ 近60日的标准差`

**通俗解释**：用"标准差"为单位，衡量当前股价偏离趋势线**多远**。

| Z值 | 解读 | 历史出现频率 |
|---|---|---|
| 0 | 股价正好在均线上 | — |
| +1 | 略偏高，但还正常 | 常见 |
| +2 | **过热**（可能回调）| 约 2.5% 的时间 |
| -2 | **过冷**（可能反弹）| 约 2.5% 的时间 |

**为什么不直接看"涨幅 %"？** 不同股票波动率不一样——特斯拉涨 10% 是日常，可口可乐涨 10% 是地震。Z值把波动率标准化了，可以**跨股票横向比较**。

**徽章规则**：

| Z值 范围 | 徽章 |
|---|---|
| < -1.5 | 🔴 深度超卖（常见反弹买点）|
| -1.5 ~ -1.0 | 🟠 轻度超卖 |
| -1.0 ~ +1.5 | ⚪ 正常区间 |
| > +1.5 | 🔴 深度超买（可能回调）|

---

### 4️⃣ 斜率（趋势强度）

**公式**：`200日均线过去 20 天涨幅 × 252/20`（年化）

**通俗解释**：这条均线本身正在以多快的速度**上升或下降**。

- `> 0` → 均线在往上走 → 长期趋势向上 ✅
- `< 0` → 均线在往下走 → 长期趋势向下 ❌

**徽章规则**：

| 斜率 范围 | 徽章 |
|---|---|
| > 10% | 🟢 强势上涨 |
| 0 ~ 10% | ⚪ 弱势上涨 |
| -10% ~ 0 | 🟠 弱势下跌 |
| < -10% | 🔴 强势下跌 |

---

### 5️⃣ 所在区间

当前 Z值 落在哪个"分桶"里。跟下面的**「未来40天表现」表格**配对使用。

比如显示 `1.0 至 1.5`，到表里找这一行，就能看到**历史上每次 Z值落在这个区间时，未来 40 天平均怎么走**。

表格各列含义：
- **样本数** — 历史上发生过几次（样本越多越可靠）
- **平均收益%** — 未来 40 天的**平均收益率**
- **中位数收益%** — 未来 40 天的**中位数收益**（不受极端值干扰，更稳健）
- **胜率%** — 未来 40 天**收益为正**的比例

---

### 📊 三张图怎么看

**主图（最上面）**：
- ⚪ 白线 = 股价
- 🟥 红色虚线 = 200 日均线
- 🟨 黄色阴影带 = 均线 ± 1.5σ 的"正常波动区间"（约等于 Z = ±1.5 的物理位置）
- 股价**跌出黄带下沿** = 超卖买点信号
- 股价**冲出黄带上沿** = 超买卖点信号

**第 2 张（绿/红柱）**：200 日均线斜率的历史变化
- 🟢 绿柱 = 上行期（趋势向上）
- 🔴 红柱 = 下行期（趋势向下）
- **颜色翻转点 = 长期趋势拐点**

**第 3 张（Z值柱）**：每天的 Z值
- 🔴 红柱（Z < -1.5）= 超卖期，潜在买点
- 🟦 蓝柱（Z > +1.5）= 超买期，潜在卖点
- ⚪ 灰柱 = 正常区间

---

### 🎯 实战决策框架 · 把所有数字拼起来用

| 斜率（趋势）| Z值（位置）| 含义 | 操作倾向 |
|---|---|---|---|
| ↑ 上行 | 极低（深度超卖）| **牛市中的回调** | 🟢 **重仓买入**（最佳买点）|
| ↑ 上行 | 中性 | 正常上涨中 | 🟡 持有 / 小幅加仓 |
| ↑ 上行 | 极高（深度超买）| **狂热顶部信号** | 🟠 减仓锁利 |
| ↓ 下行 | 极低 | 熊市中反弹 | 🔴 **不抄底**（趋势是空头）|
| ↓ 下行 | 中性 | 正常下跌中 | 🔴 观望 / 做空 |
| ↓ 下行 | 极高 | 熊市反弹乏力 | 🔴 **卖出**（最佳卖点）|

**核心思想**：
- **大方向看斜率** —— 决定要不要参与
- **入场点看 Z值** —— 决定贵还是便宜
- **预期看未来40天表格** —— 看历史上类似状态平均怎么走

---

### ⚠️ 重要提醒

1. 这是**统计模型**，不是水晶球。"历史胜率 70%" ≠ 下一次一定赢。
2. 200 日均线模型适合**有长期方向的资产**（大盘指数、龙头股）。**仙股、小盘股、暴涨暴跌的概念股不适用**。
3. 财报前后、宏观突发事件（加息、战争等）会让模型短期失效。
4. **永远设止损**。

---

*数据来源：Yahoo Finance · 仅供学习研究使用，不构成投资建议*
""")

# ============================================================
# 🔍 筛选器 Tab —— 全市场扫描
# ============================================================
with tab_screen:
    st.markdown("### 🔍 全市场超买/超卖筛选")
    st.caption(f"宇宙：{len(UNIVERSE)} 只主要美股（含七大科技、半导体、能源、工业、基础材料等）")

    sc1, sc2 = st.columns(2)
    with sc1:
        cap_choice = st.selectbox(
            "① 市值筛选",
            ["全部", "🌟 七大科技（Magnificent 7）",
             "$100B+（千亿美元以上）",
             "$200B+（两千亿美元以上）",
             "$300B+（三千亿美元以上）",
             "$400B+（四千亿美元以上）"],
        )
    with sc2:
        all_sectors = sorted({s for _, s, _ in UNIVERSE})
        sector_choice = st.multiselect("② 行业筛选（不选 = 全部）", all_sectors)

    sc3, sc4 = st.columns(2)
    with sc3:
        status_choice = st.selectbox(
            "③ 当前状态",
            ["全部",
             "🔴 深度超卖（Z < -1.5）",
             "🟠 轻度超卖（-1.5 ≤ Z < -1.0）",
             "⚪ 正常（-1.0 ≤ Z ≤ 1.5）",
             "🟦 深度超买（Z > 1.5）"],
        )
    with sc4:
        z_range = st.slider("④ Z 值精确范围", -10.0, 10.0, (-10.0, 10.0), 0.1)

    # 应用市值/板块过滤先得到候选 tickers（让用户先知道要扫描多少只）
    def filter_by_cap_sector(universe, cap_choice, sectors):
        out = []
        for t, sec, tier in universe:
            if cap_choice == "🌟 七大科技（Magnificent 7）" and t not in MAG7:
                continue
            if cap_choice == "$100B+（千亿美元以上）" and tier < 1:
                continue
            if cap_choice == "$200B+（两千亿美元以上）" and tier < 2:
                continue
            if cap_choice == "$300B+（三千亿美元以上）" and tier < 3:
                continue
            if cap_choice == "$400B+（四千亿美元以上）" and tier < 4:
                continue
            if sectors and sec not in sectors:
                continue
            out.append((t, sec, tier))
        return out

    candidates = filter_by_cap_sector(UNIVERSE, cap_choice, sector_choice)
    st.caption(f"📌 本次将扫描 **{len(candidates)}** 只股票")

    do_scan = st.button("🔍 开始扫描", type="primary", use_container_width=True)

    @st.cache_data(ttl=1800, show_spinner=False)
    def scan_universe(tickers_tuple):
        tickers = list(tickers_tuple)
        end = pd.Timestamp.today()
        start = end - pd.Timedelta(days=500)
        df = _yf_download_with_retry(tickers, start=start, end=end + pd.Timedelta(days=1),
                                     auto_adjust=True)
        rows = []
        # 处理多/单 ticker 的列结构
        if isinstance(df.columns, pd.MultiIndex):
            close_df = df["Close"]
        else:
            close_df = pd.DataFrame({tickers[0]: df["Close"]})
        for t in tickers:
            if t not in close_df.columns:
                continue
            px = close_df[t].dropna()
            if len(px) < 220:
                continue
            ma = px.rolling(200).mean()
            sd = px.rolling(60).std()
            z = (px - ma) / sd
            sl = (ma.pct_change(20) * 252 / 20) * 100
            if pd.isna(z.iloc[-1]) or pd.isna(sl.iloc[-1]):
                continue
            rows.append({
                "代码": t,
                "股价": round(float(px.iloc[-1]), 2),
                "200日均线": round(float(ma.iloc[-1]), 2),
                "偏离%": round((float(px.iloc[-1]) / float(ma.iloc[-1]) - 1) * 100, 1),
                "Z值": round(float(z.iloc[-1]), 2),
                "斜率%": round(float(sl.iloc[-1]), 1),
            })
        # 同时返回原始 close 数据，给后续画图复用
        return pd.DataFrame(rows), close_df

    if do_scan:
        if not candidates:
            st.warning("当前筛选条件下没有候选股票，请放宽市值或行业。")
        else:
            tickers_to_scan = tuple(t for t, _, _ in candidates)
            sector_map = {t: sec for t, sec, _ in candidates}
            tier_map = {t: tier for t, _, tier in candidates}

            with st.spinner(f"正在扫描 {len(tickers_to_scan)} 只股票，第一次约需 20-40 秒，已缓存的会秒回..."):
                result, close_data = scan_universe(tickers_to_scan)

            if result.empty:
                st.warning("没有取到任何数据。可能是网络问题或代码失效，请稍后重试。")
            else:
                # 加板块和信号列
                result["板块"] = result["代码"].map(sector_map)
                result["市值档"] = result["代码"].map(lambda t: {1:"$100B+",2:"$200B+",3:"$300B+",4:"$400B+"}.get(tier_map.get(t), "?"))

                def signal(z):
                    if z < -1.5: return "🔴 深度超卖"
                    if z < -1.0: return "🟠 轻度超卖"
                    if z > 1.5:  return "🟦 深度超买"
                    return "⚪ 正常"
                result["信号"] = result["Z值"].apply(signal)

                def trend(slope):
                    if slope > 10: return "🟢 强势上涨"
                    if slope > 0:  return "🟡 弱势上涨"
                    if slope > -10: return "🟠 弱势下跌"
                    return "🔴 强势下跌"
                result["趋势"] = result["斜率%"].apply(trend)

                # 应用 状态 + Z值范围 过滤
                mask = result["Z值"].between(z_range[0], z_range[1])
                if status_choice.startswith("🔴 深度超卖"):
                    mask &= result["Z值"] < -1.5
                elif status_choice.startswith("🟠 轻度超卖"):
                    mask &= result["Z值"].between(-1.5, -1.0, inclusive="left")
                elif status_choice.startswith("⚪ 正常"):
                    mask &= result["Z值"].between(-1.0, 1.5, inclusive="both")
                elif status_choice.startswith("🟦 深度超买"):
                    mask &= result["Z值"] > 1.5

                filtered = result[mask].sort_values("Z值", ascending=True)

                # 顶部摘要
                n_over_sold = (result["Z值"] < -1.5).sum()
                n_over_bought = (result["Z值"] > 1.5).sum()
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("扫描完成", f"{len(result)} 只")
                col_b.metric("符合条件", f"{len(filtered)} 只")
                col_c.metric("🔴 深度超卖", f"{n_over_sold} 只")
                col_d.metric("🟦 深度超买", f"{n_over_bought} 只")

                st.markdown("---")

                if filtered.empty:
                    st.info("没有股票符合「状态 + Z值范围」筛选。试试放宽条件？")
                else:
                    st.markdown(f"**结果（按 Z值 从低到高排序，最超卖在最上面）**")
                    display = filtered[["代码", "板块", "市值档", "股价", "200日均线", "偏离%", "Z值", "斜率%", "信号", "趋势"]]
                    st.dataframe(
                        display,
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "股价": st.column_config.NumberColumn(format="$%.2f"),
                            "200日均线": st.column_config.NumberColumn(format="$%.2f"),
                            "偏离%": st.column_config.NumberColumn(format="%+.1f%%"),
                            "Z值": st.column_config.NumberColumn(format="%.2f"),
                            "斜率%": st.column_config.NumberColumn(format="%+.1f%%"),
                        },
                        height=min(600, 38 * (len(filtered) + 1) + 10),
                    )

                    st.caption("💡 想看某只股票的完整分析？复制代码到 「📊 仪表盘」标签的股票代码框里")

                    # ---- 个股走势图网格 ----
                    MAX_CHARTS = 12
                    charts_to_show = filtered.head(MAX_CHARTS)["代码"].tolist()
                    if len(filtered) > MAX_CHARTS:
                        st.caption(f"⚠️ 共 **{len(filtered)}** 只符合，只展示前 {MAX_CHARTS} 张图（按 Z值从低到高，最超卖优先）。完整名单见上方表格。")

                    st.markdown("---")
                    st.markdown("### 📈 个股走势图")

                    # 两列网格
                    for i in range(0, len(charts_to_show), 2):
                        ch_cols = st.columns(2)
                        for j, ch_col in enumerate(ch_cols):
                            if i + j >= len(charts_to_show):
                                continue
                            tk = charts_to_show[i + j]
                            with ch_col:
                                if tk not in close_data.columns:
                                    st.warning(f"{tk}: 数据缺失")
                                    continue
                                pxs = close_data[tk].dropna()
                                if len(pxs) < 220:
                                    st.warning(f"{tk}: 数据不足")
                                    continue
                                ma_full = pxs.rolling(200).mean()
                                sd_full = pxs.rolling(60).std()
                                upper_full = ma_full + 1.5 * sd_full
                                lower_full = ma_full - 1.5 * sd_full

                                # 最近 2 年窗口
                                cutoff = pxs.index[-1] - pd.Timedelta(days=730)
                                m = pxs.index >= cutoff

                                row = filtered[filtered["代码"] == tk].iloc[0]
                                z_v, sig_v, trend_v = row["Z值"], row["信号"], row["趋势"]

                                fig_s, ax_s = plt.subplots(figsize=(8, 4.2))
                                ax_s.plot(pxs[m].index, pxs[m], color="white", lw=1.1, label=f"{tk} 股价")
                                ax_s.plot(ma_full[m].index, ma_full[m], color="#FF6B6B",
                                          lw=1.4, linestyle="--", label="200 日均线")
                                ax_s.fill_between(ma_full[m].index, lower_full[m], upper_full[m],
                                                  alpha=0.18, color="#cccc66", label="1.5σ 区间带")
                                ax_s.set_title(f"{tk}   ·   Z={z_v:.2f}   ·   {sig_v}   ·   {trend_v}",
                                               color="white", fontsize=11, fontweight="bold")
                                ax_s.set_ylabel("股价 ($)", color="white", fontsize=9)
                                ax_s.set_facecolor("#1a1a2e")
                                ax_s.grid(True, alpha=0.2)
                                ax_s.legend(loc="upper left", fontsize=8)
                                ax_s.tick_params(colors="white", labelsize=8)
                                for sp in ax_s.spines.values():
                                    sp.set_color("#444")
                                fig_s.patch.set_facecolor("#0d0d1a")
                                plt.tight_layout()
                                st.pyplot(fig_s)
                                plt.close(fig_s)
    else:
        st.info("👆 选好筛选条件，点 **开始扫描** 按钮")


# ============================================================
# 📈 相对强度 Tab —— 板块比值 + 60/200MA + MACD
# ============================================================
DEFAULT_RATIO_PAIRS = [
    ("SLV",  "SPY", "Silver/SPX"),
    ("GLD",  "SPY", "Gold/SPX"),
    ("QQQ",  "SPY", "NDX/SPX"),
    ("GLD",  "SLV", "Gold/Silver"),
    ("GDX",  "GLD", "GDX/Gold"),
    ("NVDA", "QQQ", "NVDA/NDX"),
    ("TSLA", "QQQ", "TSLA/NDX"),
    ("XOP",  "SPY", "XOP/SPX"),
    ("SMH",  "QQQ", "SMH/NDX"),
]

with tab_ratio:
    st.markdown("### 📈 相对强度比率仪表盘")
    st.caption(
        "两只标的的比值走势（分子/分母）+ 60日均线 + 200日均线 + MACD(8/17/9)。"
        "**比值上升** = 分子相对分母**强势**；**比值下降** = 弱势。"
    )

    rc1, rc2 = st.columns(2)
    with rc1:
        ratio_start = st.date_input(
            "开始日期", value=pd.Timestamp("2021-01-01").date(), key="ratio_start"
        )
    with rc2:
        ratio_end = st.date_input(
            "结束日期", value=datetime.today().date(), key="ratio_end"
        )

    default_pairs_text = "\n".join(f"{n},{d},{l}" for n, d, l in DEFAULT_RATIO_PAIRS)
    with st.expander("⚙️ 配对设置（默认 9 组主流板块比值，可自定义）", expanded=False):
        st.caption("每行一个配对，格式：`分子代码,分母代码,显示标签`")
        pairs_text = st.text_area(
            "配对列表", value=default_pairs_text, height=250, label_visibility="collapsed",
        )

    pairs = []
    for line in pairs_text.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3 and parts[0] and parts[1]:
            pairs.append((parts[0].upper(), parts[1].upper(), parts[2]))

    if not pairs:
        st.warning("请至少配置一对。")
    else:
        st.caption(f"📌 将生成 **{len(pairs)}** 组比值图")
        gen_ratio = st.button("📈 生成相对强度图", type="primary", use_container_width=True)

        if gen_ratio:
            tickers = sorted({t for p in pairs for t in p[:2]})

            with st.spinner(f"加载 {len(tickers)} 只标的数据..."):
                try:
                    raw = _yf_download_with_retry(
                        tickers,
                        start=pd.Timestamp(ratio_start),
                        end=pd.Timestamp(ratio_end) + pd.Timedelta(days=1),
                        auto_adjust=True,
                    )
                except Exception as e:
                    err_str = str(e)
                    if any(k in err_str for k in ["Too Many Requests", "Rate limited", "YFRateLimitError"]):
                        st.error("⛔ Yahoo Finance 限流，等 5-15 分钟再试或切换 VPN 节点。")
                    else:
                        st.error(f"下载失败：{err_str[:200]}")
                    st.stop()

            if raw is None or raw.empty:
                st.error("没拉到任何数据。可能是 Yahoo 限流，等几分钟或切 VPN 节点。")
                st.stop()

            if isinstance(raw.columns, pd.MultiIndex):
                closes = raw["Close"]
            else:
                closes = raw[["Close"]].copy()
                closes.columns = tickers[:1]
            closes = closes.dropna(how="all").ffill()

            def _compute_macd(s, fast=8, slow=17, signal=9):
                ema_f = s.ewm(span=fast, adjust=False).mean()
                ema_s = s.ewm(span=slow, adjust=False).mean()
                m = ema_f - ema_s
                sig = m.ewm(span=signal, adjust=False).mean()
                return m, sig, m - sig

            from matplotlib import gridspec
            from matplotlib.dates import DateFormatter, YearLocator

            # Shepherd 配色
            BG, PANEL, GRID, TEXT = "#0d0d0d", "#0d0d0d", "#2a2a2a", "#e0e0e0"
            RATIO_C, MA60_C, MA200_C = "#4a90e2", "#e87722", "#bdbdbd"
            HIST_UP, HIST_DN = "#26a69a", "#ef5350"

            n = len(pairs)
            n_cols = 3 if n >= 3 else n
            n_rows = int(np.ceil(n / n_cols))

            fig = plt.figure(figsize=(16, 4.5 * n_rows), facecolor=BG)
            outer = gridspec.GridSpec(
                n_rows, n_cols, figure=fig,
                hspace=0.55, wspace=0.22,
                left=0.04, right=0.98, top=0.94, bottom=0.04,
            )

            missing = []
            for idx, (num, den, label) in enumerate(pairs):
                r, c = divmod(idx, n_cols)
                inner = gridspec.GridSpecFromSubplotSpec(
                    2, 1, subplot_spec=outer[r, c],
                    height_ratios=[3, 1], hspace=0.05,
                )
                ax_r = fig.add_subplot(inner[0])
                ax_m = fig.add_subplot(inner[1], sharex=ax_r)

                if num not in closes.columns or den not in closes.columns:
                    ax_r.set_title(f"{label}（数据缺失）", color="#ef5350", fontsize=10)
                    ax_r.set_facecolor(PANEL)
                    ax_m.set_facecolor(PANEL)
                    missing.append(label)
                    continue

                ratio = (closes[num] / closes[den]).dropna()
                ma60 = ratio.rolling(60).mean()
                ma200 = ratio.rolling(200).mean()
                macd, sig_line, hist = _compute_macd(ratio)

                ax_r.plot(ratio.index, ratio, color=RATIO_C, lw=1.0)
                ax_r.plot(ma60.index, ma60, color=MA60_C, lw=1.3)
                ax_r.plot(ma200.index, ma200, color=MA200_C, lw=1.3)
                ax_r.set_title(label, color=TEXT, fontsize=11, fontweight="bold", pad=6)
                ax_r.tick_params(axis="x", labelbottom=False)

                bar_colors = np.where(hist >= 0, HIST_UP, HIST_DN)
                ax_m.bar(hist.index, hist, color=bar_colors, width=1.0, alpha=0.6)
                ax_m.plot(macd.index, macd, color=RATIO_C, lw=0.9)
                ax_m.plot(sig_line.index, sig_line, color=MA60_C, lw=0.9)
                ax_m.axhline(0, color=GRID, lw=0.6)

                for ax in (ax_r, ax_m):
                    ax.set_facecolor(PANEL)
                    ax.grid(True, color=GRID, lw=0.4, alpha=0.6)
                    ax.tick_params(colors=TEXT, labelsize=7)
                    for spine in ax.spines.values():
                        spine.set_color(GRID)

                ax_m.xaxis.set_major_locator(YearLocator())
                ax_m.xaxis.set_major_formatter(DateFormatter("%Y"))
                plt.setp(ax_m.get_xticklabels(), rotation=0, ha="center")

            handles = [
                plt.Line2D([0], [0], color=MA60_C, lw=2, label="60 日均线"),
                plt.Line2D([0], [0], color=MA200_C, lw=2, label="200 日均线"),
                plt.Line2D([0], [0], color=RATIO_C, lw=2, label="比值"),
            ]
            fig.legend(
                handles=handles, loc="upper center",
                bbox_to_anchor=(0.5, 0.985), ncol=3,
                frameon=False, labelcolor=TEXT, fontsize=10,
            )
            fig.text(0.04, 0.985, "相对强度比率图",
                     color=TEXT, fontsize=14, fontweight="bold", va="center")
            fig.text(0.98, 0.005, "Shepherd Capital Markets · 牧羊人资本市场",
                     color="#666", fontsize=8, ha="right", style="italic")

            st.pyplot(fig)

            if missing:
                st.warning(f"以下配对数据缺失（可能代码错误或 Yahoo 没有该数据）：{', '.join(missing)}")

            with st.expander("📖 怎么看相对强度图？", expanded=False):
                st.markdown("""
**核心概念**：比值 = 分子价格 ÷ 分母价格
- 比值**上升** → 分子相对分母**强势**（例：NVDA/QQQ 上升 = 英伟达跑赢纳指）
- 比值**下降** → 分子相对分母**弱势**

**三条线**：
- 🔵 蓝色 = 实际比值
- 🟠 橙色 = 60 日均线（短期趋势）
- ⚪ 灰色 = 200 日均线（长期趋势）

**MACD（下方）**：动量指标
- 🟢 绿柱（柱在 0 轴上方）= 短期动量偏多
- 🔴 红柱（柱在 0 轴下方）= 短期动量偏空
- 柱由红转绿 = 动量翻多信号；由绿转红 = 翻空信号

**实战用法**：
1. **板块轮动**：比值在 200 日下方但开始往上回升 → 板块从弱势转强（潜在轮入点）
2. **强势确认**：比值持续位于 60/200 日均线上方 → 趋势成立
3. **顶背离**：比值创新高但 MACD 柱在缩短 → 警惕短期反转
4. **金叉/死叉**：60 日均线穿越 200 日均线 → 中长期趋势拐点

**经典组合解读**：
- `Gold/SPX` 上升 → 避险情绪上升（黄金跑赢股票）
- `XOP/SPX` 上升 → 能源板块跑赢大盘
- `SMH/QQQ` 上升 → 半导体跑赢纳指（科技股内部强势）
- `Gold/Silver` 上升 → 通胀预期下降 / 避险升温
""")


# ============================================================
# 📊 仪表盘 Tab
# ============================================================
with tab_dash:
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    with c1:
        ticker = st.text_input("股票代码", value="TSLA", help="例如：TSLA / NVDA / AAPL / 0700.HK（港股加 .HK）").strip().upper()
    with c2:
        start_date = st.date_input("开始日期", value=(datetime.today() - timedelta(days=365 * 5)).date())
    with c3:
        end_date = st.date_input("结束日期", value=datetime.today().date())
    with c4:
        st.write("")
        st.write("")
        if st.button("🔄 刷新", use_container_width=True):
            st.cache_data.clear()

    if not ticker:
        st.warning("请输入股票代码")
        st.stop()

    @st.cache_data(show_spinner=False, ttl=3600)
    def load_data(ticker: str, start, end):
        fetch_start = pd.Timestamp(start) - pd.Timedelta(days=400)
        return _yf_download_with_retry(
            ticker,
            start=fetch_start,
            end=pd.Timestamp(end) + pd.Timedelta(days=1),
            auto_adjust=True,
        )

    with st.spinner(f"正在加载 {ticker} 数据..."):
        try:
            data = load_data(ticker, start_date, end_date)
        except Exception as e:
            err_str = str(e)
            if "Too Many Requests" in err_str or "Rate limited" in err_str or "YFRateLimitError" in err_str:
                st.error(
                    f"⛔ **Yahoo Finance 限流了**（这是数据源问题，跟你代码无关）\n\n"
                    f"**怎么办**：\n"
                    f"1. 等 5-15 分钟再试（限流窗口会自动重置）\n"
                    f"2. 切换 VPN 节点 或 直接关掉 VPN\n"
                    f"3. 用手机热点试试\n\n"
                    f"*技术细节：`{err_str[:120]}`*"
                )
            else:
                st.error(f"加载 {ticker} 数据出错：{err_str[:200]}")
            st.stop()

    if data is None or data.empty:
        st.error(
            f"找不到 `{ticker}` 的数据。可能原因：\n"
            f"1. **Yahoo Finance 限流**（最常见）—— 等 5-15 分钟再试，或切换 VPN 节点\n"
            f"2. 股票代码拼错（港股加 .HK，A 股加 .SS / .SZ）"
        )
        st.stop()

    price = data["Close"].squeeze()
    ma200 = price.rolling(window=200).mean()
    rolling_std = price.rolling(window=60).std()
    zscore = (price - ma200) / rolling_std
    slope = (ma200.pct_change(20) * 252 / 20) * 100

    mask = price.index >= pd.Timestamp(start_date)
    price_plot = price[mask]
    ma200_plot = ma200[mask]
    zscore_plot = zscore[mask].dropna()
    slope_plot = slope[mask].dropna()

    if price_plot.empty or ma200_plot.dropna().empty:
        st.error("选定的时间窗口内数据不足，无法计算 200 日均线。请把开始日期往前调一些。")
        st.stop()

    latest_price = float(price.iloc[-1])
    latest_ma200 = float(ma200.dropna().iloc[-1])
    latest_zscore = float(zscore.dropna().iloc[-1])
    latest_slope = float(slope.dropna().iloc[-1])
    distance = (latest_price / latest_ma200 - 1) * 100

    bins_list = [-np.inf, -2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0, np.inf]
    labels = ['< -2.0', '-2.0 至 -1.5', '-1.5 至 -1.0', '-1.0 至 -0.5',
              '-0.5 至 0.5', '0.5 至 1.0', '1.0 至 1.5', '1.5 至 2.0', '> 2.0']

    current_bucket = "N/A"
    for i in range(len(bins_list) - 1):
        if bins_list[i] <= latest_zscore < bins_list[i + 1]:
            current_bucket = labels[i]
            break

    if latest_slope > 10:
        regime, regime_cls, regime_dot = "强势上涨", "badge-green", "dot-white"
    elif latest_slope > 0:
        regime, regime_cls, regime_dot = "弱势上涨", "badge-neutral", "dot-green"
    elif latest_slope > -10:
        regime, regime_cls, regime_dot = "弱势下跌", "badge-amber", "dot-white"
    else:
        regime, regime_cls, regime_dot = "强势下跌", "badge-red", "dot-white"

    if latest_zscore < -1.5:
        zsignal, zsignal_cls, zsignal_dot = "深度超卖", "badge-red", "dot-white"
    elif latest_zscore < -1.0:
        zsignal, zsignal_cls, zsignal_dot = "轻度超卖", "badge-amber", "dot-white"
    elif latest_zscore > 1.5:
        zsignal, zsignal_cls, zsignal_dot = "深度超买", "badge-red", "dot-white"
    else:
        zsignal, zsignal_cls, zsignal_dot = "正常区间", "badge-neutral", "dot-green"

    z_arrow_cls = "arrow-up" if latest_zscore >= 0 else "arrow-down"
    z_arrow_ch = "↑" if latest_zscore >= 0 else "↓"
    s_arrow_cls = "arrow-up" if latest_slope >= 0 else "arrow-down"
    s_arrow_ch = "↑" if latest_slope >= 0 else "↓"

    st.write("")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.caption("当前股价")
        st.markdown(f"<div class='big-num'>${latest_price:,.2f}</div>", unsafe_allow_html=True)
    with m2:
        st.caption("200 日均线")
        st.markdown(f"<div class='big-num'>${latest_ma200:,.2f}</div>", unsafe_allow_html=True)
        arrow = "▲" if distance >= 0 else "▼"
        cls = "arrow-up" if distance >= 0 else "arrow-down"
        st.markdown(f"<span class='{cls}'>{arrow} {distance:+.1f}%</span>", unsafe_allow_html=True)
    with m3:
        st.caption("Z值（偏离度）")
        st.markdown(f"<div class='big-num'>{latest_zscore:.2f}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<span class='{z_arrow_cls}'>{z_arrow_ch}</span>"
            f"<span class='badge {zsignal_cls}'><span class='{zsignal_dot}'>●</span> {zsignal}</span>",
            unsafe_allow_html=True,
        )
    with m4:
        st.caption("斜率（趋势强度）")
        st.markdown(f"<div class='big-num'>{latest_slope:.1f}%</div>", unsafe_allow_html=True)
        st.markdown(
            f"<span class='{s_arrow_cls}'>{s_arrow_ch}</span>"
            f"<span class='badge {regime_cls}'><span class='{regime_dot}'>●</span> {regime}</span>",
            unsafe_allow_html=True,
        )
    with m5:
        st.caption("当前所在区间")
        st.markdown(f"<div class='big-num'>{current_bucket}</div>", unsafe_allow_html=True)

    st.write("")

    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(16, 13), sharex=True,
        gridspec_kw={"height_ratios": [2.5, 1.1, 1.1]},
    )

    ax1.plot(price_plot.index, price_plot, color="white", linewidth=1.2, label=f"{ticker} 股价")
    ax1.plot(ma200_plot.index, ma200_plot, color="#FF6B6B", linewidth=1.5, linestyle="--", label="200 日均线")
    ax1.fill_between(
        ma200_plot.index,
        (ma200 - 1.5 * rolling_std).reindex(ma200_plot.index),
        (ma200 + 1.5 * rolling_std).reindex(ma200_plot.index),
        alpha=0.18, color="#cccc66", label="1.5σ 区间带",
    )
    ax1.set_ylabel("股价 ($)", color="white")
    ax1.set_title(f"{ticker} — 股价 vs 200 日均线", fontsize=15, fontweight="bold", color="white")
    ax1.legend(loc="upper left", fontsize=10)
    ax1.set_facecolor("#1a1a2e")
    ax1.grid(True, alpha=0.2)

    s_colors = ["#4ECDC4" if s > 0 else "#FF6B6B" for s in slope_plot]
    ax2.bar(slope_plot.index, slope_plot, color=s_colors, alpha=0.8, width=1)
    ax2.axhline(y=0, color="white", linestyle="-", alpha=0.5)
    ax2.set_ylabel("斜率 (%)", color="white")
    ax2.set_title("200 日均线斜率（年化）  ·  绿色=上行  红色=下行", color="white")
    ax2.set_facecolor("#1a1a2e")
    ax2.grid(True, alpha=0.2)

    z_colors = ["#FF6B6B" if z < -1.5 else "#4ECDC4" if z > 1.5 else "#888888" for z in zscore_plot]
    ax3.bar(zscore_plot.index, zscore_plot, color=z_colors, alpha=0.8, width=1)
    ax3.axhline(y=-1.5, color="#FF6B6B", linestyle="--", alpha=0.7, label="超卖线 (-1.5)")
    ax3.axhline(y=1.5, color="#4ECDC4", linestyle="--", alpha=0.7, label="超买线 (+1.5)")
    ax3.axhline(y=0, color="white", linestyle="-", alpha=0.3)
    ax3.set_ylabel("Z值", color="white")
    ax3.set_title(f"Z值（相对200日均线的偏离度）  ·  当前: {latest_zscore:.2f}", color="white")
    ax3.legend(loc="upper left", fontsize=10)
    ax3.set_facecolor("#1a1a2e")
    ax3.grid(True, alpha=0.2)

    fig.patch.set_facecolor("#0d0d1a")
    for ax in (ax1, ax2, ax3):
        ax.tick_params(colors="white")
    plt.tight_layout()
    st.pyplot(fig)

    fwd_40d = price.shift(-40) / price - 1
    analysis = pd.DataFrame({"zscore": zscore, "fwd_40d": fwd_40d}).dropna()
    analysis["bucket"] = pd.cut(analysis["zscore"], bins=bins_list, labels=labels)
    summary = analysis.groupby("bucket", observed=True)["fwd_40d"].agg(
        样本数="count",
        平均收益=lambda x: round(x.mean() * 100, 2),
        中位数收益=lambda x: round(x.median() * 100, 2),
        胜率=lambda x: round((x > 0).mean() * 100, 1),
    )
    summary.columns = ["样本数", "平均收益 %", "中位数收益 %", "胜率 %"]
    summary.index.name = "Z值区间"
    summary = summary.reindex([l for l in labels if l in summary.index])

    st.markdown(f"### 📊 不同 Z值区间的「未来 40 天表现」  ·  当前所在区间：**{current_bucket}**")
    st.caption("👉 不知道这张表怎么看？点上面的 **📖 使用说明** 标签查看详细解释")

    def highlight_current(row):
        color = "background-color: #fff3cd; color: #333; font-weight: 700" if row.name == current_bucket else ""
        return [color] * len(row)

    styled = (
        summary.style
        .apply(highlight_current, axis=1)
        .format({"平均收益 %": "{:+.2f}", "中位数收益 %": "{:+.2f}", "胜率 %": "{:.1f}"})
    )
    st.dataframe(styled, use_container_width=True)

    st.caption(
        f"数据范围：{price_plot.index[0].strftime('%Y-%m-%d')} 至 {price_plot.index[-1].strftime('%Y-%m-%d')}  ·  "
        f"共 {len(price_plot)} 个交易日  ·  Shepherd Capital Markets"
    )
