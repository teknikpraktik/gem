"""Performance metrics on monthly simple returns.

Definitions (fixed, documented in reports/methodology.md):
  CAGR            (V_end / V_start) ** (12 / n_months) - 1
  volatility      stdev(monthly, ddof=1) * sqrt(12)
  Sharpe          mean(r - rf) * 12 / (stdev(r - rf, ddof=1) * sqrt(12))
  Sortino         mean(r - rf) * 12 / (sqrt(mean(min(r - rf, 0)^2)) * sqrt(12))
  max drawdown    min(V / running_max(V) - 1), V includes the start value
  Calmar          CAGR / |max drawdown|
  longest DD      longest run of months with V below its prior peak (months)
  longest underperf. vs benchmark: longest run of months in which the
                  strategy/benchmark wealth ratio is below its prior peak
  best/worst year calendar-year returns, full calendar years only
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def equity_curve(returns: pd.Series, start_value: float = 10_000.0) -> pd.Series:
    r = returns.dropna()
    if r.empty:
        return pd.Series(dtype=float)
    first = r.index[0] - pd.offsets.MonthEnd(1)
    return pd.concat([pd.Series([start_value], index=[first]), start_value * (1 + r).cumprod()])


def drawdown_curve(equity: pd.Series) -> pd.Series:
    return equity / equity.cummax() - 1.0


def _longest_below_peak(wealth: pd.Series) -> int:
    return _longest_below_peak_span(wealth)[0]


def _longest_below_peak_span(wealth: pd.Series):
    """(months, peak_label, last_label_below_peak) of the longest under-water spell."""
    longest = cur = 0
    peak = -math.inf
    peak_at = best = None
    idx = list(wealth.index)
    for i, v in enumerate(wealth.values):
        if v >= peak - 1e-15:
            peak = max(peak, v)
            peak_at = idx[i]
            cur = 0
        else:
            cur += 1
            if cur > longest:
                longest = cur
                best = (peak_at, idx[i])
    return longest, (best[0] if best else None), (best[1] if best else None)


def annual_returns(returns: pd.Series) -> pd.DataFrame:
    r = returns.dropna()
    g = r.groupby(r.index.year)
    df = pd.DataFrame({"return": g.apply(lambda x: float((1 + x).prod() - 1)), "months": g.size()})
    df["full_year"] = df["months"] == 12
    df.index.name = "year"
    return df


def compute_metrics(
    returns: pd.Series,
    rf: pd.Series | None = None,
    benchmark: pd.Series | None = None,
    weights: pd.DataFrame | None = None,
    turnover: pd.Series | None = None,
    targets: pd.Series | None = None,
    start_value: float = 10_000.0,
) -> dict:
    r = returns.dropna()
    n = len(r)
    if n == 0:
        return {"months": 0}
    eq = equity_curve(r, start_value)
    dd = drawdown_curve(eq)
    years = n / 12.0
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1
    vol = r.std(ddof=1) * math.sqrt(12) if n > 1 else float("nan")

    if rf is not None:
        rfa = rf.reindex(r.index)
        ex = (r - rfa).dropna()
    else:
        ex = r
    sharpe = ex.mean() * 12 / (ex.std(ddof=1) * math.sqrt(12)) if len(ex) > 1 and ex.std(ddof=1) > 0 else float("nan")
    downside = np.sqrt(np.mean(np.minimum(ex.values, 0.0) ** 2)) * math.sqrt(12) if len(ex) else float("nan")
    sortino = ex.mean() * 12 / downside if downside and downside > 0 else float("nan")
    mdd = float(dd.min())
    calmar = cagr / abs(mdd) if mdd < 0 else float("nan")

    yrs = annual_returns(r)
    full = yrs[yrs["full_year"]]
    out = {
        "start_date": str(r.index[0].date()),
        "end_date": str(r.index[-1].date()),
        "months": n,
        "start_value": float(eq.iloc[0]),
        "end_value": float(eq.iloc[-1]),
        "cagr": float(cagr),
        "volatility": float(vol),
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "max_drawdown": mdd,
        "calmar": float(calmar),
        "longest_drawdown_months": _longest_below_peak(eq),
        "longest_drawdown_span": "{}..{}".format(*[str(getattr(x, 'date', lambda: x)()) for x in _longest_below_peak_span(eq)[1:]]),
        "best_year": int(full["return"].idxmax()) if len(full) else None,
        "best_year_return": float(full["return"].max()) if len(full) else None,
        "worst_year": int(full["return"].idxmin()) if len(full) else None,
        "worst_year_return": float(full["return"].min()) if len(full) else None,
        "sharpe_rf": "hurdle/T-bill series of the run" if rf is not None else "none (rf=0)",
    }
    if benchmark is not None:
        b = benchmark.reindex(r.index)
        if b.notna().all():
            rel = (1 + r).cumprod() / (1 + b).cumprod()
            rel = pd.concat([pd.Series([1.0], index=[r.index[0] - pd.offsets.MonthEnd(1)]), rel])
            n_u, a_u, b_u = _longest_below_peak_span(rel)
            out["longest_underperformance_vs_benchmark_months"] = n_u
            out["longest_underperformance_span"] = f"{a_u.date()}..{b_u.date()}" if a_u is not None else None
        else:
            out["longest_underperformance_vs_benchmark_months"] = None
    if targets is not None:
        t = targets.reindex(r.index)
        switches = int((t != t.shift(1)).iloc[1:].sum())
        out["number_of_switches"] = switches
        out["switches_per_year"] = switches / years
        out["average_holding_period_months"] = n / (switches + 1)
    if turnover is not None:
        out["annual_turnover"] = float(turnover.reindex(r.index).fillna(0).sum() / 2 / years)
    if weights is not None:
        w = weights.reindex(r.index).fillna(0)
        out["time_in_asset"] = {c: float((w[c] > 0).mean()) for c in w.columns}
    return out
