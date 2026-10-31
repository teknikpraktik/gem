"""Implementation gap: index-signal portfolio vs. the same signals executed in
real Avanza funds (NAV), over the period in which the funds exist.

Measures:
  * tracking difference per fund (annualised NAV return - index SEK return)
  * documented ongoing charge
  * signal deviation (signals computed from fund NAV momentum vs index momentum,
    only once a fund has 12 months of NAV history)
  * execution delay (business days signal period end -> execution NAV)
  * investable CAGR / max drawdown of the fund portfolio vs index portfolio
"""

from __future__ import annotations

from datetime import time

import pandas as pd

from .daily import SCENARIO_B, TradingRules, run_daily_backtest
from .metrics import compute_metrics
from .returns import to_month_end, trailing_return

# signal asset -> catalog id of the Avanza fund NAV that implements it
REGIONAL_FUND_MAP = {
    "SE_USA_EQ": "AVZ_NAV_USA",
    "SE_EUROPE_EQ": "AVZ_NAV_EUROPA",
    "SE_EM_EQ": "AVZ_NAV_EM",
    "SE_SHORT_RATE": "AVZ_NAV_RANTA_KORT",
}
FUND_NAME = {"AVZ_NAV_USA": "Avanza USA", "AVZ_NAV_EUROPA": "Avanza Europa", "AVZ_NAV_EM": "Avanza Emerging Markets",
             "AVZ_NAV_RANTA_KORT": "Avanza Ränta Kort", "AVZ_NAV_GLOBAL": "Avanza Global"}


def rules_from_instruments(instruments: list[dict]) -> dict[str, TradingRules]:
    out = {}
    for it in instruments:
        tr = it.get("trading_rules")
        if not tr:
            continue
        hh, mm = (int(x) for x in str(tr["cutoff"]).split(":"))
        out[it["name"]] = TradingRules(cutoff=time(hh, mm), nav_lag_bdays=int(tr.get("nav_lag_bdays", 0)),
                                       settlement_bdays=int(tr.get("settlement_bdays", 2)),
                                       source=str(tr.get("source", "")))
    return out


def tracking_difference(nav: pd.Series, index_level_sek: pd.Series) -> dict:
    a = to_month_end(nav)["value"]
    b = to_month_end(index_level_sek)["value"]
    x, y = a.align(b, join="inner")
    m = x.notna() & y.notna()
    x, y = x[m], y[m]
    if len(x) < 13:
        return {"months": int(len(x))}
    n = len(x) - 1
    ca = (x.iloc[-1] / x.iloc[0]) ** (12 / n) - 1
    cb = (y.iloc[-1] / y.iloc[0]) ** (12 / n) - 1
    ra, rb = x.pct_change().dropna(), y.pct_change().dropna()
    return {"period": f"{x.index[0].date()}..{x.index[-1].date()}", "months": n, "fund_cagr": float(ca),
            "index_cagr": float(cb), "tracking_difference": float(ca - cb),
            "tracking_error_ann": float((ra - rb).std(ddof=1) * 12 ** 0.5)}


def implementation_gap(strategy, index_signals, index_daily: pd.DataFrame, nav: dict[str, pd.Series],
                       fund_rules: dict[str, TradingRules], fees: dict[str, str], momentum_roles: dict,
                       rf_monthly=None) -> dict:
    fund_ids = {a: REGIONAL_FUND_MAP[a] for a in index_daily.columns if a in REGIONAL_FUND_MAP}
    if any(f not in nav for f in fund_ids.values()):
        return {"status": "BLOCKED", "missing_nav": sorted(f for f in fund_ids.values() if f not in nav)}
    start = max(nav[f].dropna().index.min() for f in fund_ids.values())
    nav_df = pd.DataFrame({a: nav[f] for a, f in fund_ids.items()})
    idx_df = index_daily[index_daily.index >= start]
    rules = {a: fund_rules.get(FUND_NAME[f], TradingRules()) for a, f in fund_ids.items()}
    res_idx = run_daily_backtest("idx", index_signals, idx_df, SCENARIO_B, rf_monthly=rf_monthly, start=start)
    res_fund = run_daily_backtest("fund", index_signals, nav_df[nav_df.index >= start], SCENARIO_B, rules,
                                  rf_monthly=rf_monthly, start=start)
    td = {FUND_NAME[f]: tracking_difference(nav[f], index_daily[a]) for a, f in fund_ids.items()}
    # signal deviation from fund-NAV momentum (needs 12 months of NAV)
    nav_m = pd.DataFrame({a: trailing_return(to_month_end(nav[f])["value"].dropna(), 12)
                          for a, f in fund_ids.items()})
    from .backtest import generate_signals
    nav_sigs = generate_signals(strategy, nav_m.dropna(how="all"), momentum_roles)
    i_t = {s.as_of_date: s.target for s in index_signals if s.is_valid}
    n_t = {s.as_of_date: s.target for s in nav_sigs if s.is_valid}
    common = sorted(set(i_t) & set(n_t))
    diff = [d for d in common if i_t[d] != n_t[d]]
    return {
        "status": "OK",
        "period_start": str(start.date()),
        "index_portfolio": res_idx.metrics,
        "fund_portfolio": res_fund.metrics,
        "investable_minus_index_cagr": res_fund.metrics.get("cagr", float("nan")) - res_idx.metrics.get("cagr", float("nan")),
        "tracking_difference": td,
        "ongoing_charges": fees,
        "signal_deviation": {"months_compared": len(common), "months_different": len(diff),
                             "different_dates": [str(d) for d in diff]},
        "execution_delay_bdays_fund": res_fund.metrics.get("avg_bdays_signal_to_execution"),
        "execution_delay_bdays_index": res_idx.metrics.get("avg_bdays_signal_to_execution"),
    }


