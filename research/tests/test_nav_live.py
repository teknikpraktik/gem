import json
from datetime import date

import numpy as np
import pandas as pd
import pytest

from gem.live import regional_live_signal
from gem.nav import Instrument, NavError, validate_nav_series

DAYS = pd.bdate_range("2023-01-02", "2024-10-31")


def nav(growth_per_day):
    return pd.Series(100 * np.cumprod(np.full(len(DAYS), 1 + growth_per_day)), index=DAYS)


def navs(us=0.0004, eu=0.0002, em=0.0001):
    return {"AVANZA_USA": nav(us), "AVANZA_EUROPA": nav(eu), "AVANZA_EM": nav(em)}


YIELD = pd.Series(3.0, index=pd.bdate_range("2022-01-03", "2024-10-31"))


def test_live_signal_picks_best_region_above_cash():
    s = regional_live_signal(date(2024, 11, 1), navs(), YIELD)
    assert s["status"] == "VALID" and s["target"] == "AVANZA_USA"
    assert s["signal_period_end"] == "2024-10-31"
    assert s["returns"]["cash"] == pytest.approx((1 + 0.03 / 12) ** 12 - 1)
    json.dumps(s)  # serialisable


def test_live_signal_defensive_when_all_below_cash():
    s = regional_live_signal(date(2024, 11, 1), navs(-0.0001, -0.0002, -0.0003), YIELD)
    assert s["target"] == "AVANZA_RANTA_KORT"


def test_incomplete_month_gives_no_signal():
    n = navs()
    n["AVANZA_EM"] = n["AVANZA_EM"][:"2024-10-24"]  # EM NAV for month end not yet published
    s = regional_live_signal(date(2024, 11, 1), n, YIELD)
    assert s["status"] == "NO_SIGNAL" and "differ" in s["reason"]


def test_signal_uses_only_data_up_to_period_end():
    a = regional_live_signal(date(2024, 11, 1), navs(), YIELD)
    n = navs()
    extra = pd.bdate_range("2024-11-01", "2024-11-08")
    for k in n:  # November NAVs exist but must not affect the October signal
        n[k] = pd.concat([n[k], pd.Series(1.0, index=extra)])
    b = regional_live_signal(date(2024, 11, 8), n, YIELD)
    assert a["returns"] == b["returns"] and a["target"] == b["target"]


def test_needs_12_months_of_nav():
    short = {k: v["2024-03":] for k, v in navs().items()}
    s = regional_live_signal(date(2024, 11, 1), short, YIELD)
    assert s["status"] == "NO_SIGNAL" and "missing" in s["reason"]


def test_nav_validation_refuses_bad_series():
    inst = Instrument("X", "X", "SE0", "SEK", date(2023, 1, 5))
    with pytest.raises(NavError):
        validate_nav_series(nav(0.0001), inst)  # data before launch
    bad = nav(0.0001)["2023-02":].copy()
    bad.iloc[5] = bad.iloc[4] * 2
    with pytest.raises(NavError):
        validate_nav_series(bad, Instrument("X", "X", "SE0", "SEK", None))
