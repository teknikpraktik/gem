"""Turn catalog series into monthly return / level / momentum panels for a run."""

from __future__ import annotations

import pandas as pd

from .fx import check_sek_per_usd
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
        fx = fx_me["value"]
        check_sek_per_usd(fx)
        fx_ret = fx / fx.shift(1)
        r = ((1 + r) * fx_ret.reindex(r.index) - 1)
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