# =====================================================================================
# Investable implementation model: REGIONAL_SEK on real Avanza fund NAVs
# (kept strictly separate from the research index model)
# =====================================================================================

INSTRUMENT_OF_INDEX_ASSET = {"SE_USA_EQ": "AVANZA_USA", "SE_EUROPE_EQ": "AVANZA_EUROPA", "SE_EM_EQ": "AVANZA_EM",
                             "SE_SHORT_RATE": "AVANZA_RANTA_KORT"}
NAV_SERIES_OF_INSTRUMENT = {"AVANZA_USA": "AVZ_NAV_USA", "AVANZA_EUROPA": "AVZ_NAV_EUROPA",
                            "AVANZA_EM": "AVZ_NAV_EM", "AVANZA_RANTA_KORT": "AVZ_NAV_RANTA_KORT"}


def nav_signals(navs: dict, ssvx_yield: pd.Series, month_ends) -> list:
    """Monthly REGIONAL_SEK signals computed with the LIVE function (identical logic)."""
    from .live import regional_live_signal
    from .strategies import NO_SIGNAL, Signal

    out = []
    for m in month_ends:
        as_of = (pd.Timestamp(m) + pd.offsets.Day(1)).date()
        live = regional_live_signal(as_of, navs, ssvx_yield)
        tgt = live["target"] if live["status"] == "VALID" else NO_SIGNAL
        w = {tgt: 1.0} if tgt != NO_SIGNAL else {}
        out.append(Signal("REGIONAL_SEK", "1.0.0", pd.Timestamp(m).date(), tgt, w, live["reason"],
                          {k: v for k, v in live["returns"].items()}))
    return out


