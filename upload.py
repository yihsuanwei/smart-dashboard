import streamlit as st
import pandas as pd
from utils import list_uploaded_files, load_data, UPLOAD_DIR, FILE_TYPES, detect_file_type


def normalize_customer_id(series: pd.Series) -> pd.Series:
    """把 merchant_customer_id 清洗成純字串（去掉 .0 / 空白）"""
    return (
        series.apply(lambda x: str(int(float(x))) if pd.notnull(x) else "")
        .str.strip()
    )


def add_calculated_columns(df):
    """添加計算欄位"""
    if "mtd_new_fba_ba_90d_awas" in df.columns and "mtd_new_fba_ba_90d" in df.columns:
        df["New_AWAS_BA_%"] = df.apply(
            lambda row: (row["mtd_new_fba_ba_90d_awas"] / row["mtd_new_fba_ba_90d"])
            if pd.notnull(row["mtd_new_fba_ba_90d_awas"]) and pd.notnull(row["mtd_new_fba_ba_90d"]) and row["mtd_new_fba_ba_90d"] != 0
            else None,
            axis=1
        )
    if "mtd_fba_awas" in df.columns and "mtd_fba_ba" in df.columns:
        df["AWAS_BA_%"] = df.apply(
            lambda row: (row["mtd_fba_awas"] / row["mtd_fba_ba"])
            if pd.notnull(row["mtd_fba_awas"]) and pd.notnull(row["mtd_fba_ba"]) and row["mtd_fba_ba"] != 0
            else None,
            axis=1
        )
    if "mtd_sa_revenue_usd" in df.columns and "mtd_ord_gms" in df.columns:
        df = df.copy()
        df["mtd_TACoS"] = df.apply(
            lambda row: (row["mtd_sa_revenue_usd"] / row["mtd_ord_gms"] * 100)
            if pd.notnull(row["mtd_sa_revenue_usd"]) and pd.notnull(row["mtd_ord_gms"]) and row["mtd_ord_gms"] != 0
            else None,
            axis=1
        )
    return df


def parse_input_list(input_text):
    items = []
    for line in input_text.strip().split('\n'):
        line = line.strip()
        if ',' in line:
            items.extend([item.strip() for item in line.split(',') if item.strip()])
        elif line:
            items.append(line)
    return items


def process_and_save(uploaded_file, file_type, custom_filename,
                     option_filter_owner=False, owners_input="",
                     option_latest_customer=False,
                     option_filter_customer=False, customer_ids_input=""):
    """處理單一檔案並儲存，回傳 (success: bool, message: str)"""
    safe_filename = "".join(c for c in custom_filename if c.isalnum() or c in (' ', '-', '_')).strip()
    if not safe_filename:
        return False, "檔名包含無效字元"

    final_filename = f"{safe_filename}.csv"
    target_folder = UPLOAD_DIR / FILE_TYPES[file_type]
    target_folder.mkdir(exist_ok=True)
    target_path = target_folder / final_filename

    df, error = load_data(uploaded_file)
    if error:
        return False, error

    original_count = len(df)

    # 1. 清洗 merchant_customer_id
    if "merchant_customer_id" in df.columns:
        df["merchant_customer_id"] = normalize_customer_id(df["merchant_customer_id"])

    # 2. 篩選 nsr_opportunity_owner
    if option_filter_owner and owners_input.strip() and "nsr_opportunity_owner" in df.columns:
        input_owners = parse_input_list(owners_input)
        if input_owners:
            df = df[df["nsr_opportunity_owner"].isin(input_owners)]

    # 3. 篩選特定 merchant_customer_id
    if option_filter_customer and customer_ids_input.strip() and "merchant_customer_id" in df.columns:
        input_ids = parse_input_list(customer_ids_input)
        if input_ids:
            df = df[df["merchant_customer_id"].isin(input_ids)]

    # 4. 只保留最新一筆
    if option_latest_customer and "merchant_customer_id" in df.columns:
        if "calendar_year" in df.columns and "calendar_month" in df.columns and "marketplace_id" in df.columns:
            df['calendar_year'] = pd.to_numeric(df['calendar_year'], errors='coerce')
            df['calendar_month'] = pd.to_numeric(df['calendar_month'], errors='coerce')
            df = df.sort_values(['calendar_year', 'calendar_month'], ascending=True)
            df = df.groupby(['merchant_customer_id', 'marketplace_id'], as_index=False).tail(1)

    # 5. 添加計算欄位
    df = add_calculated_columns(df)

    # 儲存
    try:
        df.to_csv(target_path, index=False, encoding="utf-8")
        return True, f"✅ {final_filename} → {file_type}（{original_count} → {len(df)} 筆）"
    except Exception as e:
        return False, f"存檔失敗: {str(e)}"


# ===== Streamlit UI =====
st.set_page_config(page_title="Smart Dashboard - 資料處理", page_icon="📊", layout="wide")
st.title("📤 資料處理中心")
st.markdown("上傳CSV檔案並進行資料處理，處理後的檔案可在其他頁面中使用")

