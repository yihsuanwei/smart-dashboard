"""_band_utils.py — GMS Band 工具

baseline band 來自 sellers.q2_baseline_band（GMS Band(T12 2025FY)）。
current band 用 **T12 rolling**（今天往前 12 個月）對齊 baseline 口徑。

T12 GMS 來自 pkey_raw_monthly.mtd_ord_gms — 2026-05 backfill 後 2025-05~11 補齊，
T12 計算可從 db 最新月（typically 上個月）往前推 12 個月，自動隨 sync-weekly 推進。

提供：
- BANDS：門檻、顏色、emoji 對照表
- compute_band_progress：給 baseline band 字母 + current t12_gms，
  回傳 within-band log progress、距下一階差距、狀態（normal/promote/demote）
- load_t12_gms_map：從 db 撈每個 mcid 的 T12 GMS dict（dashboard 用）
- band_chip：'A' → '🟡 A'，給 dataframe 顯示用
"""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Iterable

# (letter, lower_inclusive, upper_exclusive, color_hex, emoji)
# Band G 是 exact $0；Band F 是 $0.01 ~ $10K
BANDS: list[tuple[str, float, float, str, str]] = [
    ("A", 10_000_000, float("inf"), "#B7791F", "🟫"),
    ("B", 1_000_000, 10_000_000, "#15803D", "🟢"),
    ("C", 500_000, 1_000_000, "#65A30D", "🟩"),
    ("D", 100_000, 500_000, "#CA8A04", "🟡"),
    ("E", 10_000, 100_000, "#EA580C", "🟠"),
    ("F", 0.01, 10_000, "#DC2626", "🔴"),
    ("G", 0, 0.01, "#6B7280", "⚫"),
]

_BANDS_BY_LETTER: dict[str, tuple[float, float, str, str]] = {
    letter: (lower, upper, color, emoji)
    for letter, lower, upper, color, emoji in BANDS
}

BAND_LETTERS = [b[0] for b in BANDS]  # ['A','B','C','D','E','F','G']
BAND_COLOR_MAP = {b[0]: b[3] for b in BANDS}


def band_chip(letter: str) -> str:
    """'A' → '🟫 A'；空字串 → ''"""
    if not letter:
        return ""
    info = _BANDS_BY_LETTER.get(letter)
    if not info:
        return letter
    return f"{info[3]} {letter}"


def band_letter_from_value(ytd_gms: float) -> str:
    """根據 ytd_gms 直接回傳對應 band 字母（純門檻判定，不參考 baseline）"""
    if ytd_gms is None or (isinstance(ytd_gms, float) and math.isnan(ytd_gms)):
        return ""
    v = float(ytd_gms)
    for letter, lower, upper, _, _ in BANDS:
        if letter == "G":
            # exact $0
            if v == 0:
                return "G"
        elif lower <= v < upper:
            return letter
    if v < 0:
        return ""
    return ""


def compute_band_progress(baseline_band: str, current_gms: float) -> dict:
    """以 *current* band 區間為基準算進度與差距；baseline 只用來判升/降階。

    `current_gms` 應為 T12 rolling GMS（今天往前 12 個月加總），與 baseline (T12 2025FY)
    口徑一致。歷史上曾傳 ytd_gms（年初到今天累計），但 ytd 跟 T12 是不同口徑，
    上半年 ytd 永遠偏小，會誤判成 demote — 已於 2026-05 統一改用 T12。

    舊設計（baseline 為基準）的問題：賣家掉到下一階就 clamp 0%，跟「差距 $」對不上。
    新設計：所有欄位都圍繞「current band」，AM 一眼讀懂——
    - 「我現在在哪個 band」→ Band 字母（baseline）+ 現況（↑/—/↓ + current letter）
    - 「離下一階還多遠」→ → 下一階（current 區間進度條）+ 差距 $（current 上限 − current）

    回傳：
    {
        'baseline_band': 'C',
        'current_band': 'D',
        'progress': 0.32,                     # current band 區間內的 log scale 進度
        'progress_clamped': 0.32,
        'status': 'demote',                   # baseline vs current 比較結果
        'gap_to_next': 244000.0,              # current band 上限 - current_gms
    }
    """
    v = float(current_gms or 0)
    current = band_letter_from_value(v)

    # 取 current band 區間（baseline 只在 status 用得到）
    if current and current in _BANDS_BY_LETTER:
        c_lower, c_upper, _, _ = _BANDS_BY_LETTER[current]
    else:
        c_lower, c_upper = 0.0, 0.01

    # progress：log scale within current band
    if current == "G":
        progress = 0.0
    elif current == "A":
        # A 沒有上界；log scale 從 $10M 起，每 10× 進度 +0.5，到 $1B 滿格
        if v <= c_lower:
            progress = 0.0
        else:
            decades = math.log10(v / c_lower)
            progress = min(1.0, decades / 2)
    elif c_upper <= 0 or c_lower >= c_upper:
        progress = 0.0
    elif v <= c_lower:
        progress = 0.0
    elif v >= c_upper:
        progress = 1.0
    else:
        log_l = math.log10(c_lower) if c_lower > 0 else 0.0
        log_u = math.log10(c_upper)
        progress = (math.log10(v) - log_l) / (log_u - log_l)

    progress_clamped = max(0.0, min(1.0, progress))

    # 差距到 current band 上限
    if current == "A":
        gap_to_next = 0.0
    elif current == "G":
        gap_to_next = 0.01
    else:
        gap_to_next = max(0.0, c_upper - v)

    # 狀態：current vs baseline
    if not baseline_band or baseline_band not in _BANDS_BY_LETTER or not current:
        status = "unknown"
    elif current == baseline_band:
        status = "normal"
    elif _band_rank(current) < _band_rank(baseline_band):
        status = "promote"
    else:
        status = "demote"

    return {
        "baseline_band": baseline_band,
        "current_band": current,
        "progress": progress,
        "progress_clamped": progress_clamped,
        "status": status,
        "gap_to_next": gap_to_next,
    }


