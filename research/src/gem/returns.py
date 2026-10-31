"""Time-series primitives: month-end sampling, returns, yield->return.

Month-end definition (used everywhere):
  * The *label* of a month is the last calendar day of that month.
  * The *value* is the last valid (non-NaN, non-zero-placeholder) observation
    whose date falls inside that calendar month.
  * The observation is STALE if it is more than `max_stale_bdays` business
    days (Mon-Fri, no holiday calendar) before the last business day of the
    month. Stale month-ends are set to NaN and flagged - never forward-filled.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_MAX_STALE_BDAYS = 5


def month_end_label(ts) -> pd.Timestamp:
    return (pd.Timestamp(ts) + pd.offsets.MonthEnd(0)).normalize()


def to_month_end(series: pd.Series, max_stale_bdays: int = DEFAULT_MAX_STALE_BDAYS) -> pd.DataFrame:
    """Sample an irregular/daily/monthly series at month end.

    Returns a DataFrame indexed by month-end label with columns
    `value`, `obs_date`, `stale`. Months with no observation at all are
    present (between first and last observed month) with value NaN so that
    gaps stay visible.
    """
    s = series.dropna().sort_index()
    if s.index.has_duplicates:
        raise ValueError(f"duplicate timestamps in series {series.name!r}")
    if s.empty:
        return pd.DataFrame(columns=["value", "obs_date", "stale"])
    s.index = pd.DatetimeIndex(s.index).normalize()
    labels = s.index + pd.offsets.MonthEnd(0)
    df = pd.DataFrame({"value": s.values, "obs_date": s.index}, index=labels)
    last = df.groupby(level=0).tail(1)
    full = pd.date_range(last.index.min(), last.index.max(), freq="ME")
    out = last.reindex(full)
    last_bday = full.map(lambda d: d if d.weekday() < 5 else d - pd.offsets.BDay(1))
    lag = [
        np.busday_count(o.date(), lb.date()) if pd.notna(o) else np.nan
        for o, lb in zip(out["obs_date"], last_bday)
    ]
    out["stale"] = [bool(pd.notna(l) and l > max_stale_bdays) for l in lag]
    out.loc[out["stale"], "value"] = np.nan
    out.index.name = "month_end"
    return out


def regularize_monthly(levels: pd.Series) -> pd.Series:
    """Reindex a month-end series onto a complete month-end grid (gaps -> NaN)."""
    s = levels.copy()
    s.index = pd.DatetimeIndex(s.index) + pd.offsets.MonthEnd(0)
    if s.index.has_duplicates:
        raise ValueError(f"duplicate month-ends in {levels.name!r}")
    s = s.sort_index()
    if s.dropna().empty:
        return s
    full = pd.date_range(s.dropna().index.min(), s.dropna().index.max(), freq="ME")
    return s.reindex(full)


def simple_returns(levels: pd.Series) -> pd.Series:
    """Month-over-month simple returns. A gap produces NaN, never a 2-month return."""
    s = regularize_monthly(levels)
    return (s / s.shift(1) - 1.0).rename(levels.name)


def trailing_return(levels: pd.Series, months: int = 12) -> pd.Series:
    """Trailing total return over exactly `months` calendar months.

    Requires both endpoint levels to exist on a complete month grid AND every
    intermediate month to be present (a hole inside the window means the
    series is not trustworthy for that window -> NaN).
    """
    s = regularize_monthly(levels)
    r = s / s.shift(months) - 1.0
    present = s.notna().astype(int)
    window_ok = present.rolling(months + 1).sum() == months + 1
    return r.where(window_ok).rename(levels.name)


def index_from_returns(returns: pd.Series, base: float = 100.0) -> pd.Series:
    r = returns.dropna()
    if r.empty:
        return r
    first = r.index[0] - pd.offsets.MonthEnd(1)
    idx = pd.concat([pd.Series([base], index=[first]), base * (1 + r).cumprod()])
    return idx.rename(returns.name)


def yield_to_monthly_return(annual_yield_pct: pd.Series, method: str = "simple_prior") -> pd.Series:
    """Convert an annualised money-market yield (percent) into monthly returns.

    method="simple_prior" (default):
        r_t = y_{t-1} / 100 / 12
        A bill bought at the end of month t-1 at yield y_{t-1} earns roughly
        1/12 of the annual rate during month t. Uses only information known at
        the start of the holding month (no look-ahead).
    method="compound_prior":
        r_t = (1 + y_{t-1}/100) ** (1/12) - 1

    Known approximation errors (documented in reports/methodology.md):
      * discount-basis vs. bond-equivalent yield difference (TB3MS is on a
        discount basis; error is a few bp/yr at normal rate levels),
      * a 3-month bill held for 1 month also has small price effects when
        rates move (ignored),
      * monthly-average yield series (e.g. TB3MS) vs. month-end yields.
    The result is a SYNTHETIC total-return proxy, never a verified index.
    """
    y = regularize_monthly(annual_yield_pct) / 100.0
    prior = y.shift(1)
    if method == "simple_prior":
        r = prior / 12.0
    elif method == "compound_prior":
        r = (1.0 + prior) ** (1.0 / 12.0) - 1.0
    else:
        raise ValueError(f"unknown method {method!r}")
    return r.rename(annual_yield_pct.name)


def par_bond_monthly_return(annual_yield_pct: pd.Series, maturity_years: float) -> pd.Series:
    """Synthetic constant-maturity par-bond total return from yields.

    Standard approximation: a par bond bought at y_{t-1} is repriced one month
    later at y_t with remaining maturity (M - 1/12), plus one month of coupon.
    Price uses the closed-form annuity formula with semi-annual coupons.
    Used ONLY for clearly labelled synthetic bond proxies.
    """
    y = regularize_monthly(annual_yield_pct) / 100.0
    y0, y1 = y.shift(1), y
    n = 2 * (maturity_years - 1.0 / 12.0)
    c = y0 / 2
    yy = y1 / 2
    with np.errstate(divide="ignore", invalid="ignore"):
        price = np.where(yy.abs() < 1e-12, c * n + 1.0, c / yy * (1 - (1 + yy) ** (-n)) + (1 + yy) ** (-n))
    r = pd.Series(price, index=y.index) - 1.0 + y0 / 12.0
    return r.where(y0.notna() & y1.notna()).rename(annual_yield_pct.name)
