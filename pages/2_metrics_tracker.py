import streamlit as st
from utils import list_uploaded_files, load_data, normalize_customer_id
import plotly.graph_objects as go


def render_kpi(title, value, yoy=None, mom=None):
    """渲染單一 KPI Widget"""
    def format_change(val):
        if val is None:
            return "-"
        if val > 0:
            return f"<span style='color:green'>▲ {val:.1f}%</span>"
        elif val < 0:
            return f"<span style='color:red'>▼ {abs(val):.1f}%</span>"
        else:
            return f"<span style='color:gray'>0.0%</span>"

    yoy_html = format_change(yoy)
    mom_html = format_change(mom)

    st.markdown(f"""
    <style>
    .metrics-kpi-widget {{
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: left;
        height: 120px;
        overflow: hidden;
    }}
    .metrics-kpi-title {{
        font-size: clamp(12px, 1.5vw, 17px);
        color: #555;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .metrics-kpi-value {{
        font-size: clamp(20px, 2.8vw, 32px);
        font-weight: 700;
        margin: 5px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .metrics-kpi-change {{
        font-size: clamp(11px, 1.3vw, 15px);
        color: #888;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    </style>
    <div class="metrics-kpi-widget">
      <div class="metrics-kpi-title">{title}</div>
      <div class="metrics-kpi-value">{value:,.0f}</div>
      <div class="metrics-kpi-change">
        YoY {yoy_html} &nbsp;&nbsp; MoM {mom_html}
      </div>
    </div>
    """, unsafe_allow_html=True)