def _band_rank(letter: str) -> int:
    """A=0（最高）, G=6（最低），未知 = 99"""
    try:
        return BAND_LETTERS.index(letter)
    except ValueError:
        return 99


def status_arrow(status: str) -> str:
    """status → 顯示符號"""
    return {
        "normal": "—",
        "promote": "↑",
        "demote": "↓",
        "unknown": "",
    }.get(status, "")


def t12_window(conn: sqlite3.Connection) -> tuple[int, int, int, int]:
    """以 db pkey_raw_monthly 最新月為錨，回傳 T12 起訖 (start_y, start_m, end_y, end_m)。

    T12 = 最新月往前 12 個月（含最新月）。例：最新 = 2026-04 → T12 = 2025-05 ~ 2026-04。
    這個 window 隨 sync-weekly 自動推進。
    """
    row = conn.execute(
        "SELECT year, month FROM pkey_raw_monthly ORDER BY year DESC, month DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return (0, 0, 0, 0)
    end_y, end_m = int(row[0]), int(row[1])
    # 往前 11 個月 → start = (end - 11)
    total = end_y * 12 + end_m - 11
    start_y, start_m = total // 12, total % 12
    if start_m == 0:
        start_y -= 1
        start_m = 12
    return start_y, start_m, end_y, end_m


def load_t12_gms_map(
    conn: sqlite3.Connection,
    mcids: Iterable[str] | None = None,
    marketplaces: Iterable[str] | None = None,
) -> dict[str, float]:
    """回傳 {mcid: t12_gms_sum} — 所有 marketplace 加總後的 T12 GMS。

    Args:
        conn: 已開啟的 sqlite3 連線
        mcids: 限定的 mcid 集合（None = 所有 mcid）
        marketplaces: 限定的 marketplace（None = 不限，所有 mk 加總）

    回傳的 dict 只包含在 T12 window 內**有資料**的 mcid。
    沒有的 mcid 用 .get(mcid, 0.0) 取預設 0。
    """
    sy, sm, ey, em = t12_window(conn)
    if sy == 0:
        return {}

    # T12 跨年範圍 (sy-sm 到 ey-em) 拆成兩段 UNION ALL，
    # 每段都是「year = ? AND month >=/<= ?」可走 covering index seek。
    # 之前用 OR 條件包住跨年邏輯，parameterized SQL 下 SQLite planner 會放棄
    # covering index 改 full scan，慢 20x。
    if sy == ey:
        # 同一年，單一段
        mp_clause, mp_params = _marketplace_clause(marketplaces)
        sql = (
            f"SELECT mcid, COALESCE(SUM(mtd_ord_gms), 0) AS t12_gms "
            f"FROM pkey_raw_monthly "
            f"WHERE year = ? AND month BETWEEN ? AND ?{mp_clause}"
            f" GROUP BY mcid"
        )
        params: list = [sy, sm, em] + mp_params
    else:
        # 跨年：sy 段 (>= sm) + ey 段 (<= em)，UNION ALL 後再 GROUP BY 加總
        mp_clause, mp_params = _marketplace_clause(marketplaces)
        sql = (
            f"SELECT mcid, SUM(g) AS t12_gms FROM ("
            f"  SELECT mcid, mtd_ord_gms AS g FROM pkey_raw_monthly "
            f"  WHERE year = ? AND month >= ?{mp_clause}"
            f"  UNION ALL "
            f"  SELECT mcid, mtd_ord_gms AS g FROM pkey_raw_monthly "
            f"  WHERE year = ? AND month <= ?{mp_clause}"
            f") GROUP BY mcid"
        )
        params = [sy, sm] + mp_params + [ey, em] + mp_params

    if mcids is not None:
        mcid_list = list(mcids)
        if not mcid_list:
            return {}
        # 大量 mcid filter：直接撈完再 Python 端過濾，比 chunked IN 快很多
        # 因為 chunked IN 會讓每個 chunk 重跑一次完整 query，O(N×chunks)
        full = {r[0]: float(r[1] or 0) for r in conn.execute(sql, params)}
        target = set(mcid_list)
        return {m: g for m, g in full.items() if m in target}

    return {r[0]: float(r[1] or 0) for r in conn.execute(sql, params)}


def _marketplace_clause(marketplaces: Iterable[str] | None) -> tuple[str, list]:
    """marketplaces filter SQL fragment + params。"""
    if not marketplaces:
        return "", []
    mp_list = list(marketplaces)
    ph = ",".join(["?"] * len(mp_list))
    return f" AND marketplace IN ({ph})", mp_list
