"""End-to-end research pipeline.

    python -m gem.research            # use cached raw data, fetch only what is missing
    python -m gem.research --refresh  # re-download all reachable sources
    python -m gem.research --offline  # never touch the network

Steps: fetch/cache -> parse -> data quality -> cross-validation -> panels ->
backtests (all runs x execution conventions x cost scenarios) -> reports.

Runs whose series are not all available are reported as BLOCKED with the
exact missing series and the reason; nothing is substituted silently.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import reporting
from .backtest import generate_signals, run_backtest
from .catalog import load_catalog, load_instruments
from .data.base import FetchError, RawStore
from .data.providers import fetch_raw, parse
from .execution import IDEALIZED_CLOSE, NEXT_MONTH_CLOSE
from .panel import build_panels
from .returns import simple_returns, to_month_end
from .runs import RunSpec, all_runs
from .strategies import FixedWeightStrategy
from .validation import compare_returns, quality_report, tbill_transform_check

log = logging.getLogger("gem.research")

ROOT = Path(__file__).resolve().parents[2]  # research/
EXECUTIONS = (NEXT_MONTH_CLOSE, IDEALIZED_CLOSE)
COST_SCENARIOS = {"COST_0": 0.0, "COST_10BPS": 10.0}  # per side, on traded weight

CROSS_CHECK_SERIES = [
    "ARCH_FF_RF", "ARCH_FF_US_MKT_TR", "SHILLER_SP_TR", "AJ_IBBOTSON_TBILL_30D", "AJ_TB3MS_YIELD",
    "AJ_MSCI_USA_GR", "H10_SEK_PER_USD",
]


def load_all(catalog: dict, ids: set[str], store: RawStore, refresh: bool, offline: bool, manual_dir: Path):
    data, status = {}, {}
    for sid in sorted(ids):
        e = catalog[sid]
        try:
            raw = fetch_raw(e, store, refresh=refresh, offline=offline, manual_dir=manual_dir)
            s = parse(e, raw)
            if s.empty:
                raise FetchError("parsed series is empty")
            data[sid] = s
            status[sid] = {"status": "OK", "fetch": raw.status, "sha256": raw.sha256, "url": raw.url,
                           "retrieved_at": raw.retrieved_at}
        except Exception as ex:  # noqa: BLE001 - reported, never hidden
            status[sid] = {"status": "UNAVAILABLE", "error": str(ex)[:300]}
            log.warning("series %s unavailable: %s", sid, str(ex)[:160])
    return data, status


def cross_validation(data: dict) -> list[dict]:
    out = []

    def mret(sid):
        return simple_returns(to_month_end(data[sid])["value"])

    pairs = [
        ("AJ_IBBOTSON_TBILL_30D", "ARCH_FF_RF", "Ibbotson 30d bill (compilation) vs Ken French RF (arch snapshot)"),
        ("AJ_TBILL_3M_TR", "ARCH_FF_RF", "3m bill TR (compilation, from TB3MS) vs Ken French RF (1m)"),
        ("AJ_IBBOTSON_LARGE", "ARCH_FF_US_MKT_TR", "Ibbotson Large Co. vs CRSP US market (FF)"),
        ("AJ_SP500TR", "AJ_IBBOTSON_LARGE", "S&P 500 TR (Yahoo) vs Ibbotson Large Co. (both S&P 500 TR)"),
        ("AJ_SP500TR", "ARCH_FF_US_MKT_TR", "S&P 500 TR vs CRSP US market (FF)"),
        ("AJ_MSCI_USA_GR", "AJ_SP500TR", "MSCI USA gross vs S&P 500 TR"),
        ("SHILLER_SP_TR", "AJ_SP500TR", "Shiller S&P (monthly-average prices) vs S&P 500 TR month-end"),
        ("AJ_MSCI_ACWI_EXUS_GR", "AJ_MSCI_WORLD_EXUS_GR", "ACWI ex USA vs World ex USA (EM effect)"),
        ("AJ_US_AGG", "AJ_IBBOTSON_IT_GOVT", "US Aggregate vs Ibbotson IT Govt (splice check, 1976-1999)"),
    ]
    for a, b, label in pairs:
        if a in data and b in data:
            d = compare_returns(mret(a), mret(b), a, b)
            d["label"] = label
            out.append(d)
    if "AJ_TBILL_3M_TR" in data and "AJ_TB3MS_YIELD" in data:
        chk = tbill_transform_check(to_month_end(data["AJ_TBILL_3M_TR"])["value"],
                                    to_month_end(data["AJ_TB3MS_YIELD"])["value"])
        for k, v in chk.items():
            v["label"] = f"T-bill TR index vs TB3MS transformed ({k})"
            out.append(v)
    return out


def run_one(run: RunSpec, data: dict, catalog: dict, window_override: dict) -> list:
    panels = build_panels(run, data, catalog)
    R, M, S, L = panels["returns"], panels["momentum"], panels["stale"], panels["levels"]
    strat = run.strategy
    if isinstance(strat, FixedWeightStrategy):
        sigs = generate_signals(strat, L, run.roles)
    else:
        sigs = generate_signals(strat, M, run.roles, stale=S)
    rf = R[run.rf_asset] if run.rf_asset else None
    bench = R[run.benchmark_asset] if run.benchmark_asset else None
    results = []
    windows = list(run.windows)
    if run.run_id in window_override:
        windows = window_override[run.run_id]
    # Fixed-weight portfolios do not depend on signal timing -> one execution convention.
    executions = (NEXT_MONTH_CLOSE,) if isinstance(strat, FixedWeightStrategy) else EXECUTIONS
    for wname, ws, we in windows:
        for ex in executions:
            for cname, bps in COST_SCENARIOS.items():
                rid = f"{run.run_id}__{wname}__{ex.name}__{cname}"
                res = run_backtest(
                    rid, strat, sigs, R, ex, cost_per_side_bps=bps, rf=rf, benchmark=bench,
                    data_tier=run.tier,
                    start=pd.Timestamp(ws) if ws else None, end=pd.Timestamp(we) if we else None,
                    notes=list(run.notes),
                )
                res.window = wname
                res.run_spec = run
                results.append(res)
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m gem.research")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    root = args.root
    catalog = load_catalog(root / "data" / "catalog.yaml")
    instruments = load_instruments(root / "data" / "investable_instruments.yaml")
    store = RawStore(root / "data" / "raw", root / "data" / "manifests")
    runs = all_runs()
    needed = set(CROSS_CHECK_SERIES)
    for r in runs:
        needed |= r.series_ids
    needed |= {"AJ_TBILL_3M_TR"}
    unknown = needed - set(catalog)
    if unknown:
        raise SystemExit(f"series used but not in catalog: {sorted(unknown)}")

    data, status = load_all(catalog, needed, store, args.refresh, args.offline, root / "data" / "manual")
    quality = {sid: quality_report(s, catalog[sid]) for sid, s in data.items()}
    xval = cross_validation(data)

    gen = root / "reports" / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    results, blocked = [], {}
    # 3P benchmarks are evaluated over exactly the months of the matching GEM run
    order = sorted(runs, key=lambda r: (r.tier == "BENCHMARK", r.run_id))
    window_override: dict = {}
    for run in order:
        missing = sorted(s for s in run.series_ids if s not in data)
        if missing:
            blocked[run.run_id] = {"tier": run.tier,
                                   "missing": {m: status.get(m, {}).get("error", "not loaded") for m in missing}}
            continue
        res = run_one(run, data, catalog, window_override)
        results.extend(res)
        if run.run_id.startswith("GEM_ORIGINAL_") and run.run_id.endswith("_3P"):
            suffix = run.run_id.replace("GEM_ORIGINAL_", "")
            base = [x for x in res if x.window == "FULL" and x.execution == NEXT_MONTH_CLOSE.name
                    and x.cost_per_side_bps == 0]
            if base and len(base[0].monthly):
                m = base[0].monthly.index
                wins = [("FULL", str(m[0].date()), str(m[-1].date()))]
                if any(w[0] == "REF_1974_2013" for w in run.windows):
                    wins.append(("REF_1974_2013", "1974-01-31", "2013-12-31"))
                for b in ("BUY_HOLD_US", "BUY_HOLD_EXUS", "BUY_HOLD_US_AGG", "STATIC_70_30_US"):
                    window_override[f"{b}_{suffix}"] = wins

    for r in results:
        r.export(gen / "runs" / r.run_id)
    reporting.write_all(root, catalog, status, quality, xval, results, blocked, instruments)
    log.info("runs completed: %d result sets, %d blocked runs", len(results), len(blocked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
