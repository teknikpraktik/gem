"""Generate cross-language conformance fixtures for the REGIONAL_SEK live engine.

    python research/scripts/export_live_fixtures.py [OUT.json]

Runs the Python REFERENCE implementation (gem.live.regional_live_signal) on a
set of edge cases and writes inputs + expected outputs. The TypeScript port in
web/lib/engine/regional.ts must reproduce every case exactly
(web/tests/engine.conformance.test.ts). Inputs are synthetic but shaped like
real Avanza NAV / Riksbank data (business days, holiday gaps, feeder lags).
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "src"))
from gem.live import regional_live_signal  # noqa: E402

FUNDS = ["AVANZA_USA", "AVANZA_EUROPA", "AVANZA_EM"]


def walk(seed: int, start="2023-01-02", end="2024-11-08", drift=0.0003, vol=0.01) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start, end)
    return pd.Series(100 * np.exp(np.cumsum(rng.normal(drift, vol, len(idx)))), index=idx).round(4)


def yields(level=3.0, start="2022-06-01", end="2024-11-08", seed=7) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start, end)
    return pd.Series(np.round(level + np.cumsum(rng.normal(0, 0.01, len(idx))), 3), index=idx)


def ser(s: pd.Series) -> list:
    return [[d.strftime("%Y-%m-%d"), float(v)] for d, v in s.items()]


def case(name, as_of, navs, y, note):
    out = regional_live_signal(as_of, navs, y)
    return {"name": name, "note": note, "as_of": str(as_of),
            "navs": {k: ser(v) for k, v in navs.items()}, "yields": ser(y),
            "expected": {k: out[k] for k in ("signal_period_end", "status", "target", "returns", "nav_dates", "reason")}}


def base(seeds=(1, 2, 3), drifts=(0.0006, 0.0003, 0.0001)):
    return {f: walk(s, drift=d) for f, s, d in zip(FUNDS, seeds, drifts)}


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "web" / "tests" / "fixtures" / "live_conformance.json"
    y = yields()
    cases = []
    cases.append(case("baseline", date(2024, 11, 1), base(), y, "normal month end"))
    cases.append(case("as_of_mid_month", date(2024, 10, 17), base(), y, "as_of mid-month -> previous month end"))
    neg = {f: walk(s, drift=-0.0008) for f, s in zip(FUNDS, (4, 5, 6))}
    cases.append(case("defensive_all_below_cash", date(2024, 11, 1), neg, y, "all regions below hurdle"))
    em_best = base(drifts=(0.0001, 0.0002, 0.0009))
    cases.append(case("em_best", date(2024, 11, 1), em_best, y, "EM wins"))
    n = base()
    n["AVANZA_EM"] = n["AVANZA_EM"][:"2024-10-30"]
    n["AVANZA_EUROPA"] = n["AVANZA_EUROPA"][:"2024-10-29"]
    cases.append(case("different_last_nav_dates", date(2024, 11, 1), n, y, "feeder/holiday: 1-2 day earlier last NAV is complete"))
    n = base()
    em = n["AVANZA_EM"]
    n["AVANZA_EM"] = em[(em.index < "2024-10-23") | (em.index > "2024-11-05")]
    cases.append(case("em_holiday_gap_at_month_end", date(2024, 11, 6), n, y, "EM closed 6 bdays over month end (Golden Week-like) -> NO_SIGNAL"))
    n = base()
    em = n["AVANZA_EM"]
    n["AVANZA_EM"] = em[(em.index < "2024-01-22") | (em.index > "2024-02-05")]
    cases.append(case("em_gap_in_middle", date(2024, 11, 1), n, y, "gap inside the 12m window does not matter"))
    n = base()
    em = n["AVANZA_EM"]
    n["AVANZA_EM"] = em[(em.index < "2023-10-24") | (em.index > "2023-11-06")]
    cases.append(case("em_stale_start_endpoint", date(2024, 11, 1), n, y, "12m start endpoint stale -> missing em_return"))
    short = {k: v["2024-03":] for k, v in base().items()}
    cases.append(case("history_too_short", date(2024, 11, 1), short, y, "< 12 months of NAV"))
    cases.append(case("cash_history_too_short", date(2024, 11, 1), base(), y["2024-02":], "< 13 month-end yields"))
    ys = y.copy()
    ys = ys[(ys.index < "2024-10-21") | (ys.index > "2024-10-31")]
    cases.append(case("cash_stale_in_period_month", date(2024, 11, 1), base(), ys, "yield stale in the period month (regularize trims grid)"))
    ys = y[(y.index < "2024-03-18") | (y.index > "2024-03-31")]
    cases.append(case("cash_stale_in_window", date(2024, 11, 1), base(), ys, "stale yield inside window -> missing hurdle"))
    tie = {f: walk(9) for f in FUNDS}
    cases.append(case("tie_first_region_wins", date(2024, 11, 1), tie, y, "identical NAVs: USA (first) wins"))
    n = base()
    n["AVANZA_USA"] = n["AVANZA_USA"][:"2024-10-25"]
    cases.append(case("usa_not_published_yet", date(2024, 11, 1), n, y, "month-end NAV not yet available -> NO_SIGNAL"))
    feb = {f: walk(s, start="2023-01-02", end="2024-03-08", drift=d) for f, s, d in zip(FUNDS, (1, 2, 3), (0.0006, 0.0003, 0.0001))}
    cases.append(case("leap_year_february", date(2024, 3, 1), feb, y, "Feb 2024 vs Feb 2023 month ends"))
    wk = {f: walk(s, start="2023-01-02", end="2024-07-05", drift=d) for f, s, d in zip(FUNDS, (1, 2, 3), (0.0006, 0.0003, 0.0001))}
    cases.append(case("month_end_on_weekend", date(2024, 7, 1), wk, y, "2024-06-30 is a Sunday"))
    hi = yields(level=40.0)
    cases.append(case("hurdle_above_all", date(2024, 11, 1), base(), hi, "very high cash -> defensive"))
    cases.append(case("missing_fund_series", date(2024, 11, 1), {k: v for k, v in base().items() if k != "AVANZA_EUROPA"}, y, "no NAV series for a fund"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"generator": "research/scripts/export_live_fixtures.py",
                               "reference": "research/src/gem/live.py::regional_live_signal",
                               "cases": cases}, indent=1, default=str))
    for c in cases:
        e = c["expected"]
        print(f"{c['name']:32s} {e['status']:9s} {str(e['target']):18s} {e['reason'][:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
