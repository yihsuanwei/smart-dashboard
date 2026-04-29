import pandas as pd
import json
import os
import sqlite3
from pathlib import Path


UPLOAD_DIR = Path("uploaded_data")
UPLOAD_DIR.mkdir(exist_ok=True)

SELLER_REGISTRY_PATH = UPLOAD_DIR / "seller_registry.json"

# ivory-cli 的 crm.db 路徑（smart-dashboard 直接讀同一個 db）
CRM_DB_PATH = Path(__file__).resolve().parent.parent / "ivory-cli" / "data" / "crm.db"


def get_seller_meta(mcid: str) -> dict:
    """從 crm.db 撈指定 MCID 的 meta 資料（LINE 綁定、配合度、owner 等）。

    回傳 dict，撈不到就回傳空 dict（讓呼叫端用 .get() 安全存取）。
    """
    if not mcid or not CRM_DB_PATH.exists():
        return {}
    try:
        conn = sqlite3.connect(str(CRM_DB_PATH))
        row = conn.execute(
            "SELECT mcid, name, owner, cooperation_level, line_bindind "
            "FROM sellers WHERE mcid = ?",
            (str(mcid),),
        ).fetchone()
        conn.close()
        if row is None:
            return {}
        return {
            "mcid": row[0],
            "name": row[1],
            "owner": row[2],
            "cooperation_level": row[3] or "",
            "line_bindind": int(row[4]) if row[4] is not None else 0,
        }
    except sqlite3.OperationalError:
        return {}


# 文件類型對應的子資料夾（移除 Total Year Change，改由 Sales Traffic Report 動態計算）
FILE_TYPES = {
    "P0 MCID MBR": "p0_mcid_mbr",
    "Sales Traffic Report": "sales_traffic_report",
    "Asin Report": "asin_report",
    "ASIN Trend (YTD)": "asin_trend",
}

# 創建所有子資料夾
for folder_name in FILE_TYPES.values():
    (UPLOAD_DIR / folder_name).mkdir(exist_ok=True)

def load_data(file):
    """讀取 CSV（上傳時用，file 是 UploadedFile 或 Path）"""
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


def load_data_fast(file_path):
    """優先讀 Parquet，fallback 讀 CSV。回傳 (df, error)。
    
    file_path: Path 物件（可以是 .csv 或 .parquet）
    如果傳入 .csv，會自動檢查同名 .parquet 是否存在。
    """
    file_path = Path(file_path)
    
    # 決定 parquet 路徑
    if file_path.suffix == '.parquet':
        pq_path = file_path
        csv_path = file_path.with_suffix('.csv')
    else:
        csv_path = file_path
        pq_path = file_path.with_suffix('.parquet')
    
    # 優先讀 parquet
    if pq_path.exists():
        try:
            df = pd.read_parquet(pq_path)
            return df, None
        except Exception:
            pass  # fallback to CSV
    
    # Fallback: 讀 CSV
    if csv_path.exists():
        return load_data(csv_path)
    
    return None, f"找不到檔案: {file_path}"


def save_with_parquet(df, csv_path):
    """同時存 CSV + Parquet。CSV 保留給下載，Parquet 給 dashboard 快速讀取。"""
    csv_path = Path(csv_path)
    pq_path = csv_path.with_suffix('.parquet')
    
    # 存 CSV（保留給使用者下載）
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    # 存 Parquet（dashboard 讀取用）
    try:
        df.to_parquet(pq_path, index=False)
    except Exception:
        pass  # Parquet 存失敗不影響主流程，下次讀 CSV 就好


def normalize_customer_id(series: pd.Series) -> pd.Series:
    """把 merchant_customer_id 清洗成純字串（去掉 .0 / 空白）"""
    return (
        series.apply(lambda x: str(int(float(x))) if pd.notnull(x) else "")
        .str.strip()
    )


def list_uploaded_files(file_type=None):
    """列出已存的資料檔（按修改時間排序，最新的在前）
    
    優先回傳 .parquet，如果沒有才回傳 .csv。
    同一個檔名只回傳一個（parquet 優先）。
    """
    def _collect_files(folder_path):
        """收集資料夾中的檔案，parquet 優先、去重"""
        csv_files = {f.stem: f for f in folder_path.glob("*.csv")}
        pq_files = {f.stem: f for f in folder_path.glob("*.parquet")}
        # parquet 覆蓋 csv（同名時優先用 parquet）
        merged = {**csv_files, **pq_files}
        return list(merged.values())
    
    if file_type and file_type in FILE_TYPES:
        folder_path = UPLOAD_DIR / FILE_TYPES[file_type]
        files = _collect_files(folder_path)
    else:
        all_files = []
        for folder_name in FILE_TYPES.values():
            folder_path = UPLOAD_DIR / folder_name
            all_files.extend(_collect_files(folder_path))
        # 也包含根目錄的檔案（舊檔案相容性）
        all_files.extend(UPLOAD_DIR.glob("*.csv"))
        files = all_files

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

def detect_file_type(filename: str):
    """根據檔名關鍵字自動偵測文件類型，回傳 FILE_TYPES 的 key 或 None"""
    name = filename.upper()
    if "SALES_TRAFFIC_REPORT" in name or "SALES TRAFFIC REPORT" in name:
        return "Sales Traffic Report"
    if "ASIN_REPORT" in name or "ASIN REPORT" in name or "LASTMONTHTABLE" in name:
        return "Asin Report"
    if "ASIN_TREND" in name or "ASIN TREND" in name or "TREND_YTD" in name:
        return "ASIN Trend (YTD)"
    if "P0" in name or "MCID" in name:
        return "P0 MCID MBR"
    return None


