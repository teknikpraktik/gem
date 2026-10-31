"""Parser tests against format fixtures + catalog/instrument schema tests.

The fixtures reproduce the documented public formats. Live endpoints for
FRED, Ken French and the Riksbank were blocked in the build environment, so
these tests are the only verification of those parsers so far.
"""

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from gem.catalog import QUALITY_STATUSES, load_catalog, load_instruments
from gem.data.base import RawStore
from gem.data.providers import (
    parse_aj_compilation, parse_fred_csv, parse_french_csv_text, parse_french_zip, parse_h10_mirror,
    parse_riksbank_json, parse_shiller_tr,
)
from gem.runs import all_runs

ROOT = Path(__file__).resolve().parents[1]


def test_fred_csv_new_and_old_header():
    e = {"id": "X", "provider_series_id": "DTB3"}
    new = b"observation_date,DTB3\n2024-01-02,5.25\n2024-01-03,.\n2024-01-04,5.20\n"
    old = b"DATE,DTB3\n2024-01-02,5.25\n2024-01-04,5.20\n"
    for raw in (new, old):
        s = parse_fred_csv(raw, e)
        assert list(s.values) == [5.25, 5.20]  # "." dropped, never filled


FRENCH = """This file was created by CMPT_ME_BEME_RETS using the 202409 CRSP database.
The 1-month TBill rate data until 202405 are from Ibbotson Associates.

,Mkt-RF,SMB,HML,RF
192607,    2.96,   -2.56,   -2.43,    0.22
192608,    2.64,   -1.17,    3.82,    0.25
192609,    0.36,   -1.40,    0.13,    0.23

 Annual Factors: January-December
,Mkt-RF,SMB,HML,RF
1927,   29.47,   -2.46,   -3.75,    3.12
"""


def test_french_parser_takes_first_monthly_block_only():
    df = parse_french_csv_text(FRENCH)
    assert len(df) == 3
    assert df.index[0] == pd.Timestamp("1926-07-31")
    assert df.loc["1926-08-31", "RF"] == 0.25


def test_french_zip_to_total_return_level():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("F-F_Research_Data_Factors.CSV", FRENCH)
    e = {"id": "FF_US", "fetch": {"returns": "Mkt-RF + RF"}}
    lvl = parse_french_zip(buf.getvalue(), e)
    assert lvl.index[0] == pd.Timestamp("1926-06-30") and lvl.iloc[0] == 100
    assert lvl.iloc[1] == pytest.approx(100 * (1 + (2.96 + 0.22) / 100))


def test_riksbank_json():
    raw = json.dumps([{"date": "2024-01-02", "value": 10.05}, {"date": "2024-01-03", "value": 10.11}]).encode()
    s = parse_riksbank_json(raw, {"id": "RB"})
    assert s.iloc[-1] == 10.11
    with pytest.raises(ValueError):
        parse_riksbank_json(b'{"statusCode": 429}', {"id": "RB"})


def test_shiller_drops_price_only_rows():
    raw = (b"Date,SP500,Dividend,Earnings,Consumer Price Index,Long Interest Rate,Real Price,Real Dividend,Real Earnings,PE10\n"
           b"2023-04-01,4100,68.4,0,0,0,0,0,0,0\n2023-05-01,4150,68.6,0,0,0,0,0,0,0\n"
           b"2023-06-01,4300,68.8,0,0,0,0,0,0,0\n2023-07-01,4500,0,0,0,0,0,0,0,0\n")
    lvl = parse_shiller_tr(raw, {"id": "SH"})
    assert lvl.index[-1] == pd.Timestamp("2023-06-30")
    assert lvl.iloc[1] / lvl.iloc[0] - 1 == pytest.approx((4150 + 68.6 / 12) / 4100 - 1)


def test_h10_mirror_both_headers():
    for hdr in (b"Date,Country,Exchange rate\n", b"Date,Country,Value\n"):
        raw = hdr + b"2024-01-02,Sweden,10.1\n2024-01-02,Australia,0.68\n2024-01-03,Sweden,10.2\n"
        s = parse_h10_mirror(raw, {"id": "FX", "fetch": {"country": "Sweden"}})
        assert list(s.values) == [10.1, 10.2]


def test_aj_compilation_zero_is_missing_and_cr_line_endings():
    raw = (b",,\r,MSCI,\rDate,ACWI ex USA,AGG\r12/31/87,100,0\r1/29/88,101.68,\r2/29/88,\"1,108.4\",332\r")
    s = parse_aj_compilation(raw, {"id": "A", "fetch": {"column": "ACWI ex USA"}})
    assert s.iloc[-1] == 1108.4
    b = parse_aj_compilation(raw, {"id": "B", "fetch": {"column": "AGG"}})
    assert len(b) == 1  # zero placeholder dropped


