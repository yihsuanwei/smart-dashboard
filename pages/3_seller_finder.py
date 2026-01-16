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

    # Launch Date 篩選
    if 'launch_date' in df.columns:
        import pandas as pd
        # 嘗試轉換為日期格式
        try:
            df['launch_date'] = pd.to_datetime(df['launch_date'], errors='coerce')
            launch_date_data = df['launch_date'].dropna()

            if not launch_date_data.empty:
                min_date = launch_date_data.min().date()
                max_date = launch_date_data.max().date()

                st.sidebar.markdown("**Launch Date**")
                col1, col2 = st.sidebar.columns(2)
                with col1:
                    start_date = st.date_input(
                        "開始日期",
                        value=min_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="launch_date_start"
                    )
                with col2:
                    end_date = st.date_input(
                        "結束日期",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="launch_date_end"
                    )

                # 如果日期有變動,加入篩選條件
                if start_date != min_date or end_date != max_date:
                    filters['launch_date'] = (start_date, end_date)
        except Exception as e:
            st.sidebar.warning(f"⚠️ Launch Date 欄位格式錯誤: {str(e)}")

    # GMS 分類
    st.sidebar.subheader("💰 YTD GMS")
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

    # MTD GMS 分類
    st.sidebar.subheader("💰 MTD GMS")
    if 'mtd_ord_gms' in df.columns:
        mtd_gms_data = df['mtd_ord_gms'].dropna()
        if not mtd_gms_data.empty:
            default_min_mtd_gms = max(0, int(mtd_gms_data.min()))
            default_max_mtd_gms = max(0, int(mtd_gms_data.max()))

            col1, col2 = st.sidebar.columns(2)
            with col1:
                min_mtd_gms_input = st.number_input(
                    "最小值",
                    min_value=0,
                    value=default_min_mtd_gms,
                    step=1000,
                    key="mtd_gms_min"
                )
            with col2:
                max_mtd_gms_input = st.number_input(
                    "最大值",
                    min_value=0,
                    value=default_max_mtd_gms,
                    step=1000,
                    key="mtd_gms_max"
                )

            if min_mtd_gms_input != default_min_mtd_gms or max_mtd_gms_input != default_max_mtd_gms:
                filters['mtd_ord_gms'] = (min_mtd_gms_input, max_mtd_gms_input)

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
            options=[None, 90, 75, 50, 25],
            format_func=lambda x: "All" if x is None else f"P{x}",
            key="new_ba_percentile"
        )
        if new_ba_percentile:
            new_ba_data = df['mtd_new_fba_ba_90d'].dropna()
            if not new_ba_data.empty:
                percentile_value = new_ba_data.quantile(new_ba_percentile / 100)
                filters['mtd_new_fba_ba_90d_percentile'] = (percentile_value, float('inf'))

    # BA Percentile
    if 'mtd_fba_ba' in df.columns:
        ba_percentile = st.sidebar.selectbox(
            "BA Percentile",
            options=[None, 90, 75, 50, 25],
            format_func=lambda x: "All" if x is None else f"P{x}",
            key="ba_percentile"
        )
        if ba_percentile:
            ba_data = df['mtd_fba_ba'].dropna()
            if not ba_data.empty:
                percentile_value = ba_data.quantile(ba_percentile / 100)
                filters['mtd_fba_ba_percentile'] = (percentile_value, float('inf'))

    # New AWAS/BA %
    if 'mtd_new_fba_ba_90d' in df.columns and 'mtd_fba_awas' in df.columns:
        new_ba_awas_filter = st.sidebar.selectbox(
            "New AWAS/BA %",
            options=[None, "Greater than", "Less than", "Equal to"],
            key="new_ba_awas_filter_type"
        )
        if new_ba_awas_filter:
            threshold = st.sidebar.number_input(
                "New AWAS/BA % Threshold",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=0.1,
                key="new_ba_awas_threshold"
            )
            filters['new_ba_awas_ratio'] = (new_ba_awas_filter, threshold)

    # AWAS/BA %
    if 'mtd_fba_ba' in df.columns and 'mtd_fba_awas' in df.columns:
        ba_awas_filter = st.sidebar.selectbox(
            "AWAS/BA %",
            options=[None, "Greater than", "Less than", "Equal to"],
            key="ba_awas_filter_type"
        )
        if ba_awas_filter:
            threshold = st.sidebar.number_input(
                "AWAS/BA % Threshold",
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
            if values:
                filter_type, threshold = values
                threshold_decimal = threshold / 100

                # 優先使用 New_AWAS_BA_% 欄位，如果沒有則計算
                if 'New_AWAS_BA_%' in filtered_df.columns:
                    ratio = filtered_df['New_AWAS_BA_%']
                    valid_mask = ratio.notna()
                elif 'mtd_new_fba_ba_90d' in filtered_df.columns and 'mtd_fba_awas' in filtered_df.columns:
                    # 計算比率：New BA / AWAS
                    # 避免除以零：只保留 AWAS > 0 的數據
                    valid_mask = filtered_df['mtd_fba_awas'] > 0
                    ratio = filtered_df['mtd_new_fba_ba_90d'] / filtered_df['mtd_fba_awas'].replace(0, float('nan'))
                else:
                    continue

                if filter_type == "Greater than":
                    filtered_df = filtered_df[valid_mask & (ratio > threshold_decimal)]
                elif filter_type == "Less than":
                    filtered_df = filtered_df[valid_mask & (ratio < threshold_decimal)]
                elif filter_type == "Equal to":
                    # 使用相對誤差來判斷相等（考慮浮點數精度）
                    tolerance = 0.01  # 1% tolerance
                    filtered_df = filtered_df[
                        valid_mask & (abs(ratio - threshold_decimal) <= threshold_decimal * tolerance)
                    ]
        elif col == 'ba_awas_ratio':
            # 處理 BA/AWAS 比率篩選
            if values:
                filter_type, threshold = values
                threshold_decimal = threshold / 100

                # 優先使用 AWAS_BA_% 欄位，如果沒有則計算
                if 'AWAS_BA_%' in filtered_df.columns:
                    ratio = filtered_df['AWAS_BA_%']
                    valid_mask = ratio.notna()
                elif 'mtd_fba_ba' in filtered_df.columns and 'mtd_fba_awas' in filtered_df.columns:
                    # 計算比率：BA / AWAS
                    # 避免除以零：只保留 AWAS > 0 的數據
                    valid_mask = filtered_df['mtd_fba_awas'] > 0
                    ratio = filtered_df['mtd_fba_ba'] / filtered_df['mtd_fba_awas'].replace(0, float('nan'))
                else:
                    continue

                if filter_type == "Greater than":
                    filtered_df = filtered_df[valid_mask & (ratio > threshold_decimal)]
                elif filter_type == "Less than":
                    filtered_df = filtered_df[valid_mask & (ratio < threshold_decimal)]
                elif filter_type == "Equal to":
                    # 使用相對誤差來判斷相等（考慮浮點數精度）
                    tolerance = 0.01  # 1% tolerance
                    filtered_df = filtered_df[
                        valid_mask & (abs(ratio - threshold_decimal) <= threshold_decimal * tolerance)
                    ]
        elif col == 'launch_date':
            # 處理 launch_date 日期篩選
            if 'launch_date' in filtered_df.columns and isinstance(values, tuple):
                import pandas as pd
                start_date, end_date = values
                # 確保 launch_date 欄位是日期格式
                filtered_df['launch_date'] = pd.to_datetime(filtered_df['launch_date'], errors='coerce')
                # 篩選日期範圍
                filtered_df = filtered_df[
                    (filtered_df['launch_date'].dt.date >= start_date) &
                    (filtered_df['launch_date'].dt.date <= end_date)
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

        # 取得所有數值型欄位
        all_numeric_columns = filtered_df.select_dtypes(include=['int64', 'float64']).columns.tolist()

        # 預設選擇的欄位
        default_stats_columns = ['New_AWAS_BA_%', 'AWAS_BA_%', 'mtd_TACoS']
        default_available = [col for col in default_stats_columns if col in all_numeric_columns]

        # 讓使用者選擇要分析的指標
        selected_stats_columns = st.multiselect(
            "選擇要分析的指標",
            options=all_numeric_columns,
            default=default_available if default_available else (all_numeric_columns[:3] if len(all_numeric_columns) >= 3 else all_numeric_columns),
            key="selected_stats_metrics",
            help="可以選擇多個指標來查看其統計分布、中位數和 percentile"
        )

        available_stats = selected_stats_columns

        if available_stats:
            for col_name in available_stats:
                col_data = filtered_df[col_name].dropna()

                if not col_data.empty:
                    # 格式化顯示名稱、數據和定義
                    if col_name == 'mtd_TACoS':
                        display_name = "MTD TACoS (%)"
                        definition = ""
                        plot_data = col_data  # mtd_TACoS 已經是百分比形式，不需要轉換
                        is_percentage = True
                    elif col_name == 'New_AWAS_BA_%':
                        display_name = "New AWAS BA %"
                        definition = "90 天內的 New FBA - Buyable ASIN 出數的比例"
                        plot_data = col_data * 100
                        is_percentage = True
                    elif col_name == 'AWAS_BA_%':
                        display_name = "AWAS BA %"
                        definition = "Total Buyable ASIN 出數的比例"
                        plot_data = col_data * 100
                        is_percentage = True
                    else:
                        # 自動判斷：如果欄位名稱包含 '%' 或是小數範圍在 0-1 之間，視為百分比
                        display_name = col_name.replace('_', ' ').title()
                        definition = ""

                        # 判斷是否為百分比資料
                        if '%' in col_name or (col_data.max() <= 1.0 and col_data.min() >= 0 and col_data.mean() < 1):
                            plot_data = col_data * 100
                            is_percentage = True
                            if '%' not in display_name:
                                display_name += " (%)"
                        else:
                            # 一般數值欄位（如 GMS, 訂單數等）
                            plot_data = col_data
                            is_percentage = False

                    # 顯示標題和定義
                    st.markdown(f"**{display_name}**")
                    if definition:
                        st.caption(f"💡 {definition}")

                    # 創建兩欄佈局
                    chart_col1, chart_col2 = st.columns(2)

                    with chart_col1:
                        # 箱型圖
                        import plotly.graph_objects as go

                        # 根據資料類型決定數值格式
                        if is_percentage:
                            hover_format = '%{y:.1f}<extra></extra>'
                            tick_format = '.1f'
                        else:
                            hover_format = '%{y:,.0f}<extra></extra>'  # 千分位分隔，無小數
                            tick_format = ',.0f'  # 千分位分隔

                        fig_box = go.Figure()
                        fig_box.add_trace(go.Box(
                            y=plot_data,
                            name=display_name,
                            boxmean='sd',  # 顯示平均值和標準差
                            marker_color='lightblue',
                            boxpoints='outliers',  # 只顯示異常值點
                            hovertemplate=hover_format
                        ))

                        fig_box.update_layout(
                            title=f"{display_name} - 箱型圖",
                            yaxis_title="數值",
                            height=400,
                            showlegend=False,
                            yaxis=dict(tickformat=tick_format)
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

                        # 根據資料類型格式化標註文字
                        if is_percentage:
                            mean_text = f"平均: {mean_val:.1f}"
                            median_text = f"中位數: {median_val:.1f}"
                        else:
                            mean_text = f"平均: {mean_val:,.0f}"
                            median_text = f"中位數: {median_val:,.0f}"

                        fig_hist.add_vline(
                            x=mean_val,
                            line_dash="dash",
                            line_color="red",
                            annotation_text=mean_text,
                            annotation_position="top"
                        )

                        fig_hist.add_vline(
                            x=median_val,
                            line_dash="dash",
                            line_color="green",
                            annotation_text=median_text,
                            annotation_position="bottom"
                        )

                        fig_hist.update_layout(
                            height=400,
                            showlegend=False,
                            xaxis=dict(tickformat=tick_format)
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
                        # 判斷資料類型並轉換
                        if col_name == 'mtd_TACoS':
                            display_data = col_data  # mtd_TACoS 已經是百分比形式
                            is_pct = True
                        elif col_name in ['New_AWAS_BA_%', 'AWAS_BA_%']:
                            display_data = col_data * 100
                            is_pct = True
                        elif '%' in col_name or (col_data.max() <= 1.0 and col_data.min() >= 0 and col_data.mean() < 1):
                            display_data = col_data * 100
                            is_pct = True
                        else:
                            display_data = col_data
                            is_pct = False

                        # 根據類型格式化數值
                        if is_pct:
                            stats_data.append({
                                '指標': col_name,
                                '樣本數': f"{len(col_data):,}",
                                '平均值': f"{display_data.mean():.1f}",
                                'P25': f"{display_data.quantile(0.25):.1f}",
                                'P50 (中位數)': f"{display_data.median():.1f}",
                                'P75': f"{display_data.quantile(0.75):.1f}",
                                '標準差': f"{display_data.std():.1f}",
                                '最小值': f"{display_data.min():.1f}",
                                '最大值': f"{display_data.max():.1f}"
                            })
                        else:
                            stats_data.append({
                                '指標': col_name,
                                '樣本數': f"{len(col_data):,}",
                                '平均值': f"{display_data.mean():,.0f}",
                                'P25': f"{display_data.quantile(0.25):,.0f}",
                                'P50 (中位數)': f"{display_data.median():,.0f}",
                                'P75': f"{display_data.quantile(0.75):,.0f}",
                                '標準差': f"{display_data.std():,.0f}",
                                '最小值': f"{display_data.min():,.0f}",
                                '最大值': f"{display_data.max():,.0f}"
                            })

                if stats_data:
                    stats_df = pd.DataFrame(stats_data)
                    st.dataframe(stats_df, use_container_width=True, hide_index=True)
        else:
            st.info("⚠️ 請在上方的「選擇要分析的指標」中選擇至少一個數值欄位來查看統計資訊")

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


st.set_page_config(page_title="Seller Finder", page_icon="🔍", layout="wide")
st.title("🔍 Seller Finder")

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
