"""End-to-end plumbing test of the phase-2 pipeline on SYNTHETIC data.

Purpose: prove that every Swedish code path (groups/common windows, level-based
SEK conversion, daily A/B/C scenarios, signal agreement, implementation gap)
runs once real data is present. Synthetic numbers are written to a temporary
directory only and are never reported as results.
"""

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import gem.research as research
from gem.catalog import load_catalog

ROOT = Path(__file__).resolve().parents[1]


def synthetic(entry, rng, end="2026-09-30"):
    freq = entry["frequency"]
    start = pd.Timestamp("1992-01-01")
    launch = entry.get("fetch", {}).get("launch_date")
    if launch:
        start = max(start, pd.Timestamp(str(launch)) + pd.offsets.Day(10))
    daily = "daily" in freq
    idx = pd.bdate_range(start, end) if daily else pd.date_range(start, end, freq="ME")
    n = len(idx)
    ac = entry["asset_class"]
    if ac in ("money_market_yield", "bond_yield"):
        v = np.clip(4 + np.cumsum(rng.normal(0, 0.02 if daily else 0.1, n)), 0.1, 12)
    elif ac == "fx":
        v = np.clip(8 * np.exp(np.cumsum(rng.normal(0, 0.005 if daily else 0.02, n))), 4, 14)
    else:
        mu, sd = (0.0003, 0.01) if daily else (0.007, 0.045)
        if ac.startswith("money_market") or ac == "bond":
            mu, sd = (0.0001, 0.0002) if daily else (0.003, 0.002)
        v = 100 * np.exp(np.cumsum(rng.normal(mu, sd, n)))
    return pd.Series(v, index=idx, name=entry["id"])


def test_phase2_pipeline_runs_end_to_end_on_synthetic_data(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    for f in ("catalog.yaml", "investable_instruments.yaml"):
        shutil.copy(ROOT / "data" / f, tmp_path / "data" / f)
    cat = load_catalog(tmp_path / "data" / "catalog.yaml")
    rng = np.random.default_rng(42)

    def fake_load_all(catalog, ids, store, refresh, offline, manual_dir):
        data = {sid: synthetic(catalog[sid], rng) for sid in sorted(ids)}
        status = {sid: {"status": "OK", "fetch": "SYNTHETIC", "sha256": "0" * 64, "url": "synthetic://",
                        "retrieved_at": "test"} for sid in ids}
        return data, status

    monkeypatch.setattr(research, "load_all", fake_load_all)
    monkeypatch.setattr(research, "cross_validation", lambda data: [])
    assert research.main(["--root", str(tmp_path), "--offline"]) == 0
    p2 = json.loads((tmp_path / "reports" / "generated" / "phase2.json").read_text())
    # all groups got a common window
    assert all(g["common_window"] for g in p2["group_windows"].values())
    # agreement computed for every pair
    assert all(v["status"] == "OK" for v in p2["agreement"].values())
    for v in p2["agreement"].values():
        assert v["identical"] + v["different"] == v["months"]
    # same FX on both legs -> ranking never changes (mathematical invariant)
    for v in p2["agreement"].values():
        assert v["ranking_invariance"]["ranking_mismatches"] == 0
        assert v["differences_absolute_momentum"] + v["differences_relative_momentum"] == v["different"]
    assert all("signals_changed" in v for v in p2["hurdle_sensitivity"].values())
    # provenance on every result, synthetic data flagged as such
    res = json.loads(next((tmp_path / "reports" / "generated" / "runs").glob("GEM_SEK_OPEN_OMRX_V1__FULL*/result.json")).read_text())
    assert res["provenance"]["weakest_class"] == "SYNTHETIC_TEST_ONLY"
    # daily scenarios A/B/C for both daily-enabled runs
    sc = {(d["run"], d["scenario"]) for d in p2["daily_results"]}
    for run in ("GEM_SEK_OPEN_OMRX_V1", "REGIONAL_SEK_FF_PROXY_OMRX_V1"):
        for s in ("A_PUBLISHED_CLOSE", "B_NEXT_TRADABLE", "C_CONSERVATIVE"):
            assert (run, s) in sc
    a = [d for d in p2["daily_results"] if d["label"] == "LOOKAHEAD_REFERENCE_ONLY"]
    assert a and all(d["scenario"] == "A_PUBLISHED_CLOSE" for d in a)
    # investable implementation model (Avanza NAV) runs and is separate from the index model
    nb = p2_res = json.loads((tmp_path / "reports" / "generated" / "phase2_results.json").read_text())["nav_implementation"]
    assert nb["status"] == "OK", nb
    assert set(nb["variants"]) == {"PURE_AVANZA_FUNDS", "HYBRID_SYNTH_CASH"}
    for v in nb["variants"].values():
        assert set(v["scenarios"]) == {"A_PUBLISHED_CLOSE", "B_NEXT_TRADABLE", "C_CONSERVATIVE"}
    assert nb["live_signal"]["strategy"] == "REGIONAL_SEK"
    assert (tmp_path / "reports" / "generated" / "live_signal.json").exists()
    assert nb["signal_agreement"]["months"] > 0
    # implementation gap computed
    assert p2["implementation_gap"]["status"] == "OK"
    # B executes later than A, C later than B
    m = {(d["run"], d["scenario"]): d["metrics"]["avg_bdays_signal_to_execution"] for d in p2["daily_results"]
         if d["cost"] == 0}
    r = "REGIONAL_SEK_FF_PROXY_OMRX_V1"
    assert m[(r, "A_PUBLISHED_CLOSE")] < m[(r, "B_NEXT_TRADABLE")] < m[(r, "C_CONSERVATIVE")]
