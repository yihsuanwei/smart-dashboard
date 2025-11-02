import streamlit as st
import pandas as pd
from utils import list_uploaded_files, load_data, UPLOAD_DIR, FILE_TYPES


def normalize_customer_id(series: pd.Series) -> pd.Series:
    """把 merchant_customer_id 清洗成純字串（去掉 .0 / 空白）"""
    return (
        series.apply(lambda x: str(int(float(x))) if pd.notnull(x) else "")
        .str.strip()
    )


def add_calculated_columns(df):
    """添加計算欄位"""
    # New AWAS/BA %
    if "mtd_new_fba_ba_90d_awas" in df.columns and "mtd_new_fba_ba_90d" in df.columns:
        df["New_AWAS_BA_%"] = df.apply(
            lambda row: (row["mtd_new_fba_ba_90d_awas"] / row["mtd_new_fba_ba_90d"])
            if pd.notnull(row["mtd_new_fba_ba_90d_awas"]) and pd.notnull(row["mtd_new_fba_ba_90d"]) and row["mtd_new_fba_ba_90d"] != 0
            else None,
            axis=1
        )
    # AWAS_BA_% (比例值)
    if "mtd_fba_awas" in df.columns and "mtd_fba_ba" in df.columns:
        df["AWAS_BA_%"] = df.apply(
            lambda row: (row["mtd_fba_awas"] / row["mtd_fba_ba"])
            if pd.notnull(row["mtd_fba_awas"]) and pd.notnull(row["mtd_fba_ba"]) and row["mtd_fba_ba"] != 0
            else None,
            axis=1
        )
    # 新增 mtd_TACoS 欄位
    if "mtd_sa_revenue_usd" in df.columns and "mtd_ord_gms" in df.columns:
        df = df.copy()
        df["mtd_TACoS"] = df.apply(
            lambda row: (row["mtd_sa_revenue_usd"] / row["mtd_ord_gms"] * 100)
            if pd.notnull(row["mtd_sa_revenue_usd"]) and pd.notnull(row["mtd_ord_gms"]) and row["mtd_ord_gms"] != 0
            else None,
            axis=1
        )
    return df

st.set_page_config(page_title="Smart Dashboard - 資料處理", page_icon="📊", layout="wide")

st.title("📤 資料處理中心")
st.markdown("上傳CSV檔案並進行資料處理，處理後的檔案可在其他頁面中使用")

# 確保上傳資料夾存在
UPLOAD_DIR.mkdir(exist_ok=True)

