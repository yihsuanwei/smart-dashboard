"""AI Insight via AWS Bedrock (Claude Opus 4.7)

Streamlit-friendly helpers that summarize a section's data, send it to Claude on
Bedrock, and render the response under the section header.

認證走 AWS_PROFILE=claude-code-DO-NOT-DELETE（已透過 ada credential_process 設好），
不需要 API key。Midway cookie 過期會回 ExpiredTokenException，提示跑 mwinit。

用法（caller 端）：
    clicked = ai_insight.ai_button("overall")           # 在 header 旁邊
    # ... 區塊渲染、累積數據 ...
    if clicked:
        prompt = ai_insight.build_overall_prompt(...)   # 用累積好的數據
        ai_insight.show_result("overall", prompt)
    ai_insight.show_cached("overall")                   # 顯示上次結果（rerun 後仍可見）
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import boto3
import pandas as pd
import streamlit as st
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

INSIGHTS_DIR = Path(__file__).resolve().parent / "ai_insights"

# Bedrock cross-region inference profile for Opus 4.7 in us-west-2.
# 第一次跑若 ValidationException，把這條換成 AWS console → Bedrock → Inference profiles 顯示的字串。
MODEL_ID = "us.anthropic.claude-opus-4-7"
REGION = os.environ.get("AWS_REGION", "us-west-2")

SYSTEM_PROMPT = """你是 Amazon 賣家經營顧問。針對用戶提供的 dashboard 區塊數據做分析。

