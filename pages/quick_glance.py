import streamlit as st
from utils import load_data, list_uploaded_files
import pandas as pd
import plotly.express as px


def create_filters(df):
    """創建篩選器"""
    st.sidebar.header("📋 數據篩選")

    # 數據概覽
    st.sidebar.metric("總行數", len(df))
    st.sidebar.metric("總欄位數", len(df.columns))

    filters = {}

    # Basic 分類
    st.sidebar.subheader("🔹 Basic")
    basic_fields = ['calendar_year', 'calendar_month', 'marketplace_id', 'launch_channel']
    for field in basic_fields:
        if field in df.columns:
            unique_values = df[field].dropna().unique()
            if len(unique_values) <= 50:
                selected = st.sidebar.multiselect(
                    field.replace('_', ' ').title(),
                    options=sorted(unique_values.tolist()),
                    key=f"basic_{field}"
                )
                if selected:
                    filters[field] = selected

    # GMS 分類
    st.sidebar.subheader("💰 GMS")
    if 'ytd_ord_gms' in df.columns:
        ytd_gms_data = df['ytd_ord_gms'].dropna()
        if not ytd_gms_data.empty:
            default_min_gms = max(0, int(ytd_gms_data.min()))
            default_max_gms = max(0, int(ytd_gms_data.max()))

            col1, col2 = st.sidebar.columns(2)
            with col1:
                min_gms_input = st.number_input(
                    "最小值",
                    min_value=0,
                    value=default_min_gms,
                    step=1000,
                    key="gms_min"
                )
            with col2:
                max_gms_input = st.number_input(
                    "最大值",
                    min_value=0,
                    value=default_max_gms,
                    step=1000,
                    key="gms_max"
                )

            if min_gms_input != default_min_gms or max_gms_input != default_max_gms:
                filters['ytd_ord_gms'] = (min_gms_input, max_gms_input)

    # Ads 分類
    st.sidebar.subheader("📢 Ads")

    # mtd_TACoS 使用輸入框
    if 'mtd_TACoS' in df.columns:
        tacos_data = df['mtd_TACoS'].dropna()
        if not tacos_data.empty:
            default_min_tacos = max(0.0, float(tacos_data.min()))
            default_max_tacos = max(0.0, float(tacos_data.max()))

            st.sidebar.markdown("**MTD TACoS (%)**")
            col1, col2 = st.sidebar.columns(2)
            with col1:
                min_tacos_input = st.number_input(
                    "最小值",
                    min_value=0.0,
                    value=default_min_tacos,
                    step=0.1,
                    key="tacos_min",
                    format="%.1f"
                )
            with col2:
                max_tacos_input = st.number_input(
                    "最大值",
                    min_value=0.0,
                    value=default_max_tacos,
                    step=0.1,
                    key="tacos_max",
                    format="%.1f"
                )

            if min_tacos_input != default_min_tacos or max_tacos_input != default_max_tacos:
                filters['mtd_TACoS'] = (min_tacos_input, max_tacos_input)

    # 其他 Ads 欄位
    ads_fields = ['ytd_sp_adopt', 'mtd_sp_active_seller']
    for field in ads_fields:
        if field in df.columns:
            unique_values = df[field].dropna().unique()
            if len(unique_values) <= 10:
                selected = st.sidebar.multiselect(
                    field.replace('_', ' ').title(),
                    options=sorted(unique_values.tolist()),
                    key=f"ads_{field}"
                )
                if selected:
                    filters[field] = selected

    # Selection funnel 分類
    st.sidebar.subheader("🎯 Selection Funnel")

    # New BA Percentile
    if 'mtd_new_fba_ba_90d' in df.columns:
        new_ba_percentile = st.sidebar.selectbox(
            "New BA Percentile",
            options=[None, 50, 75, 90],
            format_func=lambda x: "All" if x is None else f"Top {x}%",
            key="new_ba_percentile"
        )
        if new_ba_percentile:
            new_ba_data = df['mtd_new_fba_ba_90d'].dropna()
            if not new_ba_data.empty:
                percentile_value = new_ba_data.quantile((100 - new_ba_percentile) / 100)
                filters['mtd_new_fba_ba_90d_percentile'] = (percentile_value, float('inf'))

    # BA Percentile
    if 'mtd_fba_ba' in df.columns:
        ba_percentile = st.sidebar.selectbox(
            "BA Percentile",
            options=[None, 50, 75, 90],
            format_func=lambda x: "All" if x is None else f"Top {x}%",
            key="ba_percentile"
        )
        if ba_percentile:
            ba_data = df['mtd_fba_ba'].dropna()
            if not ba_data.empty:
                percentile_value = ba_data.quantile((100 - ba_percentile) / 100)
                filters['mtd_fba_ba_percentile'] = (percentile_value, float('inf'))

    # New BA/AWAS%
    if 'mtd_new_fba_ba_90d' in df.columns and 'mtd_fba_awas' in df.columns:
        new_ba_awas_filter = st.sidebar.selectbox(
            "New BA/AWAS% Filter",
            options=[None, "Greater than", "Less than", "Equal to"],
            key="new_ba_awas_filter_type"
        )
        if new_ba_awas_filter:
            threshold = st.sidebar.number_input(
                "New BA/AWAS% Threshold",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=0.1,
                key="new_ba_awas_threshold"
            )
            filters['new_ba_awas_ratio'] = (new_ba_awas_filter, threshold)

    # BA/AWAS%
    if 'mtd_fba_ba' in df.columns and 'mtd_fba_awas' in df.columns:
        ba_awas_filter = st.sidebar.selectbox(
            "BA/AWAS% Filter",
            options=[None, "Greater than", "Less than", "Equal to"],
            key="ba_awas_filter_type"
        )
        if ba_awas_filter:
            threshold = st.sidebar.number_input(
                "BA/AWAS% Threshold",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=0.1,
                key="ba_awas_threshold"
            )
            filters['ba_awas_ratio'] = (ba_awas_filter, threshold)

    # Feature adoption 分類
    st.sidebar.subheader("⚡ Feature Adoption")
    feature_fields = ['is_brand_rep', 'ytd_pl_launch', 'is_aplus_adopt', 'vine_launch_90days', 'ytd_fba_adopt', 'ytd_coupon_adopt']
    for field in feature_fields:
        if field in df.columns:
            unique_values = df[field].dropna().unique()
            if len(unique_values) <= 10:
                selected = st.sidebar.multiselect(
                    field.replace('_', ' ').title(),
                    options=sorted(unique_values.tolist()),
                    key=f"feature_{field}"
                )
                if selected:
                    filters[field] = selected

    return filters

