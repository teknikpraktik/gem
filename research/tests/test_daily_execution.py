from datetime import date, datetime, time

import numpy as np
import pandas as pd
import pytest

from gem.daily import (
    SCENARIO_A, SCENARIO_B, SCENARIO_C, Calendar, TradingRules, nav_date_for_order, run_daily_backtest,
    schedule_switch,
)
from gem.strategies import Signal

DAYS = pd.bdate_range("2024-01-01", "2024-06-28")
CAL = Calendar(DAYS)
IDX_RULES = TradingRules()


def sig(d, target):
    return Signal("T", "1", pd.Timestamp(d).date(), target, {target: 1.0}, "", {})


def test_published_close_executes_on_last_trading_day_of_month():
    s = schedule_switch(CAL, "2024-03-31", SCENARIO_A, IDX_RULES, IDX_RULES)  # Sunday
    assert s["execution_date"] == pd.Timestamp("2024-03-29")
    assert SCENARIO_A.label == "LOOKAHEAD_REFERENCE_ONLY" and not SCENARIO_A.lookahead_free


def test_next_tradable_executes_first_business_day_after_period_end():
    s = schedule_switch(CAL, "2024-03-31", SCENARIO_B, IDX_RULES, IDX_RULES)
    assert s["data_available_at"] == datetime(2024, 4, 1, 8, 0)
    assert s["order_submitted_at"] == datetime(2024, 4, 1, 9, 0)
    assert s["sell_nav_date"] == s["buy_nav_date"] == pd.Timestamp("2024-04-01")
    assert s["data_available_at"] > datetime(2024, 3, 29, 17, 30)  # after the signal closes


def test_conservative_adds_a_day_and_waits_for_settlement():
    s = schedule_switch(CAL, "2024-03-31", SCENARIO_C, IDX_RULES, IDX_RULES)
    assert s["sell_nav_date"] == pd.Timestamp("2024-04-02")
    assert s["buy_nav_date"] == pd.Timestamp("2024-04-04")  # T+2 settlement


def test_fund_with_next_day_nav_and_early_cutoff():
    em = TradingRules(cutoff=time(12, 0), nav_lag_bdays=1)
    assert nav_date_for_order(CAL, datetime(2024, 4, 1, 9, 0), em) == pd.Timestamp("2024-04-02")
    assert nav_date_for_order(CAL, datetime(2024, 4, 1, 13, 0), em) == pd.Timestamp("2024-04-03")
    s = schedule_switch(CAL, "2024-03-31", SCENARIO_B, IDX_RULES, em)
    assert s["buy_nav_date"] == pd.Timestamp("2024-04-02")


def _levels():
    n = len(DAYS)
    a = 100 * np.cumprod(np.full(n, 1.001))
    b = 100 * np.cumprod(np.full(n, 0.999))
    return pd.DataFrame({"A": a, "B": b}, index=DAYS)


def test_daily_backtest_values_and_timing():
    lv = _levels()
    sigs = [sig("2024-01-31", "A"), sig("2024-02-29", "B"), sig("2024-03-31", "B")]
    res = run_daily_backtest("x", sigs, lv, SCENARIO_B)
    tr = res.trades
    assert list(tr["to"]) == ["A", "B"]
    assert tr.iloc[1]["sell_nav_date"] == pd.Timestamp("2024-03-01")
    # value: bought A at close 2024-02-01, sold at close 2024-03-01, then B
    d0, d1 = pd.Timestamp("2024-02-01"), pd.Timestamp("2024-03-01")
    expected = 10_000 * lv.at[d1, "A"] / lv.at[d0, "A"] * lv["B"].iloc[-1] / lv.at[d1, "B"]
    assert res.daily["value"].iloc[-1] == pytest.approx(expected)


def test_scenario_c_is_out_of_market_between_sell_and_buy():
    lv = _levels()
    sigs = [sig("2024-01-31", "A"), sig("2024-02-29", "B")]
    res = run_daily_backtest("x", sigs, lv, SCENARIO_C)
    d = res.daily
    assert (d.loc["2024-03-04":"2024-03-05", "position"] == "CASH").all()
    assert res.metrics["avg_bdays_out_of_market_per_switch"] == 2


def test_no_lookahead_future_prices_do_not_change_past_values():
    lv = _levels()
    sigs = [sig("2024-01-31", "A"), sig("2024-02-29", "B")]
    base = run_daily_backtest("x", sigs, lv, SCENARIO_B).daily["value"]
    lv2 = lv.copy()
    lv2.loc["2024-04-15":] *= 3
    alt = run_daily_backtest("x", sigs, lv2, SCENARIO_B).daily["value"]
    pd.testing.assert_series_equal(base[:"2024-04-12"], alt[:"2024-04-12"])


def test_cost_charged_per_side():
    lv = _levels()
    sigs = [sig("2024-01-31", "A"), sig("2024-02-29", "B")]
    a = run_daily_backtest("x", sigs, lv, SCENARIO_B).daily["value"].iloc[-1]
    b = run_daily_backtest("x", sigs, lv, SCENARIO_B, cost_per_side_bps=10).daily["value"].iloc[-1]
    assert b == pytest.approx(a * (1 - 0.001) ** 2)