規則：
- 用繁體中文回覆
- 結論先講（第一行就給 takeaway），再列 2–3 個支撐論點
- 每個論點必須引用具體數字（YoY%、MoM%、絕對值）
- 如果數據不足以下結論，明說「資料不足」而不是硬掰
- 全文 250 字以內，不要 preamble、不要客套
"""


def _bedrock_client():
    """每次都建新 client + 強制 boto3 重抓 credentials。
    （不快取 — 否則 mwinit 後 streamlit 還是用舊 session 的過期憑證。）"""
    session = boto3.session.Session()
    return session.client("bedrock-runtime", region_name=REGION)


def _invoke(user_prompt: str, max_tokens: int = 1024, system: str = SYSTEM_PROMPT) -> str:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    resp = _bedrock_client().invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
    )
    payload = json.loads(resp["body"].read())
    text = payload["content"][0]["text"]
    stop_reason = payload.get("stop_reason", "")
    if stop_reason == "max_tokens":
        # 讓上層知道被截斷，可以選擇重試或處理
        raise ValueError(
            f"回應在 {max_tokens} tokens 處被截斷（stop_reason=max_tokens）。"
            f"已收到 {len(text)} 字元。"
        )
    return text


def _df_to_markdown(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df is None or df.empty:
        return "(no data)"
    truncated = df.head(max_rows)
    try:
        return truncated.to_markdown(index=False)
    except Exception:
        return truncated.to_string(index=False)


def ai_button(section_key: str, label: str = "AI 分析") -> bool:
    """Render the trigger button (tertiary style — small, no fill)."""
    return st.button(
        label,
        key=f"btn_{section_key}",
        type="tertiary",
        icon=":material/auto_awesome:",
    )


def header_with_ai(
    title: str,
    section_key: str,
    level: str = "header",
    icon: str | None = None,
) -> bool:
    """Render a header with the AI button glued to its right side.

    level: "header" (h2) or "subheader" (h3) — matches st.header / st.subheader
    icon: optional :material/xxx: prefix
    """
    title_text = f"{icon} {title}" if icon else title
    with st.container(horizontal=True, vertical_alignment="bottom", gap="small"):
        if level == "subheader":
            st.subheader(title_text, width="content")
        else:
            st.header(title_text, width="content")
        return ai_button(section_key)


def _run_mwinit(force: bool = True, timeout: int = 120) -> tuple[bool, str]:
    """在背景跑 mwinit -f 觸發瀏覽器 SSO + YubiKey。回傳 (success, message)"""
    cmd = ["mwinit", "-f"] if force else ["mwinit"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0:
            return True, (r.stdout or "Mwinit success").strip()
        return False, (r.stderr or r.stdout or f"exit {r.returncode}").strip()
    except FileNotFoundError:
        return False, "找不到 `mwinit` 指令 — 請確認已安裝 Midway CLI。"
    except subprocess.TimeoutExpired:
        return False, f"mwinit 超過 {timeout} 秒沒完成，請改在 PowerShell 跑 `mwinit -f`。"
    except Exception as e:
        return False, f"執行 mwinit 失敗：{e}"


def _is_credential_error(code: str) -> bool:
    return code in (
        "ExpiredTokenException",
        "UnrecognizedClientException",
        "InvalidSignatureException",
        "InvalidClientTokenId",
    )


def _is_credential_exception(e: Exception) -> bool:
    if isinstance(e, NoCredentialsError):
        return True
    if isinstance(e, ClientError):
        code = e.response.get("Error", {}).get("Code", "")
        return _is_credential_error(code)
    if isinstance(e, BotoCoreError):
        msg = str(e)
        return "ExpiredToken" in msg or "credential" in msg.lower()
    return False


def _format_client_error(e: Exception) -> str:
    if isinstance(e, ClientError):
        code = e.response.get("Error", {}).get("Code", "")
        if code == "ValidationException":
            return f"Bedrock model ID 無效：`{MODEL_ID}`\n\n錯誤：{e}"
        if code == "AccessDeniedException":
            return "沒有 Bedrock 權限。檢查 AWS profile 是否能 invoke 這個 model。"
        return f"Bedrock 錯誤（{code}）：{e}"
    return f"AWS SDK 錯誤：{e}"


def _manual_mwinit_button(section_key: str) -> None:
    """auto mwinit 失敗時的 fallback：手動按鈕。"""
    if st.button(
        "重試 mwinit",
        key=f"mwinit_retry_{section_key}",
        icon=":material/key:",
        type="secondary",
    ):
        with st.spinner("等你完成瀏覽器 SSO + 碰 YubiKey…"):
            ok, msg = _run_mwinit()
        if ok:
            st.success(f"驗證成功！再按一次「AI 分析」即可。\n\n{msg}")
        else:
            st.error(f"mwinit 失敗：{msg}\n\n請改在 PowerShell 手動跑 `mwinit -f`。")


def show_result(section_key: str, prompt: str) -> None:
    """Call Bedrock. 若憑證過期 → 自動跑 mwinit -f → 自動重試一次。"""
    state_key = f"ai_insight_{section_key}"

    # 第一次嘗試
    try:
        with st.spinner("Claude Opus 4.7 分析中…（約 10–30 秒）"):
            result = _invoke(prompt)
        st.session_state[state_key] = result
        return
    except Exception as e:
        if not _is_credential_exception(e):
            st.error(_format_client_error(e))
            return
        first_error = e

    # 憑證過期 → 自動跑 mwinit
    st.warning("AWS 憑證過期，自動觸發 mwinit — 請完成瀏覽器 SSO + 碰一下 YubiKey。")
    with st.spinner("等你完成瀏覽器 SSO + 碰 YubiKey…（最多 120 秒）"):
        ok, msg = _run_mwinit()
    if not ok:
        st.error(f"自動 mwinit 失敗：{msg}")
        _manual_mwinit_button(section_key)
        return

    st.info("mwinit 成功，自動重試 AI 分析…")
    try:
        with st.spinner("Claude Opus 4.7 分析中…（約 10–30 秒）"):
            result = _invoke(prompt)
        st.session_state[state_key] = result
    except Exception as e:
        if _is_credential_exception(e):
            st.error("mwinit 完成但憑證仍無效，可能是 ada 還沒重簽。等 5 秒再試一次。")
            _manual_mwinit_button(section_key)
        else:
            st.error(_format_client_error(e))


def _safe_filename(s: str) -> str:
    s = re.sub(r"[^\w一-鿿\-]+", "_", s.strip())
    return s[:80] or "unknown"


def _insights_path(seller_name: str) -> Path:
    INSIGHTS_DIR.mkdir(exist_ok=True)
    return INSIGHTS_DIR / f"{_safe_filename(seller_name)}.json"


def _load_saved(seller_name: str) -> list[dict]:
    path = _insights_path(seller_name)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_insight(seller_name: str, section: str, content: str, note: str = "") -> dict:
    path = _insights_path(seller_name)
    items = _load_saved(seller_name)
    entry = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "seller": seller_name,
        "section": section,
        "content": content,
        "note": note,
    }
    items.append(entry)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry


def _delete_insight(seller_name: str, entry_id: str) -> None:
    path = _insights_path(seller_name)
    items = _load_saved(seller_name)
    items = [it for it in items if it.get("id") != entry_id]
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


SECTION_LABELS = {
    "overall": "Overall Sales Summary",
    "business_metrics": "Business Metrics",
    "asin_level": "ASIN Level",
    "asin_table": "Complete ASIN Data",
    "annual_target": "Annual Sales Target",
    "advertising": "Advertising & Merchandising",
}


def show_cached(section_key: str, seller_name: str = "") -> None:
    """Render the most recent result (if any) + 儲存按鈕 + 歷史 expander。"""
    state_key = f"ai_insight_{section_key}"
    saved_flag_key = f"saved_{section_key}_{seller_name}"
    section_label = SECTION_LABELS.get(section_key, section_key)

    has_current = state_key in st.session_state
    history = []
    if seller_name:
        history = [it for it in _load_saved(seller_name)
                   if it.get("section") == section_label]

    if not has_current and not history:
        return

    # 與上方區塊隔開
    st.space("medium")

    # 顯示當前 session 的 AI 結果 + 儲存按鈕
    if has_current:
        with st.container(border=True):
            st.markdown(
                f"**:material/psychology: AI Insight**\n\n{st.session_state[state_key]}"
            )

            if seller_name:
                st.space("small")
                col_note, col_save = st.columns([3, 1], vertical_alignment="bottom")
                with col_note:
                    note = st.text_input(
                        "備註（選填）",
                        key=f"note_{section_key}_{seller_name}",
                        placeholder="例：8月對焦給 Sarah 用",
                    )
                with col_save:
                    if st.button(
                        "儲存",
                        key=f"save_{section_key}_{seller_name}",
                        icon=":material/save:",
                        type="secondary",
                    ):
                        _save_insight(
                            seller_name=seller_name,
                            section=section_label,
                            content=st.session_state[state_key],
                            note=note,
                        )
                        st.session_state[saved_flag_key] = True
                        st.rerun()

            if st.session_state.pop(saved_flag_key, False):
                st.toast("已儲存", icon=":material/check_circle:")

    # 顯示這個賣家的歷史 insight
    if history:
        with st.expander(
            f"已儲存的歷史 Insight（{len(history)} 筆）",
            icon=":material/folder_open:",
        ):
            for entry in reversed(history):
                with st.container(border=True):
                    saved_at = entry.get("saved_at", "")
                    note = entry.get("note", "")
                    header = f"**{saved_at}**" + (f" — _{note}_" if note else "")
                    st.markdown(header)
                    st.markdown(entry.get("content", ""))
                    if st.button(
                        "刪除",
                        key=f"del_{section_key}_{seller_name}_{entry['id']}",
                        icon=":material/delete:",
                        type="tertiary",
                    ):
                        _delete_insight(seller_name, entry["id"])
                        st.rerun()


# ============================================================
# Prompt builders
# ============================================================


def build_overall_prompt(seller_name: str, year: Any, kpi_rows: list[dict]) -> str:
    """kpi_rows: [{"name": "YTD Sales", "value": 1234567, "yoy_pct": 12.3, "is_bps": False}, ...]"""
    lines = ["| 指標 | 當期值 | YoY |", "|---|---|---|"]
    for r in kpi_rows:
        if r.get("yoy_pct") is None:
            yoy = "-"
        elif r.get("is_bps"):
            yoy = f"{r['yoy_pct']:+.0f} bps"
        else:
            yoy = f"{r['yoy_pct']:+.1f}%"
        val = r.get("value", "-")
        if isinstance(val, (int, float)):
            val = f"{val:,.2f}" if r.get("decimal") else f"{val:,.0f}"
        lines.append(f"| {r['name']} | {val} | {yoy} |")
    table = "\n".join(lines)
    return (
        f"賣家：{seller_name}\n年份：{year}\n區塊：Overall Sales Summary (YTD vs 去年同期)\n\n"
        f"{table}\n\n"
        "請找出 1–2 個最值得注意的指標（不論好壞），說明意義，並給一個下一步建議。"
    )


def build_business_metrics_prompt(
    seller_name: str,
    selected_date: str,
    rows: list[dict],
) -> str:
    """rows: [{"name": "Sales", "value": 12345, "yoy_pct": 12.3, "mom_pct": -2.1, "is_bps": False, "decimal": False}, ...]"""
    lines = ["| 指標 | 當期值 | YoY | MoM |", "|---|---|---|---|"]
    for r in rows:
        def _fmt(pct, is_bps):
            if pct is None:
                return "-"
            return f"{pct:+.0f} bps" if is_bps else f"{pct:+.1f}%"
        yoy = _fmt(r.get("yoy_pct"), r.get("is_bps", False))
        mom = _fmt(r.get("mom_pct"), r.get("is_bps", False))
        val = r.get("value", "-")
        if isinstance(val, (int, float)):
            val = f"{val:,.2f}" if r.get("decimal") else f"{val:,.0f}"
        lines.append(f"| {r['name']} | {val} | {yoy} | {mom} |")
    table = "\n".join(lines)
    return (
        f"賣家：{seller_name}\n區間：{selected_date}（vs 上月 / 去年同期）\n區塊：Business Metrics\n\n"
        f"{table}\n\n"
        "請判斷：銷售變化主要是因為流量(Sessions)、轉換率(CVR)還是客單價(AOV/ASP)？"
        "結論先講、引用具體 YoY/MoM%、最後給 1 個改善方向。"
    )


def build_action_plan_prompt(seller_name: str, insights: list[dict]) -> str:
    """合併賣家所有儲存的 insights，產出有結構的執行計畫。"""
    if not insights:
        return ""
    lines = [f"賣家：{seller_name}\n以下是所有已儲存的 AI Insights：\n"]
    for it in insights:
        section = it.get("section", "")
        saved_at = it.get("saved_at", "")
        note = it.get("note", "")
        content = it.get("content", "")
        header = f"### {section} — {saved_at}"
        if note:
            header += f"（{note}）"
        lines.append(header)
        lines.append(content)
        lines.append("")
    body = "\n".join(lines)
    return (
        f"{body}\n\n"
        "請整合上述所有 insights，輸出一份**給賣家的**執行計畫（所有 action 都是賣家要做的事）。要求：\n"
        "1. 用 JSON 格式回覆（**只能有 JSON，不要 preamble、不要 markdown code fence**）\n"
        "2. JSON schema：\n"
        '   {"summary": "整體狀況一句話", \n'
        '    "this_week": [{"action": "...", "why": "..."}, ...],\n'
        '    "this_month": [...],\n'
        '    "this_quarter": [...]}\n'
        "3. 每個 action 要具體可執行（例：「補貨 ASIN B0XXX 至 60 天 TDOS」），不能模糊（例：「優化廣告」）\n"
        "4. why 引用具體數字（YoY%、絕對值）\n"
        "5. 各層級項目數量：this_week 最多 5 條、this_month 最多 5 條、this_quarter 最多 3 條\n"
        "6. 同樣的事不要重複出現在多個層級"
    )


def _parse_plan_json(raw: str) -> dict:
    """Robust JSON parsing — 剝 markdown fence、清掉 preamble。"""
    s = raw.strip()
    # 剝 ```json ... ``` 或 ``` ... ```
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```\s*$", "", s)
    # 找第一個 { 開始（萬一 Claude 還是 preamble 了）
    start = s.find("{")
    if start > 0:
        s = s[start:]
    return json.loads(s)


def _render_action_plan_html(seller_name: str, plan_json: dict, generated_at: str) -> str:
    """把 plan dict 轉成 standalone HTML（套主題色）。"""
    def _items_html(items: list[dict]) -> str:
        if not items:
            return '<p class="empty">（無）</p>'
        rows = []
        for it in items:
            action = it.get("action", "")
            why = it.get("why", "")
            rows.append(
                f'<li><label><input type="checkbox"> '
                f'<span class="action">{action}</span>'
                f'<div class="why">{why}</div></label></li>'
            )
        return '<ul class="checklist">' + "".join(rows) + "</ul>"

    summary = plan_json.get("summary", "")
    week = _items_html(plan_json.get("this_week", []))
    month = _items_html(plan_json.get("this_month", []))
    quarter = _items_html(plan_json.get("this_quarter", []))

    plan_id = f"{_safe_filename(seller_name)}_{generated_at[:10].replace('-','')}"
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>執行計畫 — {seller_name}</title>
<style>
:root {{ --primary:#4E79A7; --bg:#FFFFFF; --text:#31333F; --muted:#9aa3b2;
         --border:#e0e3eb; --accent:#F28E2B; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:"Noto Sans TC",-apple-system,sans-serif; background:var(--bg);
        color:var(--text); line-height:1.6; padding:40px 20px; }}
main {{ max-width:780px; margin:0 auto; }}
header {{ border-bottom:3px solid var(--primary); padding-bottom:20px; margin-bottom:30px;
          display:flex; justify-content:space-between; align-items:flex-end; gap:20px; flex-wrap:wrap; }}
header h1 {{ font-size:1.8em; color:var(--primary); }}
header .meta {{ color:var(--muted); font-size:0.9em; margin-top:8px; }}
.actions {{ display:flex; gap:8px; }}
.actions button {{ background:var(--primary); color:#fff; border:none; border-radius:6px;
                    padding:8px 14px; cursor:pointer; font-size:0.9em; font-family:inherit; }}
.actions button.ghost {{ background:#fff; color:var(--primary); border:1px solid var(--primary); }}
.actions button:hover {{ opacity:0.85; }}
.summary {{ background:#f7f9fc; border-left:4px solid var(--primary);
            padding:16px 20px; border-radius:6px; margin-bottom:30px; font-size:1.05em; }}
.progress-bar {{ background:#eef2f7; border-radius:999px; height:8px; margin-bottom:24px; overflow:hidden; }}
.progress-fill {{ background:linear-gradient(90deg, var(--primary), var(--accent));
                   height:100%; width:0%; transition:width .3s; }}
.progress-text {{ font-size:0.85em; color:var(--muted); margin-bottom:24px; }}
section {{ margin-bottom:32px; }}
section h2 {{ font-size:1.25em; color:var(--primary); margin-bottom:14px;
              padding-bottom:8px; border-bottom:1px solid var(--border); }}
.checklist {{ list-style:none; }}
.checklist li {{ background:#fff; border:1px solid var(--border); border-radius:8px;
                  padding:14px 16px; margin-bottom:10px; transition:border-color .2s; }}
.checklist li:hover {{ border-color:var(--primary); }}
.checklist label {{ display:block; cursor:pointer; }}
.checklist input[type=checkbox] {{ margin-right:8px; transform:scale(1.2); accent-color:var(--primary); }}
.checklist input:checked ~ .action {{ text-decoration:line-through; color:var(--muted); }}
.action {{ font-weight:500; }}
.why {{ color:#5a6270; font-size:0.9em; margin-top:6px; margin-left:24px; }}
.empty {{ color:var(--muted); font-style:italic; padding:8px 0; }}
.toast {{ position:fixed; bottom:24px; left:50%; transform:translateX(-50%);
          background:#28a745; color:#fff; padding:10px 20px; border-radius:6px;
          font-size:0.9em; opacity:0; transition:opacity .3s; pointer-events:none; }}
.toast.show {{ opacity:1; }}
@media print {{
  body {{ padding:20px; }}
  .checklist li:hover {{ border-color:var(--border); }}
  .actions {{ display:none; }}
}}
</style>
</head>
<body data-plan-id="{plan_id}">
<main>
<header>
  <div>
    <h1>執行計畫 — {seller_name}</h1>
    <div class="meta">產生時間：{generated_at}</div>
  </div>
  <div class="actions">
    <button class="ghost" onclick="window.print()">列印 / 存 PDF</button>
    <button onclick="exportProgress()">匯出進度檔</button>
  </div>
</header>

<div class="summary">{summary}</div>

<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
<div class="progress-text" id="progressText">0 / 0 已完成</div>

<section>
<h2>本週要做（this week）</h2>
{week}
</section>

<section>
<h2>本月要做（this month）</h2>
{month}
</section>

<section>
<h2>本季方向（this quarter）</h2>
{quarter}
</section>
</main>

<div class="toast" id="toast">已儲存到本機</div>

<script>
const PLAN_ID = document.body.dataset.planId;
const STORAGE_KEY = 'plan_' + PLAN_ID;

function actionKey(li, idx) {{
  // 用 action 文字 hash 當 key（即使重排也能對應）
  const text = li.querySelector('.action')?.textContent.trim() || ('idx_' + idx);
  return text.slice(0, 100);
}}

function loadProgress() {{
  const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}');
  document.querySelectorAll('.checklist li').forEach((li, idx) => {{
    const key = actionKey(li, idx);
    const cb = li.querySelector('input[type=checkbox]');
    if (saved[key]) cb.checked = true;
  }});
  updateProgress();
}}

function saveProgress() {{
  const state = {{}};
  document.querySelectorAll('.checklist li').forEach((li, idx) => {{
    const key = actionKey(li, idx);
    const cb = li.querySelector('input[type=checkbox]');
    if (cb.checked) state[key] = true;
  }});
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  showToast('進度已儲存到瀏覽器');
  updateProgress();
}}

function updateProgress() {{
  const all = document.querySelectorAll('.checklist input[type=checkbox]');
  const done = document.querySelectorAll('.checklist input[type=checkbox]:checked');
  const pct = all.length === 0 ? 0 : (done.length / all.length * 100);
  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('progressText').textContent =
    done.length + ' / ' + all.length + ' 已完成（' + pct.toFixed(0) + '%）';
}}

function exportProgress() {{
  // 把當前勾選狀態烙進 HTML 再下載一份
  const clone = document.documentElement.cloneNode(true);
  clone.querySelectorAll('.checklist input[type=checkbox]').forEach(cb => {{
    if (cb.checked) cb.setAttribute('checked', 'checked');
    else cb.removeAttribute('checked');
  }});
  // 加一個「最後更新」標記
  const meta = clone.querySelector('header .meta');
  if (meta) meta.textContent += '　·　最後勾選：' + new Date().toLocaleString('zh-TW');
  const html = '<!DOCTYPE html>\\n' + clone.outerHTML;
  const blob = new Blob([html], {{type: 'text/html;charset=utf-8'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  const ts = new Date().toISOString().slice(0,10).replace(/-/g,'');
  a.download = PLAN_ID + '_progress_' + ts + '.html';
  a.click();
  URL.revokeObjectURL(a.href);
}}

function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2000);
}}

// 勾選自動存
document.addEventListener('change', e => {{
  if (e.target.matches('.checklist input[type=checkbox]')) saveProgress();
}});
loadProgress();
</script>
</body>
</html>"""