def apply_filters(df, filters):
    """套用篩選條件"""
    filtered_df = df.copy()

    for col, values in filters.items():
        if col == 'mtd_new_fba_ba_90d_percentile':
            # 處理 New BA 百分位數篩選
            if 'mtd_new_fba_ba_90d' in filtered_df.columns:
                min_val, max_val = values
                filtered_df = filtered_df[
                    (filtered_df['mtd_new_fba_ba_90d'] >= min_val) &
                    (filtered_df['mtd_new_fba_ba_90d'] <= max_val)
                ]
        elif col == 'mtd_fba_ba_percentile':
            # 處理 BA 百分位數篩選
            if 'mtd_fba_ba' in filtered_df.columns:
                min_val, max_val = values
                filtered_df = filtered_df[
                    (filtered_df['mtd_fba_ba'] >= min_val) &
                    (filtered_df['mtd_fba_ba'] <= max_val)
                ]
        elif col == 'new_ba_awas_ratio':
            # 處理 New BA/AWAS 比率篩選
            if values and 'mtd_new_fba_ba_90d' in filtered_df.columns and 'mtd_fba_awas' in filtered_df.columns:
                filter_type, threshold = values
                threshold_decimal = threshold / 100

                if filter_type == "Greater than":
                    filtered_df = filtered_df[
                        filtered_df['mtd_new_fba_ba_90d'] > (filtered_df['mtd_fba_awas'] * threshold_decimal)
                    ]
                elif filter_type == "Less than":
                    filtered_df = filtered_df[
                        filtered_df['mtd_new_fba_ba_90d'] < (filtered_df['mtd_fba_awas'] * threshold_decimal)
                    ]
                elif filter_type == "Equal to":
                    # 使用相對誤差來判斷相等（考慮浮點數精度）
                    tolerance = 0.01  # 1% tolerance
                    target = filtered_df['mtd_fba_awas'] * threshold_decimal
                    filtered_df = filtered_df[
                        abs(filtered_df['mtd_new_fba_ba_90d'] - target) <= (target * tolerance)
                    ]
        elif col == 'ba_awas_ratio':
            # 處理 BA/AWAS 比率篩選
            if values and 'mtd_fba_ba' in filtered_df.columns and 'mtd_fba_awas' in filtered_df.columns:
                filter_type, threshold = values
                threshold_decimal = threshold / 100

                if filter_type == "Greater than":
                    filtered_df = filtered_df[
                        filtered_df['mtd_fba_ba'] > (filtered_df['mtd_fba_awas'] * threshold_decimal)
                    ]
                elif filter_type == "Less than":
                    filtered_df = filtered_df[
                        filtered_df['mtd_fba_ba'] < (filtered_df['mtd_fba_awas'] * threshold_decimal)
                    ]
                elif filter_type == "Equal to":
                    # 使用相對誤差來判斷相等（考慮浮點數精度）
                    tolerance = 0.01  # 1% tolerance
                    target = filtered_df['mtd_fba_awas'] * threshold_decimal
                    filtered_df = filtered_df[
                        abs(filtered_df['mtd_fba_ba'] - target) <= (target * tolerance)
                    ]
        elif col in filtered_df.columns:
            # 處理一般欄位篩選
            if isinstance(values, list):  # 多選篩選
                filtered_df = filtered_df[filtered_df[col].isin(values)]
            elif isinstance(values, tuple):  # 範圍篩選
                min_val, max_val = values
                filtered_df = filtered_df[
                    (filtered_df[col] >= min_val) & (filtered_df[col] <= max_val)
                ]

    return filtered_df

