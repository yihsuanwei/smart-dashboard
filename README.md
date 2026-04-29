# Smart Dashboard

> 最後更新：2026-04-09

Ivory 的 Streamlit Dashboard，直接讀 ivory-cli 的 `crm.db`，不需要上傳 CSV。

---

## 啟動

```bash
cd C:\Users\ivorywei\Documents\Work\Tools\smart-dashboard
streamlit run Home.py
```

---

## 頁面結構

| 頁面 | 檔案 | 做什麼 |
|------|------|--------|
| Home | `Home.py` | 首頁 |
| Performance Dashboard | `pages/1_performance_dashboard.py` | P0 MBR 績效儀表板（讀 uploaded_data/ 的 Parquet） |
| CRM Dashboard | `pages/4_crm_dashboard.py` | CRM 賣家管理 + 績效分析（讀 crm.db） |

---

## CRM Dashboard 架構

### 資料來源

| DB 表 | 來源 | 用途 | 欄位數 |
|-------|------|------|--------|
| `sellers` | sync-pkey / sync-mbr 自動建立 | 賣家基本資料 + metadata | ~21 欄 |
| `performance_data` | sync-pkey（WBR PKEY） | 週度績效 | 19 欄 |
| `performance_monthly` | sync-mbr（MBR PKEY mapped） | 月度績效（精簡版） | 31 欄 |
| `pkey_raw_monthly` | sync-mbr（MBR PKEY 全量） | 月度績效（全量 144 欄） | 145 欄 |
| `notes` | ivory-cli crm log / CRM Note Server | 互動紀錄 | 7 欄 |

### Tab 結構

#### Tab 1: Performance
- 群體切換：Ignite / MM-MASS / SPARK
- 數據來源切換：WBR (Weekly) / MBR (Monthly)
- KPI 卡片：GMS、YoY、YTD GMS、Ads OPS、Promo OPS、BA
- 趨勢圖：最近 8 週或可用月份的 GMS 折線圖
- Key metrics YoY sparkline 卡片（WBR 8 項 / MBR 12 項）
- Seller detail table：該群體的賣家績效明細
  - 所有群體皆含：GMS WoW/MoM、GMS YoY、CTC WoW/MoM、CTC YoY（正綠負紅）
  - CTC 公式：(該賣家 GMS 變化) ÷ (群體前期總 GMS) × 100%，全部加總 = 整體變化率
  - 欄位表頭有 hover tooltip 說明公式與範例
- MBR 全量底表（expander）：展開才載入 `pkey_raw_monthly` 144 欄

#### Tab 2: 賣家清單
- 搜尋框（名稱 / MCID）
- 顯示：MCID、名稱、Owner、Tier、Q1/Q2 AM、GMS、Latest Note

#### Tab 3: SPARK 管理
- Q1 SPARK 客戶總覽（固定 34 家，不受全域篩選影響）
- by Owner / by Tier 分佈
- 賣家明細 + 績效 + GMS MoM / YoY / CTC MoM / CTC YoY（正綠負紅）+ Latest Note

#### Tab 4: 底表
- MBR 全量 (Monthly)：讀 `pkey_raw_monthly`，144 欄全量
  - 月份選擇器
  - 篩選器：Sub Tier / AM / Product Group / 搜尋
  - Lazy loading：預設前 200 筆（GMS 排序），開「顯示全部」才載入全量
- WBR (Weekly)：讀 `sellers` + `performance_data`
  - 篩選器：Q1 AM / Q2 AM / 配合度 / 搜尋

### 效能設計

| 策略 | 做什麼 |
|------|--------|
| SQL 層篩選 | 篩選和搜尋在 SQL WHERE 完成，不載入全量到 Python |
| LIMIT | 底表預設只載入前 200 筆，開 toggle 才載入全部 |
| `@st.cache_data(ttl=120)` | 所有查詢結果快取 120 秒 |
| 篩選器選項獨立查詢 | 用 SQL DISTINCT 取選項，不需要先載入資料 |
| Lazy load tabs | 績效資料只在對應 tab 被點開時才載入 |
| Expander | MBR 全量底表放在 expander 裡，展開才查詢 |

### DB 維護

`db_maintenance()` 函式（在 `ivory-cli/lib/db.py`）：
- `performance_monthly`：只保留最近 12 個月
- `performance_data`：只保留最近 26 週
- `pkey_raw_monthly`：全量保留（不清理）
- VACUUM：壓縮碎片空間

---

## 主題設定

`.streamlit/config.toml` 控制所有視覺樣式，不用 CSS/HTML。

---

## 相依

- `crm.db` 路徑：`~/Documents/Work/Tools/ivory-cli/data/crm.db`
- 唯讀連線（`?mode=ro`），不會改 DB
- ivory-cli 的 sync-pkey / sync-mbr 負責寫入資料
