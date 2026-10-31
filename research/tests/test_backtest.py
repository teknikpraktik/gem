import numpy as np
import pandas as pd
import pytest

from gem.backtest import generate_signals, run_backtest
from gem.execution import IDEALIZED_CLOSE, NEXT_MONTH_CLOSE
from gem.metrics import compute_metrics
from gem.returns import trailing_return
from gem.strategies import FixedWeightStrategy, GemStrategy

IDX = pd.date_range("2000-01-31", periods=48, freq="ME")


def _panel(seed=0):
    rng = np.random.default_rng(seed)
    rets = pd.DataFrame({
        "US_EQUITIES": rng.normal(0.008, 0.04, len(IDX)),
        "EX_US_EQUITIES": rng.normal(0.006, 0.05, len(IDX)),
        "US_AGG_BONDS": rng.normal(0.004, 0.01, len(IDX)),
        "TBILL": np.full(len(IDX), 0.002),
    }, index=IDX)
    levels = 100 * (1 + rets).cumprod()
    mom = pd.DataFrame({c: trailing_return(levels[c], 12) for c in levels})
    return rets, mom


ROLES = {"us": "US_EQUITIES", "exus": "EX_US_EQUITIES", "hurdle": "TBILL"}


def test_first_signal_needs_12_months():
    rets, mom = _panel()
    sigs = generate_signals(GemStrategy(), mom, ROLES)
    valid = [s for s in sigs if s.is_valid]
    assert valid[0].as_of_date == IDX[12].date()


def test_execution_lag_shifts_position_by_one_month():
    rets, mom = _panel()
    g = GemStrategy()
    sigs = generate_signals(g, mom, ROLES)
    a = run_backtest("a", g, sigs, rets, IDEALIZED_CLOSE)
    b = run_backtest("b", g, sigs, rets, NEXT_MONTH_CLOSE)
    assert a.monthly.index[0] == IDX[13]
    assert b.monthly.index[0] == IDX[14]
    # position in month M under lag-1 equals lag-0 position of month M-1
    common = b.monthly.index[1:]
    for m in common:
        prev = m - pd.offsets.MonthEnd(1)
        assert b.monthly.at[m, "signal_date"] == a.monthly.at[prev, "signal_date"]


def test_no_lookahead_future_data_does_not_change_past():
    rets, mom = _panel()
    g = GemStrategy()
    base = run_backtest("x", g, generate_signals(g, mom, ROLES), rets, NEXT_MONTH_CLOSE)
    rets2 = rets.copy()
    cut = IDX[30]
    rets2.loc[rets2.index > cut] *= -5  # violently change the future
    levels2 = 100 * (1 + rets2).cumprod()
    mom2 = pd.DataFrame({c: trailing_return(levels2[c], 12) for c in levels2})
    alt = run_backtest("y", g, generate_signals(g, mom2, ROLES), rets2, NEXT_MONTH_CLOSE)
    past = base.monthly.index[base.monthly.index <= cut]
    pd.testing.assert_series_equal(base.monthly.loc[past, "target"], alt.monthly.loc[past, "target"])
    pd.testing.assert_series_equal(base.monthly.loc[past, "net_return"], alt.monthly.loc[past, "net_return"])


def test_portfolio_return_equals_held_asset_return():
    rets, mom = _panel()
    g = GemStrategy()
    r = run_backtest("x", g, generate_signals(g, mom, ROLES), rets, IDEALIZED_CLOSE)
    for m, row in r.monthly.iterrows():
        assert row["net_return"] == pytest.approx(rets.at[m, row["target"]])


def test_no_signal_keeps_position_and_is_logged():
    rets, mom = _panel()
    mom.loc[IDX[20], "EX_US_EQUITIES"] = np.nan
    g = GemStrategy()
    r = run_backtest("x", g, generate_signals(g, mom, ROLES), rets, IDEALIZED_CLOSE)
    assert r.metrics["no_signal_count"] >= 1
    m = IDX[21]  # month that would have used the IDX[20] signal
    assert r.monthly.at[m, "signal_date"] == IDX[19].date()


def test_missing_return_stops_backtest():
    rets, mom = _panel()
    rets.loc[IDX[30]:, :] = np.nan
    g = GemStrategy()
    r = run_backtest("x", g, generate_signals(g, mom, ROLES), rets, IDEALIZED_CLOSE)
    assert r.monthly.index[-1] == IDX[29] and r.stop_reason


def test_costs_reduce_return_on_switch_only():
    rets, mom = _panel()
    g = GemStrategy()
    sigs = generate_signals(g, mom, ROLES)
    a = run_backtest("a", g, sigs, rets, IDEALIZED_CLOSE)
    b = run_backtest("b", g, sigs, rets, IDEALIZED_CLOSE, cost_per_side_bps=10)
    sw = a.monthly["target"] != a.monthly["target"].shift(1)
    sw.iloc[0] = False
    assert (b.monthly.loc[~sw, "net_return"] == a.monthly.loc[~sw, "net_return"]).all()
    if sw.any():
        m = sw[sw].index[0]
        assert b.monthly.at[m, "cost"] == pytest.approx(2 * 10 / 1e4)


def test_static_mix_rebalances_monthly():
    rets, _ = _panel()
    s = FixedWeightStrategy("STATIC_70_30", {"US_EQUITIES": 0.7, "US_AGG_BONDS": 0.3})
    avail = pd.DataFrame(1.0, index=IDX, columns=["US_EQUITIES", "US_AGG_BONDS"])
    r = run_backtest("s", s, generate_signals(s, avail, {"US_EQUITIES": "US_EQUITIES", "US_AGG_BONDS": "US_AGG_BONDS"}),
                     rets, IDEALIZED_CLOSE)
    exp = 0.7 * rets["US_EQUITIES"] + 0.3 * rets["US_AGG_BONDS"]
    assert r.monthly["gross_return"].values == pytest.approx(exp.loc[r.monthly.index].values)


def test_metrics_known_values():
    r = pd.Series([0.1, -0.5, 0.2], index=IDX[:3])
    m = compute_metrics(r)
    assert m["end_value"] == pytest.approx(10_000 * 1.1 * 0.5 * 1.2)
    assert m["max_drawdown"] == pytest.approx(-0.5)
    assert m["cagr"] == pytest.approx((1.1 * 0.5 * 1.2) ** 4 - 1)
    assert m["longest_drawdown_months"] == 2


def test_backtest_is_deterministic():
    rets, mom = _panel()
    g = GemStrategy()
    a = run_backtest("a", g, generate_signals(g, mom, ROLES), rets, NEXT_MONTH_CLOSE)
    b = run_backtest("a", g, generate_signals(g, mom, ROLES), rets, NEXT_MONTH_CLOSE)
    pd.testing.assert_frame_equal(a.monthly, b.monthly)
    assert a.metrics == b.metrics


def test_stale_flag_in_panel_gives_no_signal():
    rets, mom = _panel()
    stale = pd.DataFrame(False, index=mom.index, columns=mom.columns)
    stale.loc[IDX[25], "TBILL"] = True
    sigs = generate_signals(GemStrategy(), mom, ROLES, stale=stale)
    s = [x for x in sigs if x.as_of_date == IDX[25].date()][0]
    assert s.target == "NO_SIGNAL" and "stale" in s.reason
