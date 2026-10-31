"""Export research results as static JSON for the web app (web/data/).

    python research/scripts/export_app_data.py

Reads ONLY committed, generated research outputs (research/reports/generated/)
and writes:
  web/data/history.json          REGIONAL_SEK NAV-model signal history (research backfill, same rule)
  web/data/backtest.json         investable implementation + long research model + benchmarks
  web/data/research.json         GEM_SEK / GEM_ORIGINAL research results, OMRX validation
  web/data/bootstrap_signal.json latest signal computed by the research pipeline (used until the
                                 live cron has produced its first snapshot; always labelled as such)
No numbers are computed here except reformatting; the source file and run are recorded.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "research" / "reports" / "generated"
OUT = ROOT / "web" / "data"


def git_rev() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "log", "-1", "--format=%h", "--", str(GEN)], text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def rd(p: Path):
    return json.loads(p.read_text())


def summary_rows():
    with (GEN / "summary.csv").open() as fh:
        return list(csv.DictReader(fh))


def num(x):
    try:
        v = float(x)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def metric_block(m: dict) -> dict:
    keys = ["start_date", "end_date", "months", "cagr", "volatility", "max_drawdown", "sharpe", "sortino", "calmar",
            "number_of_switches", "number_of_trades", "longest_drawdown_months", "best_year", "best_year_return",
            "worst_year", "worst_year_return", "avg_bdays_signal_to_execution"]
    return {k: (num(m.get(k)) if k not in ("start_date", "end_date") else m.get(k)) for k in keys if k in m}


def monthly_csv(path: Path, col: str):
    if not path.exists():
        return []
    with path.open() as fh:
        return [[r[next(iter(r))], num(r[col])] for r in csv.DictReader(fh)]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {"exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "research_commit": git_rev(),
            "source": "research/reports/generated (GitHub Actions workflow 'GEM phase 2 research')"}
    nb = rd(GEN / "nav_implementation.json")
    p2 = rd(GEN / "phase2_results.json")
    rows = summary_rows()

    # ---------------- history (NAV model, same rule as live) ----------------
    hist = []
    prev = None
    for s in nb["signals"]:
        if s["signal_period_end"] < nb["first_valid_nav_signal"]:
            continue
        tgt = s["target"] if s["target"] != "NO_SIGNAL" else None
        hist.append({"signalPeriod": s["signal_period_end"], "status": "VALID" if tgt else "NO_SIGNAL",
                     "selectedFund": tgt, "previousFund": prev, "switched": bool(tgt and prev and tgt != prev),
                     "returns": s["returns"], "reason": s["reason"], "origin": "research_pipeline"})
        if tgt:
            prev = tgt
    (OUT / "history.json").write_text(json.dumps({**meta, "note": "Signals recomputed by the research pipeline on real "
        "Avanza NAVs with the same rule as the live engine (gem.live). Live cron snapshots take precedence.",
        "signals": hist}, indent=1))

    # ---------------- backtest ----------------
    variants = {}
    for vn, v in nb["variants"].items():
        variants[vn] = {"start": v["start"], "scenarios": {sc: {"label": r["label"], "metrics": metric_block(r["metrics"])}
                                                          for sc, r in v["scenarios"].items()}}
    curve = monthly_csv(GEN / "runs_daily" / "REGIONAL_SEK_NAV_IMPL__HYBRID_SYNTH_CASH__B_NEXT_TRADABLE" / "monthly.csv", "return")
    common = [r for r in rows if r["window"] == "COMMON_SE_FF_SSVX" and float(r["cost_per_side_bps"]) == 0]

    def pick(run, ex):
        r = next((x for x in common if x["run"] == run and x["execution"] == ex), None)
        return metric_block(r) if r else None

    research_long = {
        "window": "COMMON_SE_FF_SSVX",
        "description": "Research index model: Ken French USA/Europe/EM in SEK (Riksbank FX), Riksbank synthetic cash. Monthly data.",
        "REGIONAL_SEK_LOOKAHEAD_REFERENCE": pick("REGIONAL_SEK_FF_PROXY_SSVXSYNTH_V1", "IDEALIZED_CLOSE"),
        "REGIONAL_SEK_ONE_MONTH_DELAY": pick("REGIONAL_SEK_FF_PROXY_SSVXSYNTH_V1", "NEXT_MONTH_CLOSE"),
        "BUY_HOLD_GLOBAL": pick("BUY_HOLD_GLOBAL_SEK_FF_DEV_PROXY_V1__SE_FF_SSVX", "NEXT_MONTH_CLOSE"),
        "STATIC_70_30": pick("STATIC_70_30_SEK_FF_DEV_PROXY_V1__SE_FF_SSVX", "NEXT_MONTH_CLOSE"),
        "STATIC_REGIONAL_EQUAL": pick("STATIC_REGIONAL_EQUAL_SEK_FF_V1__SE_FF_SSVX", "NEXT_MONTH_CLOSE"),
    }
    bench = {vn: {k: (metric_block(m) if "status" not in m else {"status": m["status"]}) for k, m in d.items()}
             for vn, d in nb["nav_benchmarks_same_window"].items()}
    idx_same = {vn: {k: metric_block(m) for k, m in d.items()} for vn, d in nb["index_same_window"].items()}
    (OUT / "backtest.json").write_text(json.dumps({**meta,
        "investable": {"description": "REGIONAL_SEK on real Avanza fund NAVs: signal from the live function, execution on "
                       "NAV with each fund's cut-off/NAV/settlement rules. Sharpe uses rf = 0.",
                       "variants": variants, "benchmarks_same_window": bench, "index_same_window": idx_same,
                       "equity_curve_hybrid_b_monthly_returns": curve,
                       "benchmark_monthly_returns": nb.get("nav_benchmark_monthly", {}),
                       "signal_agreement_index_vs_nav": {k: v for k, v in nb["signal_agreement"].items() if k != "differences"},
                       "tracking_difference": nb["tracking_difference_vs_index_legs"]},
        "research_long": research_long}, indent=1))

    # ---------------- research (GEM_SEK, GEM_ORIGINAL, OMRX) ----------------
    gem = {"GEM_SEK_LOOKAHEAD_REFERENCE": pick("GEM_SEK_FF_PROXY_SSVXSYNTH_V1", "IDEALIZED_CLOSE"),
           "GEM_SEK_ONE_MONTH_DELAY": pick("GEM_SEK_FF_PROXY_SSVXSYNTH_V1", "NEXT_MONTH_CLOSE"),
           "GEM_ORIGINAL_FF_ONE_MONTH_DELAY": pick("GEM_ORIGINAL_FF_V1__SE_FF_SSVX", "NEXT_MONTH_CLOSE")}
    daily = {f"{d['run']}/{d['scenario']}": metric_block(d["metrics"]) for d in p2["daily_results"] if d["cost"] == 0}
    ag = p2["agreement"].get("GEM_ORIGINAL_FF_V1__SE_FF_SSVX vs GEM_SEK_FF_PROXY_SSVXSYNTH_V1", {})
    hs = p2.get("hurdle_sensitivity", {})
    repro = [r for r in rows if r["run"] == "GEM_ORIGINAL_PROXY_3P" and r["window"] == "REF_1974_2013" and float(r["cost_per_side_bps"]) == 0]
    (OUT / "research.json").write_text(json.dumps({**meta,
        "gem_sek": {"window": "1994-03..2026-09 (COMMON_SE_FF_SSVX)", "monthly": gem,
                    "daily_b": daily.get("GEM_SEK_FF_PROXY_SSVXSYNTH_V1/B_NEXT_TRADABLE"),
                    "daily_a": daily.get("GEM_SEK_FF_PROXY_SSVXSYNTH_V1/A_PUBLISHED_CLOSE"),
                    "daily_c": daily.get("GEM_SEK_FF_PROXY_SSVXSYNTH_V1/C_CONSERVATIVE"),
                    "agreement_vs_original": {k: ag.get(k) for k in ("months", "identical", "different", "agreement_pct",
                        "differences_absolute_momentum", "differences_relative_momentum", "top_years")},
                    "ranking_invariance": ag.get("ranking_invariance")},
        "omrx_validation": {"series": p2.get("omrx_validation"),
                            "hurdle_sensitivity": {k: {kk: v.get(kk) for kk in ("window", "months", "signals_changed",
                                "signal_agreement_pct", "NEXT_MONTH_CLOSE")} for k, v in hs.items() if isinstance(v, dict) and "months" in v},
                            "omrx_daily_b": daily.get("GEM_SEK_FF_OMRX_VERIFIED_V1/B_NEXT_TRADABLE"),
                            "proxy_daily_b": daily.get("GEM_SEK_FF_PROXY_SSVXSYNTH_V1__OMRX_WINDOW/B_NEXT_TRADABLE")},
        "gem_original_reproduction": {"reference": {"source": "Antonacci (2014), 1974-2013, via secondary sources", "cagr": 0.1743,
                                                    "volatility": 0.1264, "max_drawdown": -0.2272, "sharpe": 0.87},
                                      "ours": [dict(metric_block(r), execution=r["execution"]) for r in repro],
                                      "data_note": "third-party compilation (alexjansenhome/GEM), ends 2016 - research only"}},
        indent=1))

    # ---------------- bootstrap signal ----------------
    ls = rd(GEN / "live_signal.json")
    (OUT / "bootstrap_signal.json").write_text(json.dumps({**meta, "signal": ls}, indent=1))
    print("wrote", sorted(p.name for p in OUT.glob("*.json")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
