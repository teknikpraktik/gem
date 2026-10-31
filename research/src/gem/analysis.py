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
    diff = ~same
    risk_on = {"US", "EX_US"}
    absolute = diff & (x.eq("DEFENSIVE") | y.eq("DEFENSIVE"))      # risk-on/off decision differs
    relative = diff & x.isin(risk_on) & y.isin(risk_on)             # both risk-on, different region
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
        "differences_absolute_momentum": int(absolute.sum()),
        "differences_relative_momentum": int(relative.sum()),
    }


def ranking_invariance(us_usd: pd.Series, exus_usd: pd.Series, us_sek: pd.Series, exus_sek: pd.Series) -> dict:
    """Check that converting BOTH legs with the same USD/SEK series leaves the
    US-vs-ex-US ranking unchanged: (1+a)k >= (1+b)k  <=>  a >= b for k > 0."""
    df = pd.concat({"u": us_usd, "x": exus_usd, "us": us_sek, "xs": exus_sek}, axis=1).dropna()
    usd_rank = df["u"] >= df["x"]
    sek_rank = df["us"] >= df["xs"]
    mism = df.index[usd_rank != sek_rank]
    return {"months": int(len(df)), "ranking_mismatches": int(len(mism)),
            "mismatch_months": [str(d.date()) for d in mism[:20]]}


def hurdle_sensitivity(sig_a: pd.Series, sig_b: pd.Series) -> dict:
    """Same strategy, two hurdle series: how many signals change on the overlap?"""
    x, y = sig_a.align(sig_b, join="inner")
    m = x.notna() & y.notna()
    x, y = x[m], y[m]
    d = x != y
    by_year = d.groupby(x.index.year).sum() if len(x) else pd.Series(dtype=int)
    return {"months": int(len(x)), "signals_changed": int(d.sum()),
            "signal_agreement_pct": float(1 - d.mean()) if len(x) else float("nan"),
            "changed_pct": float(d.mean()) if len(x) else float("nan"),
            "changed_by_year": {int(k): int(v) for k, v in by_year.items() if v > 0},
            "changed_dates": [str(t.date()) for t in x.index[d]][:60]}


def usd_strategy_returns_in_sek(usd_returns: pd.Series, fx_raw: pd.Series) -> pd.Series:
    """Unhedged SEK investor in a USD strategy: SEK level = USD equity * SEK-per-USD."""
    eq = equity_curve(usd_returns, 1.0)
    fx = to_month_end(fx_raw)["value"]
    return sek_returns_from_usd_index(eq, fx).reindex(usd_returns.index)


def same_window_metrics(r: pd.Series, start, end, rf=None) -> dict:
    x = r[(r.index >= pd.Timestamp(start)) & (r.index <= pd.Timestamp(end))].dropna()
    return compute_metrics(x, rf=rf)
