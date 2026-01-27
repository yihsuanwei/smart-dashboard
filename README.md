# 📊 Smart Dashboard - 多檔案數據分析平台

專為 Amazon 業務分析設計的 Streamlit 數據分析工具，支援多種檔案類型的整合分析

## 🎯 功能特色

✅ **多檔案類型支援** - 支援 4 種業務檔案類型分類管理（P0 MCID MBR、Sales Traffic Report、Asin Report、ASIN Trend (YTD)）
✅ **智能檔案分類** - 自動分類存儲不同類型的業務數據
✅ **綜合分析儀表板** - Performance Dashboard 多維度績效分析（銷售、廣告、ASIN）
✅ **客戶指標追蹤** - Metrics Tracker 支援多年度趨勢對比與自訂指標
✅ **賣家快速篩選** - Seller Finder 多維度條件篩選與統計視覺化
✅ **互動式圖表** - 即時篩選和視覺化，支援 YoY/MoM 比較與熱力圖
✅ **可編輯表格** - 支援即時修改數據，自動計算 YoY 反推
✅ **本機運行** - 數據安全不上傳網路，完全離線使用

---



## 🚀 完整安裝 SOP

### 📋 步驟 1：下載並安裝 Python

1. **檢查現有 Python 版本**（如果已安裝）：
   - 按 `Windows鍵 + R`，輸入 `cmd`，按 Enter
   - 輸入 `python --version` 查看版本
   - **如果版本是 3.13.2**，可直接跳到步驟 2

2. **下載 Python 3.13.2**：
   - **必須使用**：[Python 3.13.2 (64-bit)](https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe)


   ✅ **指定版本**：僅支援 Python 3.13.2

   ⚠️ **不支援**：其他版本（包括 3.8-3.12 或 3.13.0/3.13.1）

   💡 **多版本共存**：可以與現有的 Python 版本共存，不需要移除舊版本

3. **安裝時重要設定**：
   - ✅ **必須勾選**「Add Python to PATH」（在第一個安裝畫面底部）
   - 其他選項保持預設即可

### 📂 步驟 2：準備專案檔案

1. **解壓縮**專案檔案到任意目錄（建議桌面）
2. **確認檔案結構**：
```
smart_dashboard_20260112/
├── upload.py             # 主程式（資料處理中心）
├── setup.bat             # 安裝腳本
├── start.bat             # 啟動腳本
├── requirements.txt      # 套件清單
├── utils.py              # 工具函數
├── pages/                # 分析頁面
│   ├── 1_performance_dashboard.py   # Performance Dashboard（多檔案整合分析）
│   ├── 2_metrics_tracker.py         # Metrics Tracker（客戶指標追蹤）
│   └── 3_seller_finder.py           # Seller Finder（賣家查找與篩選）
└── uploaded_data/        # 分類上傳檔案目錄
    ├── p0_mcid_mbr/             # P0 MCID MBR 檔案
    ├── sales_traffic_report/    # 銷售流量報告
    ├── asin_report/             # 商品層級報告
    └── asin_trend/              # ASIN 趨勢資料 (YTD)
```

### ⚙️ 步驟 3：安裝環境

1. **雙擊 setup.bat**
2. **等待安裝完成**（約 2-3 分鐘）
3. **看到「Setup Complete!」**即安裝成功

### 🚀 步驟 4：啟動應用

1. **雙擊 start.bat**
2. **等待黑色視窗顯示**：
   ```
   Streamlit App: http://localhost:8501
   ```
3. **瀏覽器會自動開啟**，或手動前往：http://localhost:8501

### ❌ 步驟 5：關閉應用

- 在黑色視窗按 **Ctrl+C**
- 或直接關閉視窗

---

## 📊 使用指南

### 🏠 主頁面功能

進入應用後，你會看到四個主要功能頁面：

1. **📤 Upload** - 檔案上傳、分類和預處理
2. **📊 Performance Dashboard** - 多檔案整合分析儀表板，展示銷售、廣告、ASIN 等綜合績效
3. **📈 Metrics Tracker** - 客戶指標追蹤與趨勢分析，支援多年度對比
4. **🔍 Seller Finder** - 快速數據瀏覽和篩選分析，可用於篩選指定條件的名單並下載

### 📤 Upload 使用流程