BULK_RUN_FLAG = "_ai_bulk_run_pending"
BULK_DONE_FLAG = "_ai_bulk_run_done"

# 所有 section keys — 一鍵生成會 loop 這些
ALL_SECTIONS = ["overall", "business_metrics", "asin_table", "asin_level",
                "annual_target", "advertising"]


def is_bulk_pending() -> bool:
    """各 section 在自己的 AI 觸發點 call 這個，True 就跑。"""
    return st.session_state.get(BULK_RUN_FLAG, False)


def clear_bulk_flag() -> None:
    """頁面最後 call — 清掉 pending flag、設 done flag（觸發 toast 提示）。"""
    if st.session_state.pop(BULK_RUN_FLAG, False):
        st.session_state[BULK_DONE_FLAG] = True


def render_ai_tool_popover(seller_name: str) -> None:
    """頁面頂部 popover — AI Tool（取代原本的 export button）。"""
    if not seller_name:
        return

    insights = _load_saved(seller_name)
    plans_dir = INSIGHTS_DIR / "plans"
    seller_safe = _safe_filename(seller_name)
    saved_plans = sorted(plans_dir.glob(f"*_{seller_safe}_action_plan.html"), reverse=True) \
        if plans_dir.exists() else []

    with st.popover("AI Tool", icon=":material/auto_awesome:"):
        # 動作：一鍵生成
        if st.button(
            "一鍵生成所有 Insight",
            key=f"bulk_run_{seller_name}",
            icon=":material/bolt:",
            use_container_width=True,
        ):
            st.session_state[BULK_RUN_FLAG] = True
            st.session_state[BULK_DONE_FLAG] = False
            for sec in ALL_SECTIONS:
                st.session_state.pop(f"ai_insight_{sec}", None)
            st.rerun()

        # 動作：匯出執行計畫
        _render_export_plan_inner(seller_name, insights)

        # 歷史計畫（收進 expander，預設關）
        if saved_plans:
            with st.expander(
                f"已儲存的計畫（{len(saved_plans)}）",
                icon=":material/folder_open:",
            ):
                for p in saved_plans:
                    cols = st.columns([5, 1, 1], vertical_alignment="center")
                    cols[0].caption(p.name)
                    cols[1].download_button(
                        label="",
                        data=p.read_bytes(),
                        file_name=p.name,
                        mime="text/html",
                        icon=":material/download:",
                        key=f"dl_saved_{p.name}",
                        type="tertiary",
                    )
                    if cols[2].button(
                        "",
                        icon=":material/delete:",
                        type="tertiary",
                        key=f"del_saved_{p.name}",
                    ):
                        p.unlink()
                        st.rerun()

    if st.session_state.pop(BULK_DONE_FLAG, False):
        st.toast("所有 AI Insight 生成完成", icon=":material/check_circle:")


