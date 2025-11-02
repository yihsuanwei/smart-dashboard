import streamlit as st
from utils import list_uploaded_files, load_data
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
    <div style=\"
        border:1px solid #e0e0e0; border-radius:10px; padding:15px;
        background-color:white; box-shadow:0 2px 5px rgba(0,0,0,0.05);
        text-align:left; height:120px;\">
      <div style=\"font-size:17px; color:#555;\">{title}</div>
      <div style=\"font-size:32px; font-weight:700; margin:5px 0;\">{value:,.0f}</div>
      <div style=\"font-size:15px; color:#888;\">
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
        if available_marketplaces:
            marketplace_filter = st.multiselect(
                "🌍 選擇 Marketplace ID",
                options=available_marketplaces,
                help="可選擇多個 Marketplace"
            )

    # -------------------------
    # 🔹 根據 Customer ID 和 Marketplace ID 過濾數據
    # -------------------------
    filtered_df = df.copy()

    if customer_input:
        ids = [x.strip() for x in customer_input.split(",") if x.strip()]
        if ids:
            filtered_df = filtered_df[filtered_df['merchant_customer_id'].astype(str).isin(ids)]
            st.info(f"已篩選出 {len(filtered_df)} 筆資料，包含 {len(ids)} 個Customer ID")
        else:
            st.warning("請輸入有效的Customer ID")

    # 套用 Marketplace 篩選
    if marketplace_filter:
        filtered_df = filtered_df[filtered_df['marketplace_id'].isin(marketplace_filter)]
        st.info(f"已篩選 Marketplace: {', '.join(map(str, marketplace_filter))}，剩餘 {len(filtered_df)} 筆資料")

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

        # 圖表區域 - 動態選擇欄位
        if 'calendar_year' in filtered_df.columns and 'calendar_month' in filtered_df.columns:
            st.subheader("📈 趨勢圖表")

            # 找出可繪圖的數值欄位
            numeric_columns = filtered_df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            # 移除時間欄位
            numeric_columns = [col for col in numeric_columns if col not in ['calendar_year', 'calendar_month', 'reporting_year', 'reporting_week_of_year']]

            if numeric_columns:
                # 欄位選擇和年份控制
                col_select, col_year = st.columns([2, 1])

                with col_select:
                    selected_metrics = st.multiselect(
                        "選擇要顯示的指標",
                        options=numeric_columns,
                        default=['mtd_ord_gms', 'mtd_TACoS'] if all(col in numeric_columns for col in ['mtd_ord_gms', 'mtd_TACoS']) else numeric_columns[:2],
                        help="每行最多顯示2個圖表，多的會換行顯示"
                    )

                with col_year:
                    st.write("**選擇年份:**")
                    show_2024 = st.checkbox("2024", value=True, key="show_2024")
                    show_2025 = st.checkbox("2025", value=True, key="show_2025")

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
                            if metric in filtered_df.columns:
                                with chart_cols[i]:
                                    fig = go.Figure()

                                    # 2025年資料
                                    if show_2025:
                                        current_year_data = filtered_df[filtered_df['calendar_year'] == current_year]
                                        if not current_year_data.empty:
                                            monthly_data = current_year_data[['calendar_month', metric]].dropna().sort_values('calendar_month')
                                            if not monthly_data.empty:
                                                # 判斷是否為百分比或TACoS類型的欄位
                                                is_percentage = 'tacos' in metric.lower() or '%' in metric or 'rate' in metric.lower()
                                                text_format = f"{{val:.1f}}%" if is_percentage else "{val:,.0f}"

                                                fig.add_trace(go.Scatter(
                                                    x=monthly_data['calendar_month'],
                                                    y=monthly_data[metric],
                                                    mode='lines+markers+text',
                                                    name=f'{current_year}年',
                                                    text=[text_format.format(val=val) for val in monthly_data[metric]],
                                                    textposition='top center',
                                                    textfont=dict(size=13, color='#2E86AB'),
                                                    line=dict(color='#2E86AB', width=2, shape='spline'),
                                                    marker=dict(size=4, color='#2E86AB', symbol='circle')
                                                ))

                                    # 2024年資料
                                    if show_2024:
                                        last_year_data = filtered_df[filtered_df['calendar_year'] == current_year - 1]
                                        if not last_year_data.empty:
                                            monthly_data = last_year_data[['calendar_month', metric]].dropna().sort_values('calendar_month')
                                            if not monthly_data.empty:
                                                is_percentage = 'tacos' in metric.lower() or '%' in metric or 'rate' in metric.lower()
                                                text_format = f"{{val:.1f}}%" if is_percentage else "{val:,.0f}"

                                                fig.add_trace(go.Scatter(
                                                    x=monthly_data['calendar_month'],
                                                    y=monthly_data[metric],
                                                    mode='lines+markers+text',
                                                    name=f'{current_year - 1}年',
                                                    text=[text_format.format(val=val) for val in monthly_data[metric]],
                                                    textposition='bottom center',
                                                    textfont=dict(size=12, color='#F18F01'),
                                                    line=dict(color='#F18F01', width=2, shape='spline'),
                                                    marker=dict(size=4, color='#F18F01', symbol='circle')
                                                ))

                                    # 格式化圖表標題和軸標籤
                                    display_metric = metric.replace('_', ' ').title()
                                    y_title = f"{display_metric} (%)" if 'tacos' in metric.lower() or '%' in metric else display_metric

                                    fig.update_layout(
                                        title=dict(text=display_metric, font=dict(size=14, color='#2c3e50'), x=0.5),
                                        xaxis=dict(title="月份", showgrid=True, gridcolor='#f0f0f0', tickfont=dict(size=10)),
                                        yaxis=dict(title=y_title, showgrid=True, gridcolor='#f0f0f0', tickfont=dict(size=10)),
                                        plot_bgcolor='white', paper_bgcolor='white',
                                        showlegend=True,  # 每個圖都顯示圖例
                                        legend=dict(
                                            orientation="h",
                                            yanchor="top",
                                            y=0.98,
                                            xanchor="right",
                                            x=0.98,
                                            font=dict(size=10, color='#2c3e50'),
                                            bgcolor='rgba(255,255,255,0.9)',
                                            bordercolor='#e0e0e0',
                                            borderwidth=1
                                        ),
                                        margin=dict(t=60, b=50, l=50, r=30),
                                        height=400
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("請選擇要顯示的指標")
            else:
                st.warning("沒有可用於繪圖的數值欄位")
    else:
        st.warning("⚠️ 沒有符合條件的數據")


st.set_page_config(page_title="Performance Review", page_icon="👤", layout="wide")
st.title("👤 Performance Review")

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
