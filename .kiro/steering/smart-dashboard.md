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
3. 驗證結果寫在下方「驗證紀錄」區塊

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

---

## 驗證紀錄

### 2026-04-05 — CTC 公式修正（第二次）
- 問題 1：CTC 分母用 delta 而非 GMS 總量 → 修正為 `esm_gms_curr`
- 問題 2：DB 只有 MM tier 賣家，ESM 總量 $4.3M vs 全體 $19.5M → 改為匯入全部賣家
- 驗證結果：Universe Home Inc WoW CTC = -0.1348%，CSV = -0.13%，差異 < 0.01%（四捨五入）✅
- GMS 驗證：DB ESM W13 = $19,516,959.99，跟 PKEY CSV 全體一致 ✅

### 2026-04-05 — CTC 分母修正（第一次）
- 問題：Dashboard CTC 分母只用 filtered 賣家的 delta
- 修正：改用 ESM 全體
- 結果：仍有差異，因為 DB 只有 MM tier → 觸發第二次修正