def _render_export_plan_inner(seller_name: str, insights: list) -> None:
    """匯出 plan 的核心邏輯 — popover 內呼叫。"""
    state_key = f"action_plan_{seller_name}"

    btn_label = "匯出執行計畫" if not insights else f"匯出執行計畫（{len(insights)} 筆）"
    btn_disabled = not insights
    if st.button(
        btn_label,
        key=f"export_plan_{seller_name}",
        icon=":material/checklist:",
        use_container_width=True,
        disabled=btn_disabled,
        help="先到各區塊按 AI 分析 + 儲存後才能匯出" if btn_disabled else None,
    ):
        raw = ""
        try:
            with st.spinner("整合中…Claude 正在排序執行計畫（最多 60 秒）"):
                prompt = build_action_plan_prompt(seller_name, insights)
                # JSON-only 系統提示 + 8000 token 預算（足以塞完整 plan）
                raw = _invoke(
                    prompt,
                    max_tokens=8000,
                    system="You return ONLY valid JSON. No markdown code fence, no preamble, no explanation. Just JSON.",
                )
            plan = _parse_plan_json(raw)
            generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            html = _render_action_plan_html(seller_name, plan, generated_at)
            st.session_state[state_key] = {"html": html, "generated_at": generated_at}
        except json.JSONDecodeError as e:
            st.error(
                f"AI 回覆 JSON 格式錯誤：{e}\n\n"
                f"前 800 字：\n```\n{raw[:800]}\n```\n"
                f"後 300 字：\n```\n{raw[-300:]}\n```"
            )
        except ValueError as e:
            # 被 max_tokens 截斷
            st.error(
                f"回應太長被截斷：{e}\n\n"
                f"建議：刪掉幾筆舊 insight 再重試，或聯絡開發者調高 token 上限。"
            )
        except Exception as e:
            if _is_credential_exception(e):
                st.error("AWS 憑證過期，請到下方按一次任意 AI 分析觸發 mwinit 後再試。")
            else:
                st.error(f"匯出失敗：{type(e).__name__}: {e}")

    if state_key in st.session_state:
        cached = st.session_state[state_key]
        # 檔名：YYYYMMDD_{seller}_action_plan.html
        date_part = cached["generated_at"][:10].replace("-", "")  # 2026-05-11 → 20260511
        filename = f"{date_part}_{_safe_filename(seller_name)}_action_plan.html"

        col_dl, col_save = st.columns(2)
        with col_dl:
            st.download_button(
                label="下載 HTML",
                data=cached["html"].encode("utf-8"),
                file_name=filename,
                mime="text/html",
                icon=":material/download:",
                key=f"dl_plan_{seller_name}",
                use_container_width=True,
            )
        with col_save:
            saved_flag = f"plan_saved_{seller_name}"
            if st.button(
                "儲存到本機",
                icon=":material/save:",
                key=f"save_plan_{seller_name}",
                use_container_width=True,
            ):
                plans_dir = INSIGHTS_DIR / "plans"
                plans_dir.mkdir(parents=True, exist_ok=True)
                save_path = plans_dir / filename
                save_path.write_text(cached["html"], encoding="utf-8")
                st.session_state[saved_flag] = str(save_path)
                st.rerun()
            if st.session_state.pop(saved_flag, None):
                st.toast(f"已儲存到 ai_insights/plans/{filename}",
                         icon=":material/check_circle:")


