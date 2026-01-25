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

### Q3: （在這裡繼續提問）

<!-- 寫下你的問題 -->

