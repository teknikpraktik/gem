from datetime import date, datetime, time

import numpy as np
import pandas as pd
import pytest

from gem.execution import (
    IDEALIZED_CLOSE, NEXT_MONTH_CLOSE, FundOrderModel, assert_not_before_launch, truncate_to_launch,
)
from gem.fx import check_sek_per_usd, convert_index_usd_to_sek, convert_return_usd_to_sek, invert_quote
from gem.returns import (
    index_from_returns, par_bond_monthly_return, simple_returns, to_month_end, trailing_return,
    yield_to_monthly_return,
)


# ---------- month-end resampling ----------

def test_month_end_takes_last_valid_observation():
    idx = pd.to_datetime(["2020-01-02", "2020-01-30", "2020-01-31", "2020-02-27", "2020-02-28"])
    s = pd.Series([1.0, 2.0, np.nan, 3.0, 4.0], idx)
    me = to_month_end(s)
    assert list(me.index) == [pd.Timestamp("2020-01-31"), pd.Timestamp("2020-02-29")]
    assert me["value"].tolist() == [2.0, 4.0]
    assert me["obs_date"].iloc[0] == pd.Timestamp("2020-01-30")
    assert not me["stale"].any()


def test_month_end_flags_stale_and_does_not_fill():
    idx = pd.to_datetime(["2020-01-31", "2020-02-10", "2020-03-31"])
    me = to_month_end(pd.Series([1.0, 2.0, 3.0], idx))
    feb = me.loc["2020-02-29"]
    assert bool(feb["stale"]) and np.isnan(feb["value"])


def test_month_end_keeps_gap_months_visible():
    idx = pd.to_datetime(["2020-01-31", "2020-03-31"])
    me = to_month_end(pd.Series([1.0, 3.0], idx))
    assert len(me) == 3 and np.isnan(me.loc["2020-02-29", "value"])


def test_month_end_rejects_duplicates():
    idx = pd.to_datetime(["2020-01-31", "2020-01-31"])
    with pytest.raises(ValueError):
        to_month_end(pd.Series([1.0, 2.0], idx))


def test_weekend_month_end_uses_last_business_day():
    # 2020-05-31 is a Sunday; Friday 29th is the last business day -> not stale
    me = to_month_end(pd.Series([1.0], pd.to_datetime(["2020-05-29"])))
    assert not bool(me["stale"].iloc[0])


# ---------- trailing return ----------

def _monthly(vals, start="2019-01-31"):
    return pd.Series(vals, index=pd.date_range(start, periods=len(vals), freq="ME"), dtype=float)


def test_trailing_12m_return_exact():
    s = _monthly([100 + i for i in range(13)])
    tr = trailing_return(s, 12)
    assert tr.iloc[-1] == pytest.approx(112 / 100 - 1)
    assert tr.iloc[:-1].isna().all()


def test_trailing_return_nan_if_hole_inside_window():
    vals = [100 + i for i in range(13)]
    vals[5] = np.nan
    assert np.isnan(trailing_return(_monthly(vals), 12).iloc[-1])


def test_simple_returns_no_multi_month_jump_over_gap():
    s = _monthly([100, 110, np.nan, 121])
    r = simple_returns(s)
    assert np.isnan(r.iloc[2]) and np.isnan(r.iloc[3])


def test_index_from_returns_roundtrip():
    r = _monthly([0.01, -0.02, 0.03])
    idx = index_from_returns(r)
    assert simple_returns(idx).dropna().values == pytest.approx(r.values)


# ---------- yield -> return ----------

def test_yield_to_monthly_return_uses_prior_month_yield():
    y = _monthly([6.0, 3.0, 12.0])
    r = yield_to_monthly_return(y)
    assert np.isnan(r.iloc[0])
    assert r.iloc[1] == pytest.approx(0.06 / 12)  # earned in month 2 at month-1 yield
    assert r.iloc[2] == pytest.approx(0.03 / 12)


def test_yield_compound_method():
    r = yield_to_monthly_return(_monthly([12.0, 12.0]), method="compound_prior")
    assert r.iloc[1] == pytest.approx(1.12 ** (1 / 12) - 1)


def test_yield_constant_5pct_gives_about_5pct_per_year():
    r = yield_to_monthly_return(_monthly([5.0] * 13)).dropna()
    assert (1 + r).prod() - 1 == pytest.approx((1 + 0.05 / 12) ** 12 - 1)


def test_par_bond_unchanged_yield_returns_coupon():
    r = par_bond_monthly_return(_monthly([6.0, 6.0]), 10).iloc[1]
    # unchanged yield: price ~ par (tiny roll-down from shorter maturity at par yield = 0)
    assert r == pytest.approx(0.005, abs=1e-6)


def test_par_bond_yield_rise_loses():
    assert par_bond_monthly_return(_monthly([5.0, 6.0]), 10).iloc[1] < -0.05


# ---------- FX ----------

