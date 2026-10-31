"""Randomized differential cases for the REGIONAL_SEK live engine (Python reference).

    python research/scripts/differential_cases.py OUT.json [--n 600] [--seed 20261031]

Generates N deterministic synthetic scenarios (fixed seed), runs the Python
REFERENCE implementation (gem.live.regional_live_signal) on each and writes the
inputs plus the complete reference output, including intermediate values
(`diagnostics`: 12-month endpoints per fund and the monthly cash-hurdle window).
web/tests/engine.differential.test.ts feeds the SAME inputs to the TypeScript
port and compares every field.

Scenario dimensions (each drawn per case, tags recorded per case):
  as-of date (2001-2030; month/year boundaries, February incl. leap years,
  weekend as-of days), history length (pipeline-shaped windows, long daily
  history, short history), NAV publication cut at / around the month end,
  stale-data exactly at / just inside / just outside the 3-bday NAV and 5-bday
  yield limits, gaps (holidays, multi-day closures) at both endpoints, weekend
  NAV stamps, different last NAV dates per fund, missing / empty series, yield
  gaps (whole months), NaN yields, negative yields, short yield history,
  identical momentum (ties) and momentum within 0 / 1e-15 / 1e-12 / 1e-9 of the
  cash hurdle.

NAV inputs never contain NaN (the provider contract forbids it); NaN appears
only in yields, which both implementations drop. Inputs are sorted and
duplicate-free, as delivered by the providers.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "src"))
from gem.live import regional_live_signal  # noqa: E402

FUNDS = ["AVANZA_USA", "AVANZA_EUROPA", "AVANZA_EM"]


def bdays(a: pd.Timestamp, b: pd.Timestamp) -> list[pd.Timestamp]:
    return list(pd.bdate_range(a, b)) if a <= b else []


def last_bday(me: pd.Timestamp) -> pd.Timestamp:
    return me if me.weekday() < 5 else me - pd.offsets.BDay(1)


def pick_as_of(rng) -> tuple[date, list[str]]:
    tags = []
    r = rng.random()
    year = int(rng.integers(2001, 2031))
    if r < 0.15:
        month, tags = 1, ["year_boundary"]
    elif r < 0.30:
        month, tags = 3, ["february_period"]
        if rng.random() < 0.5:
            year = int(rng.choice([2004, 2008, 2012, 2016, 2020, 2024, 2028]))
            tags.append("leap_year")
    else:
        month = int(rng.integers(1, 13))
    day = int(rng.integers(1, 11)) if rng.random() < 0.8 else int(rng.integers(11, 29))
    d = date(year, month, day)
    if d.weekday() >= 5:
        tags.append("weekend_as_of")
    return d, tags


def walk(rng, idx, drift, vol=0.01) -> np.ndarray:
    return np.round(100 * np.exp(np.cumsum(rng.normal(drift, vol, len(idx)))), 4)


def make_case(rng, i: int) -> dict:
    as_of, tags = pick_as_of(rng)
    a = pd.Timestamp(as_of)
    pe = (a.replace(day=1) - pd.offsets.Day(1)).normalize()
    se = pe - pd.offsets.MonthEnd(12)
    lb, lbs = last_bday(pe), last_bday(se)

    hist = rng.choice(["window", "long", "short"], p=[0.6, 0.3, 0.1])
    tags.append(f"history_{hist}")
    navs: dict[str, list] = {}
    drifts = rng.normal(0.0003, 0.0006, 3)
    for f, drift in zip(FUNDS, drifts):
        start = se - pd.Timedelta(days=int(rng.integers(45, 500 if hist == "long" else 60)))
        if hist == "short" and rng.random() < 0.7:
            start = se + pd.Timedelta(days=int(rng.integers(-6, 40)))
        idx = bdays(start, a - pd.Timedelta(days=1))
        if not idx:
            navs[f] = []
            continue
        vals = walk(rng, idx, drift)
        s = pd.Series(vals, index=pd.DatetimeIndex(idx))

        # publication cut around the period end: last NAV k bdays before lb (k<0: NAVs after the period)
        u = rng.random()
        if u < 0.20:
            k = int(rng.choice([0, 1, 2, 3, 3, 4]))
            cut = lb - pd.offsets.BDay(k) if k else lb
            s = s[s.index <= cut]
            tags.append(f"{f}_cut_{k}")
        elif u < 0.26:
            # closure over the month end with NAVs published afterwards
            k = int(rng.integers(1, 6))
            gap = bdays(lb - pd.offsets.BDay(k - 1), lb + pd.offsets.BDay(int(rng.integers(0, 3))))
            s = s.drop([d for d in gap if d in s.index])
            tags.append(f"{f}_closure_{k}")
        # gap at the start endpoint (stale exactly / just inside / just outside)
        if rng.random() < 0.12:
            k = int(rng.choice([2, 3, 4, 5]))
            gap = bdays(lbs - pd.offsets.BDay(k - 1), lbs + pd.offsets.BDay(int(rng.integers(0, 3))))
            s = s.drop([d for d in gap if d in s.index])
            tags.append(f"{f}_start_gap_{k}")
        # random holiday gaps elsewhere
        for _ in range(int(rng.poisson(1.0))):
            if len(s) > 5:
                j = int(rng.integers(0, len(s) - 3))
                s = s.drop(s.index[j:j + int(rng.integers(1, 4))])
        # weekend NAV stamp (seen once in real Avanza data)
        if rng.random() < 0.08 and len(s):
            sat = pe - pd.Timedelta(days=(pe.weekday() - 5) % 7)
            if sat not in s.index and sat <= a:
                s.loc[sat] = float(s.iloc[-1])
                s = s.sort_index()
                tags.append(f"{f}_weekend_nav")
        if hist == "window" and len(s):
            keep = ((s.index >= se - pd.Timedelta(days=20)) & (s.index <= se + pd.Timedelta(days=5))) | \
                   (s.index >= pe - pd.Timedelta(days=25))
            s = s[keep]
        navs[f] = s

    # ties: identical series for two funds
    if rng.random() < 0.06:
        f1, f2 = rng.choice(FUNDS, 2, replace=False)
        navs[str(f2)] = navs[str(f1)].copy() if isinstance(navs[str(f1)], pd.Series) else []
        tags.append("tie_identical")
    # missing / empty series
    u = rng.random()
    if u < 0.02:
        del navs[str(rng.choice(FUNDS))]
        tags.append("missing_series")
    elif u < 0.04:
        navs[str(rng.choice(FUNDS))] = []
        tags.append("empty_series")

    # yields
    level = float(rng.choice([-0.75, -0.25, 0.0, 0.5, 2.0, 3.5, 5.0]))
    ys = pe - pd.offsets.MonthEnd(int(rng.choice([14, 14, 14, 16, 20, 12, 11])))
    yidx = bdays(ys, a - pd.Timedelta(days=1))
    yv = np.round(level + np.cumsum(rng.normal(0, 0.01, len(yidx))), 3).astype(float)
    y = pd.Series(yv, index=pd.DatetimeIndex(yidx)) if yidx else pd.Series([], dtype=float)
    if len(y):
        if rng.random() < 0.07:  # drop a whole month
            m = pe - pd.offsets.MonthEnd(int(rng.integers(0, 13)))
            y = y[~((y.index.year == m.year) & (y.index.month == m.month))]
            tags.append("yield_month_missing")
        if rng.random() < 0.12:  # stale month end around the 5-bday limit
            m = pe - pd.offsets.MonthEnd(int(rng.integers(0, 13)))
            k = int(rng.choice([4, 5, 6, 7]))
            lbm = last_bday(m)
            y = y[~((y.index > lbm - pd.offsets.BDay(k)) & (y.index <= m))]
            tags.append(f"yield_stale_{k}")
        if rng.random() < 0.05:  # yields end before the period end
            y = y[y.index <= pe - pd.Timedelta(days=int(rng.integers(1, 20)))]
            tags.append("yield_ends_early")
        if rng.random() < 0.10:  # NaN observations
            j = rng.choice(len(y), size=min(len(y), int(rng.integers(1, 6))), replace=False)
            y.iloc[j] = np.nan
            tags.append("yield_nan")
    if rng.random() < 0.02:
        y = pd.Series([], dtype=float)
        tags.append("yield_empty")

    ser = {k: (v if isinstance(v, pd.Series) else pd.Series([], dtype=float, index=pd.DatetimeIndex([])))
           for k, v in navs.items()}
    if not isinstance(y.index, pd.DatetimeIndex):
        y.index = pd.DatetimeIndex(y.index)
    out = regional_live_signal(as_of, ser, y)

    # decision boundary: move the best fund's end NAV to (1 + hurdle) * start * (1 + eps)
    if rng.random() < 0.20 and out["returns"].get("cash") is not None:
        ends = out["diagnostics"]["endpoints"]
        cands = [f for f in FUNDS if ends.get(f, {}).get("start_nav") is not None]
        if cands:
            f = str(rng.choice(cands))
            eps = float(rng.choice([0.0, 1e-15, -1e-15, 1e-12, -1e-12, 1e-9, -1e-9]))
            e = ends[f]
            new = e["start_nav"] * (1 + out["returns"]["cash"]) * (1 + eps)
            # make it the best region as well
            for g in FUNDS:
                if g != f and ends.get(g, {}).get("start_nav") is not None and isinstance(ser.get(g), pd.Series):
                    d = pd.Timestamp(ends[g]["end_date"])
                    ser[g].loc[d] = ends[g]["start_nav"] * (1 + out["returns"]["cash"]) * 0.9
            ser[f].loc[pd.Timestamp(e["end_date"])] = new
            tags.append(f"hurdle_boundary_eps_{eps:g}")
            if rng.random() < 0.4:  # second fund with exactly the same return -> tie at the boundary
                g = str(rng.choice([x for x in FUNDS if x != f]))
                if ends.get(g, {}).get("start_nav") is not None:
                    ser[g].loc[pd.Timestamp(ends[g]["end_date"])] = new / e["start_nav"] * ends[g]["start_nav"]
                    tags.append("tie_at_boundary")
            out = regional_live_signal(as_of, ser, y)

    def enc(s: pd.Series, allow_nan: bool) -> list:
        res = []
        for d, v in s.items():
            v = float(v)
            if math.isnan(v):
                if not allow_nan:
                    raise ValueError("NaN NAV")
                res.append([d.strftime("%Y-%m-%d"), None])
            else:
                res.append([d.strftime("%Y-%m-%d"), v])
        return res

    return {"id": i, "tags": tags, "as_of": str(as_of),
            "navs": {k: enc(v, False) for k, v in ser.items()}, "yields": enc(y, True),
            "expected": {k: out[k] for k in ("strategy_version", "signal_period_end", "status", "target", "returns", "nav_dates",
                                             "reason", "diagnostics")}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20261031)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    cases = [make_case(rng, i) for i in range(a.n)]
    Path(a.out).write_text(json.dumps({"generator": "research/scripts/differential_cases.py", "seed": a.seed,
                                       "n": a.n, "cases": cases}, allow_nan=False))
    st = pd.Series([c["expected"]["status"] for c in cases]).value_counts().to_dict()
    tg = pd.Series([c["expected"]["target"] for c in cases]).value_counts(dropna=False).to_dict()
    print(json.dumps({"n": a.n, "seed": a.seed, "status": st, "target": {str(k): v for k, v in tg.items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
