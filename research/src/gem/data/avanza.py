"""Avanza fund NAV via the JSON endpoints used by avanza.se itself.

QUALITY: UNDOCUMENTED_ENDPOINT. These are not an official API: they work
anonymously today (verified from GitHub-hosted runners, 2026-10-31) but may
change without notice. They are isolated here behind the FundNavProvider
interface so that an official feed can replace them without touching strategy
or live-signal code.

Endpoints (verified against real responses, see reports/generated/nav_probe/):
  POST /_api/search/filtered-search            {"query": ISIN, "searchFilter": {"types": ["FUND"]}}
       -> hits[].orderBookId
  GET  /_api/fund-guide/guide/{orderBookId}    -> isin, name, nav, navDate, currency, productFee, managementFee
  GET  /_api/fund-guide/chart/{id}/{from}/{to}?raw=true
       -> {"dataSerie": [{"x": epoch_ms (00:00 Europe/Stockholm), "y": NAV or null}], ...}
       Short windows return DAILY NAV; long windows are downsampled to monthly points
       (stamped the 1st, holding the month's LAST NAV). Only daily windows are used.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

BASE = "https://www.avanza.se"
STOCKHOLM = ZoneInfo("Europe/Stockholm")
MAX_DAILY_GAP_DAYS = 5  # spacing above this => window was downsampled -> split


def chart_url(orderbook: str, start: date, end: date) -> str:
    return f"{BASE}/_api/fund-guide/chart/{orderbook}/{start:%Y-%m-%d}/{end:%Y-%m-%d}?raw=true"


def guide_url(orderbook: str) -> str:
    return f"{BASE}/_api/fund-guide/guide/{orderbook}"


def parse_chart(raw: bytes) -> pd.Series:
    doc = json.loads(raw)
    if "dataSerie" not in doc:
        raise ValueError(f"unexpected chart payload: {str(doc)[:200]}")
    pts = [(p["x"], p["y"]) for p in doc["dataSerie"] if p.get("y") is not None]
    if not pts:
        return pd.Series(dtype=float)
    idx = pd.DatetimeIndex([datetime.fromtimestamp(x / 1000, tz=timezone.utc).astimezone(STOCKHOLM).date()
                            for x, _ in pts])
    return pd.Series([float(y) for _, y in pts], index=idx).sort_index()


def is_daily(s: pd.Series, window_days: int | None = None) -> bool:
    """True if points are daily. A window with too few points to judge is treated as
    downsampled when it spans more than a month (cheap to split, never wrong)."""
    if s.empty:
        return True
    if len(s) == 1:
        return window_days is None or window_days <= 31
    return int(pd.Series(s.index).diff().dt.days.max()) <= MAX_DAILY_GAP_DAYS


def fetch_daily_history(get, orderbook: str, start: date, end: date, window_days: int = 365) -> tuple[pd.Series, list]:
    """Fetch daily NAV in windows; split any window that comes back downsampled.

    `get(url) -> bytes` performs (and caches) the HTTP request. Returns the NAV
    series and the list of (url, n_points) actually used.
    """
    used, pieces = [], []
    queue = []
    d = start
    while d <= end:
        e = min(d + timedelta(days=window_days - 1), end)
        queue.append((d, e))
        d = e + timedelta(days=1)
    while queue:
        a, b = queue.pop(0)
        url = chart_url(orderbook, a, b)
        s = parse_chart(get(url))
        if not is_daily(s, (b - a).days) and (b - a).days > 31:
            mid = a + (b - a) / 2
            queue[0:0] = [(a, mid), (mid + timedelta(days=1), b)]
            continue
        if not is_daily(s, (b - a).days):
            raise ValueError(f"window {a}..{b} still not daily ({len(s)} points)")
        used.append((url, int(len(s))))
        pieces.append(s)
    full = pd.concat([p for p in pieces if not p.empty]) if any(not p.empty for p in pieces) else pd.Series(dtype=float)
    full = full[~full.index.duplicated(keep="last")].sort_index()
    return full, used