def build_ads_prompt(
    seller_name: str,
    selected_period: str,
    kpi_rows: list[dict],
) -> str:
    """Advertising & Merchandising — 只送 widget 上面的三個 KPI（TACOS / Ads spending / SP ops）"""
    lines = ["| 指標 | 當期值 | YoY | MoM |", "|---|---|---|---|"]
    for r in kpi_rows:
        yoy = f"{r['yoy_pct']:+.1f}%" if r.get("yoy_pct") is not None else "-"
        mom = f"{r['mom_pct']:+.1f}%" if r.get("mom_pct") is not None else "-"
        val = r.get("value", "-")
        if isinstance(val, (int, float)):
            val = f"{val:,.2f}" if r.get("decimal") else f"{val:,.0f}"
        lines.append(f"| {r['name']} | {val} | {yoy} | {mom} |")
    table = "\n".join(lines)
    return (
        f"賣家：{seller_name}\n區間：{selected_period}\n區塊：Advertising & Merchandising\n\n"
        f"{table}\n\n"
        "請依序分析：\n"
        "1. **廣告效益** — 看 TACOS 走向，目前是健康還是失控？（一般 8–15% 正常，>20% 偏高）\n"
        "2. **廣告投資 vs 產出** — Ads spending 跟 SP ops 的成長是否同步？投入有換來足夠的廣告銷售？\n"
        "3. **YoY/MoM 對比** — 哪個指標的變化最值得注意？背後可能的原因是什麼？\n"
        "4. **下一步行動 2 條** — 是要加投、減投、還是調 keyword 結構？"
    )


