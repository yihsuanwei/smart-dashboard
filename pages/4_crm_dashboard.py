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

# 解析 tags
sellers_df["tags_list"] = sellers_df["tags"].apply(parse_tags)
sellers_df["tier"] = sellers_df["tags_list"].apply(lambda t: get_tag_value(t, "tier"))
sellers_df["spark_phase"] = sellers_df["tags_list"].apply(lambda t: get_tag_value(t, "spark-phase"))
sellers_df["is_q1_spark"] = sellers_df["tags_list"].apply(lambda t: "Q1_Spark" in t)

st.write("")

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

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 1.5, 2, 1.5])

with filter_col1:
    selected_tiers_display = st.pills(
        "Tier", all_tiers_display, default=default_display,
        selection_mode="multi", key="crm_tier_filter",
    )
    selected_tiers = [TIER_REVERSE.get(d, d) for d in (selected_tiers_display or [])]
with filter_col2:
    owners = ["All"] + sorted(sellers_df["owner"].dropna().unique().tolist())
    selected_owner = st.selectbox("Owner", owners, key="crm_owner_filter")
with filter_col3:
    search_keyword = st.text_input(":material/search: 搜尋（名稱/MCID）", key="crm_search")
with filter_col4:
    if not perf_df.empty:
        weeks = sorted(perf_df["week"].unique().tolist(), reverse=True)
        week_options = [f"W{w}" for w in weeks]
        selected_week_label = st.selectbox("週次", ["Latest"] + week_options, key="crm_week_filter")
    else:
        selected_week_label = "Latest"
        st.selectbox("週次", ["No data"], disabled=True)

# 套用篩選
filtered = sellers_df.copy()
if selected_tiers:
    filtered = filtered[filtered["tier"].isin(selected_tiers)]
if selected_owner != "All":
    filtered = filtered[filtered["owner"] == selected_owner]
if search_keyword:
    kw = search_keyword.lower()
    filtered = filtered[
        filtered["name"].str.lower().str.contains(kw, na=False) |
        filtered["mcid"].str.contains(kw, na=False)
    ]

st.write("")

# ── KPI 卡片 ──
# SPARK 從全局算（跟著 seller，不受 tier 篩選影響）
spark_q1_count = int(sellers_df["is_q1_spark"].sum())

_filtered_mcids = set(filtered["mcid"])
_week_gms = 0
_prev_gms = 0
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

_delta_gms = f"{(_week_gms - _prev_gms) / _prev_gms * 100:+.1f}%" if _prev_gms else None

_ignite_mcids = set(filtered[filtered["tier"].isin({"ignite-y4+", "ignite-y2y3"})]["mcid"])
_ignite_gms = 0
_ignite_prev = 0
if not perf_df.empty and _ignite_mcids:
    if _lw:
        _ignite_gms = perf_df[(perf_df["year"] == _max_year) & (perf_df["week"] == _lw) & (perf_df["mcid"].isin(_ignite_mcids))]["gms"].sum()
    if _pw:
        _ignite_prev = perf_df[(perf_df["year"] == _max_year) & (perf_df["week"] == _pw) & (perf_df["mcid"].isin(_ignite_mcids))]["gms"].sum()
_delta_ignite = f"{(_ignite_gms - _ignite_prev) / _ignite_prev * 100:+.1f}%" if _ignite_prev else None

kpi_row = st.columns(4, gap="medium")
with kpi_row[0]:
    with st.container(border=True, height="stretch"):
        st.metric("篩選賣家數", f"{len(filtered):,}")
with kpi_row[1]:
    with st.container(border=True, height="stretch"):
        st.metric("Q1 SPARK 家數", spark_q1_count)
with kpi_row[2]:
    with st.container(border=True, height="stretch"):
        st.metric("本週 GMS", money(_week_gms), delta=_delta_gms)
with kpi_row[3]:
    with st.container(border=True, height="stretch"):
        st.metric("Ignite 本週 GMS", money(_ignite_gms), delta=_delta_ignite)


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

tab_perf, tab_sellers, tab_spark, tab_base = st.tabs([
    ":material/trending_up: Performance",
    ":material/list: 賣家清單",
    ":material/star: SPARK 管理",
    ":material/table_chart: 底表",
])

