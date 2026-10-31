"""Turn catalog series into monthly return / level / momentum panels for a run."""

from __future__ import annotations

import pandas as pd

from .fx import check_sek_per_usd, sek_returns_from_usd_index
from .returns import (
    index_from_returns, par_bond_monthly_return, simple_returns, to_month_end, trailing_return,
    yield_to_monthly_return,
)
from .runs import Leg, RunSpec
from .strategies import LOOKBACK_MONTHS


def monthly_returns_for_series(raw: pd.Series, entry: dict) -> tuple[pd.Series, pd.Series]:
    """Return (monthly simple returns, stale flags) for one catalog series."""
    me = to_month_end(raw)
    vals, stale = me["value"], me["stale"]
    ac = entry["asset_class"]
    if entry["is_total_return"]:
        r = simple_returns(vals)
    elif ac == "money_market_yield":
        r = yield_to_monthly_return(vals, method="simple_prior")
    elif ac == "bond_yield":
        r = par_bond_monthly_return(vals, float(entry["fetch"].get("maturity_years", 5)))
    else:
        raise ValueError(f"{entry['id']}: cannot derive returns from asset_class={ac}")
    return r.rename(entry["id"]), stale.rename(entry["id"])


def leg_returns(leg: Leg, data: dict[str, pd.Series], catalog: dict[str, dict]) -> tuple[pd.Series, pd.Series]:
    pieces, stales = [], []
    prev_end = None
    for sid, end in leg.segments:
        r, st = monthly_returns_for_series(data[sid], catalog[sid])
        if prev_end is not None:
            r, st = r[r.index > prev_end], st[st.index > prev_end]
        if end is not None:
            e = pd.Timestamp(end) + pd.offsets.MonthEnd(0)
            r, st = r[r.index <= e], st[st.index <= e]
            prev_end = e
        pieces.append(r)
        stales.append(st)
    r = pd.concat(pieces).sort_index()
    st = pd.concat(stales).sort_index()
    if r.index.has_duplicates:
        raise ValueError("overlapping splice segments")
    if leg.fx_to_sek:
        fx_me = to_month_end(data[leg.fx_to_sek])
        full = pd.date_range(r.index.min() - pd.offsets.MonthEnd(1), r.index.max(), freq="ME")
        usd_level = chain_levels(r.reindex(full[1:])).reindex(full)
        r = sek_returns_from_usd_index(usd_level, fx_me["value"]).reindex(r.index)
        st = st | fx_me["stale"].reindex(st.index).fillna(False).astype(bool)
    return r, st.astype(bool)


def chain_levels(r: pd.Series, base: float = 100.0) -> pd.Series:
    """Gap-aware level index.

    Before the first valid return the chain starts at `base` one month earlier.
    A missing return breaks the chain: that month is NaN and a NEW chain starts
    at `base` at the next valid month (whose own return is not chained). So no
    level window can span a data hole and trailing_return() needs 13 fresh
    consecutive levels after any gap.
    """
    out: dict = {}
    lvl = None
    started = False
    for t, x in r.items():
        if pd.isna(x):
            lvl = None
            out[t] = float("nan")
            continue
        if lvl is None:
            if not started:
                out[t - pd.offsets.MonthEnd(1)] = base
                lvl = base
                started = True
            else:
                out[t] = base
                lvl = base
                continue
        lvl = lvl * (1 + x)
        out[t] = lvl
    return pd.Series(out, dtype=float).sort_index().rename(r.name)


def build_panels(run: RunSpec, data: dict[str, pd.Series], catalog: dict[str, dict]) -> dict:
    rets, stale = {}, {}
    for asset, leg in run.legs.items():
        rets[asset], stale[asset] = leg_returns(leg, data, catalog)
    R = pd.DataFrame(rets).sort_index()
    full = pd.date_range(R.index.min(), R.index.max(), freq="ME")
    R = R.reindex(full)
    S = pd.DataFrame(stale).reindex(full).fillna(False).astype(bool)
    L = pd.DataFrame({a: chain_levels(R[a]) for a in R}).reindex(full)
    M = pd.DataFrame({a: trailing_return(L[a].dropna(), LOOKBACK_MONTHS) for a in L}).reindex(full)
    return {"returns": R, "levels": L, "momentum": M, "stale": S}


def daily_level(leg: Leg, data: dict[str, pd.Series], catalog: dict[str, dict], max_fx_gap_days: int = 5) -> pd.Series:
    """Daily TR level for one leg (single segment). USD legs are converted with
    TR_SEK(d) = TR_USD(d) * SEKUSD(d); FX may be carried forward at most
    `max_fx_gap_days` calendar days (FX holidays), never further."""
    if len(leg.segments) != 1:
        raise ValueError("daily legs must have exactly one segment")
    sid = leg.segments[0][0]
    e = catalog[sid]
    if e["is_total_return"]:
        lv = data[sid].sort_index()
    elif e["asset_class"] == "money_market_yield":
        lv = daily_cash_level_from_yield(data[sid])
    else:
        raise ValueError(f"{sid}: daily execution needs a total-return level or a money-market yield")
    if leg.fx_to_sek:
        fx = data[leg.fx_to_sek].sort_index()
        check_sek_per_usd(fx)
        fx_on = fx.reindex(fx.index.union(lv.index)).ffill(limit=None)
        last_obs = pd.Series(fx.index, index=fx.index).reindex(fx_on.index).ffill()
        age = (fx_on.index - pd.DatetimeIndex(last_obs.values)).days
        fx_on = fx_on.where(age <= max_fx_gap_days)
        lv = lv * fx_on.reindex(lv.index)
    return lv.dropna().rename(sid)


def daily_cash_level_from_yield(y_pct: pd.Series, base: float = 100.0) -> pd.Series:
    """Daily synthetic cash index (SE_CASH_SSVX_SYNTH_V1, daily form).

    Between consecutive quote dates d0 < d1 the index accrues the yield known at d0:
        L(d1) = L(d0) * (1 + y(d0)/100 * (d1 - d0).days / 365)
    ACT/365 keeps it consistent with the monthly model r_t = y_{t-1}/12. Only the
    yield of the previous quote date is used (no look-ahead). Gaps longer than 7
    calendar days break the series (NaN), they are not bridged.
    """
    y = y_pct.dropna().sort_index()
    out = [base]
    for i in range(1, len(y)):
        days = (y.index[i] - y.index[i - 1]).days
        if days > 7:
            out.append(float("nan"))
            continue
        prev = out[-1] if out[-1] == out[-1] else base
        out.append(prev * (1 + y.iloc[i - 1] / 100 * days / 365))
    return pd.Series(out, index=y.index, name=y.name)


def build_daily_levels(run: RunSpec, data: dict[str, pd.Series], catalog: dict[str, dict]) -> pd.DataFrame:
    cols = {a: daily_level(leg, data, catalog) for a, leg in (run.daily_legs or {}).items()}
    return pd.DataFrame(cols).sort_index()