def build_target_prompt(
    seller_name: str,
    this_year: int,
    last_year_sales: dict,
    this_year_sales: dict,
    last_year_yoy: dict,
    current_target_yoy: float | None = None,
    current_peak_months_str: str = "",
) -> str:
    """年度業績目標 — AI 建議 YoY% + 旺季 + 說服文案"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def _fmt_money(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "-"
        return f"${v:,.0f}"

    def _fmt_pct(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "-"
        return f"{v:+.1f}%"

    rows = ["| 月份 | 去年 Sales | 今年 Sales | 去年 YoY |",
            "|---|---|---|---|"]
    for m in months:
        rows.append(
            f"| {m} | {_fmt_money(last_year_sales.get(m))} "
            f"| {_fmt_money(this_year_sales.get(m))} "
            f"| {_fmt_pct(last_year_yoy.get(m))} |"
        )
    table = "\n".join(rows)

    last_year_total = sum(v for v in last_year_sales.values()
                          if v is not None and not pd.isna(v))
    ytd_total = sum(v for v in this_year_sales.values()
                    if v is not None and not pd.isna(v))
    last_year_yoy_avg = [v for v in last_year_yoy.values()
                         if v is not None and not pd.isna(v)]
    avg_yoy = sum(last_year_yoy_avg) / len(last_year_yoy_avg) if last_year_yoy_avg else None

    user_setting = ""
    if current_target_yoy is not None:
        user_setting = f"\n\n賣家目前自訂的 YoY 目標：{current_target_yoy:.0f}%"
    if current_peak_months_str:
        user_setting += f"，旺季：{current_peak_months_str}"

    return (
        f"賣家：{seller_name}\n年度：{this_year}\n區塊：年度業績目標\n\n"
        f"{table}\n\n"
        f"**摘要：** 去年總銷售 {_fmt_money(last_year_total)}，"
        f"今年至今 {_fmt_money(ytd_total)}，去年平均 YoY {_fmt_pct(avg_yoy)}。"
        f"{user_setting}\n\n"
        f"你是 Amazon 客戶經理，要說服這位賣家設定一個合理且積極的 {this_year} 年 YoY 目標。請：\n"
        "1. 先給一個建議的「全年 YoY %」數字（範圍如 +20% ~ +35%，不要太保守）\n"
        "2. 給一個建議的「旺季月份」（看哪幾個月去年表現特別好）\n"
        "3. 用賣家視角的說服文案（為什麼這個目標可以達成）— 引用具體月份和數字\n"
        "4. 點出 1 個風險或挑戰，並建議怎麼克服\n\n"
        "格式範例：\n"
        "**建議目標：+28% YoY**　**旺季：3-5月、11-12月**\n\n"
        "**為什麼可達成：** [說服段落 100 字內]\n\n"
        "**注意：** [風險與克服方式 50 字內]"
    )


def _to_num(s):
    """Strip %, $, commas; return numeric Series."""
    return pd.to_numeric(
        s.astype(str)
         .str.replace("%", "", regex=False)
         .str.replace("$", "", regex=False)
         .str.replace(",", "", regex=False)
         .str.strip(),
        errors="coerce",
    )


def _inventory_risk_lines(slim: pd.DataFrame, max_n: int = 15) -> str:
    if not any(c in slim.columns for c in ("Total Days of Supply", "WOC", "Available")):
        return ""
    risks = []
    for _, row in slim.iterrows():
        tdos = pd.to_numeric(row.get("Total Days of Supply"), errors="coerce")
        woc = pd.to_numeric(row.get("WOC"), errors="coerce")
        avail = pd.to_numeric(row.get("Available"), errors="coerce")
        asin = row.get("Child ASIN", "?")
        if pd.notna(avail) and avail == 0:
            risks.append(f"{asin}: 已斷貨 (Available=0)")
        elif pd.notna(tdos) and tdos < 30:
            risks.append(f"{asin}: TDOS={tdos:.0f} 天 (低)")
        elif pd.notna(woc) and woc < 4:
            risks.append(f"{asin}: WOC={woc:.1f} 週 (低)")
    if not risks:
        return "\n\n**庫存風險：** 無偏低 ASIN（TDOS≥30 且 WOC≥4 且未斷貨）"
    return "\n\n**庫存風險 ASIN（斷貨 / TDOS<30 / WOC<4）：**\n- " + "\n- ".join(risks[:max_n])


def build_asin_prompt(
    seller_name: str,
    asin_df: pd.DataFrame,
    trend_df: pd.DataFrame | None = None,
    asin_marks: dict | None = None,
) -> str:
    """ASIN Level — Tab1 (Complete) + Tab2 (Trend) + Tab3 (B2B) 三個 tab 的整合分析"""
    df = asin_df.copy()
    sales_col = "Sales Contribution %" if "Sales Contribution %" in df.columns else None
    if sales_col:
        df[sales_col] = _to_num(df[sales_col])

    cols = [c for c in [
        "Child ASIN", "Sales Contribution %", "Sessions - Total",
        "Available", "Total Days of Supply", "WOC",
    ] if c in df.columns]
    slim = df[cols].copy() if cols else df.copy()

    top10 = (slim.sort_values(sales_col, ascending=False).head(10)
             if sales_col and sales_col in slim.columns else slim.head(10))

    sections = [f"**Top 10 by Sales Contribution：**\n{_df_to_markdown(top10)}"]

    # 標記的 ASIN（tag）
    if asin_marks:
        marked_rows = df[df["Child ASIN"].isin(asin_marks.keys())].copy() if "Child ASIN" in df.columns else pd.DataFrame()
        if not marked_rows.empty:
            marked_rows["Tag"] = marked_rows["Child ASIN"].map(asin_marks)
            keep = [c for c in [
                "Child ASIN", "Tag", "Sales Contribution %", "Sessions - Total",
                "Unit Session Percentage", "Ordered Product Sales",
            ] if c in marked_rows.columns]
            sections.append(f"\n**標記的指定 ASIN（要重點分析）：**\n{_df_to_markdown(marked_rows[keep], max_rows=30)}")

    # B2B — 全部有 B2B Sales 的 ASIN，依 B2B Sales 排序
    if "B2B Sales" in df.columns and "B2B %" in df.columns:
        b2b_sales = _to_num(df["B2B Sales"])
        b2b_total = b2b_sales.sum()
        ops_total = _to_num(df["Ordered Product Sales"]).sum() if "Ordered Product Sales" in df.columns else 0
        b2b_pct = (b2b_total / ops_total * 100) if ops_total > 0 else 0
        b2b_section = f"\n**B2B 摘要：** 整體 B2B 佔比 {b2b_pct:.2f}%（B2B Sales 總額 ${b2b_total:,.0f}）"

        b2b_all = df.copy()
        b2b_all["_b2b_sales_num"] = b2b_sales
        b2b_all = b2b_all[b2b_all["_b2b_sales_num"] > 0].sort_values("_b2b_sales_num", ascending=False)
        if not b2b_all.empty:
            keep = [c for c in ["Child ASIN", "B2B Sales", "B2B %", "Ordered Product Sales"] if c in b2b_all.columns]
            b2b_section += f"\n\n**所有有 B2B 銷售的 ASIN（依 B2B Sales 排序）：**\n{_df_to_markdown(b2b_all[keep], max_rows=20)}"
        sections.append(b2b_section)

    # YoY 異常診斷（CVR / Sessions 大跌或大漲）
    if "Unit Session Percentage" in df.columns and "Unit Session % - Last Year" in df.columns:
        diag = df.copy()
        diag["_cvr"] = _to_num(diag["Unit Session Percentage"])
        diag["_cvr_ly"] = _to_num(diag["Unit Session % - Last Year"])
        diag["_cvr_yoy_bps"] = (diag["_cvr"] - diag["_cvr_ly"]) * 100
        diag = diag[(diag["_cvr_yoy_bps"].abs() > 100)].copy()  # YoY 變化超過 100 bps
        if not diag.empty:
            diag = diag.sort_values("_cvr_yoy_bps").head(10)
            keep = [c for c in ["Child ASIN", "Unit Session Percentage",
                               "Unit Session % - Last Year", "_cvr_yoy_bps"] if c in diag.columns]
            sections.append(
                f"\n**CVR YoY 異常 ASIN（變化 > ±100 bps）：**\n{_df_to_markdown(diag[keep], max_rows=10)}"
            )

    # Trend (Tab2) — 月份欄位是 YYYY-MM 格式（如 2026-04）
    if trend_df is not None and not trend_df.empty:
        month_pat = re.compile(r"^\d{4}-\d{2}$")
        month_cols = sorted([c for c in trend_df.columns if month_pat.match(str(c))])
        if month_cols and "Child ASIN" in trend_df.columns:
            t = trend_df.copy()
            recent = month_cols[-6:]  # 最多近 6 個月
            for c in recent:
                t[c] = _to_num(t[c])
            latest = recent[-1]
            t = t.sort_values(latest, ascending=False).head(10)
            keep = ["Child ASIN"] + recent
            sections.append(
                f"\n**Trend Top 10（{recent[0]} ~ {recent[-1]}，依最新月份排序）：**\n"
                f"{_df_to_markdown(t[keep], max_rows=10)}"
            )

    sections.append(_inventory_risk_lines(slim))

    body = "\n".join(sections)
    return (
        f"賣家：{seller_name}\n區塊：ASIN Level（Complete + Trend + B2B 整合）\n\n"
        f"{body}\n\n"
        "請依序分析：\n"
        "1. **集中度** — Top 3 ASIN 佔比是否過高？需不需要分散風險？\n"
        "2. **指定 ASIN（如有 tag）** — 對標記的 ASIN 做 sales funnel 診斷（Sessions → CVR → Sales），找瓶頸\n"
        "3. **異常診斷** — CVR YoY 大幅變化的 ASIN，原因可能是什麼？該怎麼救？\n"
        "4. **趨勢** — 近 3 個月 Top ASIN 是否還在成長？有沒有要被超車？\n"
        "5. **B2B** — 高 B2B% ASIN 是否要做 BD 推廣或加固定價？\n"
        "6. **庫存風險** — 哪幾支 ASIN 必須立刻補貨？\n"
        "7. **下一步行動 3 條** — 要做的事按優先度排序"
    )


def build_asin_table_prompt(
    seller_name: str,
    table_df: pd.DataFrame,
    asin_marks: dict | None = None,
) -> str:
    """Complete ASIN Data tab 專用 — 針對表格做 sales funnel + tag ASIN + 異常診斷"""
    df = table_df.copy()
    if "Child ASIN" not in df.columns:
        return f"賣家：{seller_name}\n資料缺 Child ASIN 欄位，無法分析。"

    # Tag 標記
    if asin_marks:
        df["Tag"] = df["Child ASIN"].map(asin_marks).fillna("")

    # 數值欄轉換
    for c in ("Sales Contribution %", "Unit Session Percentage", "Sessions - Total",
              "Ordered Product Sales", "Unit Session % - Last Year"):
        if c in df.columns:
            df[c] = _to_num(df[c])

    # Funnel 重點欄位
    funnel_cols = [c for c in [
        "Child ASIN", "Tag", "Sessions - Total", "Unit Session Percentage",
        "Unit Session % - Last Year", "Ordered Product Sales",
        "Sales Contribution %",
    ] if c in df.columns]
    slim = df[funnel_cols].copy() if funnel_cols else df.copy()

    # 1. 標記 ASIN 全列出
    sections = []
    if asin_marks:
        marked = slim[slim.get("Tag", "") != ""].copy() if "Tag" in slim.columns else pd.DataFrame()
        if not marked.empty:
            sections.append(f"**指定 ASIN（已加 tag，需要 funnel 分析）：**\n{_df_to_markdown(marked, max_rows=30)}")

    # 2. 異常數字 — CVR YoY 大跌或大漲（>±100 bps）
    if "Unit Session Percentage" in slim.columns and "Unit Session % - Last Year" in slim.columns:
        anom = slim.copy()
        anom["CVR_YoY_bps"] = (anom["Unit Session Percentage"] - anom["Unit Session % - Last Year"]) * 100
        anom = anom[anom["CVR_YoY_bps"].abs() > 100].copy()
        if not anom.empty:
            anom = anom.sort_values("CVR_YoY_bps")
            keep = [c for c in ["Child ASIN", "Tag", "Sessions - Total",
                               "Unit Session Percentage", "Unit Session % - Last Year",
                               "CVR_YoY_bps", "Ordered Product Sales"] if c in anom.columns]
            sections.append(
                f"\n**CVR YoY 異常（變化 > ±100 bps）：**\n{_df_to_markdown(anom[keep], max_rows=15)}"
            )

    # 3. Top 10 by Sales
    sort_col = "Sales Contribution %" if "Sales Contribution %" in slim.columns else funnel_cols[0]
    top10 = slim.sort_values(sort_col, ascending=False).head(10)
    sections.append(f"\n**Top 10 by {sort_col}：**\n{_df_to_markdown(top10, max_rows=10)}")

    body = "\n".join(sections)
    return (
        f"賣家：{seller_name}\n區塊：Complete ASIN Data\n\n"
        f"{body}\n\n"
        "請逐項分析：\n"
        "1. **指定 ASIN 的 Sales Funnel** — 對每支 tag ASIN，分別判斷瓶頸在 (a) Sessions（流量不足）"
        "(b) CVR（轉換率低）還是 (c) Sales 已 OK，給對症下藥的建議\n"
        "2. **異常 ASIN** — 例如 CVR YoY 大跌的，可能原因（價格、Buy Box、評價、競品）+ 救法 2 條\n"
        "3. **Top ASIN 攻擊面** — Top 3 還能怎麼擴大？流量擴張 vs 客單提升\n"
        "4. **三個下一步行動** — 按優先度排序，每條 1 句話"
    )