def test_rawstore_offline_without_cache_fails(tmp_path):
    st = RawStore(tmp_path / "raw", tmp_path / "man")
    from gem.data.base import FetchError
    with pytest.raises(FetchError):
        st.fetch("x", "y", "https://example.invalid/data.csv", offline=True)


def test_catalog_schema_and_run_references():
    cat = load_catalog(ROOT / "data" / "catalog.yaml")
    assert all(e["quality_status"] in QUALITY_STATUSES for e in cat.values())
    used = set().union(*(r.series_ids for r in all_runs()))
    assert used <= set(cat), used - set(cat)
    # UNUSABLE series must not be used by any run
    assert not [s for s in used if cat[s]["quality_status"] == "UNUSABLE"]
    # yield series are flagged as not total return
    assert cat["FRED_TB3MS"]["is_total_return"] is False
    assert cat["RB_SSVX_3M"]["is_total_return"] is False


def test_original_gem_runs_never_use_proxy_labelled_strategy_id_mixup():
    for r in all_runs():
        if r.run_id == "GEM_ORIGINAL_STRICT":
            assert r.tier == "STRICT"
        if r.run_id.startswith("GEM_PROXY"):
            assert r.strategy.strategy_id != "GEM_ORIGINAL"
        if "SEK" in r.run_id:
            assert r.strategy.strategy_id != "GEM_ORIGINAL"


def test_instruments_schema():
    items = load_instruments(ROOT / "data" / "investable_instruments.yaml")
    names = {i["name"] for i in items}
    assert {"Avanza USA", "Avanza Europa", "Avanza Emerging Markets", "Avanza Global", "Avanza Ränta Kort"} <= names


# ---------- phase 2: strict manual import ----------

def _entry(**f):
    return {"id": "M", "asset_class": "money_market_index", "fetch": {"provider": "local_csv", "file": "m.csv", **f}}


def test_manual_csv_strict_schema_ok():
    from gem.data.providers import parse_local_csv
    s = parse_local_csv(b"date,value\n2024-01-02,100.0\n2024-01-03,100.01\n", _entry())
    assert len(s) == 2


@pytest.mark.parametrize("raw", [
    b"Date,Value\n2024-01-02,100\n",                 # wrong header
    b"date,value\n02/01/2024,100\n",                 # non-ISO date
    b"date,value\n2024-01-03,100\n2024-01-02,101\n", # not increasing
    b"date,value\n2024-01-02,100\n2024-01-02,101\n", # duplicate
    b"date,value\n2024-01-02,\n",                    # missing value
    b"date,value\n2024-01-02,-1\n",                  # non-positive level
])
def test_manual_csv_rejects_bad_files(raw):
    from gem.data.providers import ManualImportError, parse_local_csv
    with pytest.raises(ManualImportError):
        parse_local_csv(raw, _entry())


def test_manual_csv_rejects_data_before_launch():
    from gem.data.providers import ManualImportError, parse_local_csv
    with pytest.raises(ManualImportError):
        parse_local_csv(b"date,value\n2019-11-29,100\n", _entry(launch_date="2019-12-02"))


def test_sidecar_required(tmp_path):
    from gem.data.providers import ManualImportError, validate_sidecar
    f = tmp_path / "omrxtbill.csv"
    f.write_text("date,value\n2024-01-02,100\n")
    with pytest.raises(ManualImportError):
        validate_sidecar(f)
    (tmp_path / "omrxtbill.csv.source.yaml").write_text("source: Nasdaq\nsource_url: x\n")
    with pytest.raises(ManualImportError):
        validate_sidecar(f)
    (tmp_path / "omrxtbill.csv.source.yaml").write_text(
        "source: Nasdaq\nsource_url: x\nexported_at: 2026-10-31\nexported_by: me\n"
        "licence_terms: personal\nseries_definition: OMRXTBILL\n")
    assert validate_sidecar(f)["source"] == "Nasdaq"


def test_french_daily_parser():
    text = ",Mkt-RF,SMB,HML,RF\n19260701,    0.10,   -0.25,   -0.27,    0.009\n19260702,    0.45,   -0.33,   -0.06,    0.009\n"
    df = parse_french_csv_text(text)
    assert df.index[0] == pd.Timestamp("1926-07-01") and len(df) == 2


def test_get_with_retry_honours_429(monkeypatch):
    from gem.data import base

    class R:
        def __init__(self, code, ra=""):
            self.status_code, self.headers = code, {"Retry-After": ra} if ra else {}

    seq = iter([R(429, "3"), R(503), R(200)])
    monkeypatch.setattr(base.requests, "get", lambda *a, **k: next(seq))
    waits = []
    r = base._get_with_retry("https://x", {}, 5, sleep=waits.append)
    assert r.status_code == 200 and waits == [3.0, 4]
