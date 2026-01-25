# 🚀 Git 上傳設定指南

## 📋 目前狀態

✅ **已修正** (2026-01-25)
- Git branch 已正確設定在 `main`
- 所有變更已 commit

---

## 🔒 安全性說明（給主管看）

### 一、什麼會被上傳到 GitHub？

| 類型 | 檔案 | 會上傳？ | 說明 |
|------|------|:--------:|------|
| 程式碼 | `*.py` | ✅ | 純邏輯，不含任何數據 |
| 設定檔 | `requirements.txt` | ✅ | 套件清單 |
| 文件 | `README.md` | ✅ | 使用說明 |
| 啟動腳本 | `*.bat` | ✅ | Windows 批次檔 |
| **客戶資料** | `uploaded_data/*` | ❌ | **被 .gitignore 排除** |
| 虛擬環境 | `venv/` | ❌ | 被排除 |
| 快取 | `__pycache__/` | ❌ | 被排除 |

### 二、.gitignore 機制說明

`.gitignore` 是 Git 的標準功能，用於指定哪些檔案/資料夾**永遠不會被追蹤**。

本專案的 `.gitignore` 包含：
```
/uploaded_data
```

這代表：
- ❌ `git add .` 不會加入 uploaded_data
- ❌ `git commit` 不會包含 uploaded_data
- ❌ `git push` 不會上傳 uploaded_data
- ❌ GitHub 上看不到 uploaded_data

### 三、驗證方式

可以用以下指令確認哪些檔案會被追蹤：
```bash
git status
```

如果 `uploaded_data/` 裡有檔案，但 `git status` 沒有顯示它們，就代表 `.gitignore` 正常運作。

### 四、Deploy 後的架構

```
GitHub / Deploy 伺服器          你的電腦 (Local)
├── upload.py                   ├── upload.py
├── pages/                      ├── pages/
├── utils.py                    ├── utils.py
├── requirements.txt            ├── requirements.txt
├── uploaded_data/ (空的)       ├── uploaded_data/
│   └── (無檔案)                │   ├── 客戶A.csv ← 只存在這裡
│                               │   ├── 客戶B.csv ← 只存在這裡
│                               │   └── ...
```

**結論**：
- GitHub 上只有「空殼程式」
- 客戶資料永遠只存在使用者自己的電腦
- 每個使用者的資料互相獨立，不會互相看到

---

## 🚀 上傳到 GitHub 步驟

### Step 1：建立 GitHub Repository

1. 前往 https://github.com/new
2. Repository name: `smart-dashboard`（或你喜歡的名稱）
3. 選擇 **Private**（私有）⚠️ 重要！
4. **不要勾選**任何初始化選項（README、.gitignore、license 都不要勾）
5. 點擊 **Create repository**

### Step 2：連結並上傳

在專案資料夾執行：
```bash
git remote add origin https://github.com/你的帳號/smart-dashboard.git
git push -u origin main
```

首次 push 會要求登入 GitHub。

---

## 📤 日後更新流程

每次修改 code 後：

```bash
git add .
git commit -m "更新說明"
git push
```

---

## 👥 同事如何取得

```bash
git clone https://github.com/你的帳號/smart-dashboard.git
```

之後更新：

```bash
git pull
```

---

## ❓ 問題討論區

---

### Q1: 「不在任何 branch 上」是什麼意思？

**簡單解釋**：
Git 用 branch（分支）來管理不同版本的 code。正常情況下你應該在某個 branch 上工作（通常叫 `main` 或 `master`）。

「Detached HEAD」就像你在看一本書的某一頁，但沒有用書籤標記。你可以看，但如果翻頁就找不回來了。

**為什麼會這樣**：
可能之前執行過 `git checkout <某個 commit>` 去看舊版本，然後忘了切回來。

**怎麼修**：
```bash
git checkout -b main
```
這會建立一個叫 `main` 的 branch，並把目前的狀態保存在這個 branch 上。

---

### Q2: Deploy 也是安全的嗎？客戶資料可以存在 local 嗎？

**答案：是的，兩者都安全。**

**原理說明**：

