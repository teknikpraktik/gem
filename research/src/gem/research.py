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
    # Phase 2: synthetic Swedish cash model vs OMRX T-bill index (overlap from 2008-11)
    if "RB_SSVX_3M" in data and "FRED_OMRXTBILL" in data:
        chk = tbill_transform_check(to_month_end(data["FRED_OMRXTBILL"])["value"],
                                    to_month_end(data["RB_SSVX_3M"])["value"])
        for k, v in chk.items():
            v["label"] = f"OMRX T-bill index vs SE_CASH_SSVX_SYNTH ({k})"
            out.append(v)
    if "RB_SEK_PER_USD" in data and "H10_SEK_PER_USD" in data:
        d = compare_returns(mret("RB_SEK_PER_USD"), mret("H10_SEK_PER_USD"), "RB_SEK_PER_USD", "H10_SEK_PER_USD")
        d["label"] = "USD/SEK: Riksbank fixing vs H.10 New York noon (monthly changes)"
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


def access_report(status: dict, catalog: dict, store_manifest: Path) -> list[dict]:
    """Which hosts/endpoints failed in THIS run, and why."""
    from urllib.parse import urlparse

    from .data.providers import entry_url

    rows = []
    for sid, st in sorted(status.items()):
        e = catalog[sid]
        url = st.get("url") or entry_url(e) or f"manual:{e['fetch'].get('file', '')}"
        host = urlparse(url).netloc or url
        err = st.get("error", "")
        import re as _re
        m = _re.search(r"(Tunnel connection failed: [^'\")]+|NameResolutionError|Read timed out|HTTP Error \d+|\d{3} Client Error[^'\"]*)", err)
        rows.append({"series": sid, "host": host, "endpoint": url, "status": st["status"],
                     "fetch": st.get("fetch", ""), "error": (m.group(1) if m else err)[:200]})
    return rows


def provenance_block(run: RunSpec, catalog: dict, status: dict, data: dict) -> dict:
    """Exact data lineage of a run: version, series, provider, retrieval, period, quality."""
    series = []
    for sid in sorted(run.series_ids):
        e, st = catalog[sid], status.get(sid, {})
        s = data.get(sid)
        series.append({"id": sid, "provider": e["provider"], "provider_series_id": e["provider_series_id"],
                       "quality_status": e["quality_status"], "verification": e["verification"],
                       "retrieved_at": st.get("retrieved_at"), "sha256": st.get("sha256"), "fetch": st.get("fetch"),
                       "data_period": f"{s.index.min().date()}..{s.index.max().date()}" if s is not None else None,
                       "class": data_class(e, st)})
    return {"strategy_id": run.strategy.strategy_id, "strategy_version": run.strategy.version, "run_id": run.run_id,
            "tier": run.tier, "series": series,
            "weakest_class": max((x["class"] for x in series), key=DATA_CLASS_ORDER.index)}


DATA_CLASS_ORDER = ["PRIMARY_SOURCE_VERIFIED", "PROXY", "THIRD_PARTY", "SYNTHETIC_TEST_ONLY"]


def data_class(entry: dict, st: dict) -> str:
    if st.get("fetch") == "SYNTHETIC":
        return "SYNTHETIC_TEST_ONLY"
    p = entry["fetch"]["provider"]
    if p.startswith("github_") or p.startswith("pypi_"):
        return "THIRD_PARTY"
    if entry["quality_status"] == "VERIFIED" and p in ("fred", "riksbank", "french", "local_csv"):
        return "PRIMARY_SOURCE_VERIFIED"
    return "PROXY"


def _common_window(results, members) -> tuple[str, str] | None:
    spans = []
    for rid in members:
        rs = [r for r in results if r.run_spec.run_id == rid and r.window == "FULL"
              and r.execution == NEXT_MONTH_CLOSE.name and r.cost_per_side_bps == 0 and len(r.monthly)]
        if rs:
            spans.append((rs[0].monthly.index[0], rs[0].monthly.index[-1]))
    if not spans:
        return None
    a, b = max(x for x, _ in spans), min(y for _, y in spans)
    return (str(a.date()), str(b.date())) if a < b else None