def regional_nav_implementation(navs: dict, ssvx_yield: pd.Series, rules: dict, fees: dict,
                                index_signals: list, index_monthly: dict, index_region_returns: pd.DataFrame,
                                cash_daily: pd.Series, benchmark_navs: dict | None = None) -> dict:
    """navs: instrument_id -> daily NAV (SEK). index_signals: REGIONAL index-model signals
    (asset keys SE_*). index_monthly: {label: monthly return series of the index model}.
    index_region_returns: monthly SEK returns of the index legs (SE_USA_EQ, ...)."""
    from .daily import SCENARIOS, run_daily_backtest
    from .metrics import compute_metrics

    month_ends = pd.date_range("2020-01-31", max(s.index.max() for s in navs.values()), freq="ME")
    sigs = nav_signals(navs, ssvx_yield, month_ends)
    valid = [s for s in sigs if s.is_valid]
    first_valid = valid[0].as_of_date if valid else None
    rk_start = navs["AVANZA_RANTA_KORT"].index.min()
    out = {"first_valid_nav_signal": str(first_valid), "ranta_kort_first_nav": str(rk_start.date()),
           "signals": [{"signal_period_end": str(s.as_of_date), "target": s.target, "reason": s.reason,
                        "returns": s.inputs} for s in sigs]}

    variants = {
        # all four legs are real Avanza funds
        "PURE_AVANZA_FUNDS": (pd.DataFrame(navs), rk_start, sigs),
        # equity funds real; defensive = Riksbank synthetic cash (Ränta Kort did not exist before 2023-12)
        "HYBRID_SYNTH_CASH": (pd.DataFrame({**{k: v for k, v in navs.items() if k != "AVANZA_RANTA_KORT"},
                                            "AVANZA_RANTA_KORT": cash_daily}),
                              pd.Timestamp(first_valid) if first_valid else rk_start, sigs),
    }
    out["variants"] = {}
    for name, (lv, start, s) in variants.items():
        lv = lv[lv.index >= start - pd.Timedelta(days=40)]
        res = {}
        for sc in SCENARIOS:
            r = run_daily_backtest(f"REGIONAL_SEK_NAV_IMPL__{name}__{sc.name}", s, lv, sc,
                                   rules if sc.name != "A_PUBLISHED_CLOSE" else None, start=start)
            res[sc.name] = {"label": sc.label, "metrics": r.metrics, "_result": r}
        out["variants"][name] = {"start": str(pd.Timestamp(start).date()), "scenarios": res}

    # ---- same-window index model ----
    pure_b = out["variants"]["PURE_AVANZA_FUNDS"]["scenarios"]["B_NEXT_TRADABLE"]["_result"]
    hyb_b = out["variants"]["HYBRID_SYNTH_CASH"]["scenarios"]["B_NEXT_TRADABLE"]["_result"]
    out["index_same_window"] = {}
    for vname, rr in (("PURE_AVANZA_FUNDS", pure_b), ("HYBRID_SYNTH_CASH", hyb_b)):
        months = rr.monthly_returns.index
        out["index_same_window"][vname] = {
            lab: compute_metrics(ser.reindex(months).dropna()) for lab, ser in index_monthly.items()}

    # ---- signal agreement index model vs NAV model ----
    i_t = {s.as_of_date: INSTRUMENT_OF_INDEX_ASSET.get(s.target, s.target) for s in index_signals if s.is_valid}
    n_t = {s.as_of_date: s.target for s in sigs if s.is_valid}
    common = sorted(set(i_t) & set(n_t))
    diff = [d for d in common if i_t[d] != n_t[d]]
    region_diff = [d for d in diff if i_t[d] != "AVANZA_RANTA_KORT" and n_t[d] != "AVANZA_RANTA_KORT"]
    out["signal_agreement"] = {
        "months": len(common), "identical": len(common) - len(diff), "different": len(diff),
        "agreement_pct": (1 - len(diff) / len(common)) if common else None,
        "different_region_both_risk_on": len(region_diff),
        "different_risk_on_off": len(diff) - len(region_diff),
        "index_switches": int(sum(1 for a, b in zip(common, common[1:]) if i_t[a] != i_t[b])),
        "nav_switches": int(sum(1 for a, b in zip(common, common[1:]) if n_t[a] != n_t[b])),
        "differences": [{"date": str(d), "index": i_t[d], "nav": n_t[d]} for d in diff],
    }

    # ---- tracking difference: fund NAV vs index leg (monthly, SEK) ----
    td = {}
    for asset, iid in INSTRUMENT_OF_INDEX_ASSET.items():
        if iid == "AVANZA_RANTA_KORT" or asset not in index_region_returns:
            continue
        me = to_month_end(navs[iid])["value"]
        fr = me.pct_change()
        ir = index_region_returns[asset]
        x, y = fr.align(ir, join="inner")
        m = x.notna() & y.notna()
        x, y = x[m], y[m]
        if len(x) >= 12:
            n = len(x)
            td[iid] = {"period": f"{x.index[0].date()}..{x.index[-1].date()}", "months": n,
                       "fund_cagr": float((1 + x).prod() ** (12 / n) - 1),
                       "index_cagr": float((1 + y).prod() ** (12 / n) - 1),
                       "tracking_difference": float((1 + x).prod() ** (12 / n) - (1 + y).prod() ** (12 / n)),
                       "tracking_error_ann": float((x - y).std(ddof=1) * 12 ** 0.5),
                       "correlation": float(x.corr(y))}
    out["tracking_difference_vs_index_legs"] = td

    # ---- benchmarks on REAL Avanza fund NAVs over exactly the months of each variant ----
    me = {k: to_month_end(v)["value"] for k, v in {**navs, **(benchmark_navs or {})}.items()}
    mr = pd.DataFrame({k: v.pct_change() for k, v in me.items()})
    bench = {}
    if "AVANZA_GLOBAL" in mr:
        bench["BUY_HOLD_AVANZA_GLOBAL"] = mr["AVANZA_GLOBAL"]
        bench["STATIC_70_30_AVANZA_GLOBAL_RANTA_KORT"] = 0.7 * mr["AVANZA_GLOBAL"] + 0.3 * mr["AVANZA_RANTA_KORT"]
    bench["STATIC_REGIONAL_EQUAL_AVANZA"] = mr[["AVANZA_USA", "AVANZA_EUROPA", "AVANZA_EM"]].mean(axis=1, skipna=False)
    out["nav_benchmarks_same_window"] = {}
    for vname, rr in (("PURE_AVANZA_FUNDS", pure_b), ("HYBRID_SYNTH_CASH", hyb_b)):
        months = rr.monthly_returns.index
        out["nav_benchmarks_same_window"][vname] = {
            k: (compute_metrics(v.reindex(months)) if v.reindex(months).notna().all() else
                {"status": "incomplete window",
                 "missing_months": [str(d.date()) for d in months[v.reindex(months).isna()]][:24],
                 "missing_by_fund": {c: [str(d.date()) for d in months[mr[c].reindex(months).isna()]][:12]
                                     for c in mr.columns}})
            for k, v in bench.items()}
    out["fees"] = fees
    return out