def test_usd_to_sek_return_conversion():
    # +10% in USD, USD strengthens from 8 to 10 SEK -> (1.1*1.25)-1
    assert convert_return_usd_to_sek(0.10, 8.0, 10.0) == pytest.approx(0.375)
    # USD weakens 10 -> 8
    assert convert_return_usd_to_sek(0.10, 10.0, 8.0) == pytest.approx(1.1 * 0.8 - 1)


def test_index_conversion_and_trailing_consistency():
    usd = _monthly([100 + i for i in range(13)])
    fx = _monthly([8 + 0.1 * i for i in range(13)])
    sek = convert_index_usd_to_sek(usd, fx)
    r_sek = trailing_return(sek, 12).iloc[-1]
    assert r_sek == pytest.approx(convert_return_usd_to_sek(0.12, 8.0, 9.2))


def test_quote_convention_guard():
    with pytest.raises(ValueError):
        check_sek_per_usd(_monthly([0.1, 0.12]))  # USD per SEK given by mistake
    check_sek_per_usd(invert_quote(_monthly([0.1, 0.12])))


# ---------- execution ----------

def test_idealized_vs_next_month_schedule():
    t = pd.Timestamp("2020-03-31")
    a = IDEALIZED_CLOSE.schedule(t)
    b = NEXT_MONTH_CLOSE.schedule(t)
    assert a["first_return_month"] == pd.Timestamp("2020-04-30")
    assert b["execution_date"] == pd.Timestamp("2020-04-30")
    assert b["first_return_month"] == pd.Timestamp("2020-05-31")
    assert not IDEALIZED_CLOSE.lookahead_free and NEXT_MONTH_CLOSE.lookahead_free


def test_fund_order_cutoff():
    m = FundOrderModel(cutoff=time(14, 0))
    assert m.nav_date(datetime(2024, 1, 15, 13, 59)) == date(2024, 1, 15)
    assert m.nav_date(datetime(2024, 1, 15, 14, 0)) == date(2024, 1, 16)
    assert m.nav_date(datetime(2024, 1, 13, 10, 0)) == date(2024, 1, 15)  # Saturday


def test_fund_switch_has_time_out_of_market():
    m = FundOrderModel(cutoff=time(14, 0))
    sw = m.switch_dates(date(2024, 5, 31))  # Friday
    assert sw["data_available_date"] == date(2024, 6, 3)
    assert sw["sell_nav_date"] == date(2024, 6, 3)
    assert sw["buy_nav_date"] == date(2024, 6, 4)
    assert sw["days_out_of_market"] >= 1


def test_fund_nav_not_used_before_launch():
    s = pd.Series([1.0, 1.1], pd.to_datetime(["2019-12-31", "2020-01-31"]))
    with pytest.raises(ValueError):
        assert_not_before_launch(s, date(2020, 1, 15), "Avanza X")
    assert_not_before_launch(truncate_to_launch(s, date(2020, 1, 15)), date(2020, 1, 15), "Avanza X")


def test_chain_levels_never_bridges_gaps():
    from gem.panel import chain_levels
    r = _monthly([0.01] * 14 + [np.nan] + [0.01] * 13, start="2019-01-31")
    lv = chain_levels(r)
    tr = trailing_return(lv.dropna(), 12)
    gap = r.index[14]
    # no 12m return whose window touches the gap month
    bad = tr[(tr.index >= gap) & (tr.index < gap + pd.offsets.MonthEnd(13))].dropna()
    assert bad.empty
    assert tr.dropna().index[-1] == r.index[-1]


# ---------- phase 2: level-based USD -> SEK ----------

def test_sek_return_fx_unchanged_equals_usd_return():
    from gem.fx import sek_returns_from_usd_index
    usd = _monthly([100.0, 110.0])
    fx = _monthly([10.0, 10.0])
    assert sek_returns_from_usd_index(usd, fx).iloc[1] == pytest.approx(0.10)


def test_sek_return_includes_fx_move():
    from gem.fx import sek_returns_from_usd_index
    usd = _monthly([100.0, 110.0])
    fx = _monthly([10.0, 11.0])
    # SEK level 1000 -> 1210  => +21 %, not 10 % + 10 % = 20 %
    assert sek_returns_from_usd_index(usd, fx).iloc[1] == pytest.approx(0.21)


def test_panel_leg_uses_level_based_conversion():
    from gem.panel import leg_returns
    from gem.runs import Leg
    idx = pd.date_range("2020-01-31", periods=3, freq="ME")
    data = {"U": pd.Series([100.0, 110.0, 99.0], idx), "FX": pd.Series([10.0, 11.0, 11.0], idx)}
    cat = {"U": {"id": "U", "asset_class": "equity", "is_total_return": True},
           "FX": {"id": "FX", "asset_class": "fx", "is_total_return": False}}
    r, _ = leg_returns(Leg((("U", None),), fx_to_sek="FX"), data, cat)
    assert r.loc["2020-02-29"] == pytest.approx(1210 / 1000 - 1)
    assert r.loc["2020-03-31"] == pytest.approx(99 * 11 / 1210 - 1)
