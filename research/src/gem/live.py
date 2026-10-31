"""Live monthly REGIONAL_SEK signal from investable-instrument NAVs (prototype).

Pure function: same inputs -> same output. No trading, no account access.

Steps at each month change (as_of = the moment the signal is computed):
  1. signal_period_end = last calendar month end strictly before as_of
  2. every fund must have a NAV for the LAST COMMON NAV DATE of that month, and
     that date must be within `max_stale_bdays` business days of the month end
     (otherwise the month is not complete -> NO_SIGNAL)
  3. 12-month NAV return per region: NAV(month end t) / NAV(month end t-12) - 1
  4. Swedish cash hurdle: SE_CASH_SSVX_SYNTH_V1 from Riksbank SETB3MBENCH,
     12-month product of r_m = y_{m-1}/1200 (never the Ränta Kort fund NAV)
  5. rank USA / Europe / EM with RegionalMomentumStrategy (12 m, top-1)
  6. emit a JSON-serialisable signal with full provenance
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from .returns import to_month_end, trailing_return, yield_to_monthly_return
from .strategies import NO_SIGNAL, RegionalMomentumStrategy

REGION_TO_INSTRUMENT = {"usa": "AVANZA_USA", "europe": "AVANZA_EUROPA", "em": "AVANZA_EM"}
DEFENSIVE_INSTRUMENT = "AVANZA_RANTA_KORT"
STRATEGY = RegionalMomentumStrategy("REGIONAL_SEK", "1.0.0", regions=("usa", "europe", "em"),
                                    defensive_asset="cash")


def _bdays_between(a: pd.Timestamp, b: pd.Timestamp) -> int:
    return int(np.busday_count(a.date(), b.date()))


def regional_live_signal(as_of: date, navs: dict[str, pd.Series], ssvx_3m_yield: pd.Series,
                         *, nav_sources: dict[str, str] | None = None, max_stale_bdays: int = 3) -> dict:
    as_of_ts = pd.Timestamp(as_of)
    period_end = (as_of_ts.normalize().replace(day=1) - pd.offsets.Day(1)).normalize()  # previous month end
    out = {"strategy": STRATEGY.strategy_id, "strategy_version": STRATEGY.version, "as_of": str(as_of),
           "signal_period_end": str(period_end.date()), "status": NO_SIGNAL, "target": None,
           "returns": {}, "nav_dates": {}, "sources": nav_sources or {}, "reason": ""}

    # 2. completeness: NAVs available up to the last common NAV date of the month
    last_in_month = {}
    for region, iid in REGION_TO_INSTRUMENT.items():
        s = navs.get(iid)
        if s is None or s.empty:
            out["reason"] = f"no NAV series for {iid}"
            return out
        s = s[s.index <= period_end]
        if s.empty or s.index.max() < period_end - pd.offsets.MonthEnd(1):
            out["reason"] = f"{iid}: no NAV in {period_end:%Y-%m}"
            return out
        last_in_month[iid] = s.index.max()
        out["nav_dates"][iid] = str(s.index.max().date())
    common = min(last_in_month.values())
    if any(d != common for d in last_in_month.values()):
        out["reason"] = f"NAV dates differ at month end: {out['nav_dates']}"
        return out
    last_bday = period_end if period_end.weekday() < 5 else period_end - pd.offsets.BDay(1)
    if _bdays_between(common, last_bday) > max_stale_bdays:
        out["reason"] = f"month {period_end:%Y-%m} not complete: last common NAV {common.date()}"
        return out

    # 3. 12 m NAV momentum
    rets = {}
    for region, iid in REGION_TO_INSTRUMENT.items():
        me = to_month_end(navs[iid][navs[iid].index <= period_end])["value"]
        tr = trailing_return(me.dropna(), 12)
        v = tr.get(period_end, np.nan)
        rets[region] = None if pd.isna(v) else float(v)
    # 4. cash hurdle from Riksbank yields (month-end sampled, prior-month rule)
    y = to_month_end(ssvx_3m_yield[ssvx_3m_yield.index <= period_end])["value"]
    r_cash = yield_to_monthly_return(y).dropna()
    window = r_cash[(r_cash.index > period_end - pd.offsets.MonthEnd(12)) & (r_cash.index <= period_end)]
    cash = float((1 + window).prod() - 1) if len(window) == 12 else None
    out["returns"] = {**rets, "cash": cash}

    sig = STRATEGY.evaluate(period_end.date(), {k: rets[k] for k in ("usa", "europe", "em")}, cash)
    out["reason"] = sig.reason
    if not sig.is_valid:
        return out
    out["status"] = "VALID"
    out["target"] = DEFENSIVE_INSTRUMENT if sig.target == "cash" else REGION_TO_INSTRUMENT[sig.target]
    return out
