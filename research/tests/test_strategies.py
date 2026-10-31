from datetime import date

import pytest

from gem.strategies import (
    LOOKBACK_MONTHS, NO_SIGNAL, FixedWeightStrategy, GemStrategy, RegionalMomentumStrategy,
)

D = date(2020, 1, 31)
GEM = GemStrategy()


def target(us, exus, hurdle, **kw):
    return GEM.evaluate(D, us, exus, hurdle, **kw).target


def test_lookback_is_fixed_at_12():
    assert LOOKBACK_MONTHS == 12


def test_us_below_tbill_goes_bonds():
    assert target(0.01, 0.30, 0.02) == "US_AGG_BONDS"


def test_us_equal_tbill_goes_bonds():
    assert target(0.02, 0.30, 0.02) == "US_AGG_BONDS"


def test_us_above_tbill_and_above_exus_goes_us():
    assert target(0.10, 0.05, 0.02) == "US_EQUITIES"


def test_us_above_tbill_and_equal_exus_goes_us():
    assert target(0.10, 0.10, 0.02) == "US_EQUITIES"


def test_us_above_tbill_and_exus_above_us_goes_exus():
    assert target(0.10, 0.15, 0.02) == "EX_US_EQUITIES"


def test_exus_beating_hurdle_does_not_override_us_risk_off():
    # ex-US strongly positive but US below T-bills -> still bonds (original GEM rule)
    assert target(-0.05, 0.40, 0.01) == "US_AGG_BONDS"


@pytest.mark.parametrize("us,exus,h", [(None, 0.1, 0.0), (float("nan"), 0.1, 0.0)])
def test_missing_us_no_signal(us, exus, h):
    assert target(us, exus, h) == NO_SIGNAL


def test_missing_exus_no_signal():
    assert target(0.1, None, 0.0) == NO_SIGNAL


def test_missing_hurdle_no_signal():
    assert target(0.1, 0.2, None) == NO_SIGNAL


def test_stale_data_no_signal():
    s = GEM.evaluate(D, 0.1, 0.2, 0.0, stale_inputs=["exus"])
    assert s.target == NO_SIGNAL and "stale" in s.reason and s.weights == {}


def test_negative_hurdle_handled():
    assert target(-0.001, -0.01, -0.002) == "US_EQUITIES"


def test_full_allocation_single_asset():
    s = GEM.evaluate(D, 0.1, 0.2, 0.0)
    assert s.weights == {"EX_US_EQUITIES": 1.0}


def test_determinism():
    a = GEM.evaluate(D, 0.1, 0.2, 0.0).to_dict()
    b = GemStrategy().evaluate(D, 0.1, 0.2, 0.0).to_dict()
    assert a == b


def test_gem_sek_reuses_rule_with_own_assets():
    g = GemStrategy("GEM_SEK", us_asset="SEK_US_EQ", exus_asset="SEK_EXUS_EQ", defensive_asset="SE_SHORT_RATE")
    assert g.evaluate(D, 0.0, 0.5, 0.0).target == "SE_SHORT_RATE"
    assert g.evaluate(D, 0.2, 0.1, 0.0).target == "SEK_US_EQ"


R = RegionalMomentumStrategy()


def test_regional_winner_above_hurdle():
    s = R.evaluate(D, {"SE_USA_EQ": 0.1, "SE_EUROPE_EQ": 0.2, "SE_EM_EQ": 0.05}, 0.01)
    assert s.target == "SE_EUROPE_EQ"


def test_regional_winner_equal_hurdle_defensive():
    s = R.evaluate(D, {"SE_USA_EQ": 0.01, "SE_EUROPE_EQ": 0.0, "SE_EM_EQ": -0.1}, 0.01)
    assert s.target == "SE_SHORT_RATE"


def test_regional_tie_first_in_order_wins():
    s = R.evaluate(D, {"SE_USA_EQ": 0.1, "SE_EUROPE_EQ": 0.1, "SE_EM_EQ": 0.1}, 0.0)
    assert s.target == "SE_USA_EQ"


def test_regional_missing_region_no_signal():
    s = R.evaluate(D, {"SE_USA_EQ": 0.1, "SE_EUROPE_EQ": None, "SE_EM_EQ": 0.1}, 0.0)
    assert s.target == NO_SIGNAL


def test_fixed_weights_validation():
    with pytest.raises(ValueError):
        FixedWeightStrategy("X", {"A": 0.7, "B": 0.2})
    s = FixedWeightStrategy("STATIC_70_30", {"A": 0.7, "B": 0.3}).evaluate(D, {"A": True, "B": True})
    assert s.target == "MIXED" and s.weights == {"A": 0.7, "B": 0.3}
    s2 = FixedWeightStrategy("STATIC_70_30", {"A": 0.7, "B": 0.3}).evaluate(D, {"A": True, "B": False})
    assert s2.target == NO_SIGNAL
