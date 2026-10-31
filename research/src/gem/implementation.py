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