def show_customer_id_filter_tab(df, selected_file):
    """顯示 Customer ID 篩選 tab 的內容"""
    # 檢查是否有 merchant_customer_id 欄位
    if 'merchant_customer_id' not in df.columns:
        st.error("❌ 數據中沒有找到 'merchant_customer_id' 欄位")
        return

    # -------------------------
    # 🔹 Customer ID 篩選
    # -------------------------
    customer_input = st.text_input(
        "🔍 輸入 Merchant Customer ID (逗號分隔)",
        placeholder="例如: 12345,67890,11111",
        help="可輸入多個Customer ID，用逗號分隔"
    )

    # -------------------------
    # 🔹 Marketplace ID 篩選
    # -------------------------
    marketplace_filter = None
    if 'marketplace_id' in df.columns:
        available_marketplaces = sorted(df['marketplace_id'].dropna().unique().tolist())
        available_marketplaces_int = [int(m) for m in available_marketplaces]
        if available_marketplaces:
            marketplace_filter = st.multiselect(
                "🌍 選擇 Marketplace ID",
                options=available_marketplaces_int,
                help="可選擇多個 Marketplace"
            )

    # -------------------------
    # 🔹 Calendar Year 篩選
    # -------------------------
    year_filter = None
    if 'calendar_year' in df.columns:
        available_years = sorted(df['calendar_year'].dropna().unique().tolist())
        available_years_int = [int(y) for y in available_years]
        if available_years:
            year_filter = st.multiselect(
                "📅 選擇 Calendar Year",
                options=available_years_int,
                help="可選擇多個年份"
            )

    # -------------------------
    # 🔹 Calendar Month 篩選
    # -------------------------
    month_filter = None
    if 'calendar_month' in df.columns:
        available_months = sorted(df['calendar_month'].dropna().unique().tolist())
        available_months_int = [int(m) for m in available_months]
        if available_months:
            month_filter = st.multiselect(
                "📆 選擇 Calendar Month",
                options=available_months_int,
                help="可選擇多個月份"
            )

    # -------------------------
    # 🔹 根據 Customer ID、Marketplace ID、Year 和 Month 過濾數據
    # -------------------------
    filtered_df = df.copy()
    chart_df = df.copy()  # 用於圖表的數據，不受年月篩選影響
    has_filter_input = False

    if customer_input:
        ids = [x.strip() for x in customer_input.split(",") if x.strip()]
        if ids:
            # 正規化 merchant_customer_id 欄位（處理浮點數格式如 587171716002.0 -> 587171716002）
            filtered_df['_normalized_mcid'] = normalize_customer_id(filtered_df['merchant_customer_id'])
            chart_df['_normalized_mcid'] = normalize_customer_id(chart_df['merchant_customer_id'])
            filtered_df = filtered_df[filtered_df['_normalized_mcid'].isin(ids)]
            chart_df = chart_df[chart_df['_normalized_mcid'].isin(ids)]
            # 移除暫時欄位
            filtered_df = filtered_df.drop(columns=['_normalized_mcid'])
            chart_df = chart_df.drop(columns=['_normalized_mcid'])
            has_filter_input = True
        else:
            st.warning("請輸入有效的Customer ID")

    # 套用 Marketplace 篩選
    if marketplace_filter:
        filtered_df = filtered_df[filtered_df['marketplace_id'].isin(marketplace_filter)]
        chart_df = chart_df[chart_df['marketplace_id'].isin(marketplace_filter)]
        has_filter_input = True

    # 套用 Calendar Year 篩選（只套用到表格數據，不套用到圖表數據）
    if year_filter:
        filtered_df = filtered_df[filtered_df['calendar_year'].isin(year_filter)]
        has_filter_input = True

    # 套用 Calendar Month 篩選（只套用到表格數據，不套用到圖表數據）
    if month_filter:
        filtered_df = filtered_df[filtered_df['calendar_month'].isin(month_filter)]
        has_filter_input = True

    # 加入間距
    st.markdown("<br>", unsafe_allow_html=True)

    # 當前年月
    import datetime
    now = datetime.datetime.now()
    current_year = now.year
    current_month = now.month

    # -------------------------
    # 🔹 選擇要顯示的欄位功能
    # -------------------------
    if not filtered_df.empty:
        # 按最重要的數值欄位排序（如果存在）
        display_df = filtered_df.copy()
        if 'mtd_new_fba_ba_90d' in display_df.columns:
            display_df = display_df.sort_values('mtd_new_fba_ba_90d', ascending=False)

        # 選擇要顯示的欄位
        available_columns = display_df.columns.tolist()

        # 預設選擇重要欄位
        default_columns = []
        # 按照指定順序：1.year 2.month/week 3.merchant_customer_id 4.merchant_name 5.opportunity_owner 6.ytd_order_gms 7.mtd_ord_gms 8.wtd_ord_gms
        priority_fields = [
            'calendar_year', 'reporting_year',  # year
            'calendar_month', 'reporting_week_of_year',  # month or week
            'merchant_customer_id',  # merchant_customer_id
            'merchant_name',  # merchant_name
            'nsr_opportunity_owner',  # opportunity owner
            'ytd_ord_gms',  # ytd_order_gms
            'mtd_ord_gms', 'wtd_ord_gms'  # mtd/wtd gms
        ]
        
        for field in priority_fields:
            if field in available_columns and field not in default_columns:
                default_columns.append(field)
                if len(default_columns) >= 8:
                    break

        selected_columns = st.multiselect(
            "選擇要顯示的欄位",
            options=available_columns,
            default=default_columns[:8],
            key="seller_performance_display_columns"
        )

        if selected_columns:
            preview_df = display_df[selected_columns].copy()

            # 加入排名欄位
            if 'mtd_new_fba_ba_90d' in preview_df.columns:
                preview_df.insert(0, '排名', range(1, len(preview_df) + 1))

            st.subheader("數據預覽")
            st.dataframe(preview_df.head(100), use_container_width=True)


        else:
            st.warning("請至少選擇一個欄位來顯示數據")

        # -------------------------
        # 🔹 圖表區域 - 只在有篩選條件時顯示
        # -------------------------
        if not has_filter_input:
            st.info("💡 請輸入 Merchant Customer ID 或選擇 Marketplace ID 來查看圖表")
        elif 'calendar_year' in chart_df.columns and 'calendar_month' in chart_df.columns:
            st.subheader("📈 趨勢圖表")

            # 找出可繪圖的數值欄位
            numeric_columns = chart_df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            # 移除時間欄位
            numeric_columns = [col for col in numeric_columns if col not in ['calendar_year', 'calendar_month', 'reporting_year', 'reporting_week_of_year']]

            if numeric_columns:
                # 欄位選擇和年份控制
                col_select, col_year = st.columns([2, 1])

                with col_select:
                    # 預設三個指標：mtd_ord_gms, mtd_TACoS, mtd_sa_revenue
                    default_trend_metrics = [m for m in ['mtd_ord_gms', 'mtd_TACoS', 'mtd_sa_revenue'] if m in numeric_columns]
                    if not default_trend_metrics:
                        default_trend_metrics = numeric_columns[:2]
                    selected_metrics = st.multiselect(
                        "選擇要顯示的指標",
                        options=numeric_columns,
                        default=default_trend_metrics,
                        help="每行最多顯示2個圖表，多的會換行顯示"
                    )

                with col_year:
                    # 動態取得資料中實際存在的年份
                    available_years = sorted(chart_df['calendar_year'].dropna().unique().tolist(), reverse=True)
                    st.write("**選擇年份:**")
                    selected_years = []
                    # 定義年份對應的顏色
                    year_colors = ['#2E86AB', '#F18F01', '#28A745', '#DC3545', '#6F42C1', '#17A2B8']
                    for idx, year in enumerate(available_years[:6]):  # 最多顯示6個年份
                        if st.checkbox(str(int(year)), value=(idx < 2), key=f"show_{int(year)}"):
                            selected_years.append(int(year))

                if selected_metrics:
                    # 不限制圖表數量，但每行最多2張
                    metrics_to_plot = selected_metrics

                    # 按每行2張的方式分組處理
                    for row_start in range(0, len(metrics_to_plot), 2):
                        row_metrics = metrics_to_plot[row_start:row_start + 2]

                        # 根據這一行的圖表數量決定佈局
                        if len(row_metrics) == 1:
                            chart_cols = st.columns([1, 1])  # 讓單張圖表佔一半寬度，另一半留空
                        else:  # 2張圖表
                            chart_cols = st.columns(2)

                        for i, metric in enumerate(row_metrics):
                            if metric in chart_df.columns:
                                with chart_cols[i]:
                                    fig = go.Figure()

                                    # 根據選擇的年份動態繪製
                                    for year_idx, year in enumerate(sorted(selected_years, reverse=True)):
                                        year_data = chart_df[chart_df['calendar_year'] == year]
                                        if not year_data.empty:
                                            monthly_data = year_data[['calendar_month', metric]].dropna().sort_values('calendar_month')
                                            if not monthly_data.empty:
                                                # 判斷是否為百分比或TACoS類型的欄位
                                                is_percentage = 'tacos' in metric.lower() or '%' in metric or 'rate' in metric.lower()
                                                text_format = f"{{val:.1f}}%" if is_percentage else "{val:,.0f}"
                                                
                                                # 取得對應顏色
                                                color = year_colors[year_idx % len(year_colors)]
                                                # 第一個年份（最新）在上方顯示文字，其他在下方
                                                text_position = 'top center' if year_idx == 0 else 'bottom center'

                                                fig.add_trace(go.Scatter(
                                                    x=monthly_data['calendar_month'],
                                                    y=monthly_data[metric],
                                                    mode='lines+markers+text',
                                                    name=f'{year}年',
                                                    text=[text_format.format(val=val) for val in monthly_data[metric]],
                                                    textposition=text_position,
                                                    textfont=dict(size=12, color=color),
                                                    line=dict(color=color, width=2, shape='spline'),
                                                    marker=dict(size=4, color=color, symbol='circle'),
                                                    cliponaxis=False
                                                ))

                                    # 格式化圖表標題和軸標籤
                                    display_metric = metric.replace('_', ' ').title()
                                    y_title = f"{display_metric} (%)" if 'tacos' in metric.lower() or '%' in metric else display_metric

                                    # 計算 y 軸範圍，上下各留 15% 空間給標籤
                                    all_y_vals = []
                                    for trace in fig.data:
                                        all_y_vals.extend(trace.y)
                                    if all_y_vals:
                                        y_min = min(all_y_vals)
                                        y_max = max(all_y_vals)
                                        y_range_span = y_max - y_min if y_max != y_min else max(abs(y_max) * 0.1, 1)
                                        y_axis_min = max(0, y_min - y_range_span * 0.15)
                                        y_axis_max = y_max + y_range_span * 0.18
                                        y_range = [y_axis_min, y_axis_max]
                                    else:
                                        y_range = None

                                    fig.update_layout(
                                        title=dict(text=display_metric, font=dict(size=14, color='#2c3e50'), x=0.5, y=0.98, yanchor='top'),
                                        xaxis=dict(
                                            title="月份", showgrid=True, gridcolor='#f0f0f0',
                                            tickfont=dict(size=10),
                                            tickmode='linear', dtick=1,
                                            range=[0.5, 12.5]
                                        ),
                                        yaxis=dict(
                                            title=y_title, showgrid=True, gridcolor='#f0f0f0',
                                            tickfont=dict(size=10),
                                            range=y_range,
                                        ),
                                        plot_bgcolor='white', paper_bgcolor='white',
                                        showlegend=True,
                                        legend=dict(
                                            orientation="h",
                                            yanchor="bottom",
                                            y=1.08,
                                            xanchor="center",
                                            x=0.5,
                                            font=dict(size=10, color='#2c3e50'),
                                            bgcolor='rgba(255,255,255,0.9)',
                                            bordercolor='#e0e0e0',
                                            borderwidth=1
                                        ),
                                        margin=dict(t=100, b=50, l=55, r=30),
                                        height=450
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("請選擇要顯示的指標")
            else:
                st.warning("沒有可用於繪圖的數值欄位")
    else:
        st.warning("⚠️ 沒有符合條件的數據")


st.set_page_config(page_title="Metrics Tracker", page_icon="📈", layout="wide")
st.title("📈 Metrics Tracker")

# 初始化 session_state 來保存數據
if 'performance_review_loaded_data' not in st.session_state:
    st.session_state.performance_review_loaded_data = None
if 'performance_review_filename' not in st.session_state:
    st.session_state.performance_review_filename = None

# 選擇已上傳的檔案（只顯示 P0 MCID MBR 類型的檔案）
files = list_uploaded_files("P0 MCID MBR")
if files:
    file_options = {f.name: f for f in files}
    selected_name = st.selectbox(
        "選擇 P0 MCID MBR 檔案",
        options=list(file_options.keys())
    )
    if selected_name:
        # 檢查是否需要重新加載檔案（檔案名稱改變了）
        if st.session_state.performance_review_filename != selected_name:
            # 檔案改變了，需要重新讀取
            selected_file = file_options[selected_name]
            df, error = load_data(selected_file)
            if error:
                st.error(error)
            elif df is not None and not df.empty:
                # 儲存到 session_state
                st.session_state.performance_review_loaded_data = df
                st.session_state.performance_review_filename = selected_name
                show_customer_id_filter_tab(df, {"name": selected_name, "size": selected_file.stat().st_size})
            else:
                st.warning("⚠️ 無法讀取檔案或檔案為空")
        else:
            # 使用快取的數據
            if st.session_state.performance_review_loaded_data is not None:
                df = st.session_state.performance_review_loaded_data
                selected_file = file_options[selected_name]
                show_customer_id_filter_tab(df, {"name": selected_name, "size": selected_file.stat().st_size})
else:
    st.info("目前 P0 MCID MBR 資料夾內沒有任何檔案")