# ── Tab 1: Performance（群體切換 + WBR/MBR toggle）──
with tab_perf:

    perf_group_col, perf_view_col = st.columns([2, 1])
    with perf_group_col:
        group_choice = st.segmented_control(
            "群體", ["Ignite", "MM-MASS", "SPARK"],
            default="Ignite", key="perf_group",
        )
    with perf_view_col:
        view_choice = st.segmented_control(
            "數據來源", ["WBR (Weekly)", "MBR (Monthly)"],
            default="WBR (Weekly)", key="perf_view",
        )

    # 決定群體 MCID
    if group_choice == "Ignite":
        _group_mcids = set(sellers_df[sellers_df["tier"].isin({"ignite-y4+", "ignite-y2y3"})]["mcid"])
    elif group_choice == "MM-MASS":
        _group_mcids = set(sellers_df[sellers_df["tier"].isin({"ignite-y4+", "ignite-y2y3", "mass"})]["mcid"])
    else:  # SPARK
        _group_mcids = set(sellers_df[sellers_df["is_q1_spark"]]["mcid"])

    group_seller_count = len(_group_mcids)

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

            ly_src = perf_df[(perf_df["mcid"].isin(_group_mcids)) & (perf_df["year"] == max_y - 1) & (perf_df["week"] == cw)] if len(all_weeks) >= 1 else pd.DataFrame()
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

            st.caption(f"{group_choice} | W{cw} {max_y} | {group_seller_count} sellers")
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

            # Seller detail table
            if not curr.empty:
                detail = curr[["gms", "ads_ops", "promo_ops", "ba", "fba_ba"]].copy()
                detail = detail.reset_index()
                name_map = sellers_df.set_index("mcid")[["name", "tier", "owner"]].to_dict("index")
                detail["name"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("name", m))
                detail["tier"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("tier", ""))
                detail["owner"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("owner", ""))
                detail = detail.sort_values("gms", ascending=False)
                detail = detail[["name", "tier", "owner", "gms", "ads_ops", "promo_ops", "ba", "fba_ba"]]
                detail.columns = ["名稱", "Tier", "Owner", "GMS", "Ads OPS", "Promo OPS", "BA", "FBA BA"]
                st.dataframe(detail, use_container_width=True, hide_index=True, height=400,
                             column_config={
                                 "GMS": st.column_config.NumberColumn(format="$%.0f"),
                                 "Ads OPS": st.column_config.NumberColumn(format="$%.0f"),
                                 "Promo OPS": st.column_config.NumberColumn(format="$%.0f"),
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
            st.caption(f"{group_choice} | {mon_label} {max_y} | {group_seller_count} sellers")
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

            # Seller detail
            if not curr.empty:
                detail = curr[["gms", "ads_ops", "promo_ops", "ba", "fba_ba"]].copy()
                detail = detail.reset_index()
                name_map = sellers_df.set_index("mcid")[["name", "tier", "owner"]].to_dict("index")
                detail["name"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("name", m))
                detail["tier"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("tier", ""))
                detail["owner"] = detail["mcid"].map(lambda m: name_map.get(m, {}).get("owner", ""))
                detail = detail.sort_values("gms", ascending=False)
                detail = detail[["name", "tier", "owner", "gms", "ads_ops", "promo_ops", "ba", "fba_ba"]]
                detail.columns = ["名稱", "Tier", "Owner", "GMS", "Ads OPS", "Promo OPS", "BA", "FBA BA"]
                st.dataframe(detail, use_container_width=True, hide_index=True, height=400,
                             column_config={
                                 "GMS": st.column_config.NumberColumn(format="$%.0f"),
                                 "Ads OPS": st.column_config.NumberColumn(format="$%.0f"),
                                 "Promo OPS": st.column_config.NumberColumn(format="$%.0f"),
                             })
    else:
        st.info("沒有可用的績效數據。請先執行 sync-pkey 或 sync-mbr。")


# ── Tab 2: 賣家清單（含 Latest Note）──
with tab_sellers:
    # Lazy load notes
    notes_df = load_notes()

    # 獨立篩選器
    sl_c1, sl_c2, sl_c3 = st.columns([1, 1, 2])
    with sl_c1:
        sl_tiers = ["All"] + sorted(sellers_df["tier"].dropna().unique().tolist())
        sl_tier = st.selectbox("Tier", sl_tiers, key="sl_tier")
    with sl_c2:
        sl_owners = ["All"] + sorted(sellers_df["owner"].dropna().unique().tolist())
        sl_owner = st.selectbox("Owner", sl_owners, key="sl_owner")
    with sl_c3:
        sl_search = st.text_input(":material/search: 搜尋", key="sl_search", placeholder="名稱 / MCID")

    sl_df = sellers_df.copy()
    if sl_tier != "All":
        sl_df = sl_df[sl_df["tier"] == sl_tier]
    if sl_owner != "All":
        sl_df = sl_df[sl_df["owner"] == sl_owner]
    if sl_search:
        kw = sl_search.lower()
        sl_df = sl_df[sl_df["name"].str.lower().str.contains(kw, na=False) | sl_df["mcid"].str.contains(kw, na=False)]

    if sl_df.empty:
        st.info("查無符合條件的賣家")
    else:
        display_df = sl_df[["mcid", "name", "owner", "tier", "q1_am", "q2_am"]].copy()
        display_df.columns = ["MCID", "名稱", "Owner", "Tier", "Q1 AM", "Q2 AM"]

        # 加上最新績效
        if not perf_df.empty and _lw:
            latest_perf = perf_df[(perf_df["year"] == _max_year) & (perf_df["week"] == _lw)]
            gms_agg = latest_perf.groupby("mcid")["gms"].sum().to_dict()
            display_df["GMS"] = display_df["MCID"].map(gms_agg).fillna(0)
        else:
            display_df["GMS"] = 0

        # 加上最新 note
        if not notes_df.empty:
            latest_notes = notes_df.groupby("mcid").first().reset_index()[["mcid", "content", "created_at"]]
            latest_notes.columns = ["MCID", "Latest Note", "Note Date"]
            latest_notes["Latest Note"] = latest_notes["Latest Note"].str[:80]
            display_df = display_df.merge(latest_notes, on="MCID", how="left")

        display_df = display_df.sort_values("GMS", ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=500,
                     column_config={
                         "GMS": st.column_config.NumberColumn("GMS", format="$%.0f"),
                     })

# ── Tab 3: SPARK 管理 ──
with tab_spark:
    spark_sellers = sellers_df[sellers_df["is_q1_spark"]].copy()

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

        # 加上績效
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

        # 加上最新 note
        notes_df = load_notes()
        if not notes_df.empty:
            latest_notes = notes_df.groupby("mcid").first().reset_index()[["mcid", "content", "created_at"]]
            latest_notes.columns = ["MCID", "Latest Note", "Note Date"]
            latest_notes["Latest Note"] = latest_notes["Latest Note"].str[:60]
            spark_display = spark_display.merge(latest_notes, on="MCID", how="left")

        spark_display = spark_display.sort_values("GMS", ascending=False)
        st.dataframe(spark_display, use_container_width=True, hide_index=True, height=500,
                     column_config={
                         "GMS": st.column_config.NumberColumn(format="$%.0f"),
                         "Ads OPS": st.column_config.NumberColumn(format="$%.0f"),
                         "Promo OPS": st.column_config.NumberColumn(format="$%.0f"),
                         "BA": st.column_config.NumberColumn(format="%.0f"),
                     })


# ── Tab 4: 底表（sellers × 最新績效全欄位）──
with tab_base:
    st.caption("sellers × performance_data（最新週）全欄位 — 不受上方篩選器影響，用於核對資料正確性")

    # 底表獨立於全局 filter，永遠從完整 sellers_df 開始
    base_df = sellers_df.copy()

    # Join latest week performance
    if not perf_df.empty:
        latest_yw = perf_df.sort_values(["year", "week"], ascending=False).iloc[0]
        lw_b, ly_b = int(latest_yw["week"]), int(latest_yw["year"])
        latest_perf = perf_df[(perf_df["year"] == ly_b) & (perf_df["week"] == lw_b)].copy()
        perf_agg = latest_perf.groupby("mcid").agg(
            gms=("gms", "sum"), ytd_gms=("ytd_gms", "sum"),
            ba=("ba", "sum"), fba_ba=("fba_ba", "sum"),
            new_fba_ba=("new_fba_ba", "sum"),
            fba_awagv=("fba_awagv", "mean"), fba_awas=("fba_awas", "mean"),
            ads_spend=("ads_spend", "sum"), ads_ops=("ads_ops", "sum"),
            ytd_ads_spend=("ytd_ads_spend", "sum"), ytd_ads_ops=("ytd_ads_ops", "sum"),
            promo_count=("promo_count", "sum"), promo_ops=("promo_ops", "sum"),
            active_seller=("active_seller", "max"), gv=("gv", "sum"),
        ).reset_index()
        base_df = base_df.merge(perf_agg, on="mcid", how="left")
        perf_week_label = f"W{lw_b} {ly_b}"
    else:
        perf_week_label = "No data"

    # Filters
    bc0, bc1, bc2, bc3, bc4, bc5 = st.columns(6)
    with bc0:
        base_tiers = ["All"] + sorted(base_df["tier"].dropna().unique().tolist())
        base_tier = st.selectbox("Tier", base_tiers, key="base_tier")
    with bc1:
        base_owners = ["All"] + sorted(base_df["owner"].dropna().unique().tolist())
        base_owner = st.selectbox("Owner", base_owners, key="base_owner")
    with bc2:
        q1_ams = ["All"] + sorted(base_df["q1_am"].dropna().unique().tolist()) if "q1_am" in base_df.columns else ["All"]
        base_q1 = st.selectbox("Q1 AM", q1_ams, key="base_q1")
    with bc3:
        q2_ams = ["All"] + sorted(base_df["q2_am"].dropna().unique().tolist()) if "q2_am" in base_df.columns else ["All"]
        base_q2 = st.selectbox("Q2 AM", q2_ams, key="base_q2")
    with bc4:
        coop_levels = ["All"] + sorted([v for v in base_df["cooperation_level"].dropna().unique().tolist() if v]) if "cooperation_level" in base_df.columns else ["All"]
        base_coop = st.selectbox("配合度", coop_levels, key="base_coop")
    with bc5:
        base_search = st.text_input(":material/search: 搜尋", key="base_search", placeholder="名稱 / MCID")

    if base_tier != "All":
        base_df = base_df[base_df["tier"] == base_tier]
    if base_owner != "All":
        base_df = base_df[base_df["owner"] == base_owner]
    if base_q1 != "All" and "q1_am" in base_df.columns:
        base_df = base_df[base_df["q1_am"] == base_q1]
    if base_q2 != "All" and "q2_am" in base_df.columns:
        base_df = base_df[base_df["q2_am"] == base_q2]
    if base_coop != "All" and "cooperation_level" in base_df.columns:
        base_df = base_df[base_df["cooperation_level"] == base_coop]
    if base_search:
        kw = base_search.lower()
        base_df = base_df[
            base_df["name"].str.lower().str.contains(kw, na=False) |
            base_df["mcid"].str.contains(kw, na=False)
        ]

    # 欄位順序：tags 移到最右邊
    drop_cols = {"tags_list", "tier", "spark_phase", "is_q1_spark"}
    display_cols = [c for c in base_df.columns if c not in drop_cols and c != "tags"]
    if "tags" in base_df.columns:
        display_cols.append("tags")
    display_base = base_df[display_cols].copy()

    if "gms" in display_base.columns:
        display_base = display_base.sort_values("gms", ascending=False, na_position="last")

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

    st.caption(f"共 {len(display_base)} 筆 | 績效數據：{perf_week_label}")
    show_all = st.toggle("顯示全部", value=False, key="base_show_all")

    if show_all:
        st.dataframe(display_base, use_container_width=True, hide_index=True, height=600, column_config=col_config)
    else:
        st.dataframe(display_base.head(100), use_container_width=True, hide_index=True, height=400, column_config=col_config)
        if len(display_base) > 100:
            st.caption("預覽前 100 筆，開啟「顯示全部」看完整資料")

# ── 底部 ──
st.markdown("---")
st.caption(f":material/folder: 資料庫：{DB_PATH} | :material/refresh: 頁面刷新即讀取最新資料（F5 或 Ctrl+R）")