# ===== Seller Registry（僅存 MCID 對應）=====

def load_seller_registry():
    """載入賣家 MCID 對應表"""
    if SELLER_REGISTRY_PATH.exists():
        with open(SELLER_REGISTRY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_seller_registry(registry):
    """儲存賣家 MCID 對應表"""
    with open(SELLER_REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def set_seller_mcid(seller_key, mcid):
    """設定某個賣家的 MCID"""
    registry = load_seller_registry()
    registry[seller_key] = mcid
    save_seller_registry(registry)


def get_seller_mcid(seller_key):
    """取得某個賣家的 MCID"""
    registry = load_seller_registry()
    return registry.get(seller_key, "")


def _extract_seller_name(filename, file_type_key):
    """從檔名提取賣家名稱
    
    檔名格式: YYYY-MM-DD_賣家名稱_檔案類型.csv
    策略: 去掉日期前綴，去掉檔案類型關鍵字，剩下的就是賣家名稱
    
    也處理:
    - 重複下載的 " 1", " 2" 後綴 (如 Report 1.csv)
    - 異常前綴 (如 "TR 12months2026-01-18_...")
    """
    import re
    stem = Path(filename).stem  # 去掉 .csv
    
    # 先移除尾部的重複下載編號 (空格+數字，如 " 1", " 2")
    stem = re.sub(r'\s+\d+$', '', stem)
    
    # 去掉日期前綴 (YYYY-MM-DD_)
    # 也處理日期前面有垃圾前綴的情況 (如 "TR 12months2026-01-18_")
    stem = re.sub(r'^.*?\d{4}-\d{2}-\d{2}_', '', stem)
    
    # 如果沒有日期前綴（整個 stem 沒變），跳過這個檔案
    if stem == Path(filename).stem or not stem:
        return None
    
    # 檔案類型關鍵字（用來從檔名尾部移除，長的放前面優先匹配）
    type_keywords = [
        'ASIN_Report_lastMonthTable',
        'Sales_Traffic_Report', 'Sales Traffic Report',
        'ASIN_Report', 'ASIN Report',
        'ASIN_Trend_YTD', 'ASIN_Trend', 'ASIN Trend',
        'P0_MCID_MBR', 'MCID_MBR', 'MBR',
    ]
    
    for kw in type_keywords:
        # 移除尾部的類型關鍵字（不分大小寫）
        pattern = re.compile(re.escape(kw) + r'$', re.IGNORECASE)
        stem = pattern.sub('', stem)
    
    # 清理尾部的底線和空白
    stem = stem.strip('_ ')
    
    return stem if stem else None


def scan_sellers_from_files():
    """掃描 uploaded_data/ 各子資料夾，從檔名自動提取所有賣家名稱
    
    回傳 sorted list of seller_key strings
    """
    sellers = set()
    
    for file_type, folder_name in FILE_TYPES.items():
        folder_path = UPLOAD_DIR / folder_name
        if not folder_path.exists():
            continue
        
        for f in list(folder_path.glob("*.csv")) + list(folder_path.glob("*.parquet")):
            seller = _extract_seller_name(f.name, file_type)
            if seller:
                sellers.add(seller)
    
    return sorted(sellers, key=lambda x: x.lower())


def get_seller_list():
    """取得所有賣家列表（自動偵測 + MCID），按最新檔案時間排序
    
    回傳 [(display_name, seller_key, mcid), ...]，最近有資料更新的賣家排在前面
    """
    sellers = scan_sellers_from_files()
    registry = load_seller_registry()
    
    # 計算每個賣家最新檔案的修改時間
    def _latest_mtime(seller_key):
        latest = 0
        for folder_name in FILE_TYPES.values():
            folder_path = UPLOAD_DIR / folder_name
            if not folder_path.exists():
                continue
            for f in list(folder_path.glob("*.csv")) + list(folder_path.glob("*.parquet")):
                if seller_key in f.stem:
                    mtime = f.stat().st_mtime
                    if mtime > latest:
                        latest = mtime
        return latest
    
    # 按最新檔案時間排序（最新的在前）
    sellers_with_time = [(s, _latest_mtime(s)) for s in sellers]
    sellers_with_time.sort(key=lambda x: x[1], reverse=True)
    
    result = []
    for seller_key, _ in sellers_with_time:
        display_name = seller_key.replace('_', ' ')
        mcid = registry.get(seller_key, "")
        result.append((display_name, seller_key, mcid))
    
    return result


def find_seller_files(seller_key, file_type=None):
    """找出某個賣家在各資料夾中最新的檔案（parquet 優先）
    
    回傳 dict: {file_type: Path} 只包含找到的類型
    """
    result = {}
    search_types = {file_type: FILE_TYPES[file_type]} if file_type else FILE_TYPES
    
    for ft, folder_name in search_types.items():
        folder_path = UPLOAD_DIR / folder_name
        if not folder_path.exists():
            continue
        
        # 找出檔名包含 seller_key 的檔案（csv + parquet）
        matching_csv = [f for f in folder_path.glob("*.csv") if seller_key in f.stem]
        matching_pq = [f for f in folder_path.glob("*.parquet") if seller_key in f.stem]
        
        # 合併，parquet 優先（同名去重）
        by_stem = {f.stem: f for f in matching_csv}
        by_stem.update({f.stem: f for f in matching_pq})
        matching = list(by_stem.values())
        
        if matching:
            matching.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            result[ft] = matching[0]
    
    return result
