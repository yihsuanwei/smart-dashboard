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
from typing import Any

import boto3
import pandas as pd
import streamlit as st
from botocore.exceptions import BotoCoreError, ClientError

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


@st.cache_resource
def _bedrock_client():
    return boto3.client("bedrock-runtime", region_name=REGION)


def _invoke(user_prompt: str) -> str:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    resp = _bedrock_client().invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
    )
    payload = json.loads(resp["body"].read())
    return payload["content"][0]["text"]


def _df_to_markdown(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df is None or df.empty:
        return "(no data)"
    truncated = df.head(max_rows)
    try:
        return truncated.to_markdown(index=False)
    except Exception:
        return truncated.to_string(index=False)


def ai_button(section_key: str, label: str = ":material/auto_awesome: AI 分析") -> bool:
    """Render the trigger button. Returns True on click."""
    return st.button(label, key=f"btn_{section_key}", type="secondary")


def show_result(section_key: str, prompt: str) -> None:
    """Call Bedrock with the given prompt, stash result in session_state, and render."""
    state_key = f"ai_insight_{section_key}"
    try:
        with st.spinner("Claude Opus 4.7 分析中…（約 10–30 秒）"):
            result = _invoke(prompt)
        st.session_state[state_key] = result
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("ExpiredTokenException", "UnrecognizedClientException"):
            st.error("AWS 憑證過期了 — 跑 `mwinit` 並碰一下 YubiKey，再重試。")
        elif code == "ValidationException":
            st.error(f"Bedrock model ID 無效：`{MODEL_ID}`\n\n錯誤：{e}")
        elif code == "AccessDeniedException":
            st.error("沒有 Bedrock 權限。檢查 AWS profile 是否能 invoke 這個 model。")
        else:
            st.error(f"Bedrock 錯誤（{code}）：{e}")
    except BotoCoreError as e:
        st.error(f"AWS SDK 錯誤：{e}")


def show_cached(section_key: str) -> None:
    """Render the most recent result (if any) from session_state."""
    state_key = f"ai_insight_{section_key}"
    if state_key in st.session_state:
        with st.container(border=True):
            st.markdown(
                f"**:material/psychology: AI Insight**\n\n{st.session_state[state_key]}"
            )


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
    current_metrics: dict,
    prior_metrics: dict,
) -> str:
    keys = sorted(set(current_metrics) | set(prior_metrics))
    lines = ["| 指標 | 當期 | 前期 | 變化 |", "|---|---|---|---|"]
    for k in keys:
        cur = current_metrics.get(k)
        prev = prior_metrics.get(k)
        if cur is None or prev is None or prev == 0:
            change = "-"
        else:
            change = f"{(cur - prev) / prev * 100:+.1f}%"
        cur_str = f"{cur:,.2f}" if isinstance(cur, float) else (f"{cur:,}" if isinstance(cur, int) else "-")
        prev_str = f"{prev:,.2f}" if isinstance(prev, float) else (f"{prev:,}" if isinstance(prev, int) else "-")
        lines.append(f"| {k} | {cur_str} | {prev_str} | {change} |")
    table = "\n".join(lines)
    return (
        f"賣家：{seller_name}\n區間：{selected_date}（vs 前期）\n區塊：Business Metrics\n\n"
        f"{table}\n\n"
        "請判斷：銷售變化主要是因為流量(Sessions)、轉換率(CVR)還是客單價(AOV)？給結論+1個改善方向。"
    )


def build_asin_prompt(seller_name: str, asin_df: pd.DataFrame) -> str:
    """ASIN Level — 含庫存風險分析（Available / Total Days of Supply / WOC）"""
    df = asin_df.copy()

    sales_col = "Sales Contribution %" if "Sales Contribution %" in df.columns else None
    if sales_col:
        df[sales_col] = pd.to_numeric(
            df[sales_col].astype(str).str.replace("%", "", regex=False).str.strip(),
            errors="coerce",
        )

    cols_keep = [c for c in [
        "Child ASIN", "Sales Contribution %", "Sessions - Total",
        "Available", "Total Days of Supply", "WOC",
    ] if c in df.columns]
    slim = df[cols_keep].copy()

    top10 = (
        slim.sort_values(sales_col, ascending=False).head(10)
        if sales_col
        else slim.head(10)
    )

    inventory_summary = ""
    if "Total Days of Supply" in slim.columns or "WOC" in slim.columns or "Available" in slim.columns:
        risk_rows = []
        for _, row in slim.iterrows():
            tdos = pd.to_numeric(row.get("Total Days of Supply"), errors="coerce")
            woc = pd.to_numeric(row.get("WOC"), errors="coerce")
            avail = pd.to_numeric(row.get("Available"), errors="coerce")
            asin = row.get("Child ASIN", "?")
            if pd.notna(avail) and avail == 0:
                risk_rows.append(f"{asin}: 已斷貨 (Available=0)")
            elif pd.notna(tdos) and tdos < 30:
                risk_rows.append(f"{asin}: TDOS={tdos:.0f} 天 (低)")
            elif pd.notna(woc) and woc < 4:
                risk_rows.append(f"{asin}: WOC={woc:.1f} 週 (低)")
        if risk_rows:
            inventory_summary = (
                "\n\n**庫存風險 ASIN（斷貨 / TDOS<30 / WOC<4）：**\n- "
                + "\n- ".join(risk_rows[:15])
            )
        else:
            inventory_summary = "\n\n**庫存風險：** 無偏低 ASIN（TDOS≥30 且 WOC≥4 且未斷貨）"

    return (
        f"賣家：{seller_name}\n區塊：ASIN Level（含庫存）\n\n"
        f"**Top 10 by Sales Contribution：**\n{_df_to_markdown(top10)}\n"
        f"{inventory_summary}\n\n"
        "請給：(1) ASIN 集中度判斷（Top 3 佔比是否過高） "
        "(2) 庫存風險摘要 — 哪幾支 ASIN 需要立刻補貨 "
        "(3) 一個下一步行動建議（補貨 / 推廣 / 砍 SKU）。"
    )