UPLOAD_DIR.mkdir(exist_ok=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📁 檔案上傳")
    uploaded_files = st.file_uploader(
        "選擇CSV檔案（可複選）",
        type=['csv'],
        accept_multiple_files=True,
        help="支援UTF-8、Big5、GBK編碼，可一次選擇多個檔案"
    )

    if uploaded_files:
        st.markdown(f"已選擇 **{len(uploaded_files)}** 個檔案")

        # --- 為每個檔案建立偵測結果與設定 ---
        file_configs = []
        has_p0 = False

        for idx, uf in enumerate(uploaded_files):
            detected = detect_file_type(uf.name)
            detected_label = detected if detected else "⚠️ 無法辨識"

            with st.expander(f"📄 {uf.name}　→　{detected_label}", expanded=(detected is None)):
                # 文件類型選擇（預設為偵測結果）
                type_options = list(FILE_TYPES.keys())
                if detected and detected in type_options:
                    default_idx = type_options.index(detected)
                else:
                    default_idx = 0  # 預設第一個

                file_type = st.selectbox(
                    "文件類型",
                    options=type_options,
                    index=default_idx,
                    key=f"type_{idx}"
                )

                # 自定義檔名
                custom_filename = st.text_input(
                    "檔名（不含 .csv）",
                    value=uf.name.replace('.csv', ''),
                    key=f"name_{idx}"
                )

                # 檢查是否已存在
                safe_fn = "".join(c for c in custom_filename if c.isalnum() or c in (' ', '-', '_')).strip()
                if safe_fn:
                    check_path = UPLOAD_DIR / FILE_TYPES[file_type] / f"{safe_fn}.csv"
                    if check_path.exists():
                        st.warning(f"⚠️ 檔案已存在，上傳會覆蓋")

                file_configs.append({
                    "file": uf,
                    "file_type": file_type,
                    "custom_filename": custom_filename,
                    "idx": idx,
                })

                if file_type == "P0 MCID MBR":
                    has_p0 = True

        # --- P0 MCID MBR 專用篩選選項（全域，套用到所有 P0 檔案）---
        option_filter_owner = False
        owners_input = ""
        option_latest_customer = False
        option_filter_customer = False
        customer_ids_input = ""

        if has_p0:
            st.divider()
            st.markdown("#### ⚙️ P0 MCID MBR 處理選項")
            st.caption("以下選項會套用到所有 P0 MCID MBR 類型的檔案")

            option_filter_owner = st.checkbox(
                "篩選 nsr_opportunity_owner",
                value=False,
                help="只保留指定業務人員的資料"
            )
            if option_filter_owner:
                owners_input = st.text_area(
                    "輸入要保留的 nsr_opportunity_owner",
                    help="一行一個，或用逗號分隔",
                    placeholder="例如：Albert Lin,Alex Kuo",
                    value="Albert Lin,Alex Kuo,Chien Lee,Davy Chen,Hans Huang,Jamie Fan,Jessica Tsai,Kai Tung,Raul Lai,Susie Shih,Che-Wei Chang,Crystal Lin,Eddie Chu,Jenny Kao,Karen Hou,Shelly Huang,Silvia Lien"
                )

            option_latest_customer = st.checkbox(
                "只保留最新一筆 merchant_customer_id",
                value=False,
            )

            option_filter_customer = st.checkbox(
                "篩選特定 merchant_customer_id",
                value=False,
            )
            if option_filter_customer:
                customer_ids_input = st.text_area(
                    "輸入要保留的 merchant_customer_id",
                    help="一行一個ID，或用逗號分隔",
                )

        # --- 上傳按鈕 ---
        st.divider()
        if st.button("🚀 全部上傳並處理", type="primary", use_container_width=True):
            results = []
            progress = st.progress(0)
            for i, cfg in enumerate(file_configs):
                is_p0 = cfg["file_type"] == "P0 MCID MBR"
                success, msg = process_and_save(
                    cfg["file"],
                    cfg["file_type"],
                    cfg["custom_filename"],
                    option_filter_owner=option_filter_owner if is_p0 else False,
                    owners_input=owners_input if is_p0 else "",
                    option_latest_customer=option_latest_customer if is_p0 else False,
                    option_filter_customer=option_filter_customer if is_p0 else False,
                    customer_ids_input=customer_ids_input if is_p0 else "",
                )
                results.append((success, msg))
                progress.progress((i + 1) / len(file_configs))

            # 顯示結果
            success_count = sum(1 for s, _ in results if s)
            fail_count = len(results) - success_count

            if fail_count == 0:
                st.success(f"全部完成 ✅ 共 {success_count} 個檔案")
                st.balloons()
            else:
                st.warning(f"完成 {success_count} 個，失敗 {fail_count} 個")

            for success, msg in results:
                if success:
                    st.write(msg)
                else:
                    st.error(f"❌ {msg}")


with col2:
    st.subheader("📋 已上傳的檔案")
    existing_files = list_uploaded_files()

    if not existing_files:
        st.info("尚未上傳任何檔案")
    else:
        for i, file_path in enumerate(existing_files):
            file_type_display = "未分類"
            for type_name, folder_name in FILE_TYPES.items():
                if file_path.parent.name == folder_name:
                    file_type_display = type_name
                    break

            with st.expander(f"📄 {file_path.name} ({file_type_display})"):
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

                if st.checkbox(f"預覽資料", key=f"preview_{i}"):
                    try:
                        df, error = load_data(file_path)
                        if error:
                            st.error(f"無法讀取檔案: {error}")
                        else:
                            st.write(f"**資料筆數:** {len(df)}　**欄位數量:** {len(df.columns)}")
                            st.dataframe(df.head(), use_container_width=True)
                    except Exception as e:
                        st.error(f"預覽失敗: {e}")