```
你的電腦 (Local)
├── 程式碼 (.py 檔案)     → 會上傳到 GitHub / Deploy
├── uploaded_data/        → 不會上傳（被 .gitignore 排除）
│   ├── 客戶A的CSV
│   ├── 客戶B的CSV
│   └── ...
└── venv/                 → 不會上傳
```

**Deploy 後的運作方式**：

| 環境 | 程式碼 | 客戶資料 |
|------|--------|----------|
| GitHub | ✅ 有 | ❌ 沒有 |
| Deploy 伺服器 | ✅ 有 | ❌ 沒有（空的 uploaded_data 資料夾） |
| 你的電腦 | ✅ 有 | ✅ 有 |
| 同事的電腦 | ✅ 有（git clone） | ❌ 沒有（需自己上傳） |

**結論**：
- ✅ GitHub 上傳安全
- ✅ Deploy 安全（只有空殼程式）
- ✅ 客戶資料繼續存在你的 local，不受影響
- ✅ 每個人的 `uploaded_data/` 是獨立的，互不影響

---

### Q3: 數據運算在哪裡執行？有風險嗎？

**答案：所有運算都在「執行程式的那台電腦」上進行。**

```
┌─────────────────────────────────────────────────────────────┐
│  你的電腦 (Local 模式)                                        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                  │
│  │ Raw CSV │ →  │ Python  │ →  │ 瀏覽器  │                  │
│  │ (資料)  │    │ (運算)  │    │ (顯示)  │                  │
│  └─────────┘    └─────────┘    └─────────┘                  │
│       ↑              ↑              ↑                        │
│    你的檔案      你的電腦CPU     localhost:8501              │
│                                                              │
│  ✅ 資料不離開你的電腦                                        │
└─────────────────────────────────────────────────────────────┘
```

**風險評估**：
- ✅ Local 模式：零風險，資料不經過網路
- ⚠️ Deploy 到雲端：資料會上傳到伺服器運算（見 Q4）

---

### Q4: Dashboard 變成網頁 vs Git Clone 的差異？

這是兩種完全不同的使用方式：

**方式 A：Git Clone（目前的方式）**
```
每個人的電腦
├── 自己 clone 程式碼
├── 自己安裝 Python 環境
├── 自己上傳 CSV
├── 自己執行 streamlit run
└── 資料只在自己電腦上 ✅ 安全
```

**方式 B：Deploy 到雲端（變成網頁）**
```
雲端伺服器 (例如 Streamlit Cloud)
├── 程式碼在伺服器上
├── 使用者透過網址訪問
├── 使用者上傳 CSV → 傳到伺服器
├── 伺服器運算 → 回傳結果
└── 資料會經過伺服器 ⚠️ 需評估風險
```

**比較表**：

| 項目 | Git Clone (Local) | Deploy (雲端網頁) |
|------|-------------------|-------------------|
| 使用方式 | 每人裝在自己電腦 | 開網址就能用 |
| 安裝難度 | 需要裝 Python | 不用裝任何東西 |
| 資料位置 | 只在自己電腦 | 會傳到伺服器 |
| 資料安全 | ✅ 最安全 | ⚠️ 需信任伺服器 |
| 適合場景 | 敏感客戶資料 | 內部工具/非敏感資料 |
| 維護方式 | 每人自己 git pull | 你更新，大家自動用新版 |

**建議**：
- 如果資料涉及客戶機密 → 用 **Git Clone (Local)** 模式
- 如果只是內部非敏感資料 → 可考慮 **Deploy**
- 折衷方案：Deploy 到 **Amazon 內部伺服器**（資料不離開公司網路）

---

### Q5: Deploy vs Git Clone 實際操作比較

**你的理想情境**：Deploy 成網頁，大家開網址就能用

**現實考量**：資料會經過伺服器，需評估安全性

---

**三種方案比較：**

