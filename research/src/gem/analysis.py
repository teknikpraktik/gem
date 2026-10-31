"""Comparisons between runs: signal agreement and same-window metric deltas."""

from __future__ import annotations

import pandas as pd

from .fx import sek_returns_from_usd_index
from .metrics import compute_metrics, equity_curve
from .returns import to_month_end


def signal_roles(signals: pd.DataFrame, role_of_asset: dict) -> pd.Series:
    """Signal history (signal_date -> role) with NO_SIGNAL rows removed."""
    s = signals[signals["target"] != "NO_SIGNAL"].copy()
    idx = pd.to_datetime(s["signal_date"])
    return pd.Series(s["target"].map(role_of_asset).values, index=idx).dropna()


def signal_agreement(a: pd.Series, b: pd.Series, start=None, end=None) -> dict:
    x, y = a.align(b, join="inner")
    if start is not None:
        m = (x.index >= pd.Timestamp(start)) & (x.index <= pd.Timestamp(end))
        x, y = x[m], y[m]
    if x.empty:
        return {"months": 0}
    same = x == y
    by_year = (~same).groupby(x.index.year).sum()
    cross = pd.crosstab(x.rename("original"), y.rename("sek"))
    return {
        "first_signal": str(x.index.min().date()),
        "last_signal": str(x.index.max().date()),
        "months": int(len(x)),
        "identical": int(same.sum()),
        "different": int((~same).sum()),
        "agreement_pct": float(same.mean()),
        "differences_by_year": {int(k): int(v) for k, v in by_year.items() if v > 0},
        "top_years": [int(k) for k in by_year.sort_values(ascending=False).index[:5] if by_year[k] > 0],
        "crosstab": {f"{i}->{j}": int(cross.at[i, j]) for i in cross.index for j in cross.columns},
    }


def usd_strategy_returns_in_sek(usd_returns: pd.Series, fx_raw: pd.Series) -> pd.Series:
    """Unhedged SEK investor in a USD strategy: SEK level = USD equity * SEK-per-USD."""
    eq = equity_curve(usd_returns, 1.0)
    fx = to_month_end(fx_raw)["value"]
    return sek_returns_from_usd_index(eq, fx).reindex(usd_returns.index)


def same_window_metrics(r: pd.Series, start, end, rf=None) -> dict:
    x = r[(r.index >= pd.Timestamp(start)) & (r.index <= pd.Timestamp(end))].dropna()
    return compute_metrics(x, rf=rf)
