---
inclusion: fileMatch
fileMatchPattern: "**/Smart Dashboard/**"
---

# Smart Dashboard Steering

## TODO 規則

每次修改 Smart Dashboard 的程式碼時：
1. 先讀 `TODO.md` 確認要做什麼
2. 做完後更新 TODO 狀態（`[ ]` → `[-]` 等你驗證）
3. 如果改動涉及數字計算，必須跑驗證（見下方）
4. 更新本檔案的「計算邏輯文件」區塊

## 數字驗證規則

任何涉及數字計算的改動，必須：
1. 跟 wbr_pipeline 的 mover_shaker.csv 交叉驗證
2. 抽查至少 3 個賣家的 GMS、WoW delta、CTC
3. 跑 `python run.py crm verify`（在 ivory-cli 目錄下），確保 db 跟 xlsx 對得上
4. 驗證結果寫在下方「驗證紀錄」區塊

## 計算邏輯文件

### GMS
- 來源：crm.db → performance_data 表
- 邏輯：同一個 (mcid, year, week) 跨 marketplace 加總
- 對應 wbr_pipeline：`seller_data[(year, week, mid)]['wtd_ord_gms']`（已加總所有 marketplace）

### WoW%
- 計算：(W_curr GMS / W_prev GMS - 1) × 100
- W_prev = 當前週 - 1（如 W13 vs W12）

### YoY%
- 計算：(W_curr_2026 GMS / W_curr_2025 GMS - 1) × 100

### CTC (Contribution to Change)
- WoW CTC = 賣家的 WoW delta / ESM 全體當週 GMS 總量 × 100
- YoY CTC = 賣家的 YoY delta / ESM 全體去年同週 GMS 總量 × 100
- **分母是 ESM 全體賣家的 GMS 總量**（不是 delta），跟 wbr_pipeline 一致
- wbr_pipeline 公式：`wow_ctc = wow_delta / esm_gms_curr * 100`
- Dashboard 公式：`wow_ctc = wow_delta / esm_gms_curr * 100`（已修正一致）
- DB 現在匯入所有賣家（不只 MM tier），確保 ESM 總量跟 wbr_pipeline 一致

### sync-pkey 匯入範圍
- 匯入 PKEY CSV 中所有賣家（不篩選 sub team）
- 非 MM tier 的賣家也會存入 db，用於 CTC 分母計算
- tier 欄位：TIER_MAP 有對應就用（如 rock、silver），沒有就用 sub team 原值

### 資料新鮮度（2026-05-06 加強）
ivory-cli 現在有三層防禦確保 db 永遠同步到 xlsx 最新資料：
1. **Layer 1**：`_read_pkey_rows` 的 parquet cache 用 xlsx.size + xlsx.mtime sidecar 驗證（`*.meta.json`），任一不同就重讀 xlsx
2. **Layer 2**：`sync-weekly.bat` 開頭刪 parquet + meta，強迫從 xlsx 重讀
3. **Layer 3**：sync 完跑 `python run.py crm verify`，比對 db 最新週/月 GMS vs xlsx，不一致就 exit code 1

Dashboard 讀 db 即可——db 的數字正確性由 ivory-cli 的 verify 保證。

---

## 驗證紀錄

### 2026-05-06 — parquet cache staleness bug 修復
- **問題**：WBR xlsx 已有 W17 資料但 db 還停在 W16
- **根因**：`_read_pkey_rows` 的 cache 判斷用 `parquet.mtime >= xlsx.mtime`。W:\ 複製 xlsx 到本地時保留原始 mtime，xlsx 內容被覆蓋但 mtime 沒變，parquet cache 就永遠命中舊資料
- **修復**：
  - Layer 1：cache 判斷改用 `xlsx.size + xlsx.mtime` fingerprint，寫 `.meta.json` sidecar，讀 cache 前比對
  - Layer 2：`sync-weekly.bat` 同步前先刪 parquet + meta
  - Layer 3：新增 `python run.py crm verify` 指令，比對 db vs xlsx GMS 總量
  - 同時修 `run.py sync-pkey` 自動偵測：只挑 xlsx/csv，不挑 parquet（避免繞過 cache 驗證）
  - 同時修 `lib/weekly_sync.py` 的公槽 vs 本地比對，從只看 mtime 改成 size + mtime
- **驗證結果**：
  - W11~W17 逐週比對，DB vs xlsx 差異 = $0.00 ✓
  - 2026-01 ~ 2026-04 MBR 逐月比對，差異 = $0.00 ✓
  - 資料新鮮度：db 最新週 W17 = xlsx 最新週 W17 ✓
  - 資料新鮮度：db 最新月 2026-04 = xlsx 最新月 2026-04 ✓

### 2026-04-05 — CTC 公式修正（第二次）
- 問題 1：CTC 分母用 delta 而非 GMS 總量 → 修正為 `esm_gms_curr`
- 問題 2：DB 只有 MM tier 賣家，ESM 總量 $4.3M vs 全體 $19.5M → 改為匯入全部賣家
- 驗證結果：Universe Home Inc WoW CTC = -0.1348%，CSV = -0.13%，差異 < 0.01%（四捨五入）✅
- GMS 驗證：DB ESM W13 = $19,516,959.99，跟 PKEY CSV 全體一致 ✅

### 2026-04-05 — CTC 分母修正（第一次）
- 問題：Dashboard CTC 分母只用 filtered 賣家的 delta
- 修正：改用 ESM 全體
- 結果：仍有差異，因為 DB 只有 MM tier → 觸發第二次修正
