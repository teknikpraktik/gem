"""Avanza NAV parsing - fixtures copied from real responses (reports/generated/nav_probe)."""

import json
from datetime import date

import pandas as pd
import pytest

from gem.data.avanza import fetch_daily_history, is_daily, parse_chart

# GET /_api/fund-guide/chart/1025150/2026-09-01/2026-10-31?raw=true (excerpt, real values)
DAILY = (b'{"id":"1025150","dataSerie":[{"x":1788213600000,"y":253.94},{"x":1788300000000,"y":256.22},'
         b'{"x":1793142000000,"y":266.43},{"x":1793228400000,"y":263.49}],"name":"Avanza USA",'
         b'"fromDate":"2026-09-01","toDate":"2026-10-31"}')
# long window: monthly, stamped the 1st, null before launch (real excerpt)
MONTHLY = (b'{"id":"1025150","dataSerie":[{"x":1420153200000,"y":null},{"x":1575154800000,"y":100.23},'
           b'{"x":1577833200000,"y":104.04},{"x":1580511600000,"y":97.12}],"name":"Avanza USA"}')


def test_parse_daily_chart_dates_in_stockholm_time():
    s = parse_chart(DAILY)
    assert s.index[0] == pd.Timestamp("2026-09-01")       # 22:00 UTC previous day = 00:00 CEST
    assert s.index[-1] == pd.Timestamp("2026-10-29") and s.iloc[-1] == 263.49
    assert is_daily(s.iloc[:2])


def test_nulls_before_launch_are_dropped_and_monthly_detected():
    s = parse_chart(MONTHLY)
    assert len(s) == 3 and s.iloc[0] == 100.23
    assert not is_daily(s)


def test_fetch_splits_downsampled_windows():
    calls = []

    def get(url):
        calls.append(url)
        a, b = url.split("/chart/1/")[1].split("?")[0].split("/")
        a, b = date.fromisoformat(a), date.fromisoformat(b)
        days = pd.bdate_range(a, b)
        if (b - a).days > 62:  # server downsamples long windows to month ends
            days = pd.date_range(a, b, freq="MS")
        pts = [{"x": int(pd.Timestamp(d, tz="Europe/Stockholm").timestamp() * 1000), "y": 100 + i}
               for i, d in enumerate(days)]
        return json.dumps({"dataSerie": pts}).encode()

    s, used = fetch_daily_history(get, "1", date(2024, 1, 1), date(2024, 12, 31))
    assert is_daily(s) and s.index.min() == pd.Timestamp("2024-01-01")
    assert len(calls) > len(used) >= 6  # the year was split into <= 2-month windows


def test_parse_avanza_nav_checks_isin_and_launch():
    from gem.data.providers import parse_avanza_nav
    doc = {"guide": {"isin": "SE0012741163", "currency": "SEK"}, "chunks": [{"body": json.loads(DAILY)}]}
    e = {"id": "AVZ_NAV_USA", "currency": "SEK", "fetch": {"isin": "SE0012741163"}}
    assert parse_avanza_nav(json.dumps(doc).encode(), e).iloc[-1] == 263.49
    with pytest.raises(ValueError):
        parse_avanza_nav(json.dumps(doc).encode(), {**e, "fetch": {"isin": "SE0000000000"}})
    with pytest.raises(ValueError):
        parse_avanza_nav(json.dumps(doc).encode(), {**e, "fetch": {"isin": "SE0012741163", "launch_date": "2026-10-01"}})


def test_holiday_gaps_are_still_daily():
    # regression (Actions run 41196091780): Christmas / closed days made real daily windows
    # look downsampled under a max-gap rule
    days = pd.to_datetime(["2020-12-21", "2020-12-22", "2020-12-23", "2020-12-28", "2020-12-29",
                           "2020-12-30", "2021-01-04", "2021-01-05", "2021-01-07", "2021-01-08"])
    assert is_daily(pd.Series(range(len(days)), index=days), 24)
    monthly = pd.to_datetime(["2020-01-01", "2020-02-01", "2020-03-01"])
    assert not is_daily(pd.Series([1, 2, 3], index=monthly), 90)