**智能檔案分類系統**
1. 前往「Upload」頁面
2. 選擇 CSV 檔案並選擇檔案類型 (測試的話可用 Sample raw data 的檔案)
   - **P0 MCID MBR** - 請對應 Raw data 檔名
   - **Sales Traffic Report** - 請對應 Raw data 檔名（Overall Sales Summary 會從此檔案動態計算）
   - **Asin Report** - 請對應 Raw data 檔名
   - **ASIN Trend (YTD)** - ASIN 月度銷售趨勢資料

   提醒：一定要選擇正確、對應的檔案類型 
3. 自訂檔名並選擇資料處理選項
4. **點擊「上傳並處理」按鈕**
5. **看到氣球動畫表示上傳成功** 🎈
6. 系統自動分類存儲到對應資料夾

### 📊 Performance Dashboard 使用流程

**⚠️ 使用前準備：**
1. **先前往「Upload」頁面上傳所需檔案**
2. **確保已上傳 4 種不同類型的檔案**：
   - Sales Traffic Report（Overall Sales Summary 會從此檔案動態計算 YTD 指標）
   - P0 MCID MBR
   - Asin Report
   - ASIN Trend (YTD)（可選，用於 ASIN 趨勢分析）

**📊 分析步驟：**
1. **選擇多檔案**：從已上傳的檔案中選擇 4 種不同類型

   💡 **Raw Data 下載準備**：使用 Tampermonkey 腳本下載原始數據

   **🔧 安裝 Tampermonkey 擴充功能**
   - Chrome：前往 [Chrome Web Store](https://chrome.google.com/webstore) 搜尋「Tampermonkey」
   - Firefox：前往 [Firefox Add-ons](https://addons.mozilla.org) 搜尋「Tampermonkey」
   - Edge：前往 [Microsoft Edge Add-ons](https://microsoftedge.microsoft.com/addons) 搜尋「Tampermonkey」

   **📜 安裝數據下載腳本**：
   - 📦 [Inventory ASIN Table Viewer](https://greasyfork.org/zh-TW/scripts/551928-inventory-asin-table-viewer)（含「📈 下載 ASIN 趨勢 (YTD)」按鈕）
   - 📊 [Sales Traffic Business Report Viewer](https://greasyfork.org/zh-TW/scripts/551929-sales-traffic-business-report-viewer)
   - 📈 [Sales Dashboard Viewer](https://greasyfork.org/zh-TW/scripts/551930-sales-dashboard-viewer)

   **📋 數據下載流程**：
   - 登入指定賣家 Amazon Seller Central → 切換英文介面 → 在 landing page 腳本即可啟用 → 一鍵下載 CSV → 檔案分類上傳

2. **📈 Overall Sales Summary**：年度銷售概覽（從 Sales Traffic Report 動態計算）
   - **年份選擇器**：可選擇查看不同年份的 YTD 數據
   - 顯示 6 個關鍵 KPI（2 行 × 3 個）：YTD Sales、Total Order Items、Units Ordered、Sessions、AOV、CVR
   - 月度銷售趨勢圖（多年度對比），支援選擇顯示年份
   - **Actual 表格**：顯示實際銷售數據，YoY 正數綠字、負數紅字
   - **Forecast 表格**：年度銷售預測
     - 已過月份顯示實際數據（黑字），未來月份顯示預估數據（藍字）
     - 輸入全年 YoY 目標，系統智能分配到各月份
     - 支援手動調整各月份 YoY 目標
     - Undo（撤銷）/ Reallocate（重新分配）按鈕

3. **📊 Business Metrics**：業務指標分析
   - 選擇日期查看當月的 Sales、Total Order Items、Sessions、CVR、ASP 等指標
   - 每個指標顯示 YoY 和 MoM 變化百分比
   - 多指標趨勢對比圖表（支援選擇多個指標，每個指標獨立顯示 This Year vs Last Year）

4. **📢 Advertising & Merchandising**：廣告與促銷分析
   - **必選篩選器**：選擇 Customer ID (CID) 和 Marketplace ID
   - 選擇年月查看廣告數據
   - **第一排 KPI**：TACOS、Ads spending、SP ops（含 YoY/MoM 變化）
   - **趨勢圖**：Revenue vs Ads Spending 時間序列對比
   - **第二排 KPI**：Promotion、Deal、Coupon 數量
   - **第三排 KPI**：Promotion OPS、Deal OPS、Coupon OPS（含銷售佔比百分比）

5. **📦 ASIN Level**：商品層級分析
   - Session 和 CVR 的中位數/平均數統計（含 YoY/MoM 變化）
   - **Tab 1 - ASIN 資料表**：
     - **ASIN 銷售貢獻圓餅圖**：顯示 Top 10 ASIN 的銷售貢獻百分比
     - **完整 ASIN 資料表**：
       - 顯示所有 ASIN 的詳細數據（Sales, Sessions, Orders, CVR 等）
       - 支援熱力圖視覺化（不同指標使用不同顏色系統）
       - 自動標示 WOC (Weeks of Coverage) 警示（≤4週顯示粉紅底紅字，>8週顯示紅字）
   - **Tab 2 - 趨勢分析**（需上傳 ASIN Trend (YTD) 檔案）：
     - **TOP 10 排行表格**：並排顯示「最新月份 TOP 10」與「YTD TOP 10」ASIN 及銷售額
     - **預設顯示模式切換**：可選擇「最新月份 TOP 3」或「YTD TOP 3」作為預設顯示
     - **ASIN 銷售趨勢圖**：支援多選 ASIN 顯示趨勢對比
     - **對數刻度選項**：當 ASIN 銷售額差異大時，可開啟 Log Scale 讓所有趨勢線更清晰
     - **月度銷售資料表**：顯示各 ASIN 的月度銷售數據

### 📈 Metrics Tracker 使用流程

**功能說明**：專注於追蹤特定客戶的績效指標與趨勢變化

1. **選擇檔案**：選擇 P0 MCID MBR 類型檔案

2. **篩選客戶**：
   - 輸入 Merchant Customer ID（支援多個 ID，逗號分隔）
   - 選擇 Marketplace ID（可多選）
   - 選擇 Calendar Year（可多選）- 僅影響表格數據
   - 選擇 Calendar Month（可多選）- 僅影響表格數據

3. **數據預覽**：
   - 自訂顯示欄位（預設顯示：year, month, CID, merchant_name, opportunity_owner, ytd/mtd/wtd_ord_gms）
   - 顯示前 100 筆數據
   - 支援按 `mtd_new_fba_ba_90d` 排序
   - **Year/Month 篩選**：只影響表格顯示，不影響下方趨勢圖

4. **趨勢圖表**：
   - 選擇要顯示的業務指標（支援多選，不限數量）
   - 年份控制：動態顯示資料中的可用年份（最多 6 年）
   - 每行顯示 2 個圖表，自動排版
   - 支援所有數值型欄位的趨勢分析
   - **智能數據分離**：圖表不受 Year/Month 篩選影響，保持完整趨勢
   - **百分比自動識別**：TACoS、Rate 等欄位自動以百分比格式顯示

### 🔍 Seller Finder 使用流程

**功能說明**：快速篩選符合特定條件的賣家名單，支援多維度條件組合

1. **選擇檔案**：選擇 P0 MCID MBR 類型檔案

2. **設定篩選條件**（側邊欄）：
   - **🔹 Basic**：calendar_year、calendar_month、marketplace_id、launch_channel、launch_date（日期範圍）
   - **💰 YTD GMS**：YTD Order GMS 範圍（最小值/最大值輸入）
   - **💰 MTD GMS**：MTD Order GMS 範圍（最小值/最大值輸入）
   - **📢 Ads**：
     - MTD TACoS (%) 範圍（最小值/最大值輸入）
     - YTD SP Adopt、MTD SP Active Seller
   - **🎯 Selection Funnel**：
     - **New BA Percentile**（P90/P75/P50/P25）- 標準統計學百分位數
       - P90 = 贏過 90% 的人（保留前 10%）
       - P75 = 贏過 75% 的人（保留前 25%）
       - P50 = 中位數（保留前 50%）
       - P25 = 贏過 25% 的人（保留前 75%）
     - **BA Percentile**（P90/P75/P50/P25）- 標準統計學百分位數
     - **New AWAS/BA %**（Greater than/Less than/Equal to + 閾值百分比）
       - 計算比率：mtd_new_fba_ba_90d / mtd_fba_awas
       - 優先使用 `New_AWAS_BA_%` 欄位（如果存在）
     - **AWAS/BA %**（Greater than/Less than/Equal to + 閾值百分比）
       - 計算比率：mtd_fba_ba / mtd_fba_awas
       - 優先使用 `AWAS_BA_%` 欄位（如果存在）
   - **⚡ Feature Adoption**：is_brand_rep、ytd_pl_launch、is_aplus_adopt、vine_launch_90days、ytd_fba_adopt、ytd_coupon_adopt

3. **查看統計分析**：
   - **可自訂分析指標**：從所有數值欄位中選擇要分析的指標
   - **預設指標**：New_AWAS_BA_%、AWAS_BA_%、mtd_TACoS
   - **視覺化圖表**：
     - 箱型圖（顯示平均值、標準差、異常值）
     - 直方圖（含平均值和中位數標線）
   - **詳細統計表**：樣本數、平均值、P25/P50/P75、標準差、最小值/最大值
   - **智能格式化**：自動識別百分比欄位並正確顯示

4. **數據預覽與下載**：
   - 自訂顯示欄位（預設顯示前 6 個重要欄位：year, month, CID, merchant_name, opportunity_owner, ytd_ord_gms）
   - 支援 CID 搜尋（可輸入多個，逗號分隔）
   - 按 `mtd_new_fba_ba_90d` 排序，顯示前 100 筆
   - **下載篩選後的數據**（CSV 格式）

5. **排除功能**：
   - 可貼上要排除的 Customer ID（支援逗號或換行分隔）
   - 顯示排除前後的數據筆數
   - 預覽排除後的結果
   - **下載排除後的數據**（CSV 格式）

---

## 💻 手動安裝（setup.bat 無法執行時的備用方案）

> ⚠️ **建議優先使用 setup.bat**，只有在批次檔無法執行時才使用此方法

### 🖥️ 步驟 1：開啟命令提示字元（黑色視窗）

<details>
<summary>📖 點擊展開：如何開啟命令提示字元</summary>

**方法一（推薦）：**
1. 按鍵盤上的 `Windows 鍵` + `R`
2. 會彈出「執行」視窗
3. 輸入 `cmd` 然後按 Enter
4. 會出現一個黑色視窗

**方法二：**
1. 點擊左下角的 Windows 開始按鈕
2. 輸入「cmd」或「命令提示字元」
3. 點擊「命令提示字元」

</details>

---

### 📂 步驟 2：前往專案資料夾

在黑色視窗中，輸入以下指令（**需修改路徑**）：

```cmd
cd /d "專案資料夾的完整路徑"
```

<details>
<summary>📖 點擊展開：如何找到專案資料夾路徑</summary>

1. 用檔案總管開啟專案資料夾（就是包含 setup.bat 的那個資料夾）
2. 點擊上方網址列（會顯示類似 `C:\Users\你的名字\Desktop\smart_dashboard_20251009`）
3. 複製這個路徑
4. 貼到指令中，例如：
   ```cmd
   cd /d "C:\Users\John\Desktop\smart_dashboard_20251009"
   ```

</details>

---

### ✅ 步驟 3：確認 Python 已安裝

在黑色視窗輸入：

```cmd
python --version
```

**應該看到：**
```
Python 3.13.2
```

<details>
<summary>❌ 如果出現錯誤訊息</summary>

**看到「python 不是內部或外部命令」？**

這表示 Python 沒有正確安裝或沒有加入 PATH

**解決方法：**
1. 前往 https://python.org 下載 Python
2. 安裝時**務必勾選**「Add Python to PATH」
3. 安裝完成後重新開機
4. 再次執行此步驟

</details>

---

### 🔧 步驟 4：建立獨立環境

在黑色視窗輸入：

```cmd
python -m venv venv
```

**說明：** 這會建立一個名為 `venv` 的資料夾，裡面包含獨立的 Python 環境

⏳ 等待約 10-20 秒，完成後不會有任何訊息

---

### 🚀 步驟 5：啟動獨立環境

在黑色視窗輸入：

```cmd
venv\Scripts\activate
```

**成功的話會看到：**
命令列前面出現 `(venv)`，例如：
```
(venv) C:\Users\John\Desktop\smart_dashboard_20251009>
```

<details>
<summary>❌ 如果出現「無法執行指令碼」錯誤</summary>

**完整錯誤訊息可能是：**
`因為這個系統上已停用指令碼執行，所以無法載入...`

**解決方法：**
1. 關閉目前的命令提示字元
2. 用**系統管理員身份**重新開啟命令提示字元：
   - 在開始功能表搜尋「cmd」
   - 對「命令提示字元」按右鍵
   - 選擇「以系統管理員身份執行」
3. 重複步驟 2-5

</details>

---

### 📦 步驟 6：安裝所需套件

確認命令列前面有 `(venv)` 後，輸入：

```cmd
pip install -r requirements.txt
```

⏳ **這個步驟需要 1-2 分鐘**，會看到很多安裝訊息

**完成後會看到類似：**
```
Successfully installed streamlit-1.49.1 pandas-2.3.2 ...
```

<details>
<summary>❌ 如果安裝失敗</summary>

**可能原因：**
1. 網路連線問題
2. 防毒軟體阻擋

**解決方法：**
1. 檢查網路連線
2. 暫時關閉防毒軟體
3. 重新執行此步驟

</details>

---

### ✅ 步驟 7：驗證安裝

輸入以下指令確認安裝成功：

```cmd
streamlit --version
```

**應該看到類似：**
```
Streamlit, version 1.49.1
```

---

## 🎉 安裝完成！如何啟動應用？

### 每次使用時的啟動步驟：

1. **開啟命令提示字元**（步驟 1）
2. **前往專案資料夾**（步驟 2）
3. **啟動環境：**
   ```cmd
   venv\Scripts\activate
   ```
4. **啟動應用：**
   ```cmd
   streamlit run upload.py --server.port 8501 --server.address localhost
   ```
5. **自動開啟瀏覽器**，網址：http://localhost:8501

### 如何關閉應用？

- 在黑色視窗按 `Ctrl + C`
- 或直接關閉黑色視窗

---

## 💡 小提示

- **保持黑色視窗開啟**：應用執行期間不要關閉命令提示字元視窗
- **想要簡化啟動流程？** 建立 `start.bat` 檔案，內容如下：
  ```batch
  @echo off
  call venv\Scripts\activate
  streamlit run upload.py --server.port 8501 --server.address localhost
  pause
  ```
  之後只要雙擊 `start.bat` 就能啟動

---

## 🔧 常見問題排除

### ❓ 安裝問題

**Q: 出現「python 不是內部或外部命令」？**
A:
1. 重新安裝 Python，務必勾選「Add Python to PATH」
2. 重新開機後再試
3. 手動添加 Python 到環境變數

**Q: pip 安裝套件失敗？**
A:
1. 檢查網路連線
2. 使用國內鏡像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple streamlit pandas plotly`
3. 關閉防毒軟體重試
4. 刪除 `venv` 資料夾後重新執行 `setup.bat`

**Q: 虛擬環境建立失敗？**
A:
1. 確認 Python 已正確安裝並加入 PATH
2. 刪除 `venv` 資料夾
3. 以系統管理員身份執行 `setup.bat`
4. 確認磁碟空間足夠（至少 500MB）

### ❓ 使用問題

**Q: 瀏覽器顯示「This site can't be reached」？**
A:
1. 等待 15-20 秒讓 Streamlit 完全啟動
2. 手動前往 http://localhost:8501
3. 檢查防火牆設定

**Q: CSV 上傳後沒有數據？**
A:
1. 確認 CSV 檔案格式正確
2. 檢查檔案編碼（支援 UTF-8、Big5、GBK）
3. 確認檔案不是空的或損壞

**Q: 圖表顯示異常？**
A:
1. 重新整理頁面
2. 檢查數據欄位是否完整
3. 確認篩選條件不會過濾掉所有數據

**Q: 應用運行緩慢？**
A:
1. 關閉其他佔用記憶體的程式
2. 減少 CSV 檔案大小
3. 重新啟動應用

### ❓ 數據問題

**Q: 如何清除上傳的檔案？**
A: 刪除 `uploaded_data/`、`data/`、`csv_files/` 資料夾內的檔案

**Q: 支援哪些檔案格式？**
A: 目前僅支援 CSV 格式，編碼支援 UTF-8、Big5、GBK

**Q: 數據會被上傳到網路嗎？**
A: 不會，所有數據都在本機處理，完全離線運行

---

## 📋 系統需求

### 💻 硬體需求
- **作業系統**：Windows 10 或 Windows 11
- **記憶體**：至少 4GB RAM（建議 8GB）
- **硬碟空間**：至少 2GB 可用空間
- **處理器**：任何現代 CPU

### 🐍 軟體需求
- **Python**：3.13.2（**僅支援此版本**）
  - ⚠️ **不支援其他版本**（包括 3.8-3.12 或 3.13.0/3.13.1）
- **網路**：安裝時需要網路連線
- **瀏覽器**：Chrome、Firefox、Edge 等現代瀏覽器

---

## 🔒 隱私與安全

- ✅ **完全本機運行**，數據不會離開你的電腦
- ✅ **無需註冊**或提供個人資料
- ✅ **隨時可刪除**所有處理過的檔案
- ✅ **開源透明**，可檢視所有程式碼
- ⚠️ **不建議在公用電腦使用**敏感數據

---

## 🛠️ 開發者資訊

### 📁 專案結構說明
```
upload.py                          # Streamlit 主應用程式（資料處理中心）
pages/
├── 1_performance_dashboard.py     # Performance Dashboard（多檔案整合分析）
├── 2_metrics_tracker.py           # Metrics Tracker（客戶指標追蹤）
└── 3_seller_finder.py             # Seller Finder（賣家查找與篩選）
utils.py                           # 共用工具函數（含檔案分類邏輯）
requirements.txt                   # Python 套件依賴清單
setup.bat                          # Windows 安裝腳本
start.bat                          # Windows 啟動腳本
uploaded_data/                     # 數據存儲目錄
├── p0_mcid_mbr/                   # P0 MCID MBR 檔案
├── sales_traffic_report/          # 銷售流量報告
├── asin_report/                   # 商品層級報告
└── asin_trend/                    # ASIN 趨勢資料 (YTD)
```

### 🔧 自訂修改
如需修改分析邏輯或新增功能：
1. 編輯 `pages/` 目錄下的 Python 檔案
2. 修改 `utils.py` 中的共用函數
3. 重新啟動應用即可看到變更

### 📊 支援的數據欄位
應用會自動識別和處理 CSV 中的業務欄位：
- **時間相關**：calendar_year、calendar_month、reporting_week_of_year
- **地理相關**：marketplace_id、region、launch_channel
- **業務指標**：ytd_ord_gms、mtd_ord_gms、mtd_TACoS、CVR
- **客戶資訊**：merchant_customer_id、merchant_name、nsr_opportunity_owner
- **廣告數據**：mtd_sa_revenue_usd、SP 相關指標
- **Selection Funnel**：mtd_new_fba_ba_90d、mtd_fba_ba、AWAS 相關
- **Feature Adoption**：FBA、A+、Brand Registry 等採用狀況

---

## 📞 技術支援

如遇到問題：
1. 先查看「常見問題排除」章節
2. 確認 Python 和套件版本正確
3. 檢查檔案格式和數據完整性
4. 重新安裝環境

---

**版本 3.3.0** | **更新日期：2026-01-27** | **Overall Sales Summary 動態計算版**

---

## 🆕 版本更新歷史

### 版本 3.3.0 (2026-01-27)

**📊 Performance Dashboard - Overall Sales Summary 大改版**
- **移除 Total Year Change 檔案類型**：不再需要上傳此檔案，改由 Sales Traffic Report 動態計算
  - 檔案類型從 5 種調整為 4 種
  - UI 欄位配置從 3+2 調整為 2+2
- **新增年份選擇器**：可選擇查看不同年份的 YTD 數據
  - 當年：採用 YTD 同期比較（截至今天）
  - 歷史年份：採用全年加總比較
- **KPI 擴充至 6 個**：新增 Sessions、AOV (Average Order Value)、CVR
  - 排版從 1 行 4 個改為 2 行 × 3 個
- **動態 YoY 計算**：根據選擇年份自動計算同期比較

**📈 Metrics Tracker - 年份選擇增強**
- **動態年份選擇**：從資料中自動讀取可用年份（最多支援 6 年）
  - 不再固定為 2024/2025
  - 每個年份使用不同配色，便於區分

### 版本 3.2.2 (2026-01-18)

**📦 ASIN Level - 趨勢分析強化**
- **新增 TOP 10 排行表格**：在趨勢圖上方並排顯示兩個表格
  - 📊 最新月份 TOP 10：顯示當月銷售額最高的 10 個 ASIN
  - 🏆 YTD TOP 10：顯示年度累計銷售額最高的 10 個 ASIN
- **預設顯示模式切換**：Radio Button 可選擇「最新月份 TOP 3」或「YTD TOP 3」
  - 兩種模式都預設顯示 3 個 ASIN，避免圖表過於複雜
- **新增對數刻度選項**：Checkbox 可切換 Y 軸為 Log Scale
  - 解決 ASIN 銷售額差異過大導致趨勢線被壓平的問題
  - 對數刻度下所有 ASIN 趨勢都能清晰可見

### 版本 3.2.1 (2026-01-18)

**📊 Performance Dashboard - Actual/Forecast 表格增強**
- **新增前年資料行**：Actual 和 Forecast 表格新增前年（如 2024）Sales 資料行
  - 現在可同時查看三年數據：前年 → 去年 → 今年
  - 便於長期趨勢比較分析

**🗑️ 移除未使用功能**
- **移除 Month YoY 檔案類型**：此功能無實際資料處理邏輯，已從系統中移除
  - 檔案類型從 6 種調整為 5 種
  - UI 欄位配置從 3+3 調整為 3+2

### 版本 3.2.0 (2026-01-16)

**📊 Performance Dashboard - Forecast 功能**
- **新增 Forecast 表格**：在 Overall Sales Summary 區塊新增年度銷售預測功能
  - 顯示去年 Sales、今年 Sales（實際+預估）、YoY 三列數據
  - **實際 vs 預估區分**：已過月份顯示實際數據（黑字），未來月份顯示預估數據（藍字）
  - **智能 YoY 分配**：輸入全年 YoY 目標後，系統根據去年各月波動模式自動分配到各月份
  - **可編輯月度目標**：支援手動調整各月份 YoY 目標，自動重新計算 Sales
  - **Undo / Reallocate 按鈕**：支援撤銷上一步操作或重新智能分配

**🎨 UI/UX 優化**
- **Actual 表格**：YoY 正數顯示綠字、負數顯示紅字
- **Forecast 表格**：預估值顯示藍字，實際值顯示黑字
- **KPI 與圖表間距優化**：增加 KPI widgets 與年份選擇器之間的間距

**🔧 計算邏輯修正**
- **YoY Sum 計算修正**：改用 `(今年 Sum - 去年 Sum) / 去年 Sum × 100%` 計算全年 YoY
- **YoY Avg 欄位**：顯示 `-`（平均 YoY 百分比無意義）
- **智能分配演算法**：保持去年各月 YoY 波動模式，僅平移至符合全年目標

### 版本 3.1.6 (2025-12-23)

**📊 Performance Dashboard - B2B 數據分析**
- **油猴腳本支援**：ASIN 報表新增 B2B Sales 和 B2B % 欄位（佔整體 GMS 百分比）
- **Dashboard 智慧 B2B 警示**：僅在整體 B2B 佔比超過 5% 時觸發警告並顯示高佔比 ASIN 明細
- **欄位顯示控制**：新增顯示設定功能，可選擇性隱藏 B2B 數據、同期比較、庫存資訊、變化百分比等欄位群組
- **UI 優化**：「ASIN 標記工具」更名為「ASIN 設定與標記」，整合 Tag 管理和欄位顯示設定

### 版本 3.1.5 (2025-11-27)

**📈 Performance Dashboard**
- 新增 TACOS Trend 折線圖，支援 2024 vs 2025 年度對比

### 版本 3.1.4 (2025-11-17)

**🔍 Seller Finder 篩選器優化**
- **GMS 篩選器重新命名**：
  - "💰 GMS" → "💰 YTD GMS"（更明確標示為 Year-to-Date 數據）
- **新增 MTD GMS 篩選器**：
  - 新增 "💰 MTD GMS" 篩選器，支援篩選 `mtd_ord_gms` 欄位
  - 提供最小值/最大值範圍輸入，step 為 1000
  - 與 YTD GMS 篩選器相同的操作邏輯

**📋 篩選邏輯說明**
- **AWAS/BA % 篩選行為**：
  - 當選擇 AWAS/BA % 篩選時，會自動排除沒有數值的資料
  - 只保留有效數值進行比較（NaN 和空值會被過濾）
  - 適用於 New AWAS/BA % 和 AWAS/BA % 兩個篩選器

### 版本 3.1.3 (2025-11-13)

**📈 Metrics Tracker 篩選優化**
- **新增篩選器**：Marketplace 底下加上 Calendar Year 和 Calendar Month 篩選
- **智能數據分離**：Year/Month 篩選僅影響表格，趨勢圖表不受影響
  - 表格：顯示篩選後的特定時段數據
  - 圖表：保持完整 2024-2025 趨勢對比
- **UI 優化**：移除冗餘的篩選提示訊息，介面更簡潔

**🔍 Seller Finder 篩選邏輯修正**
- **修正百分位數邏輯**：改用標準統計學定義
  - P25 = 贏過 25% 的人（保留前 75%）
  - P50 = 贏過 50% 的人（中位數）
  - P75 = 贏過 75% 的人（保留前 25%）
  - P90 = 贏過 90% 的人（保留前 10%）
- **新增 P25 選項**：提供更多篩選彈性
- **優化選項排序**：從 P90 → P75 → P50 → P25，由高到低排列

**🎯 Selection Funnel 數字邏輯調整**
- **修正 BA/AWAS 比率篩選邏輯**：改用正確的比例計算
  - 原邏輯：比較絕對數值（錯誤）
  - 新邏輯：比較比例 `(BA / AWAS)`（正確）
- **優先使用現有欄位**：直接讀取 `New_AWAS_BA_%` 和 `AWAS_BA_%` 欄位
- **篩選器重新命名**：更符合實際欄位名稱
  - "New BA/AWAS% Filter" → "New AWAS/BA %"
  - "BA/AWAS% Filter" → "AWAS/BA %"

### 版本 3.1.2 (2025-11-11)

**🏷️ ASIN 標記功能**
- **新增 ASIN 標記工具**：在 Performance Dashboard 的 ASIN Level 區塊新增標記工具
  - 支援自訂標記（🔴 重點關注、🟡 待優化、🟢 表現良好、🔵 新品）
  - 自動儲存標記到 JSON 檔案，重新整理不會遺失
  - 標記會顯示在完整 ASIN 資料表格的 Tag 欄位中
  - 支援一鍵清空所有標記
- **Performance 分類欄位**：自動根據 Sessions 和 CVR 與中位數比較分類 ASIN
  - 高流量高轉化、高流量低轉化、低流量高轉化、低流量低轉化

**🎨 UI/UX 優化**
- ASIN 標記工具使用淺灰色背景，更清楚的視覺區隔
- 優化按鈕排版和間距，提升操作體驗

### 版本 3.1.1 (2025-11-07)

**⚡ 效能優化**
- **Metrics Tracker 載入速度優化**：
  - 頁面初始載入時僅顯示數據預覽表格，不執行圖表運算
  - 圖表僅在輸入篩選條件（Customer ID 或 Marketplace ID）後才開始渲染
  - 大幅提升初始載入速度，改善使用體驗

### 版本 3.1 (2025-11-07)

**🔄 頁面重新命名與功能調整**
- **Performance Dashboard**（原 Multi File Analysis）：強化多檔案整合分析
- **Metrics Tracker**（原 Performance Review）：新增多年度趨勢對比、可自訂指標圖表
- **Seller Finder**（原 Quick Glance）：增強篩選功能、統計視覺化、多重下載選項

**📊 Performance Dashboard 增強**
- 新增 ASIN Level 熱力圖視覺化（Sales/Sessions/Orders/CVR 不同顏色系統）
- WOC (Weeks of Coverage) 自動警示功能
- Advertising 區塊新增必選篩選器（CID + Marketplace）
- Overall Sales Summary 可編輯表格支援自動計算

**📈 Metrics Tracker 新功能**
- 支援多年度對比（2024 vs 2025）
- 不限圖表數量，每行顯示 2 張自動排版
- 支援所有數值型欄位的趨勢分析
- 新增 Marketplace 多選篩選

**🔍 Seller Finder 強化**
- 新增關鍵指標統計視覺化（箱型圖 + 直方圖）
- 詳細統計表（P25/P50/P75 百分位數）
- 支援 CID 搜尋功能
- 排除功能支援逗號或換行分隔
- 雙重下載選項（篩選後 + 排除後）

### 版本 3.0 (2025-01-14)

**🔥 核心升級**
- **智能檔案分類系統** - 5 種業務檔案類型自動分類管理
- **多檔案整合分析** - Performance Dashboard 整合多數據源
- **可編輯數據表格** - 支援即時修改和自動計算
- **增強的視覺化** - YoY/MoM 對比、趨勢分析、圓餅圖

**📈 分析功能**
- **Overall Sales Summary** - YTD 銷售概覽和月度趨勢
- **Business Metrics** - 多維度業務指標分析
- **Advertising & Merchandising** - 廣告投放效果分析
- **ASIN Level Analysis** - 商品層級深度分析

**🛠️ 技術改進**
- **模組化架構** - 更清晰的頁面分工和功能劃分
- **數據處理優化** - 支援更多數據格式和計算邏輯
- **用戶體驗提升** - 更直觀的操作流程和視覺反饋