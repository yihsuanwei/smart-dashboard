"""CRM Dashboard — 從 ivory-cli 的 SQLite 資料庫即時讀取賣家資料

不需要上傳 CSV，直接讀 crm.db。
ivory-cli 每週 sync-pkey 後，這裡馬上看到最新數據。
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ivory-cli 的資料庫路徑（絕對路徑，不依賴相對位置計算）
DB_PATH = Path.home() / "Documents" / "Work" / "Tools" / "ivory-cli" / "data" / "crm.db"

# MM tier 預設值（Dashboard 預設篩選這些）
MM_TIERS_DEFAULT = ["ignite-y4+", "ignite-y2y3", "mass"]


def get_db_connection():
    """取得 SQLite 連線（唯讀 + timeout，避免 database locked）"""
    if not DB_PATH.exists():
        return None
    uri = f"file:{DB_PATH}?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=10, check_same_thread=False)


@st.cache_data(ttl=120)
def load_sellers():
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    df = pd.read_sql("SELECT * FROM sellers", conn)
    conn.close()
    # 預先解析 tags（避免每次 rerun 都跑 lambda）
    df["tags_list"] = df["tags"].apply(parse_tags)
    df["tier"] = df["tags_list"].apply(lambda t: get_tag_value(t, "tier"))
    df["spark_phase"] = df["tags_list"].apply(lambda t: get_tag_value(t, "spark-phase"))

    # SPARK 參加期別：支援 {year}Q{N}_Spark (新) 和 Q{N}_Spark (舊,預設 2026)
    # 多期用「、」串接；沒參加過 → 空字串
    # 「is_q1_spark」保留給既有 tab 使用（這裡指目前 Q1 有參加 spark 的賣家）
    import re
    _spark_re_new = re.compile(r"^(\d{4})Q(\d)_Spark$")
    _spark_re_old = re.compile(r"^Q(\d)_Spark$")  # 向後相容

    def _extract_periods(tags):
        periods = set()
        for t in tags:
            m = _spark_re_new.match(t)
            if m:
                periods.add(f"{m.group(1)}-Q{m.group(2)}")
                continue
            m = _spark_re_old.match(t)
            if m:
                periods.add(f"2026-Q{m.group(1)}")  # fallback: 舊格式假設 2026
        return "、".join(sorted(periods))

    df["spark_periods"] = df["tags_list"].apply(_extract_periods)
    # is_q1_spark：參加過 2026 Q1 spark 的人（用 spark_periods 反推）
    df["is_q1_spark"] = df["spark_periods"].str.contains("2026-Q1", na=False)
    return df


@st.cache_data(ttl=120)
def _load_week_list():
    """只載入 year-week 清單，用於篩選器和決定要查哪幾週"""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    df = pd.read_sql(
        "SELECT DISTINCT year, week FROM performance_data ORDER BY year DESC, week DESC",
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=120)
def load_performance_weeks(year_week_pairs: tuple):
    """只載入指定的 (year, week) 組合，避免全表掃描"""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    if not year_week_pairs:
        conn.close()
        return pd.DataFrame()
    conditions = " OR ".join(
        [f"(year={y} AND week={w})" for y, w in year_week_pairs]
    )
    df = pd.read_sql(f"SELECT * FROM performance_data WHERE {conditions}", conn)
    conn.close()
    return df


@st.cache_data(ttl=120)
def _load_month_list():
    """只載入 year-month 清單"""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    df = pd.read_sql(
        "SELECT DISTINCT year, month FROM performance_monthly ORDER BY year DESC, month DESC",
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=120)
def load_performance_months(year_month_pairs: tuple):
    """只載入指定的 (year, month) 組合"""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    if not year_month_pairs:
        conn.close()
        return pd.DataFrame()
    conditions = " OR ".join(
        [f"(year={y} AND month={m})" for y, m in year_month_pairs]
    )
    df = pd.read_sql(f"SELECT * FROM performance_monthly WHERE {conditions}", conn)
    conn.close()
    return df


@st.cache_data(ttl=120)
def load_notes():
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    df = pd.read_sql("SELECT * FROM notes ORDER BY created_at DESC", conn)
    conn.close()
    return df


@st.cache_data(ttl=120)
def load_latest_notes():
    """只載入每個 mcid 最新一筆 note（賣家清單 / SPARK 用）"""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    df = pd.read_sql(
        """SELECT mcid, content, created_at
           FROM notes
           WHERE id IN (SELECT MAX(id) FROM notes GROUP BY mcid)
           ORDER BY created_at DESC""",
        conn,
    )
    conn.close()
    return df


def load_notes_for_seller(mcid: str):
    """載入指定賣家的全部 notes（不 cache，確保即時）"""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    df = pd.read_sql(
        "SELECT id, mcid, type, content, author, created_at "
        "FROM notes WHERE mcid = ? ORDER BY created_at DESC",
        conn, params=[mcid],
    )
    conn.close()
    return df


def parse_tags(tags_json):
    try:
        return json.loads(tags_json) if isinstance(tags_json, str) else []
    except Exception:
        return []


def get_tag_value(tags, prefix):
    for t in tags:
        if t.startswith(prefix + ":"):
            return t.split(":", 1)[1]
    return ""


def money(v):
    if pd.isna(v) or v is None:
        return "$0"
    return f"${int(round(v)):,}"


def pct_change(curr, prev):
    if prev is None or prev == 0 or pd.isna(prev):
        return None
    return (curr - prev) / prev * 100


def _color_pct(val):
    """百分比欄位條件顏色：正綠負紅，None 灰色"""
    if val is None or pd.isna(val):
        return "color: gray"
    return "color: #2e7d32" if val >= 0 else "color: #c62828"


# ═══════════════════════════════════════════════════════════════
# Streamlit UI
# ═══════════════════════════════════════════════════════════════

st.set_page_config(page_title="CRM Dashboard", page_icon=":material/contacts:", layout="wide")
st.title(":material/contacts: CRM Dashboard")

if not DB_PATH.exists():
    st.error(f"找不到 ivory-cli 資料庫：{DB_PATH}")
    st.stop()

# 載入核心資料（sellers 很小，直接載入；績效資料延遲到需要時才載入）
sellers_df = load_sellers()

if sellers_df.empty:
    st.warning("CRM 資料庫是空的。請先執行 sync-pkey 匯入 PKEY 資料。")
    st.stop()

# 載入 week/month 清單（極快，只有幾十行）
week_list_df = _load_week_list()
month_list_df = _load_month_list()

# 頁面初始只載入最新 2 週（KPI 卡片用），趨勢圖在 tab 內按需載入
_all_weeks_desc = list(zip(week_list_df["year"].astype(int), week_list_df["week"].astype(int))) if not week_list_df.empty else []
_kpi_week_pairs = tuple(_all_weeks_desc[:2])  # 只要最新 2 週算 WoW

# 載入 KPI 用的績效資料
perf_df = load_performance_weeks(_kpi_week_pairs)

# tags 已在 load_sellers() 內預先解析（cached），不需要每次 rerun 重跑

st.write("")

# ── 年資 cohort mapping ──
COHORT_DISPLAY = {
    "Existing - 2nd Year": "Y2",
    "Existing - 3rd Year": "Y3",
    "Existing - Aging": "Y4+",
}
COHORT_REVERSE = {v: k for k, v in COHORT_DISPLAY.items()}

# ── 篩選器 ──
# Tier 短名稱 mapping（顯示用）
TIER_DISPLAY = {
    "ignite-y4+": "Y4+",
    "ignite-y2y3": "Y2Y3",
    "mass": "MASS",
}
TIER_REVERSE = {v: k for k, v in TIER_DISPLAY.items()}

all_tiers = sorted(sellers_df["tier"].unique().tolist())
all_tiers_display = [TIER_DISPLAY.get(t, t) for t in all_tiers]
default_display = [TIER_DISPLAY.get(t, t) for t in MM_TIERS_DEFAULT if t in all_tiers]

filter_col1, filter_col2, filter_col3 = st.columns([4, 2, 2])

with filter_col1:
    selected_tiers_display = st.pills(
        "Tier", all_tiers_display, default=default_display,
        selection_mode="multi", key="crm_tier_filter",
    )
    selected_tiers = [TIER_REVERSE.get(d, d) for d in (selected_tiers_display or [])]
with filter_col2:
    all_cohorts_display = sorted(
        [COHORT_DISPLAY[c] for c in sellers_df["launch_year_cohort"].dropna().unique()
         if c in COHORT_DISPLAY],
        key=lambda x: ["Y2", "Y3", "Y4+"].index(x) if x in ["Y2", "Y3", "Y4+"] else 99,
    )
    selected_cohorts_display = st.pills(
        "年資", all_cohorts_display,
        selection_mode="multi", key="crm_cohort_filter",
    )
    selected_cohorts = [COHORT_REVERSE.get(d, d) for d in (selected_cohorts_display or [])]
with filter_col3:
    owners = ["All"] + sorted(sellers_df["owner"].dropna().unique().tolist())
    selected_owner = st.selectbox("Owner", owners, key="crm_owner_filter")

# 套用篩選
filtered = sellers_df.copy()
if selected_tiers:
    filtered = filtered[filtered["tier"].isin(selected_tiers)]
if selected_cohorts:
    filtered = filtered[filtered["launch_year_cohort"].isin(selected_cohorts)]
if selected_owner != "All":
    filtered = filtered[filtered["owner"] == selected_owner]

st.write("")

# ── KPI 卡片 ──
_filtered_mcids = set(filtered["mcid"])
_week_gms = 0
_prev_gms = 0
_ly_week_gms = 0
_lw = _pw = _max_year = 0
_weeks_desc = []

if not perf_df.empty:
    _max_year = int(perf_df["year"].max())
    _weeks_desc = sorted(perf_df[perf_df["year"] == _max_year]["week"].unique(), reverse=True)
    if len(_weeks_desc) >= 1:
        _lw = int(_weeks_desc[0])
        _week_gms = perf_df[(perf_df["year"] == _max_year) & (perf_df["week"] == _lw) & (perf_df["mcid"].isin(_filtered_mcids))]["gms"].sum()
    if len(_weeks_desc) >= 2:
        _pw = int(_weeks_desc[1])
        _prev_gms = perf_df[(perf_df["year"] == _max_year) & (perf_df["week"] == _pw) & (perf_df["mcid"].isin(_filtered_mcids))]["gms"].sum()

# YoY: 去年同週 GMS（從已載入的 perf_df 裡找，perf_df 只有最新 2 週，需要額外載入去年同週）
if _lw and _max_year:
    _ly_pair = tuple([(_max_year - 1, _lw)])
    _ly_perf = load_performance_weeks(_ly_pair)
    if not _ly_perf.empty:
        _ly_week_gms = _ly_perf[_ly_perf["mcid"].isin(_filtered_mcids)]["gms"].sum()

_delta_gms = f"{(_week_gms - _prev_gms) / _prev_gms * 100:+.1f}%" if _prev_gms else None
_yoy_gms_pct = pct_change(_week_gms, _ly_week_gms)

_ignite_mcids = set(filtered[filtered["tier"].isin({"ignite-y4+", "ignite-y2y3"})]["mcid"])
_ignite_gms = 0
_ignite_prev = 0
if not perf_df.empty and _ignite_mcids:
    if _lw:
        _ignite_gms = perf_df[(perf_df["year"] == _max_year) & (perf_df["week"] == _lw) & (perf_df["mcid"].isin(_ignite_mcids))]["gms"].sum()
    if _pw:
        _ignite_prev = perf_df[(perf_df["year"] == _max_year) & (perf_df["week"] == _pw) & (perf_df["mcid"].isin(_ignite_mcids))]["gms"].sum()
_delta_ignite = f"{(_ignite_gms - _ignite_prev) / _ignite_prev * 100:+.1f}%" if _ignite_prev else None

_wk_label = f"W{_lw}" if _lw else "本週"

kpi_row = st.columns(4, gap="medium")
with kpi_row[0]:
    with st.container(border=True, height="stretch"):
        st.metric("篩選賣家數", f"{len(filtered):,}")
with kpi_row[1]:
    with st.container(border=True, height="stretch"):
        st.metric(
            f"{_wk_label} GMS YoY",
            f"{_yoy_gms_pct:+.1f}%" if _yoy_gms_pct is not None else "N/A",
            help=f"{_wk_label} {money(_week_gms)} vs 去年同週 {money(_ly_week_gms)}" if _ly_week_gms else None,
        )
with kpi_row[2]:
    with st.container(border=True, height="stretch"):
        st.metric(f"{_wk_label} GMS", money(_week_gms), delta=_delta_gms)
with kpi_row[3]:
    with st.container(border=True, height="stretch"):
        st.metric(f"Ignite {_wk_label} GMS", money(_ignite_gms), delta=_delta_ignite)


# ── 圓餅圖：by Owner + by Tier ──
if not filtered.empty:

    include_mass = st.toggle("包含 MASS", value=False, key="chart_include_mass")

    PALETTE = ["#4E79A7", "#F28E2B", "#59A14F", "#E15759", "#76B7B2", "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC"]
    TIER_COLORS = {
        "ignite-y4+": "#4E79A7",
        "ignite-y2y3": "#F2C14E",
        "mass": "#F28E2B",
    }

    chart_df = filtered.copy()
    if not include_mass:
        chart_df = chart_df[chart_df["tier"] != "mass"]

    pie_col1, pie_col2 = st.columns(2)

    with pie_col1:
        owner_counts = chart_df["owner"].value_counts()
        total_owner = int(owner_counts.sum())
        fig1 = px.pie(values=owner_counts.values, names=owner_counts.index,
                      title="by Owner", hole=0.4, color_discrete_sequence=PALETTE)
        fig1.update_traces(textinfo="value", textfont_size=13,
                           hovertemplate="%{label}: %{value} (%{percent})<extra></extra>")
        fig1.update_layout(
            height=280, margin=dict(t=35, b=10, l=10, r=10), showlegend=True,
            legend=dict(font=dict(size=11), orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            annotations=[dict(text=f"<b>{total_owner}</b>", x=0.5, y=0.5, font_size=22, showarrow=False)],
        )
        st.plotly_chart(fig1, use_container_width=True)

    with pie_col2:
        tier_counts = chart_df["tier"].value_counts()
        total_tier = int(tier_counts.sum())
        tier_color_map = {name: TIER_COLORS.get(name, PALETTE[i % len(PALETTE)]) for i, name in enumerate(tier_counts.index)}
        fig2 = px.pie(values=tier_counts.values, names=tier_counts.index,
                      title="by Tier", hole=0.4, color=tier_counts.index,
                      color_discrete_map=tier_color_map)
        fig2.update_traces(textinfo="value", textfont_size=13,
                           hovertemplate="%{label}: %{value} (%{percent})<extra></extra>")
        fig2.update_layout(
            height=280, margin=dict(t=35, b=10, l=10, r=10), showlegend=True,
            legend=dict(font=dict(size=11), orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            annotations=[dict(text=f"<b>{total_tier}</b>", x=0.5, y=0.5, font_size=22, showarrow=False)],
        )
        st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# Tab 切換
# ═══════════════════════════════════════════════════════════════

tab_perf, tab_interaction, tab_spark, tab_base = st.tabs([
    ":material/trending_up: Performance",
    ":material/history: 互動史",
    ":material/star: SPARK 管理",
    ":material/table_chart: 底表",
])

# ── Tab 1: Performance（群體切換 + WBR/MBR toggle）──
with tab_perf:

    perf_group_col, perf_view_col = st.columns([2, 1])
    with perf_group_col:
        group_choice = st.segmented_control(
            "群體", ["MM-MASS", "Ignite", "SPARK"],
            default="Ignite", key="perf_group",
        )
    with perf_view_col:
        view_choice = st.segmented_control(
            "數據來源", ["WBR (Weekly)", "MBR (Monthly)"],
            default="WBR (Weekly)", key="perf_view",
        )

    # view_choice 強制至少一個；group_choice 可以取消 → 全部（吃上面的全域篩選）
    if not view_choice:
        view_choice = "WBR (Weekly)"

    # 決定群體 MCID
    # SPARK 固定用 Q1 全部 34 家（不受 Owner/Tier 篩選影響）
    # Ignite / MM-MASS / 未選 尊重全域 Owner / Tier 篩選
    _base = filtered  # 從全域篩選結果開始
    if group_choice == "Ignite":
        _group_mcids = set(_base[_base["tier"].isin({"ignite-y4+", "ignite-y2y3"})]["mcid"])
    elif group_choice == "MM-MASS":
        _group_mcids = set(_base[_base["tier"].isin({"ignite-y4+", "ignite-y2y3", "mass"})]["mcid"])
    elif group_choice == "SPARK":
        _group_mcids = set(sellers_df[sellers_df["is_q1_spark"]]["mcid"])
    else:
        # 三個都不選 → 吃全域篩選（tier/cohort/owner 都尊重）
        _group_mcids = set(_base["mcid"])

    group_seller_count = len(_group_mcids)

    # 群體標籤（含 tier 組成說明）
    _GROUP_TIER_DESC = {
        "Ignite": "Y4+ + Y2Y3",
        "MM-MASS": "Y4+ + Y2Y3 + MASS",
    }
    if group_choice == "SPARK":
        _group_label_tpl = f"SPARK | {{}} | {group_seller_count} sellers (Q1 BOB)"
    elif group_choice in _GROUP_TIER_DESC:
        _tier_desc = _GROUP_TIER_DESC.get(group_choice, "")
        _group_label_tpl = f"{group_choice} ({_tier_desc}) | {{}} | {group_seller_count} sellers"
    else:
        _group_label_tpl = f"全部（依上方篩選）| {{}} | {group_seller_count} sellers"

    # Lazy load: MBR 資料只在切到 MBR 時才載入
    if view_choice == "MBR (Monthly)":
        _all_months_desc = list(zip(
            month_list_df["year"].astype(int), month_list_df["month"].astype(int)
        )) if not month_list_df.empty else []
        _recent_months = _all_months_desc[:6]
        _ly_month_pairs = []
        if _recent_months:
            _max_year_m = _recent_months[0][0]
            _recent_month_nums = {m for _, m in _recent_months if _ == _max_year_m}
            _ly_month_pairs = [(y, m) for y, m in _all_months_desc if y == _max_year_m - 1 and m in _recent_month_nums]
        _needed_month_pairs = tuple(set(_recent_months + _ly_month_pairs))
        perf_monthly_df = load_performance_months(_needed_month_pairs)
    else:
        perf_monthly_df = pd.DataFrame()

    if view_choice == "WBR (Weekly)" and not perf_df.empty:
        # Lazy load: 趨勢圖需要 8 週 + 去年同期，在 tab 內按需載入
        _recent_8 = _all_weeks_desc[:8]
        _ly_pairs = []
        if _recent_8:
            _max_year_w = _recent_8[0][0]
            _recent_week_nums = {w for y, w in _recent_8 if y == _max_year_w}
            _ly_pairs = [(y, w) for y, w in _all_weeks_desc if y == _max_year_w - 1 and w in _recent_week_nums]
        _full_week_pairs = tuple(set(_recent_8 + _ly_pairs))
        perf_full_df = load_performance_weeks(_full_week_pairs)

        # Weekly view
        src = perf_full_df[perf_full_df["mcid"].isin(_group_mcids)].copy()
        if src.empty:
            st.info("此群體沒有 WBR 績效數據")
        else:
            max_y = int(src["year"].max())
            all_weeks = sorted(src[src["year"] == max_y]["week"].unique(), reverse=True)

            if len(all_weeks) >= 1:
                cw = int(all_weeks[0])
                curr = src[(src["year"] == max_y) & (src["week"] == cw)].groupby("mcid").sum(numeric_only=True)
            else:
                curr = pd.DataFrame()

            if len(all_weeks) >= 2:
                pw = int(all_weeks[1])
                prev = src[(src["year"] == max_y) & (src["week"] == pw)].groupby("mcid").sum(numeric_only=True)
            else:
                prev = pd.DataFrame()

            ly_src = perf_full_df[(perf_full_df["mcid"].isin(_group_mcids)) & (perf_full_df["year"] == max_y - 1) & (perf_full_df["week"] == cw)] if len(all_weeks) >= 1 else pd.DataFrame()
            ly = ly_src.groupby("mcid").sum(numeric_only=True) if not ly_src.empty else pd.DataFrame()

            # KPI
            g_gms = curr["gms"].sum() if not curr.empty else 0
            p_gms = prev["gms"].sum() if not prev.empty else 0
            ly_gms = ly["gms"].sum() if not ly.empty else 0
            g_ads = curr["ads_ops"].sum() if not curr.empty else 0
            p_ads = prev["ads_ops"].sum() if not prev.empty else 0
            g_promo = curr["promo_ops"].sum() if not curr.empty else 0
            p_promo = prev["promo_ops"].sum() if not prev.empty else 0
            g_ba = int(curr["ba"].sum()) if not curr.empty else 0
            p_ba = int(prev["ba"].sum()) if not prev.empty else 0
            g_ytd = curr["ytd_gms"].sum() if not curr.empty and "ytd_gms" in curr.columns else 0
            ly_ytd = ly["ytd_gms"].sum() if not ly.empty and "ytd_gms" in ly.columns else 0

            wow_gms = pct_change(g_gms, p_gms)
            yoy_gms = pct_change(g_gms, ly_gms)
            wow_ads = pct_change(g_ads, p_ads)
            wow_promo = pct_change(g_promo, p_promo)
            wow_ba = pct_change(g_ba, p_ba)
            yoy_ytd = pct_change(g_ytd, ly_ytd)

            st.caption(_group_label_tpl.format(f"W{cw} {max_y}"))
            k1, k2, k3, k4, k5, k6 = st.columns(6, gap="small")
            with k1:
                st.metric("GMS", money(g_gms), delta=f"WoW {wow_gms:+.1f}%" if wow_gms is not None else None)
            with k2:
                st.metric("YoY", f"{yoy_gms:+.1f}%" if yoy_gms is not None else "N/A")
            with k3:
                st.metric("YTD GMS", money(g_ytd), delta=f"YoY {yoy_ytd:+.1f}%" if yoy_ytd is not None else None)
            with k4:
                st.metric("Ads OPS", money(g_ads), delta=f"WoW {wow_ads:+.1f}%" if wow_ads is not None else None)
            with k5:
                st.metric("Promo OPS", money(g_promo), delta=f"WoW {wow_promo:+.1f}%" if wow_promo is not None else None)
            with k6:
                st.metric("BA", f"{g_ba:,}", delta=f"WoW {wow_ba:+.1f}%" if wow_ba is not None else None)

            # Trending: 最近 8 週 GMS
            trend_data = []
            for w in sorted(all_weeks[:8]):
                w_data = src[(src["year"] == max_y) & (src["week"] == w)]
                w_gms = w_data["gms"].sum()
                trend_data.append({"Week": f"W{w}", "GMS": w_gms})
            if trend_data:
                trend_df = pd.DataFrame(trend_data)
                fig_trend = px.line(trend_df, x="Week", y="GMS", title="Weekly GMS Trend",
                                    text="GMS", markers=True, color_discrete_sequence=["#4E79A7"])
                fig_trend.update_traces(texttemplate="$%{y:,.0f}", textposition="top center", textfont_size=10)
                fig_trend.update_layout(height=300, margin=dict(t=35, b=10), yaxis_title="", xaxis_title="",
                                        yaxis_rangemode="tozero" if g_gms == 0 else "normal")
                st.plotly_chart(fig_trend, use_container_width=True)

            # ── Metric Cards (WBR) ──
            # YoY sparkline cards for key metrics, inserted after Weekly GMS Trend
            if not curr.empty and not ly.empty:
                _WBR_METRICS = [
                    ("gms", "GMS", "$"), ("new_fba_ba", "New FBA BA", "#"),
                    ("fba_ba", "FBA BA", "#"), ("fba_awas", "FBA AWAS", "#"),
                    ("promo_count", "Promo Count", "#"), ("promo_ops", "Promo OPS", "$"),
                    ("ads_spend", "Ads Spend", "$"), ("ads_ops", "Ads OPS", "$"),
                ]
                # Build YoY trending sparkline: each week's YoY%
                _wbr_spark = {}
                for col, _, _ in _WBR_METRICS:
                    vals = []
                    for w in sorted(all_weeks[:8]):
                        w_curr = src[(src["year"] == max_y) & (src["week"] == w)][col].sum()
                        w_ly = perf_full_df[(perf_full_df["mcid"].isin(_group_mcids)) & (perf_full_df["year"] == max_y - 1) & (perf_full_df["week"] == w)][col].sum()
                        vals.append(((w_curr / w_ly - 1) * 100) if w_ly else 0)
                    _wbr_spark[col] = vals

                st.caption("Key metrics YoY")
                # All 8 metrics in one row
                with st.container(horizontal=True):
                    for col, label, fmt in _WBR_METRICS:
                        c_val = curr[col].sum() if col in curr.columns else 0
                        l_val = ly[col].sum() if col in ly.columns else 0
                        yoy_v = pct_change(c_val, l_val)
                        if fmt == "$":
                            disp = f"${c_val/1e6:.2f}M" if abs(c_val) >= 1e6 else f"${c_val/1e3:.1f}K" if abs(c_val) >= 1e3 else f"${c_val:.0f}"
                            _help = f"W{cw} {money(c_val)} vs LY {money(l_val)}"
                        else:
                            disp = f"{c_val:,.0f}"
                            _help = f"W{cw} {c_val:,.0f} vs LY {l_val:,.0f}"
                        _delta_str = f"{yoy_v:+.1f}% YoY" if yoy_v is not None else None
                        st.metric(
                            label, disp,
                            delta=_delta_str,
                            delta_color="normal",
                            help=_help,
                            border=True,
                            chart_data=_wbr_spark.get(col, []),
                            chart_type="line",
                        )

            # Seller detail table
            if not curr.empty:
                # 載入 latest notes（WBR + MBR 共用）
                _latest_notes_df = load_latest_notes()
                _notes_map = {}
                if not _latest_notes_df.empty:
                    for _, r in _latest_notes_df.iterrows():
                        _notes_map[r["mcid"]] = (r["content"], r["created_at"])

                detail = curr[["gms", "ads_ops", "promo_ops", "ba", "fba_ba"]].copy()
                detail = detail.reset_index()
                _seller_cols = ["name", "tier", "owner", "q1_am", "q2_am",
                                "cooperation_level", "line_bindind", "spark_periods"]
                name_map = sellers_df.set_index("mcid")[_seller_cols].to_dict("index")
                detail["name"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("name", m))
                detail["tier"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("tier", ""))
                detail["owner"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("owner", ""))
                detail["q1_am"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("q1_am", "") or "")
                detail["q2_am"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("q2_am", "") or "")
                detail["coop"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("cooperation_level", "") or "—")
                detail["line"] = detail["mcid"].map(lambda m: "是" if name_map.get(m, {}).get("line_bindind") else "否")
                detail["spark"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("spark_periods", "") or "")
                detail["latest_note"] = detail["mcid"].map(lambda m: _notes_map.get(m, ("", ""))[0])
                detail["note_date"] = detail["mcid"].map(lambda m: _notes_map.get(m, ("", ""))[1])

                # GMS WoW / YoY / CTC — 向量化計算（不用 iterrows）
                _total_prev_gms = prev["gms"].sum() if not prev.empty else 0
                _total_ly_gms = ly["gms"].sum() if not ly.empty else 0

                _prev_gms_s = prev["gms"] if not prev.empty else pd.Series(dtype=float)
                _ly_gms_s = ly["gms"] if not ly.empty else pd.Series(dtype=float)

                detail["_c"] = detail["mcid"].map(curr["gms"]).fillna(0)
                detail["_p"] = detail["mcid"].map(_prev_gms_s).fillna(0)
                detail["_l"] = detail["mcid"].map(_ly_gms_s).fillna(0)

                detail["GMS WoW"] = detail.apply(lambda r: pct_change(r["_c"], r["_p"]), axis=1)
                detail["GMS YoY"] = detail.apply(lambda r: pct_change(r["_c"], r["_l"]), axis=1)
                detail["CTC WoW"] = (detail["_c"] - detail["_p"]) / _total_prev_gms * 100 if _total_prev_gms else None
                detail["CTC YoY"] = (detail["_c"] - detail["_l"]) / _total_ly_gms * 100 if _total_ly_gms else None
                detail.drop(columns=["_c", "_p", "_l"], inplace=True)

                detail = detail.sort_values("gms", ascending=False)
                detail = detail[["mcid", "name", "tier", "owner", "q1_am", "q2_am",
                                 "coop", "line", "spark",
                                 "gms", "GMS WoW", "GMS YoY", "CTC WoW", "CTC YoY",
                                 "ads_ops", "promo_ops", "ba", "fba_ba",
                                 "latest_note", "note_date"]]
                detail.columns = ["MCID", "名稱", "Tier", "Owner", "Q1 AM", "Q2 AM",
                                  "配合度", "LINE", "SPARK",
                                  "GMS", "GMS WoW", "GMS YoY", "CTC WoW", "CTC YoY",
                                  "Ads OPS", "Promo OPS", "BA", "FBA BA",
                                  "Latest Note", "Note Date"]

                _n = group_seller_count
                _ctc_wow_help = f"CTC WoW = (該賣家本週 GMS − 上週 GMS) ÷ ({_n}家上週總 GMS) × 100%。例：上週總 GMS = $300萬，A 賣家本週多了 $6萬 → CTC = +6/300 = +2.0%。全部加總 = 整體 WoW%。"
                _ctc_yoy_help = f"CTC YoY = (該賣家本週 GMS − 去年同週 GMS) ÷ ({_n}家去年同週總 GMS) × 100%。例：去年同週總 GMS = $310萬，A 賣家掉了 $20萬 → CTC = −20/310 = −6.5%。全部加總 = 整體 YoY%。"
                st.dataframe(detail, use_container_width=True, hide_index=True, height=400,
                             column_config={
                                 "GMS": st.column_config.NumberColumn("GMS", format="$%.0f"),
                                 "Ads OPS": st.column_config.NumberColumn("Ads OPS", format="$%.0f"),
                                 "Promo OPS": st.column_config.NumberColumn("Promo OPS", format="$%.0f"),
                                 "GMS WoW": st.column_config.NumberColumn("GMS WoW", help="該賣家 GMS 的 Week-over-Week 變化率"),
                                 "GMS YoY": st.column_config.NumberColumn("GMS YoY", help="該賣家 GMS 的 Year-over-Year 變化率"),
                                 "CTC WoW": st.column_config.NumberColumn("CTC WoW", help=_ctc_wow_help),
                                 "CTC YoY": st.column_config.NumberColumn("CTC YoY", help=_ctc_yoy_help),
                                 "LINE": st.column_config.TextColumn("LINE", help="LINE 綁定狀態（是/否）"),
                                 "配合度": st.column_config.TextColumn("配合度"),
                                 "Latest Note": st.column_config.TextColumn("Latest Note", width="large"),
                             })

    elif view_choice == "MBR (Monthly)" and not perf_monthly_df.empty:
        # Monthly view
        src = perf_monthly_df[perf_monthly_df["mcid"].isin(_group_mcids)].copy()
        if src.empty:
            st.info("此群體沒有 MBR 績效數據")
        else:
            max_y = int(src["year"].max())
            all_months = sorted(src[src["year"] == max_y]["month"].unique(), reverse=True)
            MONTH_NAMES = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

            if len(all_months) >= 1:
                cm = int(all_months[0])
                curr = src[(src["year"] == max_y) & (src["month"] == cm)].groupby("mcid").sum(numeric_only=True)
            else:
                curr = pd.DataFrame()

            if len(all_months) >= 2:
                pm = int(all_months[1])
                prev = src[(src["year"] == max_y) & (src["month"] == pm)].groupby("mcid").sum(numeric_only=True)
            else:
                prev = pd.DataFrame()

            ly_src = perf_monthly_df[(perf_monthly_df["mcid"].isin(_group_mcids)) & (perf_monthly_df["year"] == max_y - 1) & (perf_monthly_df["month"] == cm)] if len(all_months) >= 1 else pd.DataFrame()
            ly = ly_src.groupby("mcid").sum(numeric_only=True) if not ly_src.empty else pd.DataFrame()

            g_gms = curr["gms"].sum() if not curr.empty else 0
            p_gms = prev["gms"].sum() if not prev.empty else 0
            ly_gms = ly["gms"].sum() if not ly.empty else 0
            g_ads = curr["ads_ops"].sum() if not curr.empty else 0
            p_ads = prev["ads_ops"].sum() if not prev.empty else 0
            g_promo = curr["promo_ops"].sum() if not curr.empty else 0
            p_promo = prev["promo_ops"].sum() if not prev.empty else 0
            g_ba = int(curr["ba"].sum()) if not curr.empty else 0
            p_ba = int(prev["ba"].sum()) if not prev.empty else 0
            g_ytd = curr["ytd_gms"].sum() if not curr.empty and "ytd_gms" in curr.columns else 0
            ly_ytd = ly["ytd_gms"].sum() if not ly.empty and "ytd_gms" in ly.columns else 0

            mom_gms = pct_change(g_gms, p_gms)
            yoy_gms = pct_change(g_gms, ly_gms)
            mom_ads = pct_change(g_ads, p_ads)
            mom_promo = pct_change(g_promo, p_promo)
            mom_ba = pct_change(g_ba, p_ba)
            yoy_ytd = pct_change(g_ytd, ly_ytd)

            mon_label = MONTH_NAMES.get(cm, str(cm))
            st.caption(_group_label_tpl.format(f"{mon_label} {max_y}"))
            k1, k2, k3, k4, k5, k6 = st.columns(6, gap="small")
            with k1:
                st.metric("GMS", money(g_gms), delta=f"MoM {mom_gms:+.1f}%" if mom_gms is not None else None)
            with k2:
                st.metric("YoY", f"{yoy_gms:+.1f}%" if yoy_gms is not None else "N/A")
            with k3:
                st.metric("YTD GMS", money(g_ytd), delta=f"YoY {yoy_ytd:+.1f}%" if yoy_ytd is not None else None)
            with k4:
                st.metric("Ads OPS", money(g_ads), delta=f"MoM {mom_ads:+.1f}%" if mom_ads is not None else None)
            with k5:
                st.metric("Promo OPS", money(g_promo), delta=f"MoM {mom_promo:+.1f}%" if mom_promo is not None else None)
            with k6:
                st.metric("BA", f"{g_ba:,}", delta=f"MoM {mom_ba:+.1f}%" if mom_ba is not None else None)

            # Trending: available months
            trend_data = []
            for m in sorted(all_months):
                m_data = src[(src["year"] == max_y) & (src["month"] == m)]
                m_gms = m_data["gms"].sum()
                trend_data.append({"Month": MONTH_NAMES.get(m, str(m)), "GMS": m_gms})
            if trend_data:
                trend_df = pd.DataFrame(trend_data)
                fig_trend = px.line(trend_df, x="Month", y="GMS", title="Monthly GMS Trend",
                                    text="GMS", markers=True, color_discrete_sequence=["#4E79A7"])
                fig_trend.update_traces(texttemplate="$%{y:,.0f}", textposition="top center", textfont_size=10)
                fig_trend.update_layout(height=300, margin=dict(t=35, b=10), yaxis_title="", xaxis_title="",
                                        yaxis_rangemode="tozero" if g_gms == 0 else "normal")
                st.plotly_chart(fig_trend, use_container_width=True)

            # ── Metric Cards (MBR) ──
            # YoY sparkline cards for 12 key metrics, using pkey_raw_monthly for full coverage
            if not curr.empty:
                _MBR_METRICS = [
                    ("mtd_ord_gms", "GMS", "$"), ("mtd_new_fba_ba_90d", "New FBA BA", "#"),
                    ("mtd_fba_ba", "FBA BA", "#"), ("mtd_fba_awas", "FBA AWAS", "#"),
                    ("mtd_deal_count", "Deal Count", "#"), ("mtd_deal_ops", "Deal OPS", "$"),
                    ("mtd_promotion_count", "Promo Count", "#"), ("mtd_promotion_ops", "Promo OPS", "$"),
                    ("mtd_coupon_count", "Coupon Count", "#"), ("mtd_coupon_ops", "Coupon OPS", "$"),
                    ("mtd_sa_revenue_usd", "Ads Spend", "$"), ("mtd_sa_attributed_ops_usd", "Ads OPS", "$"),
                ]
                _mbr_card_cols = ["mcid", "year", "month", "marketplace_id"] + [c for c, _, _ in _MBR_METRICS]

                # Need: current month + all available months for trending + LY months
                _mbr_months_for_cards = set()
                for m in all_months:
                    _mbr_months_for_cards.add((max_y, m))
                    _mbr_months_for_cards.add((max_y - 1, m))

                @st.cache_data(ttl=120)
                def _load_mbr_card_data(_mcids_tuple, _month_pairs_tuple, _cols_tuple):
                    """Cached: 載入 MBR metric cards 需要的 pkey_raw_monthly 資料"""
                    conn = get_db_connection()
                    if conn is None:
                        return pd.DataFrame()
                    mcid_list = list(_mcids_tuple)
                    ph = ",".join(["?"] * len(mcid_list))
                    month_conds = " OR ".join([f"(year={y} AND month={m})" for y, m in _month_pairs_tuple])
                    sql = f"SELECT {','.join(_cols_tuple)} FROM pkey_raw_monthly WHERE ({month_conds}) AND mcid IN ({ph})"
                    df = pd.read_sql(sql, conn, params=mcid_list)
                    conn.close()
                    return df

                _mbr_raw = _load_mbr_card_data(
                    tuple(sorted(_group_mcids)),
                    tuple(sorted(_mbr_months_for_cards)),
                    tuple(_mbr_card_cols),
                )

                if not _mbr_raw.empty:
                    # Aggregate by (year, month) for the group
                    _mbr_agg = _mbr_raw.groupby(["year", "month"]).sum(numeric_only=True)

                    # Current month and LY values
                    _mbr_curr = _mbr_agg.loc[(max_y, cm)] if (max_y, cm) in _mbr_agg.index else pd.Series(dtype=float)
                    _mbr_ly = _mbr_agg.loc[(max_y - 1, cm)] if (max_y - 1, cm) in _mbr_agg.index else pd.Series(dtype=float)

                    # Build YoY sparkline: each month's YoY%
                    _mbr_spark = {}
                    for col, _, _ in _MBR_METRICS:
                        vals = []
                        for m in sorted(all_months):
                            c_v = _mbr_agg.loc[(max_y, m)][col] if (max_y, m) in _mbr_agg.index and col in _mbr_agg.columns else 0
                            l_v = _mbr_agg.loc[(max_y - 1, m)][col] if (max_y - 1, m) in _mbr_agg.index and col in _mbr_agg.columns else 0
                            vals.append(((c_v / l_v - 1) * 100) if l_v else 0)
                        _mbr_spark[col] = vals

                    st.caption("Key metrics YoY")
                    # Row 1: 6 metrics (Selection funnel)
                    with st.container(horizontal=True):
                        for col, label, fmt in _MBR_METRICS[:6]:
                            c_val = _mbr_curr[col] if col in _mbr_curr.index else 0
                            l_val = _mbr_ly[col] if col in _mbr_ly.index else 0
                            yoy_v = pct_change(c_val, l_val)
                            if fmt == "$":
                                disp = f"${c_val/1e6:.2f}M" if abs(c_val) >= 1e6 else f"${c_val/1e3:.1f}K" if abs(c_val) >= 1e3 else f"${c_val:.0f}"
                                _h = f"{mon_label} {money(c_val)} vs LY {money(l_val)}"
                            else:
                                disp = f"{c_val:,.0f}"
                                _h = f"{mon_label} {c_val:,.0f} vs LY {l_val:,.0f}"
                            _delta_str = f"{yoy_v:+.1f}% YoY" if yoy_v is not None else None
                            st.metric(label, disp, delta=_delta_str,
                                      delta_color="normal", help=_h, border=True,
                                      chart_data=_mbr_spark.get(col, []), chart_type="line")
                    # Row 2: 6 metrics (Promo + Ads)
                    with st.container(horizontal=True):
                        for col, label, fmt in _MBR_METRICS[6:]:
                            c_val = _mbr_curr[col] if col in _mbr_curr.index else 0
                            l_val = _mbr_ly[col] if col in _mbr_ly.index else 0
                            yoy_v = pct_change(c_val, l_val)
                            if fmt == "$":
                                disp = f"${c_val/1e6:.2f}M" if abs(c_val) >= 1e6 else f"${c_val/1e3:.1f}K" if abs(c_val) >= 1e3 else f"${c_val:.0f}"
                                _h = f"{mon_label} {money(c_val)} vs LY {money(l_val)}"
                            else:
                                disp = f"{c_val:,.0f}"
                                _h = f"{mon_label} {c_val:,.0f} vs LY {l_val:,.0f}"
                            _delta_str = f"{yoy_v:+.1f}% YoY" if yoy_v is not None else None
                            st.metric(label, disp, delta=_delta_str,
                                      delta_color="normal", help=_h, border=True,
                                      chart_data=_mbr_spark.get(col, []), chart_type="line")

            # Seller detail
            if not curr.empty:
                # 載入 latest notes
                _latest_notes_df = load_latest_notes()
                _notes_map = {}
                if not _latest_notes_df.empty:
                    for _, r in _latest_notes_df.iterrows():
                        _notes_map[r["mcid"]] = (r["content"], r["created_at"])

                detail = curr[["gms", "ads_ops", "promo_ops", "ba", "fba_ba"]].copy()
                detail = detail.reset_index()
                _seller_cols = ["name", "tier", "owner", "q1_am", "q2_am",
                                "cooperation_level", "line_bindind", "spark_periods"]
                name_map = sellers_df.set_index("mcid")[_seller_cols].to_dict("index")
                detail["name"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("name", m))
                detail["tier"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("tier", ""))
                detail["owner"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("owner", ""))
                detail["q1_am"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("q1_am", "") or "")
                detail["q2_am"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("q2_am", "") or "")
                detail["coop"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("cooperation_level", "") or "—")
                detail["line"] = detail["mcid"].map(lambda m: "是" if name_map.get(m, {}).get("line_bindind") else "否")
                detail["spark"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("spark_periods", "") or "")
                detail["latest_note"] = detail["mcid"].map(lambda m: _notes_map.get(m, ("", ""))[0])
                detail["note_date"] = detail["mcid"].map(lambda m: _notes_map.get(m, ("", ""))[1])

                # GMS MoM / YoY / CTC — 向量化計算
                _total_prev_gms = prev["gms"].sum() if not prev.empty else 0
                _total_ly_gms = ly["gms"].sum() if not ly.empty else 0

                _prev_gms_s = prev["gms"] if not prev.empty else pd.Series(dtype=float)
                _ly_gms_s = ly["gms"] if not ly.empty else pd.Series(dtype=float)

                detail["_c"] = detail["mcid"].map(curr["gms"]).fillna(0)
                detail["_p"] = detail["mcid"].map(_prev_gms_s).fillna(0)
                detail["_l"] = detail["mcid"].map(_ly_gms_s).fillna(0)

                detail["GMS MoM"] = detail.apply(lambda r: pct_change(r["_c"], r["_p"]), axis=1)
                detail["GMS YoY"] = detail.apply(lambda r: pct_change(r["_c"], r["_l"]), axis=1)
                detail["CTC MoM"] = (detail["_c"] - detail["_p"]) / _total_prev_gms * 100 if _total_prev_gms else None
                detail["CTC YoY"] = (detail["_c"] - detail["_l"]) / _total_ly_gms * 100 if _total_ly_gms else None
                detail.drop(columns=["_c", "_p", "_l"], inplace=True)

                detail = detail.sort_values("gms", ascending=False)
                detail = detail[["mcid", "name", "tier", "owner", "q1_am", "q2_am",
                                 "coop", "line", "spark",
                                 "gms", "GMS MoM", "GMS YoY", "CTC MoM", "CTC YoY",
                                 "ads_ops", "promo_ops", "ba", "fba_ba",
                                 "latest_note", "note_date"]]
                detail.columns = ["MCID", "名稱", "Tier", "Owner", "Q1 AM", "Q2 AM",
                                  "配合度", "LINE", "SPARK",
                                  "GMS", "GMS MoM", "GMS YoY", "CTC MoM", "CTC YoY",
                                  "Ads OPS", "Promo OPS", "BA", "FBA BA",
                                  "Latest Note", "Note Date"]

                _n = group_seller_count
                _ctc_mom_help = f"CTC MoM = (該賣家本月 GMS − 上月 GMS) ÷ ({_n}家上月總 GMS) × 100%。例：上月總 GMS = $280萬，A 賣家本月多了 $5萬 → CTC = +5/280 = +1.8%。全部加總 = 整體 MoM%。"
                _ctc_yoy_help_m = f"CTC YoY = (該賣家本月 GMS − 去年同月 GMS) ÷ ({_n}家去年同月總 GMS) × 100%。例：去年同月總 GMS = $310萬，A 賣家掉了 $20萬 → CTC = −20/310 = −6.5%。全部加總 = 整體 YoY%。"
                st.dataframe(detail, use_container_width=True, hide_index=True, height=400,
                             column_config={
                                 "GMS": st.column_config.NumberColumn("GMS", format="$%.0f"),
                                 "Ads OPS": st.column_config.NumberColumn("Ads OPS", format="$%.0f"),
                                 "Promo OPS": st.column_config.NumberColumn("Promo OPS", format="$%.0f"),
                                 "GMS MoM": st.column_config.NumberColumn("GMS MoM", help="該賣家 GMS 的 Month-over-Month 變化率"),
                                 "GMS YoY": st.column_config.NumberColumn("GMS YoY", help="該賣家 GMS 的 Year-over-Year 變化率"),
                                 "CTC MoM": st.column_config.NumberColumn("CTC MoM", help=_ctc_mom_help),
                                 "CTC YoY": st.column_config.NumberColumn("CTC YoY", help=_ctc_yoy_help_m),
                                 "LINE": st.column_config.TextColumn("LINE", help="LINE 綁定狀態（是/否）"),
                                 "配合度": st.column_config.TextColumn("配合度"),
                                 "Latest Note": st.column_config.TextColumn("Latest Note", width="large"),
                             })
            with st.expander(f":material/table_chart: 全量底表（{mon_label} {max_y} · 144 欄）", expanded=False):

                @st.cache_data(ttl=120)
                def _load_raw_for_group(_mcids_tuple, year, month, limit):
                    conn = get_db_connection()
                    if conn is None:
                        return pd.DataFrame(), 0
                    mcid_list = list(_mcids_tuple)
                    placeholders = ",".join(["?"] * len(mcid_list))
                    total = conn.execute(
                        f"SELECT COUNT(*) FROM pkey_raw_monthly WHERE year=? AND month=? AND mcid IN ({placeholders})",
                        [year, month] + mcid_list,
                    ).fetchone()[0]
                    df = pd.read_sql(
                        f"SELECT * FROM pkey_raw_monthly WHERE year=? AND month=? AND mcid IN ({placeholders}) "
                        f"ORDER BY mtd_ord_gms DESC LIMIT ?",
                        conn, params=[year, month] + mcid_list + [limit],
                    )
                    conn.close()
                    return df, total

                _show_all_perf_raw = st.toggle("顯示全部", value=False, key="perf_mbr_raw_all")
                _raw_limit = 99999 if _show_all_perf_raw else 200
                _raw_df, _raw_total = _load_raw_for_group(
                    tuple(sorted(_group_mcids)), max_y, cm, _raw_limit
                )
                st.caption(f"顯示 {len(_raw_df):,} / {_raw_total:,} 筆 | {len(_raw_df.columns)} 欄")
                _raw_money = [c for c in _raw_df.columns if any(k in c for k in ["gms","ops","spend","revenue","asp"])]
                _raw_cfg = {c: st.column_config.NumberColumn(format="$%.0f") for c in _raw_money if c in _raw_df.columns}
                st.dataframe(_raw_df, use_container_width=True, hide_index=True, height=400, column_config=_raw_cfg)
    else:
        st.info("沒有可用的績效數據。請先執行 sync-pkey 或 sync-mbr。")


# ── Tab 2: 互動史（選賣家看 notes 歷史）──
with tab_interaction:
    # 從全域篩選結果開始
    sl_df = filtered.copy()

    if sl_df.empty:
        st.info("目前沒有符合篩選條件的賣家")
    else:
        seller_options = sl_df.sort_values("name").apply(
            lambda r: f"{r['name']}  ({r['mcid']})", axis=1
        ).tolist()
        selected = st.selectbox(
            ":material/history: 查看賣家 Notes 歷史",
            options=["（選擇賣家）"] + seller_options,
            key="notes_history_select",
        )
        if selected != "（選擇賣家）":
            sel_mcid = selected.split("(")[-1].rstrip(")").strip()
            all_notes = load_notes_for_seller(sel_mcid)
            if all_notes.empty:
                st.caption("這個賣家還沒有任何 note")
            else:
                st.caption(f"共 {len(all_notes)} 筆紀錄")
                for _, n in all_notes.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.markdown(f"**{n['created_at']}**")
                        c2.caption(n['type'])
                        c3.caption(f"by {n['author']}")
                        st.text(n['content'])

# ── Tab 3: SPARK 管理 ──
with tab_spark:
    spark_sellers = filtered[filtered["is_q1_spark"]].copy()

    if spark_sellers.empty:
        st.info("目前沒有 SPARK 客戶")
    else:
        # Overview KPI
        st.caption(f"Q1 SPARK | {len(spark_sellers)} sellers")

        spark_by_owner = spark_sellers["owner"].value_counts()
        spark_by_tier = spark_sellers["tier"].value_counts()

        with st.container(border=True):
            sp_k1, sp_k2, sp_k3 = st.columns(3)
            with sp_k1:
                st.metric("總家數", len(spark_sellers))
            with sp_k2:
                tier_str = " · ".join([f"{t}: {c}" for t, c in spark_by_tier.items()])
                st.caption("by Tier")
                st.write(tier_str)
            with sp_k3:
                owner_str = " · ".join([f"{o}: {c}" for o, c in spark_by_owner.items()])
                st.caption("by Owner")
                st.write(owner_str)

        # SPARK 賣家明細
        spark_display = spark_sellers[["mcid", "name", "owner", "tier"]].copy()
        spark_display.columns = ["MCID", "名稱", "Owner", "Tier"]

        # 加上績效（週度 GMS）
        if not perf_df.empty and _lw:
            latest_perf = perf_df[(perf_df["year"] == _max_year) & (perf_df["week"] == _lw)]
            perf_agg = latest_perf.groupby("mcid").agg(
                gms=("gms", "sum"), ads_ops=("ads_ops", "sum"),
                promo_ops=("promo_ops", "sum"), ba=("ba", "sum"),
            ).reset_index()
            perf_agg.columns = ["MCID", "GMS", "Ads OPS", "Promo OPS", "BA"]
            spark_display = spark_display.merge(perf_agg, on="MCID", how="left").fillna(0)
        else:
            for c in ["GMS", "Ads OPS", "Promo OPS", "BA"]:
                spark_display[c] = 0

        # ── GMS MoM / YoY / CTC（月度）──
        spark_display["GMS MoM"] = None
        spark_display["GMS YoY"] = None
        spark_display["CTC MoM"] = None
        spark_display["CTC YoY"] = None
        if not month_list_df.empty:
            _ml = list(zip(month_list_df["year"].astype(int), month_list_df["month"].astype(int)))
            if _ml:
                _cm_y, _cm_m = _ml[0]  # 最新月
                # 上月
                _pm_y, _pm_m = (_cm_y, _cm_m - 1) if _cm_m > 1 else (_cm_y - 1, 12)
                # 去年同月
                _ly_y, _ly_m = _cm_y - 1, _cm_m
                _spark_mcids = set(spark_display["MCID"])
                _month_pairs = tuple({(_cm_y, _cm_m), (_pm_y, _pm_m), (_ly_y, _ly_m)})
                _mperf = load_performance_months(_month_pairs)
                if not _mperf.empty:
                    _mperf = _mperf[_mperf["mcid"].isin(_spark_mcids)]
                    _mg = _mperf.groupby(["mcid", "year", "month"])["gms"].sum().reset_index()
                    _cm_gms = _mg[(_mg["year"] == _cm_y) & (_mg["month"] == _cm_m)].set_index("mcid")["gms"]
                    _pm_gms = _mg[(_mg["year"] == _pm_y) & (_mg["month"] == _pm_m)].set_index("mcid")["gms"]
                    _ly_gms = _mg[(_mg["year"] == _ly_y) & (_mg["month"] == _ly_m)].set_index("mcid")["gms"]
                    # SPARK 34 家前期總額（CTC 分母）
                    _total_pm = _pm_gms.sum()
                    _total_ly = _ly_gms.sum()
                    for idx, row in spark_display.iterrows():
                        _mid = row["MCID"]
                        _c = _cm_gms.get(_mid, 0)
                        _p = _pm_gms.get(_mid, 0)
                        _l = _ly_gms.get(_mid, 0)
                        spark_display.at[idx, "GMS MoM"] = pct_change(_c, _p)
                        spark_display.at[idx, "GMS YoY"] = pct_change(_c, _l)
                        # CTC = (個別變化) ÷ (前期總額) × 100
                        if _total_pm != 0:
                            spark_display.at[idx, "CTC MoM"] = (_c - _p) / _total_pm * 100
                        if _total_ly != 0:
                            spark_display.at[idx, "CTC YoY"] = (_c - _l) / _total_ly * 100

        # 加上最新 note（不截斷）
        _latest_notes = load_latest_notes()
        if not _latest_notes.empty:
            latest_notes = _latest_notes[["mcid", "content", "created_at"]].copy()
            latest_notes.columns = ["MCID", "Latest Note", "Note Date"]
            spark_display = spark_display.merge(latest_notes, on="MCID", how="left")

        spark_display = spark_display.sort_values("GMS", ascending=False)

        _ctc_mom_help_s = "CTC MoM = (該賣家本月 GMS − 上月 GMS) ÷ (34家上月總 GMS) × 100%。例：上月 34 家總 GMS = $280萬，A 賣家本月多了 $5萬 → CTC MoM = +5/280 = +1.8%。全部加總 = 整體 MoM%。"
        _ctc_yoy_help_s = "CTC YoY = (該賣家本月 GMS − 去年同月 GMS) ÷ (34家去年同月總 GMS) × 100%。例：去年同月 34 家總 GMS = $310萬，Phrozen 掉了 $20萬 → CTC YoY = −20/310 = −6.5%。全部加總 = 整體 YoY%。"
        _pct_cols_s = ["GMS MoM", "GMS YoY", "CTC MoM", "CTC YoY"]
        st.dataframe(spark_display, use_container_width=True, hide_index=True, height=500,
                     column_config={
                         "GMS": st.column_config.NumberColumn("GMS", format="$%.0f"),
                         "Ads OPS": st.column_config.NumberColumn("Ads OPS", format="$%.0f"),
                         "Promo OPS": st.column_config.NumberColumn("Promo OPS", format="$%.0f"),
                         "GMS MoM": st.column_config.NumberColumn("GMS MoM", help="該賣家 GMS 的 Month-over-Month 變化率"),
                         "GMS YoY": st.column_config.NumberColumn("GMS YoY", help="該賣家 GMS 的 Year-over-Year 變化率"),
                         "CTC MoM": st.column_config.NumberColumn("CTC MoM", help=_ctc_mom_help_s),
                         "CTC YoY": st.column_config.NumberColumn("CTC YoY", help=_ctc_yoy_help_s),
                         "Latest Note": st.column_config.TextColumn("Latest Note", width="large"),
                     })
with tab_base:

    base_view = st.segmented_control(
        "數據來源", ["MBR 全量 (Monthly)", "WBR (Weekly)"],
        default="MBR 全量 (Monthly)", key="base_view",
    )
    if not base_view:
        base_view = "MBR 全量 (Monthly)"

    if base_view == "MBR 全量 (Monthly)":
        # ── MBR 全量：SQL 層篩選 + lazy loading ──

        @st.cache_data(ttl=300)
        def _load_raw_month_list():
            conn = get_db_connection()
            if conn is None:
                return pd.DataFrame()
            df = pd.read_sql(
                "SELECT DISTINCT year, month FROM pkey_raw_monthly ORDER BY year DESC, month DESC",
                conn,
            )
            conn.close()
            return df

        @st.cache_data(ttl=300)
        def _load_raw_filter_options(year: int, month: int):
            """一次查完所有文字欄位的 distinct 值（單條 SQL，極快）"""
            conn = get_db_connection()
            if conn is None:
                return {}
            _text_cols = [
                "sub_tier", "am", "sp_primary_pg", "sp_primary_gl",
                "main_tier", "status", "launch_year_cohort",
                "marketplace", "region", "launch_program", "launch_channel",
                "launch_year_group", "launch_year",
                "is_brand_reg", "is_brand_rep",
                "is_carryover_nsr", "seller_age",
            ]
            # 一條 UNION ALL 一次撈完，比 17 次 SELECT DISTINCT 快 10 倍以上
            unions = " UNION ALL ".join(
                f"SELECT '{col}' as col, {col} as val FROM pkey_raw_monthly "
                f"WHERE year=? AND month=? AND {col} != '' GROUP BY {col}"
                for col in _text_cols
            )
            params = []
            for _ in _text_cols:
                params.extend([year, month])
            rows = conn.execute(unions, params).fetchall()
            conn.close()

            options: dict[str, list[str]] = {}
            for col_name, val in rows:
                options.setdefault(col_name, []).append(val)
            # 排序
            for k in options:
                options[k].sort()
            return options

        @st.cache_data(ttl=120)
        def _query_raw_monthly(year: int, month: int, text_filters: tuple,
                               search: str, limit: int,
                               numeric_filters: tuple = ()):
            """SQL 層篩選 + 排序 + LIMIT，只回傳需要的資料。

            text_filters: tuple of (column, tuple_of_values) — 每個欄位多選 AND 交集
            numeric_filters: tuple of (column, operator, value) 三元組
            """
            conn = get_db_connection()
            if conn is None:
                return pd.DataFrame(), 0
            conditions = ["year = ?", "month = ?"]
            params: list = [year, month]
            # 文字欄位篩選（multiselect AND 交集）
            for col, vals in text_filters:
                if vals:
                    ph = ",".join(["?"] * len(vals))
                    conditions.append(f"{col} IN ({ph})")
                    params.extend(vals)
            if search:
                conditions.append(
                    "(mcid LIKE ? OR merchant_name LIKE ? OR sp_primary_gl LIKE ?)"
                )
                pattern = f"%{search}%"
                params.extend([pattern, pattern, pattern])
            # 數值篩選
            _valid_ops = {"=", ">", ">=", "<", "<="}
            for col, op, val in numeric_filters:
                if op not in _valid_ops:
                    continue
                conditions.append(f"{col} {op} ?")
                params.append(val)

            where = " AND ".join(conditions)

            total = conn.execute(
                f"SELECT COUNT(*) FROM pkey_raw_monthly WHERE {where}", params
            ).fetchone()[0]

            df = pd.read_sql(
                f"SELECT * FROM pkey_raw_monthly WHERE {where} "
                f"ORDER BY mtd_ord_gms DESC LIMIT ?",
                conn, params=params + [limit],
            )
            conn.close()
            return df, total

        raw_ml = _load_raw_month_list()
        if raw_ml.empty:
            st.info("pkey_raw_monthly 沒有資料。請先執行 sync-mbr。")
        else:
            @st.fragment
            def _mbr_base_fragment():
                # 月份選擇器
                ym_options = [f"{int(r['year'])}-{int(r['month']):02d}" for _, r in raw_ml.iterrows()]
                bc_ym = st.selectbox("月份", ym_options, key="base_raw_ym")
                sel_year, sel_month = int(bc_ym.split("-")[0]), int(bc_ym.split("-")[1])

                # 載入篩選器選項
                filter_options = _load_raw_filter_options(sel_year, sel_month)
                _available_cols = sorted(filter_options.keys())

                # 欄位顯示名稱 mapping
                _COL_LABELS = {
                    "sub_tier": "Sub Tier", "am": "AM", "sp_primary_pg": "Product Group",
                    "sp_primary_gl": "GL", "main_tier": "Main Tier", "status": "Status",
                    "launch_year_cohort": "年資 Cohort", "marketplace": "Marketplace",
                    "region": "Region", "launch_program": "Launch Program",
                    "launch_channel": "Launch Channel", "launch_year_group": "Launch Year Group",
                    "launch_year": "Launch Year", "is_brand_reg": "Brand Reg",
                    "is_brand_rep": "Brand Rep", "is_carryover_nsr": "Carryover NSR",
                    "seller_age": "Seller Age",
                }
                _col_display = [_COL_LABELS.get(c, c) for c in _available_cols]
                _col_reverse = {_COL_LABELS.get(c, c): c for c in _available_cols}

                # 搜尋框
                raw_search = st.text_input(":material/search: 搜尋", key="raw_search",
                                           placeholder="名稱 / MCID / GL")

                # ── 動態欄位篩選（可加可刪）──
                text_selections: list[tuple] = []

                with st.expander(":material/filter_list: 欄位篩選（交集）", expanded=True):
                    if "mbr_tf_count" not in st.session_state:
                        st.session_state.mbr_tf_count = 1

                    rows_to_delete = []
                    for i in range(st.session_state.mbr_tf_count):
                        tf1, tf2, tf3 = st.columns([2, 5, 0.5])
                        with tf1:
                            sel_col_display = st.selectbox(
                                "欄位", ["（不篩選）"] + _col_display,
                                key=f"mbr_tf_col_{i}", label_visibility="collapsed",
                            )
                        with tf2:
                            if sel_col_display != "（不篩選）":
                                db_col = _col_reverse[sel_col_display]
                                col_options = filter_options.get(db_col, [])
                                sel_vals = st.multiselect(
                                    "值", col_options,
                                    key=f"mbr_tf_val_{i}", label_visibility="collapsed",
                                    placeholder="選擇值...",
                                )
                                if sel_vals:
                                    text_selections.append((db_col, tuple(sel_vals)))
                            else:
                                st.empty()
                        with tf3:
                            if st.button("✕", key=f"mbr_tf_del_{i}", help="刪除此條件"):
                                rows_to_delete.append(i)

                    bc_add, bc_reset = st.columns([1, 1])
                    with bc_add:
                        if st.button(":material/add: 新增條件", key="mbr_tf_add"):
                            st.session_state.mbr_tf_count += 1
                    with bc_reset:
                        if st.button(":material/refresh: 重置", key="mbr_tf_reset"):
                            keys_to_clear = [k for k in st.session_state if k.startswith("mbr_tf_")]
                            for k in keys_to_clear:
                                del st.session_state[k]
                            st.session_state.mbr_tf_count = 1

                    if rows_to_delete:
                        old_count = st.session_state.mbr_tf_count
                        new_idx = 0
                        new_state = {}
                        for old_idx in range(old_count):
                            if old_idx in rows_to_delete:
                                continue
                            for suffix in ["col", "val"]:
                                old_key = f"mbr_tf_{suffix}_{old_idx}"
                                new_key = f"mbr_tf_{suffix}_{new_idx}"
                                if old_key in st.session_state:
                                    new_state[new_key] = st.session_state[old_key]
                            new_idx += 1
                        keys_to_clear = [k for k in st.session_state if k.startswith("mbr_tf_") and k != "mbr_tf_count"]
                        for k in keys_to_clear:
                            del st.session_state[k]
                        for k, v in new_state.items():
                            st.session_state[k] = v
                        st.session_state.mbr_tf_count = max(new_idx, 1)

                # ── 進階數值篩選 ──
                _NUMERIC_COLS_MBR = [
                    ("mtd_ord_gms", "GMS"), ("ytd_ord_gms", "YTD GMS"),
                    ("mtd_fba_ord_gms", "FBA GMS"), ("mtd_ba", "BA"),
                    ("mtd_fba_ba", "FBA BA"), ("mtd_new_fba_ba_90d", "New FBA BA"),
                    ("mtd_fba_awagv", "FBA AWAGV"), ("mtd_fba_awas", "FBA AWAS"),
                    ("mtd_sa_revenue_usd", "Ads Spend"), ("mtd_sa_attributed_ops_usd", "Ads OPS"),
                    ("mtd_promotion_count", "Promo Count"), ("mtd_promotion_ops", "Promo OPS"),
                    ("mtd_deal_count", "Deal Count"), ("mtd_deal_ops", "Deal OPS"),
                    ("mtd_coupon_count", "Coupon Count"), ("mtd_coupon_ops", "Coupon OPS"),
                    ("mtd_gv", "GV"), ("mtd_ord_units", "Units"),
                    ("mtd_ord_asp", "ASP"), ("mtd_awas", "AWAS"),
                    ("mtd_awagv", "AWAGV"),
                ]
                _NUM_COL_MAP = {label: col for col, label in _NUMERIC_COLS_MBR}
                _NUM_LABELS = [label for _, label in _NUMERIC_COLS_MBR]
                _OPS = [">=", "<=", ">", "<", "="]

                numeric_filters_raw: list[tuple] = []

                with st.expander(":material/filter_alt: 進階數值篩選", expanded=False):
                    if "mbr_nf_count" not in st.session_state:
                        st.session_state.mbr_nf_count = 1

                    nf_rows_to_delete = []
                    for i in range(st.session_state.mbr_nf_count):
                        nf1, nf2, nf3, nf4 = st.columns([3, 1.5, 2, 0.5])
                        with nf1:
                            sel_col = st.selectbox(
                                "欄位", ["（不篩選）"] + _NUM_LABELS,
                                key=f"mbr_nf_col_{i}", label_visibility="collapsed",
                            )
                        with nf2:
                            sel_op = st.selectbox(
                                "運算子", _OPS,
                                key=f"mbr_nf_op_{i}", label_visibility="collapsed",
                            )
                        with nf3:
                            sel_val = st.number_input(
                                "值", value=0.0, step=1.0,
                                key=f"mbr_nf_val_{i}", label_visibility="collapsed",
                            )
                        with nf4:
                            if st.button("✕", key=f"mbr_nf_del_{i}", help="刪除此條件"):
                                nf_rows_to_delete.append(i)
                        if sel_col != "（不篩選）":
                            db_col = _NUM_COL_MAP[sel_col]
                            numeric_filters_raw.append((db_col, sel_op, sel_val))

                    nf_add, nf_reset = st.columns([1, 1])
                    with nf_add:
                        if st.button(":material/add: 新增條件", key="mbr_nf_add"):
                            st.session_state.mbr_nf_count += 1
                    with nf_reset:
                        if st.button(":material/refresh: 重置", key="mbr_nf_reset"):
                            keys_to_clear = [k for k in st.session_state if k.startswith("mbr_nf_")]
                            for k in keys_to_clear:
                                del st.session_state[k]
                            st.session_state.mbr_nf_count = 1

                    if nf_rows_to_delete:
                        old_count = st.session_state.mbr_nf_count
                        new_idx = 0
                        new_state = {}
                        for old_idx in range(old_count):
                            if old_idx in nf_rows_to_delete:
                                continue
                            for suffix in ["col", "op", "val"]:
                                old_key = f"mbr_nf_{suffix}_{old_idx}"
                                new_key = f"mbr_nf_{suffix}_{new_idx}"
                                if old_key in st.session_state:
                                    new_state[new_key] = st.session_state[old_key]
                            new_idx += 1
                        keys_to_clear = [k for k in st.session_state if k.startswith("mbr_nf_") and k != "mbr_nf_count"]
                        for k in keys_to_clear:
                            del st.session_state[k]
                        for k, v in new_state.items():
                            st.session_state[k] = v
                        st.session_state.mbr_nf_count = max(new_idx, 1)

                # 顯示筆數控制
                show_all_raw = st.toggle("顯示全部", value=False, key="raw_show_all")
                display_limit = 99999 if show_all_raw else 200

                # SQL 層查詢
                raw_df, total_count = _query_raw_monthly(
                    sel_year, sel_month,
                    tuple(text_selections),
                    raw_search, display_limit,
                    tuple(numeric_filters_raw),
                )

                showing = len(raw_df)
                st.caption(
                    f"顯示 {showing:,} / {total_count:,} 筆 | "
                    f"{sel_year}-{sel_month:02d} | {len(raw_df.columns)} 欄"
                )

                raw_money_cols = [c for c in raw_df.columns if any(
                    kw in c for kw in ["gms", "ops", "spend", "revenue", "asp"]
                )]
                raw_col_config = {}
                for c in raw_money_cols:
                    if c in raw_df.columns:
                        raw_col_config[c] = st.column_config.NumberColumn(format="$%.0f")

                st.dataframe(raw_df, use_container_width=True, hide_index=True,
                             height=500, column_config=raw_col_config)

                if showing < total_count and not show_all_raw:
                    st.caption(f"預覽前 {showing} 筆（GMS 排序），開啟「顯示全部」看完整 {total_count:,} 筆")

            _mbr_base_fragment()

    else:
        # ── WBR：SQL 層篩選 + lazy loading ──

        @st.cache_data(ttl=300)
        def _load_wbr_filter_options():
            """載入 WBR 底表篩選器選項"""
            conn = get_db_connection()
            if conn is None:
                return [], [], []
            q1s = [r[0] for r in conn.execute(
                "SELECT DISTINCT q1_am FROM sellers WHERE q1_am IS NOT NULL AND q1_am != '' ORDER BY q1_am"
            ).fetchall()]
            q2s = [r[0] for r in conn.execute(
                "SELECT DISTINCT q2_am FROM sellers WHERE q2_am IS NOT NULL AND q2_am != '' ORDER BY q2_am"
            ).fetchall()]
            coops = [r[0] for r in conn.execute(
                "SELECT DISTINCT cooperation_level FROM sellers WHERE cooperation_level IS NOT NULL AND cooperation_level != '' ORDER BY cooperation_level"
            ).fetchall()]
            conn.close()
            return q1s, q2s, coops

        @st.cache_data(ttl=120)
        def _query_wbr_base(tier_filter: tuple, owner_filter: str,
                            q1_am: str, q2_am: str, coop: str,
                            sub_tiers: tuple, pgs: tuple,
                            search: str, limit: int,
                            numeric_filters: tuple = ()):
            """SQL 層 JOIN sellers + performance_data 最新週，帶篩選 + LIMIT

            sub_tiers / pgs: tuple of selected values（空 = 不篩選）
            numeric_filters: tuple of (column, operator, value) 三元組
            """
            conn = get_db_connection()
            if conn is None:
                return pd.DataFrame(), 0, "No data"

            # 找最新 (year, week)
            latest = conn.execute(
                "SELECT year, week FROM performance_data ORDER BY year DESC, week DESC LIMIT 1"
            ).fetchone()
            if latest is None:
                conn.close()
                return pd.DataFrame(), 0, "No data"
            ly, lw = latest[0], latest[1]

            # 建構 SQL
            sql = """
                SELECT s.mcid, s.name, s.owner, s.q1_am, s.q2_am,
                       s.cooperation_level, s.created_at, s.updated_at,
                       s.launch_date, s.launch_year, s.seller_age,
                       s.launch_program, s.launch_channel,
                       s.sp_primary_pg, s.sp_primary_gl,
                       s.is_brand_reg, s.is_brand_rep,
                       s.main_tier, s.sub_tier, s.status,
                       COALESCE(p.gms, 0) as gms,
                       COALESCE(p.ytd_gms, 0) as ytd_gms,
                       COALESCE(p.ba, 0) as ba,
                       COALESCE(p.fba_ba, 0) as fba_ba,
                       COALESCE(p.new_fba_ba, 0) as new_fba_ba,
                       COALESCE(p.fba_awagv, 0) as fba_awagv,
                       COALESCE(p.fba_awas, 0) as fba_awas,
                       COALESCE(p.ads_spend, 0) as ads_spend,
                       COALESCE(p.ads_ops, 0) as ads_ops,
                       COALESCE(p.ytd_ads_spend, 0) as ytd_ads_spend,
                       COALESCE(p.ytd_ads_ops, 0) as ytd_ads_ops,
                       COALESCE(p.promo_count, 0) as promo_count,
                       COALESCE(p.promo_ops, 0) as promo_ops,
                       COALESCE(p.active_seller, 0) as active_seller,
                       COALESCE(p.gv, 0) as gv,
                       s.tags
                FROM sellers s
                LEFT JOIN (
                    SELECT mcid,
                           SUM(gms) as gms, SUM(ytd_gms) as ytd_gms,
                           SUM(ba) as ba, SUM(fba_ba) as fba_ba,
                           SUM(new_fba_ba) as new_fba_ba,
                           AVG(fba_awagv) as fba_awagv, AVG(fba_awas) as fba_awas,
                           SUM(ads_spend) as ads_spend, SUM(ads_ops) as ads_ops,
                           SUM(ytd_ads_spend) as ytd_ads_spend, SUM(ytd_ads_ops) as ytd_ads_ops,
                           SUM(promo_count) as promo_count, SUM(promo_ops) as promo_ops,
                           MAX(active_seller) as active_seller, SUM(gv) as gv
                    FROM performance_data
                    WHERE year = ? AND week = ?
                    GROUP BY mcid
                ) p ON s.mcid = p.mcid
                WHERE 1=1
            """
            params = [ly, lw]

            # Tier 篩選（用 tags JSON LIKE）
            if tier_filter:
                tier_conditions = " OR ".join(["s.tags LIKE ?" for _ in tier_filter])
                sql += f" AND ({tier_conditions})"
                params.extend([f'%"tier:{t}"%' for t in tier_filter])

            # Owner 篩選
            if owner_filter != "All":
                sql += " AND s.owner = ?"
                params.append(owner_filter)

            if q1_am != "All":
                sql += " AND s.q1_am = ?"
                params.append(q1_am)
            if q2_am != "All":
                sql += " AND s.q2_am = ?"
                params.append(q2_am)
            if coop != "All":
                sql += " AND s.cooperation_level = ?"
                params.append(coop)
            if sub_tiers:
                ph = ",".join(["?"] * len(sub_tiers))
                sql += f" AND s.sub_tier IN ({ph})"
                params.extend(sub_tiers)
            if pgs:
                ph = ",".join(["?"] * len(pgs))
                sql += f" AND s.sp_primary_pg IN ({ph})"
                params.extend(pgs)
            if search:
                sql += " AND (s.name LIKE ? OR s.mcid LIKE ?)"
                pattern = f"%{search}%"
                params.extend([pattern, pattern])
            # 數值篩選（作用在 JOIN 後的欄位，包含 p.* 和 s.* 欄位）
            _valid_ops = {"=", ">", ">=", "<", "<="}
            for col, op, val in numeric_filters:
                if op not in _valid_ops:
                    continue
                sql += f" AND {col} {op} ?"
                params.append(val)

            # COUNT
            count_sql = f"SELECT COUNT(*) FROM ({sql})"
            total = conn.execute(count_sql, params).fetchone()[0]

            # 資料（帶排序 + LIMIT）
            sql += " ORDER BY gms DESC LIMIT ?"
            params.append(limit)

            df = pd.read_sql(sql, conn, params=params)
            conn.close()
            return df, total, f"W{lw} {ly}"

        # 篩選器選項
        opt_q1s, opt_q2s, opt_coops = _load_wbr_filter_options()

        @st.cache_data(ttl=300)
        def _load_wbr_seller_filter_options():
            """載入 sellers 表的 sub_tier / sp_primary_pg 選項"""
            conn = get_db_connection()
            if conn is None:
                return [], []
            sub_tiers = [r[0] for r in conn.execute(
                "SELECT DISTINCT sub_tier FROM sellers WHERE sub_tier IS NOT NULL AND sub_tier != '' ORDER BY sub_tier"
            ).fetchall()]
            pgs = [r[0] for r in conn.execute(
                "SELECT DISTINCT sp_primary_pg FROM sellers WHERE sp_primary_pg IS NOT NULL AND sp_primary_pg != '' ORDER BY sp_primary_pg"
            ).fetchall()]
            conn.close()
            return sub_tiers, pgs

        opt_sub_tiers_wbr, opt_pgs_wbr = _load_wbr_seller_filter_options()

        @st.fragment
        def _wbr_base_fragment():
            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                base_sub_tier = st.multiselect("Sub Tier", opt_sub_tiers_wbr, key="base_sub_tier",
                                               placeholder="全部")
            with bc2:
                base_pg = st.multiselect("Product Group", opt_pgs_wbr, key="base_pg",
                                         placeholder="全部")
            with bc3:
                base_search = st.text_input(":material/search: 搜尋", key="base_search", placeholder="名稱 / MCID")

            bc4, bc5, bc6 = st.columns(3)
            with bc4:
                base_q1 = st.selectbox("Q1 AM", ["All"] + opt_q1s, key="base_q1")
            with bc5:
                base_q2 = st.selectbox("Q2 AM", ["All"] + opt_q2s, key="base_q2")
            with bc6:
                base_coop = st.selectbox("配合度", ["All"] + opt_coops, key="base_coop")

            # ── 進階數值篩選 ──
            _NUMERIC_COLS_WBR = [
                ("gms", "GMS"), ("ytd_gms", "YTD GMS"),
                ("ba", "BA"), ("fba_ba", "FBA BA"),
                ("new_fba_ba", "New FBA BA"),
                ("fba_awagv", "FBA AWAGV"), ("fba_awas", "FBA AWAS"),
                ("ads_spend", "Ads Spend"), ("ads_ops", "Ads OPS"),
                ("ytd_ads_spend", "YTD Ads Spend"), ("ytd_ads_ops", "YTD Ads OPS"),
                ("promo_count", "Promo Count"), ("promo_ops", "Promo OPS"),
                ("active_seller", "Active Seller"), ("gv", "GV"),
            ]
            _NUM_COL_MAP_W = {label: col for col, label in _NUMERIC_COLS_WBR}
            _NUM_LABELS_W = [label for _, label in _NUMERIC_COLS_WBR]
            _OPS_W = [">=", "<=", ">", "<", "="]

            numeric_filters_wbr: list[tuple] = []

            with st.expander(":material/filter_alt: 進階數值篩選", expanded=False):
                if "wbr_nf_count" not in st.session_state:
                    st.session_state.wbr_nf_count = 1

                wbr_nf_rows_to_delete = []
                for i in range(st.session_state.wbr_nf_count):
                    nf1, nf2, nf3, nf4 = st.columns([3, 1.5, 2, 0.5])
                    with nf1:
                        sel_col = st.selectbox(
                            "欄位", ["（不篩選）"] + _NUM_LABELS_W,
                            key=f"wbr_nf_col_{i}", label_visibility="collapsed",
                        )
                    with nf2:
                        sel_op = st.selectbox(
                            "運算子", _OPS_W,
                            key=f"wbr_nf_op_{i}", label_visibility="collapsed",
                        )
                    with nf3:
                        sel_val = st.number_input(
                            "值", value=0.0, step=1.0,
                            key=f"wbr_nf_val_{i}", label_visibility="collapsed",
                        )
                    with nf4:
                        if st.button("✕", key=f"wbr_nf_del_{i}", help="刪除此條件"):
                            wbr_nf_rows_to_delete.append(i)
                    if sel_col != "（不篩選）":
                        db_col = _NUM_COL_MAP_W[sel_col]
                        numeric_filters_wbr.append((db_col, sel_op, sel_val))

                wnf_add, wnf_reset = st.columns([1, 1])
                with wnf_add:
                    if st.button(":material/add: 新增條件", key="wbr_nf_add"):
                        st.session_state.wbr_nf_count += 1
                with wnf_reset:
                    if st.button(":material/refresh: 重置", key="wbr_nf_reset"):
                        keys_to_clear = [k for k in st.session_state if k.startswith("wbr_nf_")]
                        for k in keys_to_clear:
                            del st.session_state[k]
                        st.session_state.wbr_nf_count = 1

                if wbr_nf_rows_to_delete:
                    old_count = st.session_state.wbr_nf_count
                    new_idx = 0
                    new_state = {}
                    for old_idx in range(old_count):
                        if old_idx in wbr_nf_rows_to_delete:
                            continue
                        for suffix in ["col", "op", "val"]:
                            old_key = f"wbr_nf_{suffix}_{old_idx}"
                            new_key = f"wbr_nf_{suffix}_{new_idx}"
                            if old_key in st.session_state:
                                new_state[new_key] = st.session_state[old_key]
                        new_idx += 1
                    keys_to_clear = [k for k in st.session_state if k.startswith("wbr_nf_") and k != "wbr_nf_count"]
                    for k in keys_to_clear:
                        del st.session_state[k]
                    for k, v in new_state.items():
                        st.session_state[k] = v
                    st.session_state.wbr_nf_count = max(new_idx, 1)

            show_all = st.toggle("顯示全部", value=False, key="base_show_all")
            wbr_limit = 99999 if show_all else 200

            display_base, wbr_total, perf_week_label = _query_wbr_base(
                tuple(selected_tiers) if selected_tiers else (),
                selected_owner,
                base_q1, base_q2, base_coop,
                tuple(base_sub_tier), tuple(base_pg),
                base_search, wbr_limit,
                tuple(numeric_filters_wbr),
            )

            showing = len(display_base)
            st.caption(
                f"顯示 {showing:,} / {wbr_total:,} 筆 | "
                f"績效數據：{perf_week_label}"
            )

            # Column config
            col_config = {}
            money_cols = ["gms", "ytd_gms", "ads_spend", "ads_ops", "ytd_ads_spend", "ytd_ads_ops", "promo_ops"]
            int_cols_base = ["ba", "fba_ba", "promo_count", "active_seller", "gv"]

            COLUMN_LABELS = {
                "mcid": "MCID", "name": "名稱", "owner": "Owner",
                "cooperation_level": "配合度",
                "q1_am": "Q1 AM", "q2_am": "Q2 AM",
                "created_at": "建立時間", "updated_at": "更新時間",
                "gms": "GMS", "ytd_gms": "YTD GMS",
                "ba": "BA", "fba_ba": "FBA BA",
                "new_fba_ba": "New FBA BA", "fba_awagv": "FBA AWAGV", "fba_awas": "FBA AWAS",
                "ads_spend": "Ads Spend", "ads_ops": "Ads OPS",
                "ytd_ads_spend": "YTD Ads Spend", "ytd_ads_ops": "YTD Ads OPS",
                "promo_count": "Promo Count", "promo_ops": "Promo OPS",
                "active_seller": "Active", "gv": "GV",
                "tags": "Tags",
            }

            for col in display_base.columns:
                label = COLUMN_LABELS.get(col)
                if not label:
                    continue
                if col in money_cols:
                    col_config[col] = st.column_config.NumberColumn(label, format="$%.0f")
                elif col in int_cols_base:
                    col_config[col] = st.column_config.NumberColumn(label, format="%.0f")
                else:
                    col_config[col] = st.column_config.Column(label)

            st.dataframe(display_base, use_container_width=True, hide_index=True,
                         height=500, column_config=col_config)

            if showing < wbr_total and not show_all:
                st.caption(f"預覽前 {showing} 筆（GMS 排序），開啟「顯示全部」看完整 {wbr_total:,} 筆")

        _wbr_base_fragment()

# ── 底部 ──
st.markdown("---")
st.caption(f":material/folder: 資料庫：{DB_PATH} | :material/refresh: 頁面刷新即讀取最新資料（F5 或 Ctrl+R）")