| 方案 | 同事怎麼用 | 更新流程 | 資料安全 | 麻煩程度 |
|------|-----------|---------|---------|---------|
| A. 直接傳檔案 | 收到 zip → 解壓 → 跑 | 你傳檔 → 他們換檔 | ✅ 最安全 | 😫 最麻煩 |
| B. Git Clone | 首次 clone → 之後 `git pull` | 你 push → 他們 pull | ✅ 安全 | 😐 中等 |
| C. Deploy 網頁 | 開網址就用 | 你 push → 自動更新 | ⚠️ 需評估 | 😊 最輕鬆 |

---

**方案 B 實際流程（Git Clone）：**

```
首次設定（一次性）：
同事執行 → git clone https://github.com/你的帳號/smart-dashboard.git
         → cd smart-dashboard
         → setup.bat（安裝環境）

日常使用：
同事執行 → start.bat（啟動 dashboard）

你更新後：
你通知   → "我更新了，請 pull"
同事執行 → git pull（一行指令，2 秒完成）
```

**比傳檔案好在哪？**
- 傳檔案：下載 zip → 解壓 → 覆蓋舊檔 → 可能搞混版本
- Git pull：一行指令，自動合併，保留他們自己的 uploaded_data

---

**方案 C：Deploy 到內部伺服器（折衷方案）**

如果想要「開網址就用」但又要安全，可以考慮：

| Deploy 目標 | 資料安全性 | 說明 |
|------------|-----------|------|
| Streamlit Cloud（公開） | ⚠️ 資料到外部伺服器 | 不建議放客戶資料 |
| Amazon 內部伺服器 | ✅ 資料不離開公司網路 | 需要 IT 協助設定 |
| 自己的 EC2 | ✅ 你控制伺服器 | 需要一些 DevOps 知識 |

---

### Q6: update.bat 是什麼？詳細解釋

**概念**：把「打指令」這件事變成「雙擊一個檔案」

---

**目前同事要更新的步驟（手動）：**
```
1. 打開命令提示字元（黑色視窗）
2. cd 到專案資料夾
3. 輸入 git pull
4. 輸入 venv\Scripts\activate
5. 輸入 streamlit run upload.py --server.port 8501 --server.address localhost
```
→ 對不熟的人來說很麻煩，容易打錯

---

**有了 update.bat 之後：**
```
1. 雙擊 update.bat
2. 完成 ✅
```
→ 電腦自動執行上面所有步驟

---

**update.bat 裡面長這樣：**
```batch
@echo off
echo 正在檢查更新...
git pull
echo.
echo 正在啟動 Smart Dashboard...
call venv\Scripts\activate
streamlit run upload.py --server.port 8501 --server.address localhost
pause
```

---

**完整流程圖解：**

```
┌─────────────────────────────────────────────────────────────────┐
│  首次設定（同事只做一次）                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 安裝 Git        → https://git-scm.com/download/win          │
│     （下載 → 一直按下一步 → 完成）                                 │
│                                                                  │
│  2. 安裝 Python     → 你給他們的 README 裡有連結                   │
│     （記得勾 Add to PATH）                                        │
│                                                                  │
│  3. Clone 專案      → 在想放的資料夾，右鍵 → Git Bash Here        │
│                     → 輸入：git clone https://github.com/xxx     │
│                                                                  │
│  4. 安裝環境        → 雙擊 setup.bat                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                         設定完成！
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  日常使用（每次都這樣）                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  想用 Dashboard？  → 雙擊 start.bat                              │
│                                                                  │
│  你說有更新？      → 雙擊 update.bat（會自動更新 + 啟動）          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

**同事資料夾裡會有這些 .bat 檔：**

| 檔案 | 功能 | 什麼時候用 |
|------|------|-----------|
| `setup.bat` | 安裝 Python 環境 | 首次設定，只用一次 |
| `start.bat` | 啟動 Dashboard | 平常使用 |
| `update.bat` | 更新程式 + 啟動 | 你說有新版本時 |

---

**你的工作流程：**

```
你改好 code
    ↓
git add .
git commit -m "修了什麼"
git push
    ↓
跟同事說：「更新了，雙擊 update.bat」
    ↓
同事雙擊 update.bat → 自動完成
```

---

要我現在幫你建立 `update.bat` 嗎？

---

### Q7: （在這裡繼續提問）

<!-- 寫下你的問題 -->

