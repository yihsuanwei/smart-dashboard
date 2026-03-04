import streamlit as st
from utils import list_uploaded_files, load_data
import pandas as pd

import base64


def render_kpi_widget(title, value, yoy_pct=None, mom_pct=None, prefix="", suffix="", show_change_percent=True, help_text=None):
    """渲染 KPI Widget"""
    def format_change(val, show_percent=True):
        if val is None or val == "-":
            return "-"

        # 格式化數值(加千分位)
        if show_percent:
            formatted_val = f"{val:.1f}%"
        else:
            formatted_val = f"{val:,.0f} bps"

        if val > 0:
            return f"<span style='color:green'>▲ {formatted_val}</span>"
        elif val < 0:
            return f"<span style='color:red'>▼ {abs(val):,.1f}{' bps' if not show_percent else '%'}</span>"
        else:
            return f"<span style='color:black'>0.0{' bps' if not show_percent else '%'}</span>"

    yoy_html = format_change(yoy_pct, show_change_percent)
    mom_html = format_change(mom_pct, show_change_percent)

    # 格式化數值
    if isinstance(value, (int, float)):
        # 如果是小數，保留小數位；如果是整數，顯示為整數
        if isinstance(value, float) and value % 1 != 0:
            formatted_value = f"{value:,.2f}"
        else:
            formatted_value = f"{round(value):,}"
    else:
        formatted_value = str(value)

    # 如果有 help_text，在標題旁邊加上 tooltip 圖示
    title_with_help = title
    if help_text:
        # HTML encode the help text for proper display and preserve line breaks
        help_text_escaped = help_text.replace('"', '&quot;').replace("'", '&#39;').replace('\n', '<br>')
        title_with_help = f'''{title} <span class="info-tooltip">
            <span class="info-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" style="vertical-align: middle;">
                    <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5" fill="none"/>
                    <text x="8" y="11" text-anchor="middle" font-size="10" font-weight="bold" fill="currentColor">?</text>
                </svg>
            </span>
            <span class="info-content">{help_text_escaped}</span>
        </span>'''

    st.markdown(f"""
    <style>
    .kpi-widget {{
        border:1px solid #e0e0e0;
        border-radius:10px;
        padding: 10px 12px;
        background-color:white;
        box-shadow:0 2px 5px rgba(0,0,0,0.05);
        text-align:center;
        min-height: 90px;
        display:flex;
        flex-direction:column;
        justify-content:center;
        gap: 2px;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        cursor: pointer;
        z-index: 1;
        position: relative;
        overflow: visible;
    }}
    .kpi-widget:hover {{
        transform: translateY(-20px) scale(1.15);
        box-shadow: 0 20px 40px rgba(255,153,0,0.4);
        z-index: 999;
        border-color: #FF9900;
        border-width: 2px;
    }}
    .kpi-title {{
        font-size: clamp(11px, 1.4vw, 17px);
        color: #555;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: visible;
        position: relative;
        line-height: 1.2;
    }}
    .kpi-value {{
        font-size: clamp(16px, 2.2vw, 28px);
        font-weight: 700;
        margin: 2px 0;
        color: #000;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.2;
    }}
    .kpi-change {{
        font-size: clamp(9px, 1.1vw, 13px);
        color: #888;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.2;
    }}
    .info-tooltip {{
        display: inline-block;
        margin-left: 6px;
        position: relative;
        cursor: help;
        vertical-align: middle;
    }}
    .info-icon {{
        color: #999;
        transition: all 0.3s ease;
        display: inline-block;
        vertical-align: middle;
    }}
    .info-tooltip:hover .info-icon {{
        color: #FF9900;
        transform: scale(1.15);
    }}
    .info-content {{
        visibility: hidden;
        opacity: 0;
        position: absolute;
        bottom: 150%;
        left: 50%;
        transform: translateX(-50%);
        background-color: rgba(40, 40, 40, 0.98);
        color: white;
        padding: 14px 18px;
        border-radius: 10px;
        font-size: 12.5px;
        line-height: 1.7;
        min-width: 260px;
        max-width: 340px;
        width: max-content;
        z-index: 999999;
        box-shadow: 0 6px 20px rgba(0,0,0,0.35);
        font-weight: normal;
        text-align: left;
        pointer-events: none;
        white-space: normal;
        transition: all 0.3s ease;
    }}
    .info-content::after {{
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border: 8px solid transparent;
        border-top-color: rgba(40, 40, 40, 0.98);
    }}
    .info-tooltip:hover .info-content {{
        visibility: visible;
        opacity: 1;
    }}
    </style>
    <div class="kpi-widget">
      <div class="kpi-title">{title_with_help}</div>
      <div class="kpi-value">{prefix}{formatted_value}{suffix}</div>
      <div class="kpi-change">
        YoY {yoy_html} | MoM {mom_html}
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_widget_with_percentage(title, value, percentage, yoy_pct=None, mom_pct=None):
    """渲染帶有百分比的 KPI Widget（用於 Promotion/Deal/Coupon OPS）"""
    def format_change(val):
        if val is None or val == "-":
            return "-"
        if val > 0:
            return f"<span style='color:green'>▲ {val:.1f}%</span>"
        elif val < 0:
            return f"<span style='color:red'>▼ {abs(val):.1f}%</span>"
        else:
            return f"<span style='color:black'>0.0%</span>"

    yoy_html = format_change(yoy_pct)
    mom_html = format_change(mom_pct)
    formatted_value = f"${round(value):,} <span class='kpi-pct-inline'>({percentage:.0f}%)</span>"

    st.markdown(f"""
    <style>
    .kpi-widget-with-percentage {{
        border:1px solid #e0e0e0;
        border-radius:10px;
        padding: 10px 12px;
        background-color:white;
        box-shadow:0 2px 5px rgba(0,0,0,0.05);
        text-align:center;
        min-height: 90px;
        display:flex;
        flex-direction:column;
        justify-content:center;
        gap: 2px;
        transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        cursor: pointer;
        z-index: 1;
        position: relative;
        overflow: visible;
    }}
    .kpi-widget-with-percentage:hover {{
        transform: translateY(-20px) scale(1.15);
        box-shadow: 0 20px 40px rgba(255,153,0,0.4);
        z-index: 999;
        border-color: #FF9900;
        border-width: 2px;
    }}
    .kpi-widget-with-percentage .kpi-title {{
        font-size: clamp(11px, 1.4vw, 17px);
        color: #555;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.2;
    }}
    .kpi-widget-with-percentage .kpi-value {{
        font-size: clamp(16px, 2.2vw, 28px);
        font-weight: 700;
        margin: 2px 0;
        color: #000;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.2;
    }}
    .kpi-widget-with-percentage .kpi-change {{
        font-size: clamp(9px, 1.1vw, 13px);
        color: #888;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.2;
    }}
    .kpi-pct-inline {{
        font-size: clamp(10px, 1.3vw, 17px);
        color: #888;
    }}
    </style>
    <div class="kpi-widget-with-percentage">
      <div class="kpi-title">{title}</div>
      <div class="kpi-value">{formatted_value}</div>
      <div class="kpi-change">
        YoY {yoy_html} | MoM {mom_html}
      </div>
    </div>
    """, unsafe_allow_html=True)


def match_date(row_date, target_date):
    """日期匹配函數"""
    try:
        if '/' in str(row_date) and '/' in str(target_date):
            row_parsed = pd.to_datetime(str(row_date), format='%m/%d/%Y')
            target_parsed = pd.to_datetime(str(target_date), format='%m/%d/%Y')
            return row_parsed == target_parsed
        else:
            return str(row_date) == str(target_date)
    except:
        return str(row_date) == str(target_date)


def calculate_metric_yoy_mom(sales_df, date_col, metric_col, original_date, cvr_mode=False):
    """
    計算指標的 YoY 和 MoM

    Args:
        sales_df: 數據 DataFrame
        date_col: 日期欄位名稱
        metric_col: 指標欄位名稱
        original_date: 當前日期字串
        cvr_mode: 是否為 CVR 模式（使用減法而非百分比）

    Returns:
        (current_value, yoy_change, mom_change)
    """
    current_value = 0
    yoy_change = None
    mom_change = None

    # 取得當前數據
    mask = sales_df[date_col].apply(lambda x: match_date(x, original_date))
    current_data = sales_df[mask][metric_col].dropna()
    if not current_data.empty:
        current_value = current_data.iloc[0]

    try:
        current_date = pd.to_datetime(original_date)

        # 計算前一個月的日期
        last_month_date = current_date - pd.DateOffset(months=1)
        last_month_str = last_month_date.strftime('%Y/%m/%d')
        last_month_mask = sales_df[date_col].apply(lambda x: match_date(x, last_month_str))
        last_month_data = sales_df[last_month_mask][metric_col].dropna()

        # 計算去年同月的日期
        last_year_date = current_date - pd.DateOffset(years=1)
        last_year_str = last_year_date.strftime('%Y/%m/%d')
        last_year_mask = sales_df[date_col].apply(lambda x: match_date(x, last_year_str))
        last_year_data = sales_df[last_year_mask][metric_col].dropna()

        # 計算 YoY
        if not last_year_data.empty:
            last_year_value = last_year_data.iloc[0]
            if cvr_mode:
                # CVR 使用差值 * 10000 = bps
                yoy_change = (current_value - last_year_value) * 10000
            elif last_year_value != 0:
                yoy_change = ((current_value - last_year_value) / last_year_value) * 100

        # 計算 MoM
        if not last_month_data.empty:
            last_month_value = last_month_data.iloc[0]
            if cvr_mode:
                # CVR 使用差值 * 10000 = bps
                mom_change = (current_value - last_month_value) * 10000
            elif last_month_value != 0:
                mom_change = ((current_value - last_month_value) / last_month_value) * 100
    except:
        pass

    return current_value, yoy_change, mom_change


def render_business_metric_widget(sales_df, date_col, original_date, metric_config):
    """
    渲染業務指標 Widget

    Args:
        sales_df: 數據 DataFrame
        date_col: 日期欄位名稱
        original_date: 當前日期
        metric_config: 配置字典 {
            'title': 'Widget 標題',
            'column_keywords': ['keyword1', 'keyword2'],  # 搜尋欄位的關鍵字
            'cvr_mode': False,  # 是否為 CVR 模式
            'prefix': '$',  # 數值前綴
            'suffix': '%'   # 數值後綴
        }
    """
    # 尋找目標欄位
    target_cols = [col for col in sales_df.columns
                   if any(kw in col.lower() for kw in metric_config['column_keywords'])]

    if target_cols:
        # 優先選擇不包含特定後綴的基本欄位
        basic_cols = [col for col in target_cols
                      if not any(suffix in col.lower()
                                for suffix in ['this year so far', '% change', 'last year'])]
        metric_col = basic_cols[0] if basic_cols else target_cols[0]

        # 計算指標
        value, yoy, mom = calculate_metric_yoy_mom(
            sales_df, date_col, metric_col, original_date,
            cvr_mode=metric_config.get('cvr_mode', False)
        )

        # 格式化數值
        if isinstance(value, (int, float)):
            if metric_config.get('cvr_mode', False):
                # CVR 模式：保留兩位小數
                value = round(value, 2)
            elif metric_config.get('decimal_mode', False):
                # 小數模式（如 Average sales/order item）：保留兩位小數
                value = round(value, 2)
            else:
                # 其他模式：四捨五入為整數
                value = round(value)

        # 渲染 Widget（保留懸停效果）
        render_kpi_widget(
            metric_config['title'],
            value,
            yoy,
            mom,
            prefix=metric_config.get('prefix', ''),
            suffix=metric_config.get('suffix', ''),
            show_change_percent=metric_config.get('show_change_percent', True)
        )


def calculate_yoy_mom_from_df(df, column_name, current_year, current_month):
    """
    從 DataFrame 計算 YoY 和 MoM（用於 Advertising 區塊）

    Returns:
        (current_value, yoy_change, mom_change)
    """
    yoy_change = None
    mom_change = None
    current_value = 0

    if column_name in df.columns:
        # 當前月份數據
        current_mask = (df['calendar_year'] == current_year) & (df['calendar_month'] == current_month)
        current_data = df[current_mask][column_name].dropna()
        if not current_data.empty:
            current_value = current_data.sum()

            # 計算去年同月 (YoY)
            last_year = current_year - 1
            last_year_mask = (df['calendar_year'] == last_year) & (df['calendar_month'] == current_month)
            last_year_data = df[last_year_mask][column_name].dropna()
            if not last_year_data.empty:
                last_year_value = last_year_data.sum()
                if last_year_value != 0:
                    yoy_change = ((current_value - last_year_value) / last_year_value) * 100
                else:
                    yoy_change = "-"

            # 計算上個月 (MoM)
            if current_month == 1:
                last_month = 12
                last_month_year = current_year - 1
            else:
                last_month = current_month - 1
                last_month_year = current_year

            last_month_mask = (df['calendar_year'] == last_month_year) & (df['calendar_month'] == last_month)
            last_month_data = df[last_month_mask][column_name].dropna()
            if not last_month_data.empty:
                last_month_value = last_month_data.sum()
                if last_month_value != 0:
                    mom_change = ((current_value - last_month_value) / last_month_value) * 100
                else:
                    mom_change = "-"

    return current_value, yoy_change, mom_change


st.set_page_config(page_title="Performance Dashboard", page_icon="📊", layout="wide")
st.title("📊 Performance Dashboard")

# 增加空間
st.markdown("<div style='margin: 40px 0;'></div>", unsafe_allow_html=True)

# 定義四種文件類型（移除 Total Year Change，改由 Sales Traffic Report 動態計算）
file_types = ["Sales Traffic Report", "P0 MCID MBR", "Asin Report", "ASIN Trend (YTD)"]

# ===== 賣家切換器 =====
from utils import get_seller_list, find_seller_files

seller_list = get_seller_list()  # [(display_name, seller_key, mcid), ...]

# 初始化 session_state
if 'multi_file_loaded_data' not in st.session_state:
    st.session_state.multi_file_loaded_data = {}

selected_files = {}
loaded_data = {}

# 預設值
current_seller_key = ""
current_mcid = ""

if seller_list:
    # 建立選項（不再在 label 裡顯示 MCID）
    seller_options_display = []
    seller_options_map = {}
    for display_name, seller_key, mcid in seller_list:
        seller_options_display.append(display_name)
        seller_options_map[display_name] = (seller_key, mcid)

    # 賣家下拉 + MCID 同一行
    sel_col, mcid_col, _ = st.columns([1, 1, 2])
    with sel_col:
        selected_seller_label = st.selectbox(
            "選擇客戶",
            options=seller_options_display,
            key="seller_switcher",
            label_visibility="collapsed",
        )

    current_seller_key, current_mcid = seller_options_map[selected_seller_label]

    with mcid_col:
        if current_mcid:
            st.markdown(f"<div style='line-height:38px;padding-top:4px;color:#333;font-size:16px;font-weight:500;'>MCID: {current_mcid}</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:24px'></div>", unsafe_allow_html=True)

    # 自動找出該賣家的所有檔案並靜默載入
    seller_files = find_seller_files(current_seller_key)

    # P0 MCID MBR 是全域資料（不分賣家），自動載入最新的 P0 檔案
    if "P0 MCID MBR" not in seller_files:
        p0_files = list_uploaded_files("P0 MCID MBR")
        if p0_files:
            seller_files["P0 MCID MBR"] = p0_files[0]  # 最新的

    for file_type in file_types:
        auto_file = seller_files.get(file_type)
        if auto_file:
            cache_key = f"{current_seller_key}_{file_type}_{auto_file.name}"
            if st.session_state.get(f"{file_type}_cache_key") != cache_key:
                df, error = load_data(auto_file)
                if error is None:
                    st.session_state.multi_file_loaded_data[file_type] = df
                    st.session_state[f"{file_type}_cache_key"] = cache_key
                    loaded_data[file_type] = df
            else:
                if file_type in st.session_state.multi_file_loaded_data:
                    loaded_data[file_type] = st.session_state.multi_file_loaded_data[file_type]
            selected_files[file_type] = auto_file

else:
    # 沒有偵測到賣家時，顯示手動選擇模式
    st.info("💡 尚未偵測到任何賣家。請先到「資料處理中心」上傳檔案（檔名需包含賣家名稱）。")

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    columns = [col1, col2, col3, col4]

    for i, file_type in enumerate(file_types):
        with columns[i]:
            st.markdown(f"**📁 {file_type}**")
            files = list_uploaded_files(file_type)

            if files:
                file_options = {f.name: f for f in files}
                selected_name = st.selectbox(
                    f"選擇 {file_type} 檔案",
                    options=list(file_options.keys()),
                    key=f"select_{file_type.replace(' ', '_').lower()}"
                )

                if selected_name:
                    selected_file = file_options[selected_name]
                    selected_files[file_type] = selected_file

                    cache_key = f"{file_type}_filename"
                    if cache_key not in st.session_state or st.session_state[cache_key] != selected_name:
                        df, error = load_data(selected_file)
                        if error:
                            st.error(f"無法讀取檔案: {error}")
                        else:
                            st.session_state.multi_file_loaded_data[file_type] = df
                            st.session_state[cache_key] = selected_name
                            loaded_data[file_type] = df
                    else:
                        if file_type in st.session_state.multi_file_loaded_data:
                            loaded_data[file_type] = st.session_state.multi_file_loaded_data[file_type]
            else:
                st.info(f"目前沒有 {file_type} 類型的檔案")

# Overall Sales Summary 區塊（從 Sales Traffic Report 動態計算）
if "Sales Traffic Report" in loaded_data:
    # 標題與年份選擇器並排
    header_col, year_select_col = st.columns([3, 1])
    with header_col:
        st.header("📈 Overall Sales Summary")

    # 從 Sales Traffic Report 取得可用年份
    available_years = []
    traffic_df = loaded_data["Sales Traffic Report"]
    if 'Date' in traffic_df.columns:
        try:
            traffic_df_temp = traffic_df.copy()
            traffic_df_temp['Date'] = pd.to_datetime(traffic_df_temp['Date'], format='%Y/%m/%d', errors='coerce')
            available_years = sorted(traffic_df_temp['Date'].dt.year.dropna().unique().astype(int).tolist(), reverse=True)
        except:
            pass

    # 如果沒有可用年份，使用當前年份和前一年
    if not available_years:
        from datetime import datetime
        current_year = datetime.now().year
        available_years = [current_year, current_year - 1]

    with year_select_col:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        selected_ytd_year = st.selectbox(
            "選擇年份",
            options=available_years,
            index=0,
            key="ytd_year_selector"
        )

    # 創建兩行 widget 欄位：第一行 3 個，第二行 3 個
    widget_row1_col1, widget_row1_col2, widget_row1_col3 = st.columns(3)

    # 行間距（與 Business Metrics 一致）
    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)

    widget_row2_col1, widget_row2_col2, widget_row2_col3 = st.columns(3)

    # 定義六個指標的配置（第一行 3 個，第二行 3 個）
    ytd_metrics = [
        # 第一行
        {
            'column': widget_row1_col1,
            'title': 'YTD Sales',
            'keywords': ['ordered product sales'],
            'prefix': '$',
            'decimal': False,
            'help_text': 'YoY 計算採同期比較法：今年資料截至當前日期，去年則計算至相同日期，確保比較基準一致。\n\nYoY calculation uses same-period comparison: current year data up to today\'s date, compared with prior year data up to the same date.'
        },
        {
            'column': widget_row1_col2,
            'title': 'YTD - Total Order Items',
            'keywords': ['total order items'],
            'prefix': '',
            'decimal': False,
            'help_text': 'YoY 計算採同期比較法：今年資料截至當前日期，去年則計算至相同日期，確保比較基準一致。\n\nYoY calculation uses same-period comparison: current year data up to today\'s date, compared with prior year data up to the same date.'
        },
        {
            'column': widget_row1_col3,
            'title': 'YTD - Units Ordered',
            'keywords': ['units ordered'],
            'prefix': '',
            'decimal': False,
            'help_text': 'YoY 計算採同期比較法：今年資料截至當前日期，去年則計算至相同日期，確保比較基準一致。\n\nYoY calculation uses same-period comparison: current year data up to today\'s date, compared with prior year data up to the same date.'
        },
        # 第二行
        {
            'column': widget_row2_col1,
            'title': 'YTD - Sessions',
            'keywords': ['sessions - total'],
            'prefix': '',
            'decimal': False,
            'help_text': 'YoY 計算採同期比較法：今年資料截至當前日期，去年則計算至相同日期，確保比較基準一致。\n\nYoY calculation uses same-period comparison: current year data up to today\'s date, compared with prior year data up to the same date.'
        },
        {
            'column': widget_row2_col2,
            'title': 'AOV (Average Order Value)',
            'keywords': ['average order value'],
            'prefix': '$',
            'decimal': True,  # 需要保留兩位小數
            'help_text': '平均訂單金額 = 銷售額 / 訂單數\nAOV = Ordered Product Sales / Total Order Items\n\nYoY 計算採同期比較法。'
        },
        {
            'column': widget_row2_col3,
            'title': 'CVR',
            'keywords': ['cvr'],
            'prefix': '',
            'suffix': '%',
            'decimal': True,  # 需要保留兩位小數
            'cvr_mode': True,  # CVR 使用 bps 差值計算 YoY
            'help_text': '轉換率 = 訂單數 / 瀏覽次數\nCVR = Total Order Items / Sessions × 100%\n\nYoY 變化以 bps（基點）表示。'
        }
    ]

    # 從 Sales Traffic Report 動態計算 YTD
    from datetime import datetime
    current_year = datetime.now().year

    traffic_df = loaded_data["Sales Traffic Report"].copy()
    if 'Date' in traffic_df.columns:
        try:
            traffic_df['Date'] = pd.to_datetime(traffic_df['Date'], format='%Y/%m/%d', errors='coerce')
            traffic_df['Year'] = traffic_df['Date'].dt.year
            traffic_df['DayOfYear'] = traffic_df['Date'].dt.dayofyear

            # 根據選擇的年份決定計算邏輯
            if selected_ytd_year == current_year:
                # 當前年份：YTD 同期比較（截至今天）
                today_day_of_year = datetime.now().timetuple().tm_yday
                selected_year_df = traffic_df[(traffic_df['Year'] == selected_ytd_year) & (traffic_df['DayOfYear'] <= today_day_of_year)]
                prior_year_df = traffic_df[(traffic_df['Year'] == selected_ytd_year - 1) & (traffic_df['DayOfYear'] <= today_day_of_year)]
            else:
                # 歷史年份：全年加總比較
                selected_year_df = traffic_df[traffic_df['Year'] == selected_ytd_year]
                prior_year_df = traffic_df[traffic_df['Year'] == selected_ytd_year - 1]

            # 欄位對照
            metric_columns = {
                'YTD Sales': 'Ordered Product Sales',
                'YTD - Total Order Items': 'Total Order Items',
                'YTD - Units Ordered': 'Units Ordered',
                'YTD - Sessions': 'Sessions - Total',
                'AOV (Average Order Value)': None,  # 需要計算：Sales / Total Order Items
                'CVR': None  # 需要計算：Total Order Items / Sessions × 100%
            }

            for metric in ytd_metrics:
                with metric['column']:
                    col_name = metric_columns.get(metric['title'])

                    if metric['title'] == 'AOV (Average Order Value)':
                        # 計算平均訂單金額 = 銷售額 / 訂單數 (Total Order Items)
                        sales_sum = selected_year_df['Ordered Product Sales'].apply(
                            lambda x: float(str(x).replace('$', '').replace(',', '')) if pd.notna(x) else 0
                        ).sum()
                        orders_sum = selected_year_df['Total Order Items'].apply(
                            lambda x: float(str(x).replace(',', '')) if pd.notna(x) else 0
                        ).sum()
                        value = sales_sum / orders_sum if orders_sum > 0 else 0

                        # 計算去年同期
                        prior_sales = prior_year_df['Ordered Product Sales'].apply(
                            lambda x: float(str(x).replace('$', '').replace(',', '')) if pd.notna(x) else 0
                        ).sum()
                        prior_orders = prior_year_df['Total Order Items'].apply(
                            lambda x: float(str(x).replace(',', '')) if pd.notna(x) else 0
                        ).sum()
                        prior_value = prior_sales / prior_orders if prior_orders > 0 else 0
                    elif metric['title'] == 'CVR':
                        # 計算轉換率 = 訂單數 / 瀏覽次數 × 100% (Total Order Items / Sessions)
                        orders_sum = selected_year_df['Total Order Items'].apply(
                            lambda x: float(str(x).replace(',', '')) if pd.notna(x) else 0
                        ).sum()
                        sessions_sum = selected_year_df['Sessions - Total'].apply(
                            lambda x: float(str(x).replace(',', '')) if pd.notna(x) else 0
                        ).sum()
                        value = (orders_sum / sessions_sum * 100) if sessions_sum > 0 else 0

                        # 計算去年同期
                        prior_orders = prior_year_df['Total Order Items'].apply(
                            lambda x: float(str(x).replace(',', '')) if pd.notna(x) else 0
                        ).sum()
                        prior_sessions = prior_year_df['Sessions - Total'].apply(
                            lambda x: float(str(x).replace(',', '')) if pd.notna(x) else 0
                        ).sum()
                        prior_value = (prior_orders / prior_sessions * 100) if prior_sessions > 0 else 0
                    elif col_name and col_name in selected_year_df.columns:
                        # 清理並加總數值
                        value = selected_year_df[col_name].apply(
                            lambda x: float(str(x).replace('$', '').replace(',', '').replace('%', '')) if pd.notna(x) else 0
                        ).sum()
                        prior_value = prior_year_df[col_name].apply(
                            lambda x: float(str(x).replace('$', '').replace(',', '').replace('%', '')) if pd.notna(x) else 0
                        ).sum()
                    else:
                        value = 0
                        prior_value = 0

                    # 計算 YoY 變化
                    if metric.get('cvr_mode', False):
                        # CVR 使用 bps（基點）差值：(current - prior) * 100
                        change = (value - prior_value) * 100 if prior_value > 0 else None
                    elif prior_value > 0:
                        change = ((value - prior_value) / prior_value) * 100
                    else:
                        change = None

                    # 格式化數值
                    if isinstance(value, (int, float)):
                        value_rounded = round(value, 2) if metric.get('decimal', False) else round(value)
                    else:
                        value_rounded = value

                    render_kpi_widget(
                        metric['title'],
                        value_rounded,
                        change,
                        prefix=metric.get('prefix', ''),
                        suffix=metric.get('suffix', ''),
                        help_text=metric.get('help_text'),
                        show_change_percent=not metric.get('cvr_mode', False)  # CVR 不顯示 % 符號
                    )
        except Exception as e:
            st.warning(f"計算 YTD 時發生錯誤: {e}")

    # 增加 KPI widgets 與下方元素的間距
    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

    # 月度銷售趨勢圖 - 從 Sales Traffic Report 讀取
    if "Sales Traffic Report" in loaded_data:

        sales_traffic_df = loaded_data["Sales Traffic Report"]

        # 檢查必要欄位是否存在
        if 'Date' in sales_traffic_df.columns and 'Ordered Product Sales' in sales_traffic_df.columns:

            # 處理資料：解析日期並聚合
            try:
                # 複製 DataFrame 避免修改原始資料
                df_processed = sales_traffic_df.copy()

                # 解析 Date 欄位 (格式: 2024/1/1 → 2024-01)
                df_processed['Date'] = pd.to_datetime(df_processed['Date'], format='%Y/%m/%d', errors='coerce')
                df_processed = df_processed.dropna(subset=['Date'])

                # 提取年份和月份
                df_processed['Year'] = df_processed['Date'].dt.year.astype(int)
                df_processed['Month'] = df_processed['Date'].dt.month.astype(int)

                # 清理 Ordered Product Sales 欄位 (移除 $, 逗號等)
                if df_processed['Ordered Product Sales'].dtype == 'object':
                    df_processed['Ordered Product Sales'] = df_processed['Ordered Product Sales'].astype(str).str.replace('$', '', regex=False)
                    df_processed['Ordered Product Sales'] = df_processed['Ordered Product Sales'].str.replace(',', '', regex=False)
                    df_processed['Ordered Product Sales'] = pd.to_numeric(df_processed['Ordered Product Sales'], errors='coerce')

                # 按年份和月份聚合 (使用 sum)
                monthly_sales = df_processed.groupby(['Year', 'Month'])['Ordered Product Sales'].sum().reset_index()
                monthly_sales = monthly_sales.sort_values(['Year', 'Month'])

                # 偵測所有年份
                available_years = sorted(monthly_sales['Year'].unique(), reverse=True)

                # 建立 year_columns 字典 (保持與原邏輯相容)
                year_columns = {str(year): year for year in available_years}

            except Exception as e:
                st.error(f"⚠️ 處理 Sales Traffic Report 資料時發生錯誤: {str(e)}")
                year_columns = {}
        else:
            st.warning("⚠️ Sales Traffic Report 缺少必要欄位 (Date, Ordered Product Sales)")
            year_columns = {}

        if year_columns:
            # 排序年份
            sorted_years = sorted(year_columns.keys(), reverse=True)

            # 年份選擇器 - 預設選擇全部年份
            selected_years = st.multiselect(
                "Select Years",
                options=sorted_years,
                default=sorted_years,  # 預設選擇全部年份
                key="selected_years_for_chart",
                label_visibility="collapsed"
            )

            if selected_years and len(selected_years) > 0:
                # 準備圖表資料 - 建立完整的12個月結構
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

                # 轉換選擇的年份為整數
                sorted_selected_years = sorted([int(year) for year in selected_years], reverse=True)

                # 建立圖表資料字典
                chart_data_dict = {}
                for year in sorted_selected_years:
                    year_data = []
                    for month_num in range(1, 13):
                        # 從 monthly_sales 中查找對應年月的資料
                        mask = (monthly_sales['Year'] == year) & (monthly_sales['Month'] == month_num)
                        month_sales = monthly_sales[mask]['Ordered Product Sales']

                        if not month_sales.empty:
                            year_data.append(month_sales.values[0])
                        else:
                            year_data.append(None)  # 沒有資料的月份

                    chart_data_dict[str(year)] = year_data

                # 開始繪製圖表
                import plotly.graph_objects as go

                fig = go.Figure()

                # 定義顏色配置：年代越新顏色越深
                # 使用橘色系：從淺灰 → 鮮豔橘色
                color_scheme = [
                    '#C0C0C0',  # 淺灰色 (最舊)
                    '#FFB366',  # 亮橘色
                    '#FF9933',  # 鮮豔橘色
                    '#FF7F00',  # 純橘色
                    '#FF6600',  # 深橘色
                    '#E65500',  # 濃橘色 (最新)
                ]

                # 為每個選擇的年份添加長條圖 (sorted_selected_years 已經是從新到舊排序)
                for i, year in enumerate(sorted_selected_years):
                    year_str = str(year)
                    if year_str in chart_data_dict:
                        # 反轉索引，讓最新的年份（索引0）使用最深的顏色（列表最後）
                        color_index = min(len(sorted_selected_years) - 1 - i, len(color_scheme) - 1)

                        fig.add_trace(go.Bar(
                            x=month_names,
                            y=chart_data_dict[year_str],
                            name=f'{year}',
                            marker_color=color_scheme[color_index],
                            yaxis='y'
                        ))

                # 如果選擇了至少兩個年份，添加 YoY 折線圖
                if len(sorted_selected_years) >= 2:
                    # 計算相鄰年份之間的 YoY（從最新年份與前一年比較）
                    for i in range(len(sorted_selected_years) - 1):
                        newer_year = sorted_selected_years[i]
                        older_year = sorted_selected_years[i + 1]

                        # 計算 YoY %
                        newer_data = chart_data_dict[str(newer_year)]
                        older_data = chart_data_dict[str(older_year)]

                        yoy_values = []
                        yoy_text = []
                        for month_idx in range(12):
                            newer_val = newer_data[month_idx]
                            older_val = older_data[month_idx]

                            if newer_val is not None and older_val is not None and older_val != 0:
                                yoy = ((newer_val - older_val) / older_val) * 100
                                yoy_values.append(yoy)
                                yoy_text.append(f'{yoy:.1f}%')
                            else:
                                yoy_values.append(None)
                                yoy_text.append('')

                        # 添加折線圖 (在月份迴圈外)
                        line_colors = ['#8B4513', '#CD853F', '#DEB887']  # 咖啡色系
                        fig.add_trace(go.Scatter(
                            x=month_names,
                            y=yoy_values,
                            name=f'{newer_year} vs {older_year} YoY %',
                            mode='lines+markers+text',
                            line=dict(color=line_colors[i % len(line_colors)], width=2),
                            marker=dict(size=8),
                            text=yoy_text,
                            textposition='top center',
                            yaxis='y2',
                            connectgaps=False
                        ))

                    # 設置雙軸
                    fig.update_layout(
                        yaxis=dict(
                            title='Sales ($)',
                            side='left',
                            separatethousands=True
                        ),
                        yaxis2=dict(
                            title='YoY Change (%)',
                            overlaying='y',
                            side='right'
                        ),
                        barmode='group',
                        hovermode='x unified',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        height=400
                    )

                    st.plotly_chart(fig, use_container_width=True)

                # ========== 年度目標設定表格 (固定顯示最近三年) ==========
                all_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

                # 載入/儲存目標的輔助函數
                import json
                from pathlib import Path
                from datetime import datetime

                targets_file = Path("uploaded_data/sales_targets.json")

                def load_targets():
                    """載入已儲存的目標"""
                    if targets_file.exists():
                        with open(targets_file, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    return {}

                def save_targets(targets_data):
                    """儲存目標到 JSON"""
                    targets_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(targets_file, 'w', encoding='utf-8') as f:
                        json.dump(targets_data, f, ensure_ascii=False, indent=2)

                def smart_allocate(annual_yoy_target, last_year_sales_dict, previous_yoy_values):
                    """
                    智能分配: 保持去年 YoY 的波動形狀，整體平移到符合全年目標
                    
                    關鍵：Sum YoY = (今年Sum - 去年Sum) / 去年Sum
                    所以要確保各月 YoY 加權平均（權重=去年sales）等於目標
                    """
                    annual_yoy_target = max(0, annual_yoy_target)
                    
                    # 計算去年 Sum
                    last_year_sum = sum(v for v in last_year_sales_dict.values() if v and pd.notna(v))
                    if last_year_sum == 0:
                        return {m: int(annual_yoy_target) for m in all_months}
                    
                    # 計算去年各月的權重（佔全年的比例）
                    weights = {}
                    for month in all_months:
                        last_sales = last_year_sales_dict.get(month)
                        if last_sales and pd.notna(last_sales):
                            weights[month] = last_sales / last_year_sum
                        else:
                            weights[month] = 0
                    
                    # 計算去年 YoY 的加權平均（只計算有數據且合理的月份）
                    # 過濾掉異常值：YoY 超過 500% 或低於 -90% 視為異常
                    weighted_yoy_sum = 0
                    valid_yoy_count = 0
                    for month in all_months:
                        yoy = previous_yoy_values.get(month)
                        if yoy is not None and pd.notna(yoy) and -90 <= yoy <= 500:
                            weighted_yoy_sum += yoy * weights[month]
                            valid_yoy_count += 1
                    
                    # 如果去年 YoY 數據不足（少於 6 個月有效且合理），直接使用均勻分配
                    if valid_yoy_count < 6:
                        return {m: int(annual_yoy_target) for m in all_months}
                    
                    last_year_weighted_avg = weighted_yoy_sum
                    
                    # 計算各月 YoY 跟加權平均的差距（波動形狀）
                    # 異常值的月份使用 0 差距
                    yoy_diff = {}
                    for month in all_months:
                        yoy = previous_yoy_values.get(month)
                        if yoy is not None and pd.notna(yoy) and -90 <= yoy <= 500:
                            yoy_diff[month] = yoy - last_year_weighted_avg
                        else:
                            yoy_diff[month] = 0
                    
                    # 初始分配：目標 + 差距
                    initial_yoy = {}
                    for month in all_months:
                        initial_yoy[month] = annual_yoy_target + yoy_diff[month]
                    
                    # 計算加權平均 YoY（這就是 Sum YoY）
                    def calc_weighted_avg_yoy(yoy_dict):
                        total = 0
                        for month in all_months:
                            total += yoy_dict[month] * weights[month]
                        return total
                    
                    # 迭代調整，確保加權平均 = 目標
                    # 因為差距的加權和應該是 0，所以理論上 initial_yoy 的加權平均就是 annual_yoy_target
                    # 但四捨五入會產生誤差，需要校正
                    
                    # 先四捨五入
                    result = {}
                    for month in all_months:
                        result[month] = max(0, int(round(initial_yoy[month])))
                    
                    # 計算目前的加權平均
                    current_weighted_avg = calc_weighted_avg_yoy(result)
                    
                    # 如果有誤差，逐步調整權重最大的月份
                    max_iterations = 50
                    for _ in range(max_iterations):
                        diff = annual_yoy_target - current_weighted_avg
                        if abs(diff) < 0.5:  # 誤差小於 0.5% 就停止
                            break
                        
                        # 找到權重最大的月份來調整
                        max_month = max(all_months, key=lambda m: weights.get(m, 0))
                        
                        if diff > 0:
                            result[max_month] += 1
                        else:
                            result[max_month] = max(0, result[max_month] - 1)
                        
                        current_weighted_avg = calc_weighted_avg_yoy(result)
                    
                    return result

                # 獲取當前檔案名稱作為識別
                current_file_key = st.session_state.get('Sales Traffic Report_filename', 'default')
                all_targets = load_targets()

                # 從所有可用年份中取得最近三年 (不受上方選擇器影響)
                all_available_years = sorted([int(y) for y in available_years], reverse=True)

                # 定義今年、去年、前年
                this_year = all_available_years[0] if len(all_available_years) > 0 else None
                last_year = all_available_years[1] if len(all_available_years) > 1 else None
                year_before_last = all_available_years[2] if len(all_available_years) > 2 else None

                # 確保 chart_data_dict 包含所有需要的年份資料
                for year in [this_year, last_year, year_before_last]:
                    if year and str(year) not in chart_data_dict:
                        year_data = []
                        for month_num in range(1, 13):
                            mask = (monthly_sales['Year'] == year) & (monthly_sales['Month'] == month_num)
                            month_sales = monthly_sales[mask]['Ordered Product Sales']
                            if not month_sales.empty:
                                year_data.append(month_sales.values[0])
                            else:
                                year_data.append(None)
                        chart_data_dict[str(year)] = year_data

                # 取得各年份數據
                year_before_last_sales = {}  # 前年 (2024)
                last_year_sales = {}          # 去年 (2025)
                this_year_sales = {}          # 今年 (2026)
                last_year_yoy = {}            # 去年 YoY (2025 vs 2024)

                for month_idx, month in enumerate(all_months):
                    # 前年 Sales
                    if year_before_last and str(year_before_last) in chart_data_dict:
                        year_before_last_sales[month] = chart_data_dict[str(year_before_last)][month_idx]
                    else:
                        year_before_last_sales[month] = None

                    # 去年 Sales
                    if last_year and str(last_year) in chart_data_dict:
                        last_year_sales[month] = chart_data_dict[str(last_year)][month_idx]
                    else:
                        last_year_sales[month] = None

                    # 今年 Sales
                    if this_year and str(this_year) in chart_data_dict:
                        this_year_sales[month] = chart_data_dict[str(this_year)][month_idx]
                    else:
                        this_year_sales[month] = None

                    # 去年 YoY (去年 vs 前年)
                    last_val = last_year_sales[month]
                    prev_val = year_before_last_sales[month]
                    if last_val is not None and prev_val is not None and prev_val != 0:
                        last_year_yoy[month] = ((last_val - prev_val) / prev_val) * 100
                    else:
                        last_year_yoy[month] = None

                # 初始化目標 YoY session state
                target_session_key = f"target_yoy_values_{current_file_key}_{this_year}"
                undo_session_key = f"target_yoy_undo_{current_file_key}_{this_year}"

                # 從儲存的數據載入預設值
                saved_annual_target = 30.0
                if current_file_key in all_targets and str(this_year) in all_targets[current_file_key]:
                    saved_annual_target = float(all_targets[current_file_key][str(this_year)].get('annual_yoy_target', 30.0))

                st.markdown("---")

                if this_year and last_year:
                    # ========== Actual ==========
                    st.markdown("**Actual**")

                    # 計算今年 vs 去年的 YoY
                    this_year_yoy = {}
                    for month in all_months:
                        this_val = this_year_sales.get(month)
                        last_val = last_year_sales.get(month)
                        if this_val and pd.notna(this_val) and last_val and pd.notna(last_val) and last_val != 0:
                            this_year_yoy[month] = ((this_val - last_val) / last_val) * 100
                        else:
                            this_year_yoy[month] = None

                    # 計算 Sum 和 Avg
                    def calc_sum(data_dict):
                        vals = [v for v in data_dict.values() if v and pd.notna(v)]
                        return sum(vals) if vals else None

                    def calc_avg(data_dict):
                        vals = [v for v in data_dict.values() if v and pd.notna(v)]
                        return sum(vals) / len(vals) if vals else None

                    actual_rows = []

                    # 前年 Sales (year_before_last)
                    if year_before_last:
                        row_year_before_last = {'項目': f'{year_before_last} Sales'}
                        for month in all_months:
                            val = year_before_last_sales.get(month)
                            row_year_before_last[month] = f'${int(val):,}' if val and pd.notna(val) else '-'
                        year_before_last_sum = calc_sum(year_before_last_sales)
                        year_before_last_avg = calc_avg(year_before_last_sales)
                        row_year_before_last['Sum'] = f'${int(year_before_last_sum):,}' if year_before_last_sum else '-'
                        row_year_before_last['Avg.'] = f'${int(year_before_last_avg):,}' if year_before_last_avg else '-'
                        actual_rows.append(row_year_before_last)

                    # 去年 Sales
                    row_last_year = {'項目': f'{last_year} Sales'}
                    for month in all_months:
                        val = last_year_sales.get(month)
                        row_last_year[month] = f'${int(val):,}' if val and pd.notna(val) else '-'
                    last_year_sum = calc_sum(last_year_sales)
                    last_year_avg = calc_avg(last_year_sales)
                    row_last_year['Sum'] = f'${int(last_year_sum):,}' if last_year_sum else '-'
                    row_last_year['Avg.'] = f'${int(last_year_avg):,}' if last_year_avg else '-'
                    actual_rows.append(row_last_year)

                    # 今年 Sales
                    row_this_year = {'項目': f'{this_year} Sales'}
                    for month in all_months:
                        val = this_year_sales.get(month)
                        row_this_year[month] = f'${int(val):,}' if val and pd.notna(val) else '-'
                    this_year_sum = calc_sum(this_year_sales)
                    this_year_avg = calc_avg(this_year_sales)
                    row_this_year['Sum'] = f'${int(this_year_sum):,}' if this_year_sum else '-'
                    row_this_year['Avg.'] = f'${int(this_year_avg):,}' if this_year_avg else '-'
                    actual_rows.append(row_this_year)

                    # YoY
                    row_yoy = {'項目': 'YoY'}
                    for month in all_months:
                        val = this_year_yoy.get(month)
                        row_yoy[month] = f'{val:.0f}%' if val and pd.notna(val) else '-'
                    row_yoy['Sum'] = '-'
                    row_yoy['Avg.'] = '-'
                    actual_rows.append(row_yoy)

                    actual_df = pd.DataFrame(actual_rows)
                    st.dataframe(actual_df, use_container_width=True, hide_index=True)

                    # ========== Forecast ==========
                    st.markdown("**Forecast**")

                    # 初始化目標值
                    annual_target_key = f"last_annual_target_{current_file_key}_{this_year}"
                    if annual_target_key not in st.session_state:
                        st.session_state[annual_target_key] = saved_annual_target

                    if target_session_key not in st.session_state:
                        if current_file_key in all_targets and str(this_year) in all_targets[current_file_key]:
                            saved_data = all_targets[current_file_key][str(this_year)]
                            saved_targets = saved_data.get('monthly_targets', {})
                            if saved_targets:
                                st.session_state[target_session_key] = {
                                    month: float(saved_targets[month]['target_yoy'])
                                    for month in all_months if month in saved_targets
                                }
                            else:
                                allocated = smart_allocate(saved_annual_target, last_year_sales, last_year_yoy)
                                st.session_state[target_session_key] = allocated
                        else:
                            allocated = smart_allocate(saved_annual_target, last_year_sales, last_year_yoy)
                            st.session_state[target_session_key] = allocated

                    # 初始化 undo 堆疊
                    if undo_session_key not in st.session_state:
                        st.session_state[undo_session_key] = []

                    # 取得當前目標值
                    current_targets = st.session_state[target_session_key]

                    # 建立目標設定表格數據
                    target_rows = []

                    # 前年 Sales (參考用)
                    if year_before_last:
                        row_year_before_last_ref = {'項目': f'{year_before_last} Sales'}
                        for month in all_months:
                            val = year_before_last_sales.get(month)
                            row_year_before_last_ref[month] = f'${int(val):,}' if val and pd.notna(val) else '-'
                        year_before_last_sum = calc_sum(year_before_last_sales)
                        year_before_last_avg = calc_avg(year_before_last_sales)
                        row_year_before_last_ref['Sum'] = f'${int(year_before_last_sum):,}' if year_before_last_sum else '-'
                        row_year_before_last_ref['Avg.'] = f'${int(year_before_last_avg):,}' if year_before_last_avg else '-'
                        target_rows.append(row_year_before_last_ref)

                    # 去年 Sales (參考用)
                    row_last_year_ref = {'項目': f'{last_year} Sales'}
                    for month in all_months:
                        val = last_year_sales.get(month)
                        row_last_year_ref[month] = f'${int(val):,}' if val and pd.notna(val) else '-'
                    row_last_year_ref['Sum'] = f'${int(last_year_sum):,}' if last_year_sum else '-'
                    row_last_year_ref['Avg.'] = f'${int(last_year_avg):,}' if last_year_avg else '-'
                    target_rows.append(row_last_year_ref)

                    # 判斷當前月份（用來區分實際 vs 預估）
                    from datetime import datetime
                    current_month_num = datetime.now().month
                    month_to_num = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                                    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

                    # 今年 Sales（實際 + 預估混合）
                    row_estimated = {'項目': f'{this_year} Sales'}
                    estimated_values = []
                    actual_months = []  # 記錄哪些月份是實際值
                    
                    for month in all_months:
                        month_num = month_to_num[month]
                        actual_sales = this_year_sales.get(month)
                        last_sales = last_year_sales.get(month)
                        target_yoy = current_targets.get(month, saved_annual_target)
                        
                        # 已過的月份（< 當前月份）且有實際數據 → 用實際值
                        if month_num < current_month_num and actual_sales and pd.notna(actual_sales):
                            row_estimated[month] = f'${int(actual_sales):,}'
                            estimated_values.append(int(actual_sales))
                            actual_months.append(month)
                        # 未過的月份或沒有實際數據 → 用預估值（藍色）
                        elif last_sales and pd.notna(last_sales):
                            estimated = int(last_sales * (1 + target_yoy / 100))
                            row_estimated[month] = f'<span style="color:#e57373">${estimated:,}</span>'
                            estimated_values.append(estimated)
                        else:
                            row_estimated[month] = '-'
                    
                    estimated_sum = sum(estimated_values) if estimated_values else 0
                    estimated_avg = sum(estimated_values) / len(estimated_values) if estimated_values else 0
                    
                    # 判斷 Sum 和 Avg 是否包含預估值（如果有任何月份不在 actual_months 中，就是包含預估）
                    has_estimated = len(actual_months) < len(all_months)
                    if has_estimated:
                        row_estimated['Sum'] = f'<span style="color:#e57373">${estimated_sum:,}</span>'
                        row_estimated['Avg.'] = f'<span style="color:#e57373">${int(estimated_avg):,}</span>'
                    else:
                        row_estimated['Sum'] = f'${estimated_sum:,}'
                        row_estimated['Avg.'] = f'${int(estimated_avg):,}'
                    target_rows.append(row_estimated)

                    # YoY（實際 + 預估混合）- 整數，不要小數
                    row_target_yoy_display = {'項目': 'YoY'}
                    has_estimated_yoy = False
                    for month in all_months:
                        month_num = month_to_num[month]
                        actual_sales = this_year_sales.get(month)
                        last_sales = last_year_sales.get(month)
                        target_yoy = current_targets.get(month, saved_annual_target)
                        
                        # 已過的月份且有實際數據 → 計算實際 YoY
                        if month_num < current_month_num and actual_sales and pd.notna(actual_sales) and last_sales and pd.notna(last_sales) and last_sales != 0:
                            actual_yoy = ((actual_sales - last_sales) / last_sales) * 100
                            row_target_yoy_display[month] = f'{int(round(actual_yoy))}%'
                        # 未過的月份 → 用目標 YoY（淺紅色）
                        else:
                            row_target_yoy_display[month] = f'<span style="color:#e57373">{int(round(target_yoy))}%</span>'
                            has_estimated_yoy = True
                    # YoY Sum = 用全年 Sum 計算，Avg 顯示 -
                    if last_year_sum and last_year_sum != 0:
                        yoy_sum_calculated = ((estimated_sum - last_year_sum) / last_year_sum) * 100
                        if has_estimated_yoy:
                            row_target_yoy_display['Sum'] = f'<span style="color:#e57373">{int(round(yoy_sum_calculated))}%</span>'
                        else:
                            row_target_yoy_display['Sum'] = f'{int(round(yoy_sum_calculated))}%'
                    else:
                        row_target_yoy_display['Sum'] = '-'
                    row_target_yoy_display['Avg.'] = '-'
                    target_rows.append(row_target_yoy_display)

                    # 用 HTML 表格顯示（支援顏色字體）
                    target_display_df = pd.DataFrame(target_rows)
                    
                    # 轉換為 HTML 表格
                    html_table = '<table style="width:100%; border-collapse:collapse; font-size:14px;">'
                    html_table += '<thead><tr style="background-color:#fff0f0;">'
                    for col in target_display_df.columns:
                        html_table += f'<th style="padding:8px; text-align:center; border-bottom:2px solid #ddd;">{col}</th>'
                    html_table += '</tr></thead><tbody>'
                    
                    for idx, row in target_display_df.iterrows():
                        html_table += '<tr>'
                        for col in target_display_df.columns:
                            val = row[col]
                            html_table += f'<td style="padding:8px; text-align:center; border-bottom:1px solid #eee;">{val}</td>'
                        html_table += '</tr>'
                    html_table += '</tbody></table>'
                    
                    st.markdown(html_table, unsafe_allow_html=True)

                    # 全年 YoY 目標輸入 + 可編輯的月度 YoY
                    st.markdown("---")

                    # 全年目標輸入（縮小欄位）
                    col_input, col_spacer = st.columns([1, 5])
                    with col_input:
                        annual_yoy_target = st.number_input(
                            f"目標 % (user input)",
                            min_value=0,  # 目標 YoY 不可為負
                            max_value=500,
                            value=max(0, int(st.session_state[annual_target_key])),  # 確保不為負，整數
                            step=1,
                            key=f"annual_yoy_input_{this_year}",
                            help="輸入全年 YoY 目標後，系統會智能分配到各月份"
                        )

                    # 檢查全年目標是否改變
                    annual_target_changed = abs(st.session_state[annual_target_key] - annual_yoy_target) > 0.01

                    if annual_target_changed:
                        st.session_state[annual_target_key] = annual_yoy_target
                        st.session_state[undo_session_key].append(current_targets.copy())
                        allocated = smart_allocate(annual_yoy_target, last_year_sales, last_year_yoy)
                        st.session_state[target_session_key] = allocated
                        st.rerun()

                    # 可編輯的月度目標 YoY
                    editable_row = {'項目': f'{this_year} 目標 YoY (%)'}
                    for month in all_months:
                        editable_row[month] = current_targets.get(month, annual_yoy_target)
                    editable_df = pd.DataFrame([editable_row])

                    editable_column_config = {
                        '項目': st.column_config.TextColumn('項目', disabled=True, width='medium')
                    }
                    for month in all_months:
                        editable_column_config[month] = st.column_config.NumberColumn(
                            f'✏️ {month}',
                            min_value=0,  # 目標 YoY 不可為負
                            max_value=500,
                            step=1,  # 整數步進
                            format='%d',  # 整數格式
                            width='small'
                        )

                    # 讓數字靠左對齊的 CSS
                    st.markdown("""
                    <style>
                        [data-testid="stDataEditor"] td {
                            text-align: left !important;
                        }
                        [data-testid="stDataEditor"] input {
                            text-align: left !important;
                        }
                    </style>
                    """, unsafe_allow_html=True)

                    edited_df = st.data_editor(
                        editable_df,
                        column_config=editable_column_config,
                        use_container_width=True,
                        hide_index=True,
                        num_rows='fixed',
                        key=f"target_editor_{this_year}_{int(annual_yoy_target)}"
                    )

                    # 提取編輯後的目標值
                    edited_targets = {}
                    for month in all_months:
                        edited_targets[month] = int(round(edited_df[month].iloc[0]))

                    # 按鈕區域（三個按鈕靠右，平均間隔）
                    btn_spacer, btn_col1, btn_col2, btn_col3 = st.columns([7, 1, 1, 1])
                    
                    button_clicked = False

                    with btn_col1:
                        undo_disabled = len(st.session_state.get(undo_session_key, [])) == 0
                        if st.button("Undo", key=f"undo_targets_{this_year}", disabled=undo_disabled, use_container_width=True):
                            button_clicked = True
                            if st.session_state[undo_session_key]:
                                previous_state = st.session_state[undo_session_key].pop()
                                st.session_state[target_session_key] = previous_state
                                st.rerun()

                    with btn_col2:
                        if st.button("🪄 Reallocate", key=f"reset_targets_{this_year}", use_container_width=True):
                            button_clicked = True
                            st.session_state[undo_session_key].append(current_targets.copy())
                            new_targets = smart_allocate(annual_yoy_target, last_year_sales, last_year_yoy)
                            st.session_state[target_session_key] = new_targets

                            if current_file_key in all_targets and str(this_year) in all_targets[current_file_key]:
                                del all_targets[current_file_key][str(this_year)]
                                save_targets(all_targets)

                            st.rerun()

                    with btn_col3:
                        if st.button("Save Changes", key=f"save_targets_{this_year}", type="primary", use_container_width=True):
                            button_clicked = True
                            if current_file_key not in all_targets:
                                all_targets[current_file_key] = {}

                            monthly_targets = {}
                            for month in all_months:
                                target_yoy = current_targets.get(month, annual_yoy_target)
                                last_sales = last_year_sales.get(month)

                                estimated_sales = None
                                if last_sales and pd.notna(last_sales):
                                    estimated_sales = int(last_sales * (1 + target_yoy / 100))

                                monthly_targets[month] = {
                                    'target_yoy': float(target_yoy),
                                    'estimated_sales': estimated_sales
                                }

                            all_targets[current_file_key][str(this_year)] = {
                                'annual_yoy_target': float(annual_yoy_target),
                                'monthly_targets': monthly_targets,
                                'modified_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }

                            save_targets(all_targets)
                            # 自訂 toast 1.5 秒後消失
                            st.markdown("""
                            <style>
                                .custom-toast {
                                    position: fixed;
                                    bottom: 20px;
                                    right: 20px;
                                    background-color: #d4edda;
                                    color: #155724;
                                    padding: 12px 24px;
                                    border-radius: 8px;
                                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                                    z-index: 9999;
                                    animation: fadeInOut 1.5s ease-in-out forwards;
                                    font-size: 14px;
                                }
                                @keyframes fadeInOut {
                                    0% { opacity: 0; transform: translateY(20px); }
                                    15% { opacity: 1; transform: translateY(0); }
                                    85% { opacity: 1; transform: translateY(0); }
                                    100% { opacity: 0; transform: translateY(-10px); }
                                }
                            </style>
                            <div class="custom-toast">✅ Saved!</div>
                            """, unsafe_allow_html=True)

                    # 檢查是否有變更（只有在沒有按鈕被點擊時才處理）
                    if not button_clicked:
                        has_changes = any(
                            abs(edited_targets[month] - current_targets.get(month, annual_yoy_target)) > 0.01
                            for month in all_months
                        )

                        if has_changes:
                            st.session_state[undo_session_key].append(current_targets.copy())
                            st.session_state[target_session_key] = edited_targets
                            st.rerun()

                    if current_file_key in all_targets and str(this_year) in all_targets[current_file_key]:
                        last_modified = all_targets[current_file_key][str(this_year)].get('modified_at')
                        if last_modified:
                            st.caption(f"💾 Last saved: {last_modified}")
                else:
                    st.info("⚠️ 需要至少兩年的資料才能設定目標")

            else:
                st.warning("⚠️ 請至少選擇一個年份")
        else:
            st.warning("⚠️ 未在資料中找到年份欄位")

# Business Metrics 區塊
if "Sales Traffic Report" in loaded_data:
    st.header("📊 Business Metrics")

    sales_df = loaded_data["Sales Traffic Report"]

    # 尋找 Date 欄位
    date_columns = [col for col in sales_df.columns if 'date' in col.lower()]

    if date_columns:
        # 使用第一個找到的日期欄位
        date_col = date_columns[0]

        # 取得所有可用的日期，並排序
        available_dates = sales_df[date_col].dropna().unique()

        # 嘗試將日期轉換為 datetime 以便排序
        try:
            # 嘗試不同的日期格式進行轉換
            available_dates_converted = []
            date_mapping = {}  # 用於儲存顯示格式到原始值的對照

            for date_str in available_dates:
                try:
                    # 自動解析日期（支援多種格式）
                    parsed_date = pd.to_datetime(str(date_str))

                    # 轉換為 YYYY-MM 格式
                    display_format = parsed_date.strftime('%Y-%m')
                    date_mapping[display_format] = str(date_str)
                    available_dates_converted.append((parsed_date, display_format))
                except:
                    # 如果解析失敗，保持原格式
                    available_dates_converted.append((None, str(date_str)))
                    date_mapping[str(date_str)] = str(date_str)

            # 只對成功轉換的日期進行排序
            datetime_dates = [(d, fmt) for d, fmt in available_dates_converted if d is not None]
            if datetime_dates:
                datetime_dates = sorted(datetime_dates, key=lambda x: x[0], reverse=True)
                available_dates = [fmt for _, fmt in datetime_dates]
            else:
                available_dates = sorted([fmt for _, fmt in available_dates_converted], reverse=True)

            # 儲存對照表到 session state
            st.session_state.date_mapping = date_mapping
        except Exception as e:
            # 如果轉換失敗，就直接排序字串
            available_dates = sorted([str(d) for d in available_dates], reverse=True)
            st.session_state.date_mapping = {d: d for d in available_dates}

        # 日期選擇下拉選單 — 預設選上一個完整月份
        # available_dates 已按時間倒序排列 (如 ['2026-03', '2026-02', '2026-01', ...])
        from datetime import datetime
        now = datetime.now()
        last_complete_month = f"{now.year}-{now.month - 1:02d}" if now.month > 1 else f"{now.year - 1}-12"
        default_date_index = 0
        if last_complete_month in available_dates:
            default_date_index = available_dates.index(last_complete_month)
        elif len(available_dates) > 1:
            default_date_index = 1  # 跳過最新的（可能不完整）

        selected_date = st.selectbox(
            "選擇日期",
            options=available_dates,
            index=default_date_index,
            key="business_metrics_date"
        )

        # 根據選擇的日期篩選數據
        # 使用對照表找出原始日期值
        original_date = st.session_state.date_mapping.get(selected_date, selected_date)

        # 使用更靈活的日期匹配
        mask = sales_df[date_col].apply(lambda x: match_date(x, original_date))
        filtered_sales_df = sales_df[mask]

        if not filtered_sales_df.empty:
            # Sales Widget
            st.subheader(f"📈 {selected_date}")

            # 創建 widget 欄位
            metric_col1, metric_col2, metric_col3 = st.columns(3)

            st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)

            metric_col4, metric_col5 = st.columns(2)

            # 定義業務指標配置
            business_metrics = [
                {
                    'column': metric_col1,
                    'title': 'Sales',
                    'column_keywords': ['ordered product sales'],
                    'prefix': '$'
                },
                {
                    'column': metric_col2,
                    'title': 'Total Order Items',
                    'column_keywords': ['total order items']
                },
                {
                    'column': metric_col3,
                    'title': 'Sessions',
                    'column_keywords': ['sessions - total']
                },
                {
                    'column': metric_col4,
                    'title': 'CVR',
                    'column_keywords': ['order item session percentage'],
                    'cvr_mode': True,
                    'suffix': '%',
                    'show_change_percent': False
                },
                {
                    'column': metric_col5,
                    'title': 'ASP',
                    'column_keywords': ['average selling price'],
                    'prefix': '$',
                    'decimal_mode': True  # 保留兩位小數
                }
            ]

            # 批量渲染業務指標
            for metric in business_metrics:
                with metric['column']:
                    render_business_metric_widget(sales_df, date_col, original_date, metric)

        # 在 L819 之後添加圖表區塊
        st.markdown("---")
        st.subheader("📈 Business Metrics Trends")

        # 獲取所有數值欄位（排除日期欄位）
        numeric_columns = []
        for col in sales_df.columns:
            if col != date_col:
                # 嘗試將欄位轉換為數值，忽略錯誤
                numeric_series = pd.to_numeric(sales_df[col], errors='coerce')
                # 如果轉換後至少有一個非空值，則認為是數值欄位
                if not numeric_series.isnull().all():
                    numeric_columns.append(col)

        # 預設選擇的欄位
        default_metrics = [
            'Ordered Product Sales',
            'Total Order Items',
            'Sessions - Total',
            'Order Item Session Percentage',
            'Average Selling Price'
        ]

        # 找出實際存在的預設欄位
        actual_default_metrics = []
        for default_metric in default_metrics:
            # 尋找包含關鍵詞的欄位
            matching_cols = [col for col in numeric_columns if default_metric.lower() in col.lower()]
            if matching_cols:
                # 優先選擇不包含特定後綴的基本欄位
                basic_cols = [col for col in matching_cols if not any(
                    suffix in col.lower() for suffix in ['this year so far', '% change', 'last year'])]
                if basic_cols:
                    actual_default_metrics.append(basic_cols[0])
                else:
                    actual_default_metrics.append(matching_cols[0])

        # 去重
        actual_default_metrics = list(dict.fromkeys(actual_default_metrics))

        # 如果沒有找到預設欄位，則選擇前5個數值欄位
        if not actual_default_metrics and numeric_columns:
            actual_default_metrics = numeric_columns[:5]

        # 多選框讓用戶選擇要顯示的指標
        selected_metrics = st.multiselect(
            "選擇要顯示的業務指標 (每個指標一張圖)",
            options=numeric_columns,
            default=actual_default_metrics,
            key="business_metrics_chart_selection"
        )

        if selected_metrics and len(available_dates) > 1:
            import plotly.graph_objects as go

            # 先解析日期，取得資料中實際存在的年份
            sales_df_copy = sales_df.copy()
            sales_df_copy['parsed_date'] = pd.to_datetime(sales_df_copy[date_col], errors='coerce')
            all_dates_in_df = sales_df_copy['parsed_date'].dropna()
            
            if not all_dates_in_df.empty:
                # 動態取得資料中實際存在的年份
                available_years_in_data = sorted(all_dates_in_df.dt.year.unique().tolist(), reverse=True)
                
                # 年份選擇器
                col_year_select, _ = st.columns([1, 3])
                with col_year_select:
                    selected_chart_years = st.multiselect(
                        "選擇要顯示的年份",
                        options=available_years_in_data,
                        default=available_years_in_data,  # 預設選擇全部年份
                        key="business_metrics_year_selection"
                    )

                # 定義年份對應的顏色
                year_colors = ['#2E86AB', '#F18F01', '#28A745', '#DC3545', '#6F42C1', '#17A2B8']

                def create_comparison_chart(metric, sales_df_copy, selected_years):
                    if not selected_years:
                        return None

                    months_map = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
                    month_order = list(months_map.values())

                    fig = go.Figure()
                    
                    # 為每個選擇的年份添加線條
                    for year_idx, year in enumerate(sorted(selected_years, reverse=True)):
                        year_data = []
                        for month_num, month_name in months_map.items():
                            year_mask = (sales_df_copy['parsed_date'].dt.year == year) & (sales_df_copy['parsed_date'].dt.month == month_num)
                            year_series = sales_df_copy.loc[year_mask, metric]
                            year_value = year_series.iloc[0] if not year_series.empty else None
                            year_data.append(year_value)
                        
                        color = year_colors[year_idx % len(year_colors)]
                        fig.add_trace(go.Scatter(
                            x=month_order, 
                            y=year_data, 
                            name=f'{year}', 
                            mode='lines+markers',
                            line=dict(color=color, width=2),
                            marker=dict(size=6, color=color)
                        ))

                    fig.update_layout(
                        title=f"{metric} (YoY Comparison)",
                        xaxis_title="Month",
                        yaxis_title="Value",
                        height=350,
                        legend_title_text='Year',
                        margin=dict(l=40, r=40, t=40, b=40)
                    )
                    return fig

                if selected_chart_years:
                    # 為每個選擇的指標生成一個圖表，每行兩個
                    num_metrics = len(selected_metrics)
                    for i in range(0, num_metrics, 2):
                        col1, col2 = st.columns(2)

                        with col1:
                            metric1 = selected_metrics[i]
                            fig1 = create_comparison_chart(metric1, sales_df_copy, selected_chart_years)
                            if fig1:
                                st.plotly_chart(fig1, use_container_width=True)

                        if i + 1 < num_metrics:
                            with col2:
                                metric2 = selected_metrics[i+1]
                                fig2 = create_comparison_chart(metric2, sales_df_copy, selected_chart_years)
                                if fig2:
                                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("請選擇至少一個年份來顯示圖表")
            else:
                st.warning("無法從日期欄位解析有效日期")

        elif selected_metrics and len(available_dates) <= 1:
            st.info("需要至少2個日期的數據才能顯示趨勢圖表")

        elif not selected_metrics:
            st.info("請選擇至少一個業務指標來顯示圖表")

        else:
            st.warning(f"未找到日期 {selected_date} 的數據")
    else:
        st.warning("未找到 Date 欄位")
        if st.checkbox("顯示所有欄位 (調試)", key="debug_all_columns"):
            st.write("**Sales Traffic Report 所有欄位:**")
            st.write(list(sales_df.columns))

# ASIN Level 區塊
if "Asin Report" in loaded_data:
    st.markdown("---")
    st.header("📦 ASIN Level")

    asin_df = loaded_data["Asin Report"]

    # 創建三個分頁（使用自訂 CSS 增加字體大小）
    st.markdown("""
        <style>
        button[data-baseweb="tab"] {
            font-size: 18px !important;
            padding: 12px 20px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Complete ASIN Data", "📈 Trend", "🏢 B2B"])

    # ==================== Tab 3: B2B 分析 ====================
    with tab3:
        # B2B 分析區塊
        if 'B2B Sales' in asin_df.columns and 'B2B %' in asin_df.columns:
            # 計算整體 B2B 佔比（確保轉換為數值型別）
            try:
                # 處理可能的字串格式（移除 $ 符號）
                def clean_number(val):
                    if pd.isna(val):
                        return 0.0
                    if isinstance(val, str):
                        return float(val.replace('$', '').replace(',', '').strip())
                    return float(val)

                total_sales = asin_df['Ordered Product Sales'].apply(clean_number).sum() if 'Ordered Product Sales' in asin_df.columns else 0.0
                total_b2b = asin_df['B2B Sales'].apply(clean_number).sum()
                b2b_percentage = (total_b2b / total_sales * 100) if total_sales > 0 else 0.0
            except Exception as e:
                st.error(f"計算 B2B 佔比時發生錯誤: {e}")
                b2b_percentage = 0.0

            # 顯示整體 B2B 佔比（計算方式：全部 ASIN 的 B2B Sales 總和 / Ordered Product Sales 總和）
            st.metric("整體 B2B 佔比", f"{b2b_percentage:.2f}%",
                     help="計算方式：全部 ASIN 的 B2B Sales 總和 ÷ Ordered Product Sales 總和")

            # 根據 5% 門檻顯示狀態
            if b2b_percentage > 5:
                # 綠底顯示 (使用 markdown 加上 CSS，縮小上邊距)
                st.markdown(
                    f'<div style="background-color: #d4edda; padding: 16px 20px; border-radius: 8px; border-left: 5px solid #28a745; margin: -10px 0 20px 0;">'
                    f'<p style="margin: 0; font-size: 16px; line-height: 1.6;"><strong>B2B 佔整體 GMV > 5%</strong></p>'
                    f'<p style="margin: 8px 0 0 0; font-size: 14px; color: #155724;">當前佔比：{b2b_percentage:.2f}%</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                st.markdown("**以下 ASIN 需關注（B2B% > 5%）：**")

                # 只顯示 B2B% > 5% 的 ASIN
                high_b2b_asins = asin_df[asin_df['B2B %'].apply(
                    lambda x: float(str(x).replace('%', '').strip()) if pd.notna(x) else 0
                ) > 5].copy()

                if not high_b2b_asins.empty:
                    # 排序：按 B2B Sales 降序
                    high_b2b_asins = high_b2b_asins.sort_values('B2B Sales', ascending=False)

                    # 選擇要顯示的欄位
                    display_columns = ['Child ASIN']
                    if 'Title' in high_b2b_asins.columns:
                        display_columns.append('Title')
                    display_columns.extend(['B2B Sales', 'B2B %', 'Ordered Product Sales'])

                    # 定義 B2B% 的樣式函數
                    def highlight_b2b_percentage(val):
                        """B2B% >= 5% 時顯示紅底"""
                        try:
                            # 移除 % 符號並轉換為數字
                            num_val = float(str(val).replace('%', '').strip())
                            if num_val >= 5:
                                return 'background-color: pink; color: red;'
                        except:
                            pass
                        return ''

                    # 應用樣式
                    styled_df = high_b2b_asins[display_columns].style.applymap(
                        highlight_b2b_percentage,
                        subset=['B2B %']
                    )

                    # 顯示表格
                    st.dataframe(
                        styled_df,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    # 沒有單一 ASIN 的 B2B% > 5%，顯示所有有 B2B 銷售的 ASIN
                    st.info("沒有單一 ASIN 的 B2B% > 5%，以下顯示所有有 B2B 銷售的 ASIN：")
                    
                    b2b_asins = asin_df[asin_df['B2B Sales'].apply(
                        lambda x: clean_number(x) > 0
                    )].copy()
                    
                    if not b2b_asins.empty:
                        b2b_asins = b2b_asins.sort_values('B2B Sales', ascending=False)
                        
                        display_columns = ['Child ASIN']
                        if 'Title' in b2b_asins.columns:
                            display_columns.append('Title')
                        display_columns.extend(['B2B Sales', 'B2B %', 'Ordered Product Sales'])
                        
                        def highlight_b2b_percentage(val):
                            try:
                                num_val = float(str(val).replace('%', '').strip())
                                if num_val >= 5:
                                    return 'background-color: pink; color: red;'
                            except:
                                pass
                            return ''
                        
                        styled_df = b2b_asins[display_columns].style.applymap(
                            highlight_b2b_percentage,
                            subset=['B2B %']
                        )
                        
                        st.dataframe(
                            styled_df,
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("目前沒有 ASIN 有 B2B 銷售記錄")
            else:
                # 灰底顯示（縮小上邊距）
                st.markdown(
                    f'<div style="background-color: #f8f9fa; padding: 16px 20px; border-radius: 8px; border-left: 5px solid #6c757d; margin: -10px 0 20px 0;">'
                    f'<p style="margin: 0; font-size: 16px; line-height: 1.6;"><strong>B2B 佔整體 GMV < 5%</strong></p>'
                    f'<p style="margin: 8px 0 0 0; font-size: 14px; color: #495057;">當前佔比：{b2b_percentage:.2f}%</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # 仍然顯示有 B2B 銷售的 ASIN（如果有的話）
                b2b_asins = asin_df[asin_df['B2B Sales'].apply(
                    lambda x: clean_number(x) > 0
                )].copy()

                if not b2b_asins.empty:
                    st.markdown("**有 B2B 銷售的 ASIN：**")
                    # 排序：按 B2B Sales 降序
                    b2b_asins = b2b_asins.sort_values('B2B Sales', ascending=False)

                    display_columns = ['Child ASIN']
                    if 'Title' in b2b_asins.columns:
                        display_columns.append('Title')
                    display_columns.extend(['B2B Sales', 'B2B %', 'Ordered Product Sales'])

                    # 定義 B2B% 的樣式函數
                    def highlight_b2b_percentage(val):
                        """B2B% >= 5% 時顯示紅底"""
                        try:
                            # 移除 % 符號並轉換為數字
                            num_val = float(str(val).replace('%', '').strip())
                            if num_val >= 5:
                                return 'background-color: pink; color: red;'
                        except:
                            pass
                        return ''

                    # 應用樣式
                    styled_df = b2b_asins[display_columns].style.applymap(
                        highlight_b2b_percentage,
                        subset=['B2B %']
                    )

                    st.dataframe(
                        styled_df,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("目前沒有 ASIN 有 B2B 銷售記錄")

        else:
            st.info("此資料中沒有 B2B 銷售數據")

    # ==================== Tab 1: 完整 ASIN 資料 ====================
    with tab1:
        # 兩個widget
        col1, col2 = st.columns(2)

        st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)

        with col1:
            session_median = 0
            session_mean = 0
            session_median_yoy = None
            session_median_mom = None
            session_mean_yoy = None
            session_mean_mom = None
            if 'Sessions - Total' in asin_df.columns:
                # 排除0的資料
                session_data = asin_df['Sessions - Total'].dropna()
                session_data = session_data[session_data != 0]
                if not session_data.empty:
                    session_median = round(session_data.median())
                    session_mean = round(session_data.mean())
            if 'Sessions - Total - Prior Period' in asin_df.columns:
                prior_session_data = asin_df['Sessions - Total - Prior Period'].dropna()
                prior_session_data = prior_session_data[prior_session_data != 0]
                if not prior_session_data.empty:
                    prior_session_median = round(prior_session_data.median())
                    prior_session_mean = round(prior_session_data.mean())
                    session_median_mom = (session_median - prior_session_median) / prior_session_median
                    session_mean_mom = (session_mean - prior_session_mean) / prior_session_mean

            if 'Sessions - Total - Last Year' in asin_df.columns:
                last_year_session_data = asin_df['Sessions - Total - Last Year'].dropna()
                last_year_session_data = last_year_session_data[last_year_session_data != 0]
                if not last_year_session_data.empty:
                    last_session_median = round(last_year_session_data.median())
                    last_session_mean = round(last_year_session_data.mean())
                    session_median_yoy = (session_median - last_session_median) / last_session_median
                    session_mean_yoy = (session_mean - last_session_mean) / last_session_mean

            render_kpi_widget("Session (中位數)", session_median, session_median_yoy, session_median_mom)

        with col2:
            cvr_median = 0
            cvr_mean = 0
            cvr_median_yoy = None
            cvr_median_mom = None
            cvr_mean_yoy = None
            cvr_mean_mom = None
            if 'Unit Session Percentage' in asin_df.columns:
                # 排除0的資料，並移除 % 符號進行計算
                cvr_data = asin_df['Unit Session Percentage'].dropna()
                # 移除 % 符號並轉換為數值
                cvr_data = cvr_data.apply(
                    lambda x: float(str(x).replace('%', '').strip()) if pd.notna(x) else 0
                )
                cvr_data = cvr_data[cvr_data != 0]
                if not cvr_data.empty:
                    cvr_median = round(cvr_data.median(), 2)
                    cvr_mean = round(cvr_data.mean(), 2)
            if 'Unit Session % - Prior Period' in asin_df.columns:
                prior_cvr_data = asin_df['Unit Session % - Prior Period'].dropna()
                prior_cvr_data = prior_cvr_data.apply(
                    lambda x: float(str(x).replace('%', '').strip()) if pd.notna(x) else 0
                )
                prior_cvr_data = prior_cvr_data[prior_cvr_data != 0]
                if not prior_cvr_data.empty:
                    prior_cvr_median = round(prior_cvr_data.median(), 2)
                    prior_cvr_mean = round(prior_cvr_data.mean(), 2)
                    cvr_median_mom = (cvr_median - prior_cvr_median) * 10000
                    cvr_mean_mom = (cvr_mean - prior_cvr_mean) * 10000
            if 'Unit Session % - Last Year' in asin_df.columns:
                last_cvr_data = asin_df['Unit Session % - Last Year'].dropna()
                last_cvr_data = last_cvr_data.apply(
                    lambda x: float(str(x).replace('%', '').strip()) if pd.notna(x) else 0
                )
                last_cvr_data = last_cvr_data[last_cvr_data != 0]
                if not last_cvr_data.empty:
                    last_cvr_median = round(last_cvr_data.median(), 2)
                    last_cvr_mean = round(last_cvr_data.mean(), 2)
                    cvr_median_yoy = (cvr_median - last_cvr_median) * 10000
                    cvr_mean_yoy = (cvr_mean - last_cvr_mean) * 10000

            render_kpi_widget("CVR (中位數)", cvr_median, cvr_median_yoy, cvr_median_mom, suffix="%", show_change_percent=False)

        # 顯示平均數
        col3, col4 = st.columns(2)

        with col3:
            render_kpi_widget("Session (平均數)", session_mean, session_mean_yoy, session_mean_mom)

        with col4:
            render_kpi_widget("CVR (平均數)", cvr_mean, cvr_mean_yoy, cvr_mean_mom, suffix="%", show_change_percent=False)

        # ASIN Sales 圓餅圖
        st.markdown("---")
        st.subheader("📊 ASIN Sales Contribution")

        if 'Sales Contribution %' in asin_df.columns and 'Child ASIN' in asin_df.columns:
            import plotly.graph_objects as go

            # 準備數據
            pie_data = asin_df[['Child ASIN', 'Sales Contribution %']].dropna().copy()

            # 將 Sales Contribution % 轉換為數值（去除 % 符號）
            pie_data['Sales Contribution %'] = pie_data['Sales Contribution %'].apply(
                lambda x: float(str(x).replace('%', '').strip()) if pd.notna(x) else 0
            )

            if not pie_data.empty:
                # 只取前10名，其餘合併為「其他」
                top_10 = pie_data.nlargest(10, 'Sales Contribution %')

                # 如果超過10筆，將剩餘的合併為「其他」
                if len(pie_data) > 10:
                        others_sum = pie_data.iloc[10:]['Sales Contribution %'].sum()
                        # 創建「其他」的資料
                        others_row = pd.DataFrame({
                            'Child ASIN': ['其他'],
                            'Sales Contribution %': [others_sum]
                        })
                        # 合併前10名和「其他」
                        chart_data = pd.concat([top_10, others_row], ignore_index=True)
                else:
                    chart_data = top_10

                # 創建圓餅圖
                fig = go.Figure(data=[go.Pie(
                    labels=chart_data['Child ASIN'],
                    values=chart_data['Sales Contribution %'],
                    hole=0.3,  # 甜甜圈圖效果
                    textposition='auto',
                    textinfo='label+percent',
                    hovertemplate='<b>%{label}</b><br>貢獻度: %{value}%<br>佔比: %{percent}<extra></extra>'
                )])

                fig.update_layout(
                    title="各 ASIN 銷售貢獻百分比",
                    height=500,
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.05
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

                # 顯示主力 ASIN (貢獻度最高的前3名)
                top_asins = pie_data.nlargest(3, 'Sales Contribution %')
                st.markdown("**主力 ASIN TOP 3:**")
                for idx, row in top_asins.iterrows():
                    st.write(f"🏆 **{row['Child ASIN']}**: {row['Sales Contribution %']:.2f}%")

                # 顯示完整的資料表格
                st.markdown("---")
                st.markdown("**完整 ASIN 資料:**")

                # === ASIN 標記工具 (MVP) ===
                import json
                from pathlib import Path

                # 載入已儲存的標記
                marks_file = Path("uploaded_data/asin_marks.json")
                if 'asin_marks' not in st.session_state:
                    if marks_file.exists():
                        with open(marks_file, 'r', encoding='utf-8') as f:
                            st.session_state.asin_marks = json.load(f)
                    else:
                        st.session_state.asin_marks = {}

                # 載入已儲存的自定義 Tag 清單
                tags_file = Path("uploaded_data/asin_tags_config.json")
                if 'asin_tags_config' not in st.session_state:
                    if tags_file.exists():
                        with open(tags_file, 'r', encoding='utf-8') as f:
                            st.session_state.asin_tags_config = json.load(f)
                    else:
                        # 預設 Tag 清單
                        st.session_state.asin_tags_config = [
                            "🔴 重點關注",
                            "🟡 待優化",
                            "🟢 表現良好",
                            "🔵 新品"
                        ]

                # 添加 expander 背景樣式
                st.markdown("""
                    <style>
                    /* 未展開時的標題列背景 */
                    div[data-testid="stExpander"] details summary {
                        background-color: #f5f5f5;
                        border-radius: 5px;
                        padding: 10px;
                    }
                    /* 展開後標題列背景（上半部圓角） */
                    div[data-testid="stExpander"] details[open] summary {
                        background-color: #f5f5f5;
                        border-radius: 5px 5px 0 0;
                        padding: 10px;
                    }
                    /* 展開後的內容區域背景（白色） */
                    div[data-testid="stExpander"] details[open] > div:not(summary) {
                        background-color: white;
                        padding: 15px;
                        border-radius: 0 0 5px 5px;
                    }
                    </style>
                """, unsafe_allow_html=True)

                # 標記工具 UI
                with st.expander("⚙️ ASIN 設定與標記", expanded=False):

                    # ===== ASIN 標記區塊 =====
                    with st.expander("🏷️ ASIN 標記", expanded=False):

                        # 管理 Tag 子區塊
                        st.markdown("**➕ 新增 Tag**")
                        tag_col1, tag_col2 = st.columns([3, 1])
                        with tag_col1:
                            new_tag_name = st.text_input(
                                "輸入 Tag 名稱",
                                key="new_tag_name_input",
                                placeholder="例如: 🟣 高優先級、⭐ 明星商品"
                            )
                        with tag_col2:
                            st.markdown("<div style='margin-bottom: 8px;'>&nbsp;</div>", unsafe_allow_html=True)
                            if st.button("新增", key="add_new_tag"):
                                if new_tag_name and new_tag_name.strip():
                                    if new_tag_name not in st.session_state.asin_tags_config:
                                        st.session_state.asin_tags_config.append(new_tag_name)
                                        # 自動儲存
                                        with open(tags_file, 'w', encoding='utf-8') as f:
                                            json.dump(st.session_state.asin_tags_config, f, ensure_ascii=False, indent=2)
                                        st.success(f"已新增 Tag: {new_tag_name}")
                                        st.rerun()
                                    else:
                                        st.warning("此 Tag 已存在")
                                else:
                                    st.warning("請輸入 Tag 名稱")

                        st.markdown("---")
                        st.markdown("**目前的 Tag 清單**")

                        if st.session_state.asin_tags_config:
                            for idx, tag in enumerate(st.session_state.asin_tags_config):
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.text(tag)
                                with col2:
                                    if st.button("刪除", key=f"delete_tag_{idx}"):
                                        # 刪除 Tag
                                        st.session_state.asin_tags_config.remove(tag)
                                        # 同時清除所有使用此 Tag 的 ASIN 標記
                                        asins_to_remove = [asin for asin, label in st.session_state.asin_marks.items() if label == tag]
                                        for asin in asins_to_remove:
                                            del st.session_state.asin_marks[asin]
                                        # 儲存
                                        with open(tags_file, 'w', encoding='utf-8') as f:
                                            json.dump(st.session_state.asin_tags_config, f, ensure_ascii=False, indent=2)
                                        with open(marks_file, 'w', encoding='utf-8') as f:
                                            json.dump(st.session_state.asin_marks, f, ensure_ascii=False, indent=2)
                                        st.success(f"已刪除 Tag: {tag}")
                                        st.rerun()
                        else:
                            st.info("目前沒有 Tag，請新增")

                        if st.button("重置為預設 Tag", key="reset_tags"):
                            st.session_state.asin_tags_config = [
                                "🔴 重點關注",
                                "🟡 待優化",
                                "🟢 表現良好",
                                "🔵 新品"
                            ]
                            with open(tags_file, 'w', encoding='utf-8') as f:
                                json.dump(st.session_state.asin_tags_config, f, ensure_ascii=False, indent=2)
                            st.success("已重置為預設 Tag")
                            st.rerun()

                        st.markdown("---")

                        # 標記 ASIN 子區塊
                        st.markdown("**✏️ 標記 ASIN**")
                        col_a, col_b, col_c = st.columns([4, 3, 2])
                        with col_a:
                            mark_asin = st.text_input("輸入 ASIN", key="mark_asin_input", placeholder="例如: B0DNK675T9")
                        with col_b:
                            # 動態讀取 Tag 清單
                            tag_options = ["無"] + st.session_state.asin_tags_config
                            mark_label = st.selectbox("Tag", tag_options, key="mark_label")
                        with col_c:
                            # 添加空白標籤來對齊按鈕
                            st.markdown("<div style='margin-bottom: 8px;'>&nbsp;</div>", unsafe_allow_html=True)
                            btn_col1, btn_col2 = st.columns([1, 1])
                            with btn_col1:
                                if st.button("套用", key="apply_mark"):
                                    if mark_asin:
                                        if mark_label == "無":
                                            # 移除標記
                                            if mark_asin in st.session_state.asin_marks:
                                                del st.session_state.asin_marks[mark_asin]
                                        else:
                                            # 新增/更新標記
                                            st.session_state.asin_marks[mark_asin] = mark_label
                                        # 自動儲存
                                        with open(marks_file, 'w', encoding='utf-8') as f:
                                            json.dump(st.session_state.asin_marks, f, ensure_ascii=False, indent=2)
                                        st.success(f"已標記 {mark_asin}")
                                        st.rerun()
                            with btn_col2:
                                if st.button("清空", key="clear_all_marks"):
                                    st.session_state.asin_marks = {}
                                    if marks_file.exists():
                                        marks_file.unlink()
                                    st.success("已清空所有標記")
                                    st.rerun()

                        # 顯示目前的標記
                        if st.session_state.asin_marks:
                            st.markdown("**目前標記：**")
                            for asin, label in st.session_state.asin_marks.items():
                                st.text(f"{label} {asin}")

                    # ===== 顯示設定區塊 =====
                    with st.expander("📊 顯示設定", expanded=False):
                        st.markdown("**選擇要顯示的欄位群組**")

                        col1, col2 = st.columns(2)
                        with col1:
                            show_b2b = st.checkbox("🏢 B2B 數據", value=False, key="show_b2b_columns")
                            show_comparison = st.checkbox("📈 同期比較", value=True, key="show_comparison_columns")
                        with col2:
                            show_inventory = st.checkbox("📦 庫存資訊", value=True, key="show_inventory_columns")
                            show_percentage = st.checkbox("📊 變化百分比", value=True, key="show_percentage_columns")

                        st.info("💡 取消勾選的欄位群組將在下方表格中隱藏")

                # 顯示所有欄位的完整資料
                display_df = asin_df.copy()

                # 新增分類欄位：根據 Sessions 和 CVR 與中位數的比較
                def classify_asin(row):
                    """根據 Sessions 和 CVR 與中位數比較，進行分類"""
                    # 取得該列的 Sessions 和 CVR
                    row_sessions = row.get('Sessions - Total', None)
                    row_cvr = row.get('Unit Session Percentage', None)

                    # 處理 CVR（移除 % 符號）
                    if pd.notna(row_cvr):
                        try:
                            row_cvr = float(str(row_cvr).replace('%', '').strip())
                        except:
                            row_cvr = None

                    # 檢查數據是否有效
                    if pd.isna(row_sessions) or row_sessions == 0 or pd.isna(row_cvr) or row_cvr == 0:
                        return "-"

                    # 與中位數比較
                    sessions_high = row_sessions > session_median
                    cvr_high = row_cvr > cvr_median

                    # 分類邏輯
                    if sessions_high and cvr_high:
                        return "高流量高轉化"
                    elif sessions_high and not cvr_high:
                        return "高流量低轉化"
                    elif not sessions_high and cvr_high:
                        return "低流量高轉化"
                    else:
                        return "低流量低轉化"

                # 應用分類函數
                display_df.insert(1, 'Performance', display_df.apply(classify_asin, axis=1))

                # 新增標記欄位
                if st.session_state.asin_marks:
                    display_df.insert(2, 'Tag', display_df['Child ASIN'].map(st.session_state.asin_marks).fillna('-'))

                # 如果有 Sales Contribution % 欄位，按照貢獻度排序（在重命名之前）
                contribution_col = 'Sales Contribution %'
                if contribution_col in display_df.columns:
                    # 創建一個用於排序的數值欄位
                    display_df['_sort_value'] = display_df['Sales Contribution %'].apply(
                        lambda x: float(str(x).replace('%', '').strip()) if pd.notna(x) else 0
                    )
                    # 排序（由高到低）
                    display_df = display_df.sort_values('_sort_value', ascending=False)
                    # 移除排序用的欄位
                    display_df = display_df.drop(columns=['_sort_value'])

                # ===== 根據顯示設定過濾欄位 =====
                columns_to_remove = []

                # B2B 數據
                if not st.session_state.get('show_b2b_columns', True):
                    b2b_columns = ['B2B Sales', 'B2B %']
                    columns_to_remove.extend([col for col in b2b_columns if col in display_df.columns])

                # 同期比較
                if not st.session_state.get('show_comparison_columns', True):
                    comparison_columns = [
                        'Ordered Product Sales - Prior Period', 'Ordered Product Sales - Last Year',
                        'Sessions - Total - Prior Period', 'Sessions - Total - Last Year',
                        'Total Order Items - Prior Period', 'Total Order Items - Last Year',
                        'Unit Session % - Prior Period', 'Unit Session % - Last Year'
                    ]
                    columns_to_remove.extend([col for col in comparison_columns if col in display_df.columns])

                # 庫存資訊
                if not st.session_state.get('show_inventory_columns', True):
                    inventory_columns = ['Available', 'Total Days of Supply', 'WOC']
                    columns_to_remove.extend([col for col in inventory_columns if col in display_df.columns])

                # 變化百分比
                if not st.session_state.get('show_percentage_columns', True):
                    percentage_columns = ['MoM', 'YoY']
                    columns_to_remove.extend([col for col in percentage_columns if col in display_df.columns])

                # 移除欄位
                if columns_to_remove:
                    display_df = display_df.drop(columns=columns_to_remove, errors='ignore')

                # 重新命名欄位標題
                column_rename_map = {
                    'Ordered Product Sales': 'Sales',
                    'Ordered Product Sales - Prior Period': 'Sales-lm',
                    'Ordered Product Sales - Last Year': 'Sales-ly',
                    'Sessions - Total': 'Sessions',
                    'Sessions - Total - Prior Period': 'Sessions-lm',
                    'Sessions - Total - Last Year': 'Sessions-ly',
                    'Total Order Items':'Orders',
                    'Total Order Items - Prior Period': 'Orders-lm',
                    'Total Order Items - Last Year': 'Orders-ly',
                    'Unit Session Percentage': 'CVR',
                    'Unit Session % - Prior Period': 'CVR-lm',
                    'Unit Session % - Last Year': 'CVR-ly',
                    'Sales Contribution %':'Sales %',
                    'Total Days of Supply':'TDoS'
                    # 'Original Column Name': 'New Display Name',
                }
                display_df = display_df.rename(columns=column_rename_map)

                # 重設索引，從1開始編號
                display_df = display_df.reset_index(drop=True)
                display_df.index = display_df.index + 1

                # 定義樣式函數：將 MoM 和 YoY 的正值顯示為綠色，負值顯示為紅色
                def color_mom_yoy(val):
                    """根據正負值返回顏色"""
                    try:
                        # 嘗試將值轉換為數字（移除可能的 % 符號和 bps 文字）
                        num_val = float(str(val).replace('%', '').replace('bps', '').strip())
                        if num_val > 0:
                            return 'color: green'
                        elif num_val < 0:
                            return 'color: red'
                        else:
                            return 'color: black'
                    except:
                        return ''



                # 格式化數值欄位
                def format_values(df):
                    formatted_df = df.copy()
                    for col in formatted_df.columns:
                        if any(keyword in col.lower() for keyword in ['sales', 'revenue']):
                            # Sales 相關欄位加上$符號和千位逗號
                            formatted_df[col] = formatted_df[col].apply(
                                lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) and pd.notna(x) else x
                            )
                        elif any(keyword in col.lower() for keyword in ['available', 'total days of supply', 'totaldays', 'woc', 'tdos']):
                            # Available, total days of supply, totaldays, woc, tdos 欄位顯示為整數
                            formatted_df[col] = formatted_df[col].apply(
                                lambda x: f"{round(x):,}" if isinstance(x, (int, float)) and pd.notna(x) else x
                            )
                    return formatted_df

                formatted_display_df = format_values(display_df)

                # 找出 MoM 和 YoY 相關的欄位
                mom_yoy_cols = [col for col in formatted_display_df.columns if 'mom' in col.lower() or 'yoy' in col.lower()]

                # 從分組中提取各類型欄位
                sales_percentage_cols = [col for col in display_df.columns if col.lower() == 'sales %']
                sales_cols = [col for col in display_df.columns if col.lower() in ['sales', 'sales-lm', 'sales-ly']]
                sessions_cols = [col for col in display_df.columns if col.lower() in ['sessions', 'sessions-lm', 'sessions-ly']]
                orders_cols = [field for field in display_df.columns if field.lower() in ['orders', 'orders-lm', 'orders-ly']]
                cvr_cols = [field for field in display_df.columns if field.lower() in ['cvr', 'cvr-lm', 'cvr-ly']]

                # 預先計算每組欄位的最小最大值
                def calculate_group_min_max(df, cols):
                    """計算一組欄位的全局最小最大值"""
                    all_values = []
                    for col in cols:
                        if col in df.columns:
                            for val in df[col]:
                                try:
                                    if isinstance(val, str):
                                        numeric_val = float(val.replace('$', '').replace(',', '').replace('%', '').strip())
                                    else:
                                        numeric_val = float(val) if pd.notna(val) else 0
                                    if numeric_val > 0:
                                        all_values.append(numeric_val)
                                except:
                                    pass

                    if all_values:
                        return min(all_values), max(all_values)
                    return None, None

                # 計算各組的最小最大值
                sales_percentage_min, sales_percentage_max = calculate_group_min_max(formatted_display_df, sales_percentage_cols)
                sales_min, sales_max = calculate_group_min_max(formatted_display_df, sales_cols)
                sessions_min, sessions_max = calculate_group_min_max(formatted_display_df, sessions_cols)
                orders_min, orders_max = calculate_group_min_max(formatted_display_df, orders_cols)
                cvr_min, cvr_max = calculate_group_min_max(formatted_display_df, cvr_cols)

                # 定義通用熱力圖背景色函數
                def apply_heatmap(col, target_cols, light_rgb, dark_rgb, group_min, group_max):
                    """為指定欄位添加熱力圖背景，並根據背景明度調整字體顏色

                    Args:
                        col: 欄位資料
                        target_cols: 目標欄位列表
                        light_rgb: 淺色 RGB 元組 (r, g, b)
                        dark_rgb: 深色 RGB 元組 (r, g, b)
                        group_min: 該組欄位的全局最小值
                        group_max: 該組欄位的全局最大值
                    """
                    if col.name not in target_cols:
                        return [''] * len(col)

                    # 檢查是否有有效的最小最大值
                    if group_min is None or group_max is None:
                        return [''] * len(col)

                    # 提取數值（移除格式化的 $、逗號和 % 符號）
                    numeric_values = []
                    for val in col:
                        try:
                            if isinstance(val, str):
                                # 移除 $、逗號、% 符號和空格
                                numeric_val = float(val.replace('$', '').replace(',', '').replace('%', '').strip())
                            else:
                                numeric_val = float(val) if pd.notna(val) else 0
                            numeric_values.append(numeric_val)
                        except:
                            numeric_values.append(0)

                    # 為每個值生成背景色和字體顏色
                    styles = []
                    for val in numeric_values:
                        if val <= 0:
                            styles.append('')
                        else:
                            # 正規化到 0-1 之間（使用整組的最小最大值）
                            if group_max > group_min:
                                normalized = (val - group_min) / (group_max - group_min)
                            else:
                                normalized = 0.5

                            # 使用線性插值計算顏色
                            r = int(light_rgb[0] - (light_rgb[0] - dark_rgb[0]) * normalized)
                            g = int(light_rgb[1] - (light_rgb[1] - dark_rgb[1]) * normalized)
                            b = int(light_rgb[2] - (light_rgb[2] - dark_rgb[2]) * normalized)

                            # 計算明度 (luminance) 來決定字體顏色
                            # 使用公式: luminance = 0.299*R + 0.587*G + 0.114*B
                            luminance = 0.299 * r + 0.587 * g + 0.114 * b

                            # 如果背景較亮（luminance > 128），使用深色字體；否則使用淺色字體
                            text_color = 'black' if luminance > 128 else 'white'

                            bg_color = f'rgb({r}, {g}, {b})'
                            styles.append(f'background-color: {bg_color}; color: {text_color}')

                    return styles

                # 應用樣式
                styled_df = formatted_display_df.style

                # 應用 MoM/YoY 文字顏色
                if mom_yoy_cols:
                    styled_df = styled_df.apply(lambda x: [color_mom_yoy(v) if x.name in mom_yoy_cols else '' for v in x], axis=0)

                if sales_percentage_cols:
                    styled_df = styled_df.apply(lambda x: apply_heatmap(x, sales_percentage_cols, (227, 242, 253), (25, 118, 210), sales_percentage_min, sales_percentage_max), axis=0)

                # 應用 Sales 熱力圖背景色（藍色系：淺藍 #E3F2FD 到深藍 #1976D2）
                if sales_cols:
                    styled_df = styled_df.apply(lambda x: apply_heatmap(x, sales_cols, (227, 242, 253), (25, 118, 210), sales_min, sales_max), axis=0)

                # 應用 Sessions 熱力圖背景色（綠色系：淺綠 #E1F5E0 到深綠 #2E7D32）
                if sessions_cols:
                    styled_df = styled_df.apply(lambda x: apply_heatmap(x, sessions_cols, (225, 245, 224), (46, 125, 50), sessions_min, sessions_max), axis=0)

                # 應用 Orders 熱力圖背景色（紫色系：很淡紫 #F3E5F5 到中紫 #9C27B0）
                if orders_cols:
                    styled_df = styled_df.apply(lambda x: apply_heatmap(x, orders_cols, (246, 235, 255), (186, 102, 255), orders_min, orders_max), axis=0)

                # 應用 CVR 熱力圖背景色（橘黃色系：淺橘黃 #FFF3E0 到深橘 #F57C00）
                if cvr_cols:
                    styled_df = styled_df.apply(lambda x: apply_heatmap(x, cvr_cols, (255, 243, 224), (245, 124, 0), cvr_min, cvr_max), axis=0)


                def highlight_woc(val):
                    """針對 WOC 欄位條件上色"""
                    if float(val) <= 4:
                        return "background-color: pink; color: red;"
                    elif float(val) > 8:
                        return "color: red;"
                    else:
                        return ""

                styled_df = styled_df.applymap(highlight_woc, subset=["WOC"])

                st.dataframe(styled_df, use_container_width=True)
            else:
                st.warning("無可用的 Sales Contribution % 資料")
        else:
            st.warning("未找到 Sales Contribution % 欄位")

    # ==================== Tab 2: 趨勢分析 ====================
    with tab2:
        # 檢查是否有載入 ASIN Trend 資料
        if "ASIN Trend (YTD)" in loaded_data:
            trend_df = loaded_data["ASIN Trend (YTD)"]

            if trend_df is not None and not trend_df.empty:
                # 確認第一欄是 Child ASIN
                if 'Child ASIN' not in trend_df.columns:
                    # 假設第一欄是 ASIN
                    trend_df.rename(columns={trend_df.columns[0]: 'Child ASIN'}, inplace=True)

                # 取得所有月份欄位（只保留符合日期格式的欄位，如 2025-01）
                import re
                month_pattern = re.compile(r'^\d{4}-\d{2}$')  # 匹配 YYYY-MM 格式
                month_columns = [col for col in trend_df.columns
                                if month_pattern.match(str(col))]

                if month_columns:
                    # 計算最新「完整」月份的銷售額（用於排序）
                    # 例如：現在是 2/2，最新完整月份應該是 1 月，而不是 2 月
                    from datetime import datetime
                    today = datetime.now()
                    # 取得上個月的年月（最新完整月份）
                    if today.month == 1:
                        last_complete_year = today.year - 1
                        last_complete_month = 12
                    else:
                        last_complete_year = today.year
                        last_complete_month = today.month - 1
                    last_complete_month_str = f"{last_complete_year}-{last_complete_month:02d}"
                    
                    # 如果最新完整月份存在於資料中，使用它；否則使用資料中最後一個月份
                    if last_complete_month_str in month_columns:
                        latest_month = last_complete_month_str
                    else:
                        latest_month = month_columns[-1]
                    
                    trend_df['_latest_numeric'] = pd.to_numeric(trend_df[latest_month], errors='coerce').fillna(0)

                    # 計算 YTD 總銷售額
                    trend_df['_ytd_total'] = trend_df[month_columns].apply(
                        lambda row: pd.to_numeric(row, errors='coerce').sum(), axis=1
                    )

                    # 嘗試從 Asin Report 取得 Title 對照表
                    asin_title_map = {}
                    if "Asin Report" in loaded_data and loaded_data["Asin Report"] is not None:
                        asin_report_df = loaded_data["Asin Report"]
                        if 'Child ASIN' in asin_report_df.columns and 'Title' in asin_report_df.columns:
                            asin_title_map = dict(zip(asin_report_df['Child ASIN'], asin_report_df['Title']))

                    # 取得最新月份 TOP 10 ASIN（用於表格顯示）
                    top_10_latest_df = trend_df.nlargest(10, '_latest_numeric')[['Child ASIN', latest_month]].copy()
                    top_10_latest_df.columns = ['ASIN', 'Sales']
                    # 加入 Title 欄位（保留完整內容，由 column_config 控制顯示）
                    top_10_latest_df.insert(1, 'Title', top_10_latest_df['ASIN'].map(asin_title_map).fillna('-'))
                    top_10_latest_df['Sales'] = top_10_latest_df['Sales'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "-")

                    # 取得 YTD TOP 10 ASIN（用於表格顯示）
                    top_10_ytd_df = trend_df.nlargest(10, '_ytd_total')[['Child ASIN', '_ytd_total']].copy()
                    top_10_ytd_df.columns = ['ASIN', 'Sales']
                    # 加入 Title 欄位（保留完整內容，由 column_config 控制顯示）
                    top_10_ytd_df.insert(1, 'Title', top_10_ytd_df['ASIN'].map(asin_title_map).fillna('-'))
                    top_10_ytd_df['Sales'] = top_10_ytd_df['Sales'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "-")

                    # 預設顯示的 ASIN（兩種模式都只取前 3 名）
                    top_3_latest = trend_df.nlargest(3, '_latest_numeric')['Child ASIN'].tolist()
                    top_3_ytd = trend_df.nlargest(3, '_ytd_total')['Child ASIN'].tolist()

                    # ASIN 選擇器與趨勢圖（放在前面）
                    st.markdown("**📈 銷售趨勢圖**")

                    # 預設顯示模式切換
                    default_mode = st.radio(
                        "預設顯示模式",
                        ["最新月份 TOP 3", "YTD TOP 3"],
                        horizontal=True,
                        key="asin_default_mode"
                    )

                    # 表格欄位設定（Title 欄位預設較窄，可拖曳擴展）
                    column_config = {
                        "ASIN": st.column_config.TextColumn("ASIN", width="small"),
                        "Title": st.column_config.TextColumn("Title", width="medium", help="拖曳欄位邊框可顯示更多內容"),
                        "Sales": st.column_config.TextColumn("Sales", width="small")
                    }

                    # 顯示 TOP 10 表格（並排）
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**📊 最新月份 TOP 10** ({latest_month})")
                        st.dataframe(top_10_latest_df, use_container_width=True, hide_index=True, column_config=column_config)
                    with col2:
                        st.markdown("**🏆 YTD TOP 10**")
                        st.dataframe(top_10_ytd_df, use_container_width=True, hide_index=True, column_config=column_config)

                    # 根據模式決定預設 ASIN（都只選 3 個）
                    if default_mode == "最新月份 TOP 3":
                        default_asins = top_3_latest
                    else:
                        default_asins = top_3_ytd

                    # 多選框 - 根據選擇的模式預設 ASIN
                    selected_asins = st.multiselect(
                        "選擇要顯示的 ASIN（可多選）",
                        options=trend_df['Child ASIN'].tolist(),
                        default=default_asins,
                        key="asin_trend_selector"
                    )

                    if selected_asins:
                        # 準備繪圖資料 - 轉換為 Long Format
                        plot_data = []
                        for asin in selected_asins:
                            asin_row = trend_df[trend_df['Child ASIN'] == asin]
                            if not asin_row.empty:
                                for month in month_columns:
                                    sales = pd.to_numeric(asin_row[month].iloc[0], errors='coerce')
                                    if pd.notna(sales):
                                        # 對數刻度時，將 0 轉為 None 讓線條跳過該點
                                        plot_data.append({
                                            'Child ASIN': asin,
                                            'Month': month,
                                            'Sales': sales if sales > 0 else None
                                        })

                        plot_df = pd.DataFrame(plot_data)

                        if not plot_df.empty:
                            import plotly.express as px

                            # Y軸刻度選項
                            use_log_scale = st.checkbox(
                                "使用對數刻度 (Log Scale)",
                                value=True,
                                help="當 ASIN 銷售額差異大時，使用對數刻度可讓所有趨勢線更清晰可見",
                                key="asin_trend_log_scale"
                            )

                            # 繪製折線圖
                            fig = px.line(
                                plot_df,
                                x='Month',
                                y='Sales',
                                color='Child ASIN',
                                markers=True,
                                title='ASIN 月度銷售趨勢',
                                labels={'Sales': 'Ordered Product Sales ($)', 'Month': '月份'},
                                log_y=use_log_scale
                            )

                            fig.update_layout(
                                hovermode='x unified',
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                )
                            )

                            fig.update_traces(
                                hovertemplate='<b>%{fullData.name}</b><br>Sales: $%{y:,.2f}<extra></extra>',
                                connectgaps=True  # 跳過 0 值點，連接前後資料
                            )

                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("選擇的 ASIN 沒有有效的銷售資料")
                    else:
                        st.info("請選擇至少一個 ASIN 來顯示趨勢圖")

                    # 顯示資料表（放在趨勢圖後面）
                    st.markdown("---")
                    st.markdown("**📊 月度銷售資料表**")
                    # 只顯示 Child ASIN 和月份欄位，排除所有輔助欄位
                    display_columns = ['Child ASIN'] + month_columns
                    display_df = trend_df[display_columns].copy()
                    # 格式化月份欄位為 $xxx,xxx 格式
                    for col in month_columns:
                        display_df[col] = pd.to_numeric(display_df[col], errors='coerce').apply(
                            lambda x: f"${x:,.0f}" if pd.notna(x) else "-"
                        )
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.warning("檔案中沒有找到月份欄位")
            else:
                st.warning("無法載入趨勢資料或資料為空")
        else:
            st.info("""
            📌 **如何使用 ASIN 趨勢分析：**

            1. 使用油猴腳本的「📈 下載 ASIN 趨勢 (YTD)」按鈕下載趨勢資料
            2. 前往 **Upload** 頁面上傳 ASIN Trend (YTD) 檔案
            3. 資料會自動顯示在此區塊
            """)

# Advertising & Merchandising 區塊
if "P0 MCID MBR" in loaded_data:
    st.markdown("---")
    st.header("📢 Advertising & Merchandising")

    ads_df = loaded_data["P0 MCID MBR"]

    # CID 下拉選單（必選）
    if 'merchant_customer_id' in ads_df.columns:
        # 取得所有唯一的 merchant_customer_id，並清洗格式
        available_cids = ads_df['merchant_customer_id'].dropna().unique()

        # 清洗 CID 格式（去除 .0）
        cleaned_cids = []
        for cid in available_cids:
            try:
                # 如果是數值，轉換為整數字串
                if pd.notna(cid):
                    cleaned_cid = str(int(float(cid)))
                    cleaned_cids.append(cleaned_cid)
            except:
                # 如果轉換失敗，使用原始字串
                cleaned_cids.append(str(cid))

        # 排序並去重
        cleaned_cids = sorted(list(set(cleaned_cids)))

        # 根據賣家 MCID 自動預選
        auto_cid_index = 0  # 預設「請選擇...」
        if seller_list and current_mcid:
            # 嘗試在 cleaned_cids 中找到匹配的 MCID
            for idx, cid in enumerate(cleaned_cids):
                if cid == current_mcid or cid == str(current_mcid).strip():
                    auto_cid_index = idx + 1  # +1 因為第一個是「請選擇...」
                    break

        # 顯示下拉選單
        cid_input = st.selectbox(
            "選擇 CID (merchant_customer_id):",
            options=["請選擇..."] + cleaned_cids,
            index=auto_cid_index,
            key="ads_cid_selector"
        )

        # 如果自動匹配成功，不需要額外提示

        # 如果沒有選擇 CID，顯示提示並停止後續處理
        if cid_input == "請選擇...":
            st.warning("⚠️ 請先選擇一個 CID (merchant_customer_id) 才能查看數據")
            st.stop()
    else:
        st.warning("未找到 merchant_customer_id 欄位")
        st.stop()

    # 根據 CID 篩選數據
    if 'merchant_customer_id' in ads_df.columns:
        # 更靈活的CID匹配邏輯
        def match_cid(df_cid, input_cid):
            if pd.isna(df_cid):
                return False
            try:
                # 多種格式轉換和匹配
                df_str = str(df_cid).strip().replace('.0', '')
                input_str = str(input_cid).strip()

                # 字串匹配
                if df_str == input_str or df_str.lower() == input_str.lower():
                    return True

                # 數值匹配
                try:
                    df_num = float(df_cid)
                    input_num = float(input_cid)
                    if df_num == input_num:
                        return True
                except:
                    pass

                # 整數匹配
                try:
                    df_int = int(float(df_cid))
                    input_int = int(float(input_cid))
                    if df_int == input_int:
                        return True
                except:
                    pass

                return False
            except:
                return False

        cid_filtered_df = ads_df[ads_df['merchant_customer_id'].apply(lambda x: match_cid(x, cid_input))].copy()

        if cid_filtered_df.empty:
            # 顯示可用的 CID 列表供參考
            available_cids = ads_df['merchant_customer_id'].dropna().unique()[:10]
            st.error(f"❌ 找不到 CID '{cid_input}' 的數據")
            st.info(f"💡 可用的 CID 範例: {list(available_cids)}")
            st.stop()
    else:
        st.warning("未找到 merchant_customer_id 欄位")
        st.stop()

    # Marketplace ID 篩選器（預設選第一個）
    marketplace_filter = None
    if 'marketplace_id' in cid_filtered_df.columns:
        available_marketplaces = sorted(cid_filtered_df['marketplace_id'].dropna().unique())
        if available_marketplaces:
            marketplace_filter = st.selectbox(
                "選擇 Marketplace",
                options=list(available_marketplaces),
                index=0,
                key="ads_marketplace_selector"
            )
        else:
            st.warning("未找到任何 Marketplace ID")
            st.stop()
    else:
        st.warning("未找到 marketplace_id 欄位")
        st.stop()

    # 年月選擇器 - 使用 YYYY-MM 格式
    if 'calendar_year' in cid_filtered_df.columns and 'calendar_month' in cid_filtered_df.columns:
        # 創建年月組合列表
        ads_df_temp = cid_filtered_df.dropna(subset=['calendar_year', 'calendar_month'])
        if not ads_df_temp.empty:
            # 創建 YYYY-MM 格式的選項
            year_month_combinations = ads_df_temp.apply(
                lambda row: f"{int(row['calendar_year'])}-{int(row['calendar_month']):02d}",
                axis=1
            ).unique()
            available_year_months = sorted(year_month_combinations, reverse=True)

            selected_year_month = st.selectbox(
                "選擇年月",
                options=available_year_months,
                index=0,
                key="ads_year_month_selector"
            )

            # 解析選擇的年月
            selected_year = int(selected_year_month.split('-')[0])
            selected_month = int(selected_year_month.split('-')[1])
        else:
            st.warning("未找到有效的年月資料")
            selected_year = 2025
            selected_month = 1
    else:
        st.warning("未找到 calendar_year 或 calendar_month 欄位")
        selected_year = 2025
        selected_month = 1

    # 篩選數據 - 先根據 CID 和 marketplace_id 篩選
    filtered_ads_df = cid_filtered_df[cid_filtered_df['marketplace_id'] == marketplace_filter].copy()

    # 再根據年月篩選
    if 'calendar_year' in cid_filtered_df.columns:
        filtered_ads_df = filtered_ads_df[filtered_ads_df['calendar_year'] == selected_year]
    if 'calendar_month' in cid_filtered_df.columns:
        filtered_ads_df = filtered_ads_df[filtered_ads_df['calendar_month'] == selected_month]

    # 第一排 KPI
    with st.container():
        widget_row1_col1, widget_row1_col2, widget_row1_col3 = st.columns(3)

    # Widget 1: TACOS
    with widget_row1_col1:
        # 計算當前 TACOS
        tacos_value = 0
        tacos_yoy = None
        tacos_mom = None

        if 'mtd_sa_revenue_usd' in cid_filtered_df.columns and 'mtd_ord_gms' in cid_filtered_df.columns:
            # 當前月份
            current_mask = (cid_filtered_df['calendar_year'] == selected_year) & (cid_filtered_df['calendar_month'] == selected_month)
            current_ads = cid_filtered_df[current_mask]['mtd_sa_revenue_usd'].dropna().sum()
            current_gms = cid_filtered_df[current_mask]['mtd_ord_gms'].dropna().sum()

            if current_gms > 0:
                tacos_value = (current_ads / current_gms) * 100

                # 計算去年同月 (YoY)
                last_year = selected_year - 1
                last_year_mask = (cid_filtered_df['calendar_year'] == last_year) & (cid_filtered_df['calendar_month'] == selected_month)
                last_year_ads = cid_filtered_df[last_year_mask]['mtd_sa_revenue_usd'].dropna().sum()
                last_year_gms = cid_filtered_df[last_year_mask]['mtd_ord_gms'].dropna().sum()

                if last_year_gms > 0:
                    last_year_tacos = (last_year_ads / last_year_gms) * 100
                    if last_year_tacos != 0:
                        tacos_yoy = ((tacos_value - last_year_tacos) / last_year_tacos) * 100

                # 計算上個月 (MoM)
                if selected_month == 1:
                    last_month = 12
                    last_month_year = selected_year - 1
                else:
                    last_month = selected_month - 1
                    last_month_year = selected_year

                last_month_mask = (cid_filtered_df['calendar_year'] == last_month_year) & (cid_filtered_df['calendar_month'] == last_month)
                last_month_ads = cid_filtered_df[last_month_mask]['mtd_sa_revenue_usd'].dropna().sum()
                last_month_gms = cid_filtered_df[last_month_mask]['mtd_ord_gms'].dropna().sum()

                if last_month_gms > 0:
                    last_month_tacos = (last_month_ads / last_month_gms) * 100
                    if last_month_tacos != 0:
                        tacos_mom = ((tacos_value - last_month_tacos) / last_month_tacos) * 100

        render_kpi_widget("TACOS", round(tacos_value, 2) if tacos_value > 0 else 0, tacos_yoy, tacos_mom, suffix="%")

    # Widget 2: Ads spending
    with widget_row1_col2:
        ads_spending_value, ads_spending_yoy, ads_spending_mom = calculate_yoy_mom_from_df(
            cid_filtered_df, 'mtd_sa_revenue_usd', selected_year, selected_month
        )
        render_kpi_widget("Ads spending", round(ads_spending_value) if isinstance(ads_spending_value, (int, float)) else ads_spending_value, ads_spending_yoy, ads_spending_mom, prefix="$")

    # Widget 3: SP ops
    with widget_row1_col3:
        sp_ops_value, sp_ops_yoy, sp_ops_mom = calculate_yoy_mom_from_df(
            cid_filtered_df, 'mtd_sa_attributed_ops_usd', selected_year, selected_month
        )
        render_kpi_widget("SP ops", round(sp_ops_value) if isinstance(sp_ops_value, (int, float)) else sp_ops_value, sp_ops_yoy, sp_ops_mom, prefix="$")

    # TACOS 折線圖 (2024 vs 2025)
    with st.container():
        st.markdown("<div style='margin-top: 30px; margin-bottom: 30px;'></div>", unsafe_allow_html=True)

        if 'mtd_ord_gms' in cid_filtered_df.columns and 'mtd_sa_revenue_usd' in cid_filtered_df.columns:
            import plotly.graph_objects as go

            # 準備數據：按年和月分組並計算 TACOS
            if 'calendar_year' in cid_filtered_df.columns and 'calendar_month' in cid_filtered_df.columns:
                tacos_df_chart = cid_filtered_df.copy()

                # 按年份和月份分組
                grouped_tacos = tacos_df_chart.groupby(['calendar_year', 'calendar_month']).agg({
                    'mtd_ord_gms': 'sum',
                    'mtd_sa_revenue_usd': 'sum'
                }).reset_index()

                # 計算 TACOS (%)
                grouped_tacos['tacos'] = (grouped_tacos['mtd_sa_revenue_usd'] / grouped_tacos['mtd_ord_gms'] * 100).fillna(0)

                # 獲取所有可用的年份
                available_years = sorted(grouped_tacos['calendar_year'].unique())

                if len(available_years) >= 1:
                    # 月份對應
                    months_map = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                                  7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
                    month_order = list(months_map.values())

                    # 準備繪圖數據
                    plot_data = []
                    for month_num, month_name in months_map.items():
                        row_data = {'Month': month_name}
                        for year in available_years:
                            year_month_data = grouped_tacos[
                                (grouped_tacos['calendar_year'] == year) &
                                (grouped_tacos['calendar_month'] == month_num)
                            ]
                            if not year_month_data.empty:
                                row_data[str(int(year))] = year_month_data['tacos'].iloc[0]
                            else:
                                row_data[str(int(year))] = None
                        plot_data.append(row_data)

                    plot_df = pd.DataFrame(plot_data)

                    # 創建圖表
                    fig_tacos = go.Figure()

                    # 與 Business Metrics Trends 保持一致的顏色配置（使用 Plotly 默認顏色順序）
                    latest_year = available_years[-1]  # 最新年份
                    last_year = available_years[-2] if len(available_years) >= 2 else None  # 前一年

                    # 先添加最新年份
                    latest_year_str = str(int(latest_year))
                    if latest_year_str in plot_df.columns:
                        fig_tacos.add_trace(go.Scatter(
                            x=plot_df['Month'],
                            y=plot_df[latest_year_str],
                            name=latest_year_str,
                            mode='lines+markers'
                        ))

                    # 再添加前一年
                    if last_year is not None:
                        last_year_str = str(int(last_year))
                        if last_year_str in plot_df.columns:
                            fig_tacos.add_trace(go.Scatter(
                                x=plot_df['Month'],
                                y=plot_df[last_year_str],
                                name=last_year_str,
                                mode='lines+markers'
                            ))

                    # 如果有更多年份
                    if len(available_years) > 2:
                        for year in available_years[:-2]:
                            year_str = str(int(year))
                            if year_str in plot_df.columns:
                                fig_tacos.add_trace(go.Scatter(
                                    x=plot_df['Month'],
                                    y=plot_df[year_str],
                                    name=year_str,
                                    mode='lines+markers'
                                ))

                    # 設置布局
                    fig_tacos.update_layout(
                        title="TACOS Trend (YoY Comparison)",
                        xaxis_title="Month",
                        yaxis_title="TACOS (%)",
                        hovermode='x unified',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                            title_text='Year'
                        ),
                        height=350,
                        yaxis=dict(separatethousands=True),
                        margin=dict(l=40, r=40, t=40, b=40)
                    )

                    st.plotly_chart(fig_tacos, use_container_width=True)

    # Revenue & Ads Spending 折線圖
    with st.container():
        st.markdown("<div style='margin-top: 30px; margin-bottom: 30px;'></div>", unsafe_allow_html=True)

        if 'mtd_ord_gms' in cid_filtered_df.columns and 'mtd_sa_revenue_usd' in cid_filtered_df.columns:
            import plotly.graph_objects as go

            # 準備數據：按年月分組並加總
            if 'calendar_year' in cid_filtered_df.columns and 'calendar_month' in cid_filtered_df.columns:
                # 創建年月欄位用於排序和顯示
                ads_df_chart = cid_filtered_df.copy()
                ads_df_chart['year_month'] = ads_df_chart.apply(
                    lambda row: f"{int(row['calendar_year'])}-{int(row['calendar_month']):02d}"
                    if pd.notna(row['calendar_year']) and pd.notna(row['calendar_month']) else None,
                    axis=1
                )

                # 移除沒有年月的資料
                ads_df_chart = ads_df_chart.dropna(subset=['year_month'])

                # 按年月分組並加總
                grouped_data = ads_df_chart.groupby('year_month').agg({
                    'mtd_ord_gms': 'sum',
                    'mtd_sa_revenue_usd': 'sum'
                }).reset_index()

                # 排序
                grouped_data = grouped_data.sort_values('year_month')

                if not grouped_data.empty:
                    # 創建圖表
                    fig = go.Figure()

                    # Revenue 線 (藍色)
                    fig.add_trace(go.Scatter(
                        x=grouped_data['year_month'],
                        y=grouped_data['mtd_ord_gms'],
                        name='Revenue',
                        mode='lines+markers',
                        line=dict(color='#1f77b4', width=2),
                        marker=dict(size=6)
                    ))

                    # Ads Spending 線 (橘色)
                    fig.add_trace(go.Scatter(
                        x=grouped_data['year_month'],
                        y=grouped_data['mtd_sa_revenue_usd'],
                        name='Ads Spending',
                        mode='lines+markers',
                        line=dict(color='#ff7f0e', width=2),
                        marker=dict(size=6)
                    ))

                    # 設置布局
                    fig.update_layout(
                        xaxis_title="Year-Month",
                        yaxis_title="Amount ($)",
                        hovermode='x unified',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        height=350,
                        yaxis=dict(separatethousands=True)
                    )

                    st.plotly_chart(fig, use_container_width=True)

    # 第二排 KPI
    with st.container():
        widget_row2_col1, widget_row2_col2, widget_row2_col3 = st.columns(3)

    # 定義 Promotion/Deal/Coupon 指標配置
    merchandising_metrics = [
        {
            'column': widget_row2_col1,
            'title': 'Promotion',
            'column_name': 'mtd_promotion_count'
        },
        {
            'column': widget_row2_col2,
            'title': 'Deal',
            'column_name': 'mtd_deal_count'
        },
        {
            'column': widget_row2_col3,
            'title': 'Coupon',
            'column_name': 'mtd_coupon_count'
        }
    ]

    # 批量渲染第二排指標
    for metric in merchandising_metrics:
        with metric['column']:
            value, yoy, mom = calculate_yoy_mom_from_df(
                cid_filtered_df, metric['column_name'], selected_year, selected_month
            )
            render_kpi_widget(metric['title'], round(value) if isinstance(value, (int, float)) else value, yoy, mom)

    # 第三排 KPI
    with st.container():
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        widget_row3_col1, widget_row3_col2, widget_row3_col3 = st.columns(3)

    # 計算總金額用於占比計算
    def get_total_gms(df, year, month):
        if 'mtd_ord_gms' in df.columns:
            mask = (df['calendar_year'] == year) & (df['calendar_month'] == month)
            data = df[mask]['mtd_ord_gms'].dropna()
            return data.sum() if not data.empty else 0
        return 0

    total_gms = get_total_gms(cid_filtered_df, selected_year, selected_month)

    # 定義 OPS 指標配置（帶百分比）
    ops_metrics = [
        {
            'column': widget_row3_col1,
            'title': 'Promotion OPS',
            'column_name': 'mtd_promotion_ops'
        },
        {
            'column': widget_row3_col2,
            'title': 'Deal OPS',
            'column_name': 'mtd_deal_ops'
        },
        {
            'column': widget_row3_col3,
            'title': 'Coupon OPS',
            'column_name': 'mtd_coupon_ops'
        }
    ]

    # 批量渲染第三排指標（帶百分比）
    for metric in ops_metrics:
        with metric['column']:
            value, yoy, mom = calculate_yoy_mom_from_df(
                cid_filtered_df, metric['column_name'], selected_year, selected_month
            )
            percentage = (value / total_gms * 100) if total_gms > 0 else 0
            render_kpi_widget_with_percentage(metric['title'], value, percentage, yoy, mom)

