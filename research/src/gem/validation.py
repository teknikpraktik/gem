"""Data-quality checks and cross-source validation.

Checks never repair data. They report; the pipeline decides (NaN -> NO_SIGNAL).
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .returns import simple_returns, to_month_end, yield_to_monthly_return

EXTREME_MONTHLY_MOVE = {
    "equity": 0.25,
    "bond": 0.08,
    "money_market_return": 0.02,
    "money_market_index": 0.02,
    "money_market_yield": None,  # yields: check level changes instead
    "bond_yield": None,
    "fx": 0.15,
    "fund_nav": 0.25,
}


def quality_report(series: pd.Series, entry: dict) -> dict:
    """Raw-level and month-end-level checks for one series."""
    raw = series.sort_index()
    rep = {
        "id": entry["id"],
        "quality_status": entry["quality_status"],
        "verification": entry["verification"],
        "is_total_return": entry["is_total_return"],
        "raw_obs": int(len(raw)),
        "raw_first": str(raw.index.min().date()) if len(raw) else None,
        "raw_last": str(raw.index.max().date()) if len(raw) else None,
        "raw_duplicates": int(raw.index.duplicated().sum()),
        "raw_nan": int(raw.isna().sum()),
        "non_positive": int((raw <= 0).sum()) if entry["asset_class"] not in ("money_market_yield", "bond_yield") else 0,
    }
    if rep["raw_duplicates"]:
        rep["month_end_status"] = "DUPLICATES - not usable"
        return rep
    me = to_month_end(raw)
    rep["month_ends"] = int(len(me))
    rep["month_end_first"] = str(me.index.min().date()) if len(me) else None
    rep["month_end_last"] = str(me["value"].last_valid_index().date()) if me["value"].notna().any() else None
    rep["stale_month_ends"] = [str(d.date()) for d in me.index[me["stale"]]]
    gaps = me.index[me["value"].isna() & ~me["stale"]]
    rep["missing_month_ends"] = [str(d.date()) for d in gaps]
    thr = EXTREME_MONTHLY_MOVE.get(entry["asset_class"])
    if thr is not None:
        r = simple_returns(me["value"]).dropna()
        ext = r[r.abs() > thr]
        rep["extreme_moves"] = {str(d.date()): round(float(v), 4) for d, v in ext.items()}
    else:
        lv = me["value"].dropna()
        ch = lv.diff().dropna()
        ext = ch[ch.abs() > 3.0]  # > 300bp/month change in a yield level
        rep["extreme_moves"] = {str(d.date()): round(float(v), 3) for d, v in ext.items()}
    return rep


def compare_returns(a: pd.Series, b: pd.Series, name_a: str, name_b: str) -> dict:
    """Compare two monthly-return series over their overlap."""
    x, y = a.align(b, join="inner")
    m = x.notna() & y.notna()
    x, y = x[m], y[m]
    if len(x) < 12:
        return {"a": name_a, "b": name_b, "overlap_months": int(len(x))}
    d = x - y
    ann_a = (1 + x).prod() ** (12 / len(x)) - 1
    ann_b = (1 + y).prod() ** (12 / len(y)) - 1
    return {
        "a": name_a,
        "b": name_b,
        "overlap": f"{x.index.min().date()}..{x.index.max().date()}",
        "overlap_months": int(len(x)),
        "correlation": float(np.corrcoef(x, y)[0, 1]),
        "mean_abs_monthly_diff": float(d.abs().mean()),
        "max_abs_monthly_diff": float(d.abs().max()),
        "max_abs_diff_month": str(d.abs().idxmax().date()),
        "tracking_error_ann": float(d.std(ddof=1) * math.sqrt(12)),
        "cagr_a": float(ann_a),
        "cagr_b": float(ann_b),
        "cagr_diff": float(ann_a - ann_b),
    }


def compare_sign_agreement(a: pd.Series, b: pd.Series) -> float:
    x, y = a.align(b, join="inner")
    m = x.notna() & y.notna()
    return float((np.sign(x[m]) == np.sign(y[m])).mean()) if m.any() else float("nan")


def tbill_transform_check(tr_index_monthly: pd.Series, yield_monthly: pd.Series) -> dict:
    """How well does r_t = y_{t-1}/1200 reproduce a T-bill TR index?"""
    r_idx = simple_returns(tr_index_monthly)
    out = {}
    for method in ("simple_prior", "compound_prior"):
        r_y = yield_to_monthly_return(yield_monthly, method=method)
        out[method] = compare_returns(r_idx, r_y, "tr_index", f"yield_{method}")
    # same-month (look-ahead) variant to identify the compiler's construction
    y = yield_monthly.copy()
    y.index = y.index + pd.offsets.MonthEnd(0)
    r_same = (y / 1200.0)
    out["simple_same_month"] = compare_returns(r_idx, r_same, "tr_index", "yield_same_month")
    return out