def run_daily(run: RunSpec, data: dict, catalog: dict, window) -> list:
    from .daily import SCENARIOS, run_daily_backtest
    from .panel import build_daily_levels

    panels = build_panels(run, data, catalog)
    sigs = generate_signals(run.strategy, panels["momentum"], run.roles, stale=panels["stale"])
    lv = build_daily_levels(run, data, catalog)
    rf = panels["returns"][run.rf_asset] if run.rf_asset else None
    out = []
    for sc in SCENARIOS:
        for cname, bps in COST_SCENARIOS.items():
            res = run_daily_backtest(f"{run.run_id}__DAILY__{sc.name}__{cname}", sigs, lv, sc,
                                     cost_per_side_bps=bps, rf_monthly=rf,
                                     start=window[0] if window else None, end=window[1] if window else None)
            res.run_spec = run
            res.cost = bps
            out.append(res)
    return out


def main(argv=None) -> int:
    from .analysis import signal_agreement, signal_roles, usd_strategy_returns_in_sek
    from .metrics import compute_metrics
    from .runs import AGREEMENT_PAIRS, ROLE_OF_ASSET

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
    needed = set(CROSS_CHECK_SERIES) | {"AJ_TBILL_3M_TR", "RB_SEK_PER_USD", "RB_SSVX_1M", "RB_SSVX_6M",
                                         "FRED_OECD_SE_3M_TREASURY", "FRED_DEXSDUS"}
    needed |= {sid for sid, e in catalog.items() if sid.startswith("AVZ_NAV_")}
    for r in runs:
        needed |= r.series_ids | r.daily_series_ids
    unknown = needed - set(catalog)
    if unknown:
        raise SystemExit(f"series used but not in catalog: {sorted(unknown)}")

    data, status = load_all(catalog, needed, store, args.refresh, args.offline, root / "data" / "manual")
    for sid, st in status.items():
        st["transform"] = catalog[sid].get("transform") or (
            "level (total-return index)" if catalog[sid]["is_total_return"] else "none (not a return series)")
    quality = {sid: quality_report(s, catalog[sid]) for sid, s in data.items()}
    xval = cross_validation(data)

    gen = root / "reports" / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    results, blocked = [], {}
    order = sorted(runs, key=lambda r: (r.tier == "BENCHMARK", r.run_id))
    window_override: dict = {}
    ran: set[str] = set()
    for run in order:
        missing = sorted(s for s in run.series_ids if s not in data)
        if missing:
            blocked[run.run_id] = {"tier": run.tier, "group": run.group,
                                   "missing": {m: status.get(m, {}).get("error", "not loaded") for m in missing}}
            continue
        res = run_one(run, data, catalog, window_override)
        results.extend(res)
        ran.add(run.run_id)
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

    # ---- comparison groups: rerun every member over the group's COMMON window ----
    groups: dict[str, list[str]] = {}
    for r in runs:
        if r.group:
            groups.setdefault(r.group, []).append(r.run_id)
    group_windows = {}
    for g, members in sorted(groups.items()):
        ok = [m for m in members if m in ran]
        need_swedish = any(next(x for x in runs if x.run_id == m).tier == "SWEDISH" for m in ok)
        w = _common_window(results, ok) if need_swedish else None
        group_windows[g] = {"members": members, "ran": ok, "common_window": w}
        if w:
            for m in ok:
                spec = next(x for x in runs if x.run_id == m)
                results.extend(run_one(spec, data, catalog, {m: [(f"COMMON_{g}", w[0], w[1])]}))

    # ---- daily execution scenarios A/B/C ----
    daily_results, daily_blocked = [], {}
    for r in runs:
        if not r.daily_legs:
            continue
        miss = sorted(s for s in (r.series_ids | r.daily_series_ids) if s not in data)
        if miss:
            daily_blocked[r.run_id] = {m: status.get(m, {}).get("error", "not loaded") for m in miss}
            continue
        w = (group_windows.get(r.group) or {}).get("common_window")
        daily_results.extend(run_daily(r, data, catalog, w))

    # ---- GEM_ORIGINAL vs GEM_SEK signal agreement ----
    agreement = {}
    for a_id, b_id in AGREEMENT_PAIRS:
        if a_id not in ran or b_id not in ran:
            agreement[f"{a_id} vs {b_id}"] = {"status": "BLOCKED",
                                              "missing_runs": [x for x in (a_id, b_id) if x not in ran]}
            continue
        spec_b = next(x for x in runs if x.run_id == b_id)
        w = (group_windows.get(spec_b.group) or {}).get("common_window")
        pick = lambda rid, win: next(x for x in results if x.run_spec.run_id == rid and x.window == win
                                     and x.execution == IDEALIZED_CLOSE.name and x.cost_per_side_bps == 0)
        win = f"COMMON_{spec_b.group}" if w else "FULL"
        ra, rb = pick(a_id, win), pick(b_id, win)
        ag = signal_agreement(signal_roles(ra.signals, ROLE_OF_ASSET), signal_roles(rb.signals, ROLE_OF_ASSET),
                              *(w if w else (None, None)))
        spec_a = next(x for x in runs if x.run_id == a_id)
        orig_sek = usd_strategy_returns_in_sek(ra.returns, data[spec_a.sek_fx_for_comparison])
        common = orig_sek.dropna().index.intersection(rb.returns.dropna().index)
        m_a = compute_metrics(orig_sek.loc[common])
        m_b = compute_metrics(rb.returns.loc[common])
        ag.update({"status": "OK", "window": win, "original_in_sek": m_a, "sek_model": m_b,
                   "cagr_diff_sek_minus_original": m_b["cagr"] - m_a["cagr"],
                   "maxdd_diff_sek_minus_original": m_b["max_drawdown"] - m_a["max_drawdown"]})
        # programmatic check: same FX on both legs must not change US vs ex-US ranking
        from .analysis import ranking_invariance
        from .panel import build_panels as _bp
        pa, pb = _bp(spec_a, data, catalog), _bp(spec_b, data, catalog)
        ag["ranking_invariance"] = ranking_invariance(pa["momentum"]["US_EQUITIES"], pa["momentum"]["EX_US_EQUITIES"],
                                                      pb["momentum"]["SEK_US_EQ"], pb["momentum"]["SEK_EXUS_EQ"])
        agreement[f"{a_id} vs {b_id}"] = ag

    # ---- hurdle sensitivity: OMRX (verified) vs Riksbank SSVX proxy, same strategy ----
    from .analysis import hurdle_sensitivity
    hurdle = {}
    for a_id, b_id in (("GEM_SEK_OPEN_OMRX_V1", "GEM_SEK_OPEN_SSVXSYNTH_V1"),
                       ("REGIONAL_SEK_FF_PROXY_OMRX_V1", "REGIONAL_SEK_FF_PROXY_SSVXSYNTH_V1")):
        if a_id in ran and b_id in ran:
            pick_full = lambda rid: next(x for x in results if x.run_spec.run_id == rid and x.window == "FULL"
                                         and x.execution == IDEALIZED_CLOSE.name and x.cost_per_side_bps == 0)
            sa = pick_full(a_id).signals.set_index(pd.to_datetime(pick_full(a_id).signals["signal_date"]))["target"]
            sb = pick_full(b_id).signals.set_index(pd.to_datetime(pick_full(b_id).signals["signal_date"]))["target"]
            sa, sb = sa[sa != "NO_SIGNAL"], sb[sb != "NO_SIGNAL"]
            hurdle[f"{a_id} vs {b_id}"] = hurdle_sensitivity(sa, sb)
        else:
            hurdle[f"{a_id} vs {b_id}"] = {"status": "BLOCKED"}

    # ---- implementation gap (REGIONAL_SEK on Avanza funds) ----
    from .implementation import implementation_gap, rules_from_instruments
    impl = {"status": "BLOCKED", "reason": "daily index data for REGIONAL_SEK_FF_PROXY_OMRX_V1 unavailable"}
    reg = next(x for x in runs if x.run_id == "REGIONAL_SEK_FF_PROXY_OMRX_V1")
    if not any(k == reg.run_id for k in daily_blocked) and reg.run_id in ran:
        from .panel import build_daily_levels
        panels = build_panels(reg, data, catalog)
        sigs = generate_signals(reg.strategy, panels["momentum"], reg.roles, stale=panels["stale"])
        nav = {sid: s for sid, s in data.items() if sid.startswith("AVZ_NAV_")}
        fees = {it["name"]: it["ongoing_charge"] for it in instruments}
        impl = implementation_gap(reg.strategy, sigs, build_daily_levels(reg, data, catalog), nav,
                                  rules_from_instruments(instruments), fees, reg.roles,
                                  rf_monthly=panels["returns"]["SE_SHORT_RATE"])

    for r in results:
        r.provenance = provenance_block(r.run_spec, catalog, status, data)
        r.export(gen / "runs" / r.run_id)
    access = access_report(status, catalog, store.manifest)
    reporting.write_all(root, catalog, status, quality, xval, results, blocked, instruments)
    reporting.write_phase2(root, catalog, status, access, results, blocked, group_windows, daily_results,
                           daily_blocked, agreement, impl, runs, hurdle)
    log.info("runs completed: %d monthly result sets, %d daily result sets, %d blocked runs",
             len(results), len(daily_results), len(blocked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
