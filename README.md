# 📊 Smart Dashboard - 多檔案數據分析平台

專為 Amazon 業務分析設計的 Streamlit 數據分析工具，支援多種檔案類型的整合分析

## 🎯 功能特色

✅ **多檔案類型支援** - 支援 5 種業務檔案類型分類管理
✅ **智能檔案分類** - 自動分類存儲不同類型的業務數據
✅ **綜合分析儀表板** - Spark Performance Review 多維度分析
✅ **互動式圖表** - 即時篩選和視覺化，支援 YoY/MoM 比較
✅ **本機運行** - 數據安全不上傳網路
✅ **多頁面分析** - 資料處理、快速瀏覽、績效評估、多檔案分析

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
smart_dashboard_20251011/
├── upload.py             # 主程式（資料處理中心）
├── setup.bat             # 安裝腳本
├── start.bat             # 啟動腳本
├── requirements.txt      # 套件清單
├── utils.py              # 工具函數
├── pages/                # 分析頁面
│   ├── quick_glance.py          # 快速瀏覽分析
│   ├── performance_review.py    # 績效評估
│   └── multi_file_analysis.py   # 多檔案整合分析
└── uploaded_data/        # 分類上傳檔案目錄
    ├── p0_mcid_mbr/             # P0 MCID MBR 檔案
    ├── sales_traffic_report/    # 銷售流量報告
    ├── total_year_change/       # 年度變化數據
    ├── month_yoy/               # 月度同比數據
    └── asin_report/             # 商品層級報告
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
2. **📊 Multi File Analysis** - 多檔案整合分析，主要看指定單一客戶的 Performance
3. **👤 Performance Review** - 客戶績效評估和趨勢分析 (待更新)
4. **📑 Quick Glance** - 快速數據瀏覽和篩選分析，可用於篩選指定條件的名單並下載

### 📤 Upload 使用流程

**智能檔案分類系統**
1. 前往「Upload」頁面
2. 選擇 CSV 檔案並選擇檔案類型 (測試的話可用 Sample raw data 的檔案)
   - **P0 MCID MBR** - 請對應 Raw data 檔名
   - **Sales Traffic Report** - 請對應 Raw data 檔名
   - **Total Year Change** - 請對應 Raw data 檔名
   - **Month YoY** - 請對應 Raw data 檔名
   - **Asin Report** - 請對應 Raw data 檔名
   
   提醒：一定要選擇正確、對應的檔案類型 
3. 自訂檔名並選擇資料處理選項
4. **點擊「上傳並處理」按鈕**
5. **看到氣球動畫表示上傳成功** 🎈
6. 系統自動分類存儲到對應資料夾

### 📊 Multi File Analysis 使用流程

**⚠️ 使用前準備：**
1. **先前往「Upload」頁面上傳所需檔案**
2. **確保已上傳 5 種不同類型的檔案**：
   - Sales Traffic Report
   - Total Year Change  
   - Month YoY
   - P0 MCID MBR
   - Asin Report

**📊 分析步驟：**
1. **選擇多檔案**：從已上傳的檔案中選擇 5 種不同類型
   
   💡 **Raw Data 下載準備**：使用 Tampermonkey 腳本下載原始數據
   
   **🔧 安裝 Tampermonkey 擴充功能**
   - Chrome：前往 [Chrome Web Store](https://chrome.google.com/webstore) 搜尋「Tampermonkey」
   - Firefox：前往 [Firefox Add-ons](https://addons.mozilla.org) 搜尋「Tampermonkey」
   - Edge：前往 [Microsoft Edge Add-ons](https://microsoftedge.microsoft.com/addons) 搜尋「Tampermonkey」
   
   **📜 安裝數據下載腳本**：
   - 📦 [Inventory ASIN Table Viewer](https://greasyfork.org/zh-TW/scripts/551928-inventory-asin-table-viewer) 
   - 📊 [Sales Traffic Business Report Viewer](https://greasyfork.org/zh-TW/scripts/551929-sales-traffic-business-report-viewer) 
   - 📈 [Sales Dashboard Viewer](https://greasyfork.org/zh-TW/scripts/551930-sales-dashboard-viewer)
   
   **📋 數據下載流程**：
   - 登入指定賣家 Amazon Seller Central → 切換英文介面 → 在 landing page 腳本即可啟用 → 一鍵下載 CSV → 檔案分類上傳
2. **Overall Sales Summary**：功能說明
   - YTD Sales、Total Order Items 等 KPI
   - 月度銷售趨勢圖（支援可編輯表格）
3. **Business Metrics**：功能說明
   - 選擇日期查看 Sales、CVR、Sessions 等指標
   - 多指標趨勢對比圖表
4. **Advertising & Merchandising**：功能說明
   - 輸入 MCID，選擇市場、年月查看數據
   - Ads Spend & Revenue 趨勢圖
5. **ASIN Level**：功能說明
   - Session 和 CVR 的中位數/平均數分析
   - ASIN 銷售貢獻圓餅圖

### 📑 Quick Glance 使用流程

1. **選擇檔案**：選擇 P0 MCID MBR 類型檔案
2. **設定篩選條件**：
   - Basic：年份、市場、渠道
   - GMS：YTD Order GMS 範圍
   - Ads：TACoS、SP 採用率等
   - Selection Funnel：BA、AWAS 相關指標
   - Feature Adoption：品牌代表、A+ 等功能採用
3. **查看統計**：關鍵指標統計（平均值、百分位數）
4. **數據預覽**：可自訂顯示欄位，支援 CID 搜尋
5. **排除功能**：可排除特定 Customer ID

### 👤 Performance Review 使用流程

1. **選擇檔案**：選擇 P0 MCID MBR 類型檔案
2. **輸入 Customer ID**：可輸入多個 ID（逗號分隔）
3. **查看 KPI**：MTD GMS、TACoS 等關鍵指標
4. **趨勢分析**：支援多指標、多年份對比圖表
5. **自訂分析**：可選擇顯示欄位和圖表指標

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
upload.py                 # Streamlit 主應用程式（資料處理中心）
pages/
├── quick_glance.py       # 快速瀏覽分析頁面
├── performance_review.py # 績效評估頁面
└── multi_file_analysis.py # 多檔案整合分析頁面
utils.py                  # 共用工具函數（含檔案分類邏輯）
requirements.txt          # Python 套件依賴清單
setup.bat                # Windows 安裝腳本
start.bat                # Windows 啟動腳本
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

**版本 3.0** | **更新日期：2025-01-14** | **多檔案整合分析版本**

---

## 🆕 版本 3.0 新功能

### 🔥 核心升級
- **智能檔案分類系統** - 5 種業務檔案類型自動分類管理
- **Spark Performance Review** - 多檔案整合分析儀表板
- **可編輯數據表格** - 支援即時修改和自動計算
- **增強的視覺化** - YoY/MoM 對比、趨勢分析、圓餅圖

### 📈 分析功能
- **Overall Sales Summary** - YTD 銷售概覽和月度趨勢
- **Business Metrics** - 多維度業務指標分析
- **Advertising & Merchandising** - 廣告投放效果分析
- **ASIN Level Analysis** - 商品層級深度分析

### 🛠️ 技術改進
- **模組化架構** - 更清晰的頁面分工和功能劃分
- **數據處理優化** - 支援更多數據格式和計算邏輯
- **用戶體驗提升** - 更直觀的操作流程和視覺反饋