# 分成兩列
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📁 檔案上傳")
    uploaded_file = st.file_uploader(
        "選擇CSV檔案",
        type=['csv'],
        help="支援UTF-8、Big5、GBK編碼"
    )

    # 檢測檔案變更並重置 file_type
    if uploaded_file is not None:
        # 獲取當前檔案的唯一識別（檔名+大小）
        current_file_id = f"{uploaded_file.name}_{uploaded_file.size}"

        # 如果是新檔案，重置 file_type
        if "last_uploaded_file_id" not in st.session_state or st.session_state.last_uploaded_file_id != current_file_id:
            st.session_state.last_uploaded_file_id = current_file_id
            st.session_state.file_type_selection = "請選擇..."

    if uploaded_file is not None:
        # 文件類型選擇
        file_type = st.selectbox(
            "選擇文件類型",
            options=["請選擇..."] + list(FILE_TYPES.keys()),
            help="選擇文件類型以決定存儲位置",
            key="file_type_selection"
        )

        # 自定義檔名輸入
        custom_filename = st.text_input(
            "自定義檔名 (不含副檔名)",
            value=uploaded_file.name.replace('.csv', ''),
            help="輸入您想要的檔名，系統會自動加上.csv副檔名"
        )

        # 資料處理選項 - 只在 P0 MCID MBR 時顯示
        option_filter_owner = False
        owners_input = ""
        option_latest_customer = False
        option_filter_customer = False
        customer_ids_input = ""

        if file_type == "P0 MCID MBR":
            st.warning("⚠️ 資料量龐大的檔案建議先選擇以下篩選器")

            # 處理選項 checkboxes
            option_filter_owner = st.checkbox(
                "篩選 nsr_opportunity_owner",
                value=False,
                help="只保留指定業務人員的資料"
            )

            # 如果選擇篩選業務人員，顯示輸入框
            if option_filter_owner:
                owners_input = st.text_area(
                    "輸入要保留的 nsr_opportunity_owner",
                    help="一行一個業務人員名稱，或用逗號分隔",
                    placeholder="例如：\nAlbert Lin\nAlex Kuo\n或 Albert Lin,Alex Kuo,Chien Lee",
                    value="Albert Lin,Alex Kuo,Chien Lee,Davy Chen,Hans Huang,Jamie Fan,Jessica Tsai,Kai Tung,Raul Lai,Susie Shih,Che-Wei Chang,Crystal Lin,Eddie Chu,Jenny Kao,Karen Hou,Shelly Huang,Silvia Lien"
                )

            option_latest_customer = st.checkbox(
                "只保留最新一筆 merchant_customer_id",
                value=False,
                help="每個merchant_customer_id只保留最新的一筆資料"
            )

            option_filter_customer = st.checkbox(
                "篩選特定 merchant_customer_id",
                value=False,
                help="只保留指定的merchant_customer_id資料"
            )

            # 如果選擇篩選特定customer_id，顯示輸入框
            if option_filter_customer:
                customer_ids_input = st.text_area(
                    "輸入要保留的 merchant_customer_id",
                    help="一行一個ID，或用逗號分隔",
                    placeholder="例如：\n12345\n67890\n或 12345,67890,11111"
                )

        # 檢查是否選擇了文件類型
        if file_type == "請選擇...":
            st.warning("⚠️ 請選擇文件類型")
        # 檢查檔名是否有效
        elif custom_filename:
            # 清理檔名，移除不安全字元
            safe_filename = "".join(c for c in custom_filename if c.isalnum() or c in (' ', '-', '_')).strip()
            if not safe_filename:
                st.warning("⚠️ 檔名包含無效字元，請使用英文、數字、空格、連字號或底線")
            else:
                final_filename = f"{safe_filename}.csv"
                # 根據選擇的文件類型確定存儲路徑
                target_folder = UPLOAD_DIR / FILE_TYPES[file_type]
                target_path = target_folder / final_filename

                # 檢查檔案是否已存在，顯示警告和確認選項
                file_exists = target_path.exists()

                if file_exists:
                    st.warning(f"⚠️ 檔案 '{final_filename}' 已存在於 {file_type} 資料夾中，上傳會覆蓋現有檔案")
                upload_button = st.button("🚀 上傳並處理", type="primary")

                # 執行上傳邏輯
                if upload_button:
                    with st.spinner("處理中..."):
                        # 先處理資料
                        df, error = load_data(uploaded_file)
                        if error:
                            st.error(f"❌ {error}")
                        else:
                            # 套用資料處理邏輯
                            original_count = len(df)

                            # 1. 基本資料清洗 - 清洗 merchant_customer_id
                            if "merchant_customer_id" in df.columns:
                                df["merchant_customer_id"] = normalize_customer_id(df["merchant_customer_id"])

                            # 定義解析輸入的函數
                            def parse_input_list(input_text):
                                items = []
                                for line in input_text.strip().split('\n'):
                                    line = line.strip()
                                    if ',' in line:
                                        items.extend([item.strip() for item in line.split(',') if item.strip()])
                                    elif line:
                                        items.append(line)
                                return items

                            # 2. 篩選 nsr_opportunity_owner
                            if option_filter_owner and owners_input.strip() and "nsr_opportunity_owner" in df.columns:
                                input_owners = parse_input_list(owners_input)
                                if input_owners:
                                    df = df[df["nsr_opportunity_owner"].isin(input_owners)]
                                    st.info(f"篩選業務人員後: {len(df)} 筆資料 (保留: {', '.join(input_owners[:3])}{'...' if len(input_owners) > 3 else ''})")

                            # 3. 篩選特定 merchant_customer_id
                            if option_filter_customer and customer_ids_input.strip():
                                input_ids = parse_input_list(customer_ids_input)
                                if input_ids and "merchant_customer_id" in df.columns:
                                    df = df[df["merchant_customer_id"].isin(input_ids)]
                                    st.info(f"篩選指定客戶ID後: {len(df)} 筆資料")

                            # 4. 只保留最新一筆 merchant_customer_id + marketplace_id
                            if option_latest_customer and "merchant_customer_id" in df.columns:
                                # 必須要有 calendar_year, calendar_month 和 marketplace_id 欄位
                                if "calendar_year" not in df.columns or "calendar_month" not in df.columns:
                                    st.error("❌ 缺少必要欄位：需要 calendar_year 和 calendar_month 才能保留最新一筆資料")
                                elif "marketplace_id" not in df.columns:
                                    st.error("❌ 缺少必要欄位：需要 marketplace_id 才能保留最新一筆資料")
                                else:
                                    try:
                                        # 轉換為數值型態，確保排序正確
                                        df['calendar_year'] = pd.to_numeric(df['calendar_year'], errors='coerce')
                                        df['calendar_month'] = pd.to_numeric(df['calendar_month'], errors='coerce')

                                        # 先按 calendar_year, calendar_month 排序（升序）
                                        df = df.sort_values(['calendar_year', 'calendar_month'], ascending=True)
                                        # 按 merchant_customer_id + marketplace_id 分組，保留每組最後一筆（最新）
                                        df = df.groupby(['merchant_customer_id', 'marketplace_id'], as_index=False).tail(1)
                                        st.info(f"保留最新一筆後: {len(df)} 筆資料 (按 merchant_customer_id + marketplace_id 分組)")
                                    except Exception as e:
                                        st.error(f"❌ 無法按 calendar_year/calendar_month 排序: {e}")

                            # 5. 添加計算欄位
                            df = add_calculated_columns(df)

                            # 顯示處理結果統計
                            st.success(f"資料處理完成：{original_count} → {len(df)} 筆資料")

                            # 儲存到指定路徑
                            try:
                                df.to_csv(target_path, index=False, encoding="utf-8")
                                st.balloons()  # 顯示慶祝動畫
                            except Exception as e:
                                st.error(f"❌ 存檔失敗: {str(e)}")
        else:
            st.warning("⚠️ 請輸入檔名")

