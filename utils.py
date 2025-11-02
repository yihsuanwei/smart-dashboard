import pandas as pd
import os
from pathlib import Path


UPLOAD_DIR = Path("uploaded_data")
UPLOAD_DIR.mkdir(exist_ok=True)

# 文件類型對應的子資料夾
FILE_TYPES = {
    "P0 MCID MBR": "p0_mcid_mbr",
    "Sales Traffic Report": "sales_traffic_report",
    "Total Year Change": "total_year_change",
    "Month YoY": "month_yoy",
    "Asin Report": "asin_report",
}

# 創建所有子資料夾
for folder_name in FILE_TYPES.values():
    (UPLOAD_DIR / folder_name).mkdir(exist_ok=True)

def load_data(file):
    """讀取 CSV"""
    try:
        for encoding in ['utf-8', 'big5', 'gbk']:
            try:
                df = pd.read_csv(file, encoding=encoding)
                return df, None
            except UnicodeDecodeError:
                continue
        return None, "無法讀取檔案編碼"
    except Exception as e:
        return None, f"讀取檔案失敗: {str(e)}"


def normalize_customer_id(series: pd.Series) -> pd.Series:
    """把 merchant_customer_id 清洗成純字串（去掉 .0 / 空白）"""
    return (
        series.apply(lambda x: str(int(float(x))) if pd.notnull(x) else "")
        .str.strip()
    )


def list_uploaded_files(file_type=None):
    """列出已存的 CSV 檔（按修改時間排序，最新的在前）"""
    if file_type and file_type in FILE_TYPES:
        folder_path = UPLOAD_DIR / FILE_TYPES[file_type]
        files = list(folder_path.glob("*.csv"))
    else:
        # 如果沒指定類型，列出所有子資料夾中的檔案
        all_files = []
        for folder_name in FILE_TYPES.values():
            folder_path = UPLOAD_DIR / folder_name
            all_files.extend(folder_path.glob("*.csv"))
        # 也包含根目錄的檔案（舊檔案相容性）
        all_files.extend(UPLOAD_DIR.glob("*.csv"))
        files = all_files

    # 按照修改時間排序，最新的在前
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return files


def add_calculated_columns(df):
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