def create_visualizations(df):
    """創建視覺化圖表"""
    st.header("📈 數據視覺化")

    # 選擇要視覺化的欄位
    numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    text_columns = df.select_dtypes(include=['object']).columns.tolist()

    col1, col2 = st.columns(2)

    with col1:
        if text_columns:
            # 類別分佈圖
            selected_cat = st.selectbox("選擇類別欄位", text_columns, key="viz_cat")
            if selected_cat:
                value_counts = df[selected_cat].value_counts().head(10)
                fig = px.bar(
                    x=value_counts.values,
                    y=value_counts.index,
                    orientation='h',
                    title=f"{selected_cat} 分佈"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

    with col2:
        if numeric_columns:
            # 數值分佈直方圖
            selected_num = st.selectbox("選擇數值欄位", numeric_columns, key="viz_num")
            if selected_num:
                fig = px.histogram(
                    df,
                    x=selected_num,
                    title=f"{selected_num} 分佈"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)


def show_original_analysis_tab(df, selected_file):
    """顯示原始分析 tab 的內容"""
    # 準備最終 df
    final_df = df.copy()
    
    # 使用 session state 保存狀態
    if 'exclude_file_uploaded' not in st.session_state:
        st.session_state.exclude_file_uploaded = None
        st.session_state.final_df = df.copy()
    
    # 建立篩選器（使用處理後的數據）
    filters = create_filters(final_df)

    # 套用篩選
    filtered_df = apply_filters(final_df, filters)

    # 顯示篩選後的結果
    st.header(f"🔍 篩選結果 ({len(filtered_df)} / {len(final_df)} 行)")

    if len(filtered_df) != len(final_df):
        st.info(f"已篩選掉 {len(final_df) - len(filtered_df)} 行數據")

    if len(final_df) != len(df):
        st.info(f"原始數據 {len(df)} 筆，去重後 {len(final_df)} 筆，篩選後 {len(filtered_df)} 筆")

    # 📊 關鍵指標統計
    if not filtered_df.empty:
        st.subheader("📊 關鍵指標統計")

        # 計算統計數據的欄位
        stats_columns = ['New_AWAS_BA_%', 'AWAS_BA_%', 'mtd_TACoS']
        available_stats = [col for col in stats_columns if col in filtered_df.columns]

        if available_stats:
            for col_name in available_stats:
                col_data = filtered_df[col_name].dropna()

                if not col_data.empty:
                    # 格式化顯示名稱、數據和定義
                    if col_name == 'mtd_TACoS':
                        display_name = "MTD TACoS (%)"
                        definition = ""
                        plot_data = col_data  # mtd_TACoS 已經是百分比形式，不需要轉換
                    elif col_name == 'New_AWAS_BA_%':
                        display_name = "New AWAS BA %"
                        definition = "90 天內的 New FBA - Buyable ASIN 出數的比例"
                        plot_data = col_data * 100
                    elif col_name == 'AWAS_BA_%':
                        display_name = "AWAS BA %"
                        definition = "Total Buyable ASIN 出數的比例"
                        plot_data = col_data * 100
                    else:
                        display_name = col_name.replace('_%', ' %')
                        definition = ""
                        plot_data = col_data * 100

                    # 顯示標題和定義
                    st.markdown(f"**{display_name}**")
                    if definition:
                        st.caption(f"💡 {definition}")

                    # 創建兩欄佈局
                    chart_col1, chart_col2 = st.columns(2)

                    with chart_col1:
                        # 箱型圖
                        import plotly.graph_objects as go

                        fig_box = go.Figure()
                        fig_box.add_trace(go.Box(
                            y=plot_data,
                            name=display_name,
                            boxmean='sd',  # 顯示平均值和標準差
                            marker_color='lightblue',
                            boxpoints='outliers',  # 只顯示異常值點
                            hovertemplate='%{y:.1f}<extra></extra>'  # 設定懸停顯示格式為一位小數
                        ))

                        fig_box.update_layout(
                            title=f"{display_name} - 箱型圖",
                            yaxis_title="數值",
                            height=400,
                            showlegend=False,
                            yaxis=dict(tickformat='.1f')  # Y軸刻度顯示一位小數
                        )

                        st.plotly_chart(fig_box, use_container_width=True)

                    with chart_col2:
                        # 直方圖
                        fig_hist = px.histogram(
                            plot_data,
                            x=plot_data.values,
                            nbins=30,
                            title=f"{display_name} - 直方圖",
                            labels={'x': '數值', 'count': '頻率'}
                        )

                        # 添加平均值和中位數的垂直線
                        mean_val = plot_data.mean()
                        median_val = plot_data.median()

                        fig_hist.add_vline(
                            x=mean_val,
                            line_dash="dash",
                            line_color="red",
                            annotation_text=f"平均: {mean_val:.1f}",
                            annotation_position="top"
                        )

                        fig_hist.add_vline(
                            x=median_val,
                            line_dash="dash",
                            line_color="green",
                            annotation_text=f"中位數: {median_val:.1f}",
                            annotation_position="bottom"
                        )

                        fig_hist.update_layout(
                            height=400,
                            showlegend=False
                        )

                        st.plotly_chart(fig_hist, use_container_width=True)

                    st.markdown("---")

            # 詳細統計表格
            if len(available_stats) > 0:
                st.markdown("#### 📋 詳細統計表")
                stats_data = []

                for col_name in available_stats:
                    col_data = filtered_df[col_name].dropna()
                    if not col_data.empty:
                        # 判斷是否需要轉換為百分比
                        if col_name == 'mtd_TACoS':
                            display_data = col_data  # mtd_TACoS 已經是百分比形式
                        else:
                            display_data = col_data * 100  # 其他欄位需要乘以100

                        stats_data.append({
                            '指標': col_name,
                            '樣本數': len(col_data),
                            '平均值': f"{display_data.mean():.1f}",
                            'P25': f"{display_data.quantile(0.25):.1f}",
                            'P50 (中位數)': f"{display_data.median():.1f}",
                            'P75': f"{display_data.quantile(0.75):.1f}",
                            '標準差': f"{display_data.std():.1f}",
                            '最小值': f"{display_data.min():.1f}",
                            '最大值': f"{display_data.max():.1f}"
                        })

                if stats_data:
                    stats_df = pd.DataFrame(stats_data)
                    st.dataframe(stats_df, use_container_width=True, hide_index=True)
        else:
            st.info("⚠️ 未找到相關統計欄位 (New_AWAS_BA_%, AWAS_BA_%, mtd_TACoS)")

    # 篩選後的數據預覽和下載
    if not filtered_df.empty:
        # 按最重要的數值欄位排序（如果存在）
        display_df = filtered_df.copy()
        if 'mtd_new_fba_ba_90d' in display_df.columns:
            display_df = display_df.sort_values('mtd_new_fba_ba_90d', ascending=False)

        # 選擇要顯示的欄位
        available_columns = display_df.columns.tolist()

        # 預設選擇重要欄位
        default_columns = []
        # 按照指定順序：1.year 2.month/week 3.merchant_customer_id 4.merchant_name 5.opportunity_owner 6.ytd_order_gms
        priority_fields = [
            'calendar_year', 'reporting_year',  # year
            'calendar_month', 'reporting_week_of_year',  # month or week
            'merchant_customer_id',  # merchant_customer_id
            'merchant_name',  # merchant_name
            'nsr_opportunity_owner',  # opportunity owner
            'ytd_ord_gms'  # ytd_order_gms
        ]
        
        for field in priority_fields:
            if field in available_columns and field not in default_columns:
                default_columns.append(field)
                if len(default_columns) >= 6:
                    break

        selected_columns = st.multiselect(
            "選擇要顯示的欄位",
            options=available_columns,
            default=default_columns[:6],
            key="main_data_display_columns"
        )

        if selected_columns:

            # Customer ID 篩選功能
            customer_id_input = st.text_input(
                "🔍 指定 CID",
                placeholder="12345,56788",
                key="customer_id_filter"
            )
            
            # 根據 Customer ID 篩選數據
            final_display_df = display_df.copy()
            if customer_id_input.strip() and 'merchant_customer_id' in display_df.columns:
                display_df["merchant_customer_id"] = (
                    display_df["merchant_customer_id"].astype(str).str.strip()
                )
                customer_ids = [id.strip() for id in customer_id_input.replace("\n", ",").split(",") if id.strip()]
                if customer_ids:
                    final_display_df = display_df[
                        display_df["merchant_customer_id"].isin(customer_ids)
                    ]
                    st.info(f"已篩選出 {len(final_display_df)} 筆符合 Customer ID 的數據")
                   
            preview_df = final_display_df[selected_columns].copy()

            # 加入排名欄位
            if 'mtd_new_fba_ba_90d' in preview_df.columns:
                preview_df.insert(0, '排名', range(1, len(preview_df) + 1))

            st.subheader("數據預覽")
            st.dataframe(preview_df.head(100), use_container_width=True)

            # 下載按鈕（使用最終篩選後的數據）
            csv_data = final_display_df.to_csv(index=False, encoding='utf-8')
            st.download_button(
                label="💾 下載篩選後的數據",
                data=csv_data,
                file_name=f"filtered_{selected_file['name']}",
                mime="text/csv"
            )
        else:
            st.warning("請至少選擇一個欄位來顯示數據")

    # 篩選：排除指定的 MCID
    st.header("🚫 排除指定的 MCID")

    exclude_input = st.text_area(
        "貼上要排除的 Customer ID (可用逗號或換行分隔)",
        placeholder="12345, 67890\n88888",
        key="exclude_customer_id"
    )

    final_filtered_df = filtered_df.copy()

    if exclude_input.strip() and "merchant_customer_id" in final_filtered_df.columns:
        # 支援逗號、換行分隔
        final_filtered_df["merchant_customer_id"] = (
            final_filtered_df["merchant_customer_id"].astype(str).str.strip()
        )
        exclude_ids = [x.strip() for x in exclude_input.replace("\n", ",").split(",") if x.strip()]
        before = len(final_filtered_df)
        final_filtered_df = final_filtered_df[~final_filtered_df["merchant_customer_id"].astype(str).isin(exclude_ids)]
        after = len(final_filtered_df)

        st.success(f"✅ 已排除 {len(exclude_ids)} 個 CID，篩選後剩下 {after} 筆 (原本 {before})")

        # 預覽結果
        st.dataframe(final_filtered_df.head(100), use_container_width=True)

        # 提供下載
        csv_data = final_filtered_df.to_csv(index=False, encoding="utf-8")
        st.download_button(
            label="💾 下載排除後的數據",
            data=csv_data,
            file_name=f"excluded_filtered_{selected_file['name']}",
            mime="text/csv",
            key="download_excluded_data"
        )


st.set_page_config(page_title="Quick Glance", page_icon="📑", layout="wide")
st.title("📑 Quick Glance")

# 初始化 session_state 來保存數據
if 'quick_glance_loaded_data' not in st.session_state:
    st.session_state.quick_glance_loaded_data = None
if 'quick_glance_filename' not in st.session_state:
    st.session_state.quick_glance_filename = None

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
        if st.session_state.quick_glance_filename != selected_name:
            # 檔案改變了，需要重新讀取
            selected_file = file_options[selected_name]
            df, error = load_data(selected_file)
            if error:
                st.error(error)
            elif df is not None and not df.empty:
                # 儲存到 session_state
                st.session_state.quick_glance_loaded_data = df
                st.session_state.quick_glance_filename = selected_name
                show_original_analysis_tab(df, {"name": selected_name, "size": selected_file.stat().st_size})
            else:
                st.warning("⚠️ 無法讀取檔案或檔案為空")
        else:
            # 使用快取的數據
            if st.session_state.quick_glance_loaded_data is not None:
                df = st.session_state.quick_glance_loaded_data
                selected_file = file_options[selected_name]
                show_original_analysis_tab(df, {"name": selected_name, "size": selected_file.stat().st_size})
else:
    st.info("目前 P0 MCID MBR 資料夾內沒有任何檔案")