with col2:
    st.subheader("📋 已上傳的檔案")
    uploaded_files = list_uploaded_files()

    if not uploaded_files:
        st.info("尚未上傳任何檔案")
    else:
        for i, file_path in enumerate(uploaded_files):
            # 判斷文件類型
            file_type_display = "未分類"
            for type_name, folder_name in FILE_TYPES.items():
                if file_path.parent.name == folder_name:
                    file_type_display = type_name
                    break

            with st.expander(f"📄 {file_path.name} ({file_type_display})"):
                # 檔案資訊
                file_stats = file_path.stat()
                col_info, col_action = st.columns([3, 1])

                with col_info:
                    st.write(f"**文件類型:** {file_type_display}")
                    st.write(f"**大小:** {file_stats.st_size:,} bytes")
                    st.write(f"**修改時間:** {pd.Timestamp.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M')}")

                with col_action:
                    if st.button(f"🗑️ 刪除", key=f"delete_{i}"):
                        try:
                            file_path.unlink()
                            st.success("檔案已刪除")
                            st.rerun()
                        except Exception as e:
                            st.error(f"刪除失敗: {e}")

                # 資料預覽
                if st.checkbox(f"預覽資料", key=f"preview_{i}"):
                    try:
                        df, error = load_data(file_path)
                        if error:
                            st.error(f"無法讀取檔案: {error}")
                        else:
                            st.write(f"**資料筆數:** {len(df)}")
                            st.write(f"**欄位數量:** {len(df.columns)}")
                            st.write("**前5筆資料:**")
                            st.dataframe(df.head(), use_container_width=True)

                            with st.expander("欄位資訊"):
                                col_info = pd.DataFrame({
                                    '欄位名稱': df.columns,
                                    '資料型態': df.dtypes,
                                    '非空值數量': df.count(),
                                    '空值數量': df.isnull().sum()
                                })
                                st.dataframe(col_info, use_container_width=True)
                    except Exception as e:
                        st.error(f"預覽失敗: {e}")
