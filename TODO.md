# TODO

功能需求與討論。你寫需求，我在下方回覆。

---

<!-- 在這裡寫你想改的功能，格式隨意 -->

## 1. Upload MCID tagging

> upload MCID tagging 功能，目前太複雜，想要 user 上傳檔案以後用彈窗跳出讓user輸入，這在上一個版本有做過，你查一下。另外要有一個機制是，如果先前已經上傳過檔案，要有地方可以補CID

**Kiro 回覆：**

目前 upload 頁底部有一個 expander「MCID 管理」，用 data_editor 列出所有賣家讓你編輯。你覺得這個太複雜，想改成：

- **上傳後彈窗**：上傳完成後跳 `st.dialog`，列出這次上傳偵測到的賣家，讓 user 直接填 MCID（之前做過，後來被你退回說想改到 upload 頁用 expander）
- **補填機制**：已上傳但沒填 MCID 的賣家，保留一個地方可以補

問題是：你之前退回彈窗是因為「UI 要簡單」。現在是想回到彈窗方案嗎？還是 expander 保留但簡化？彈窗

請確認方向，我再動手。

---

## 2. Dashboard 選擇客戶 UI

> 選擇客戶下拉選單太長、不需要 CID 下面那條切線。簡單來說 UI 醜

**Kiro 回覆：**

目前的問題：
- `st.selectbox` 佔了半頁寬（`st.columns([1, 1])` 的左半邊）
- MCID 顯示在下方用 `st.caption`
- 下面有一條 `st.markdown("---")` 分隔線

我的提案：
- 把選擇客戶縮窄，例如 `st.columns([1, 2])` 甚至 `[1, 3]`，讓下拉選單短一點
- MCID 放在同一行右邊，不換行
- 移除 MCID 下方的分隔線

這樣可以嗎？或者你有其他想法？

Performance Dashboard MCID 顯示得太小，顏色也不對 UI 不好看