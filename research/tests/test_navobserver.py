import csv
from datetime import date, datetime, timezone

from gem.navobserver import expected_nav_date, observe


class Resp:
    def __init__(self, body, status=200):
        self.body, self.status_code = body, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self.body


def test_expected_nav_date_skips_weekend():
    assert expected_nav_date(date(2026, 10, 5)) == date(2026, 10, 2)  # Monday -> Friday
    assert expected_nav_date(date(2026, 10, 1)) == date(2026, 9, 30)


def test_observe_first_seen_and_errors(tmp_path):
    from gem.nav import load_instruments
    from gem.navobserver import ROOT
    insts = load_instruments(ROOT / "data" / "investable_instruments.yaml")
    by_ob = {i.orderbook_id: i for i in insts.values()}
    nav_date = {"v": "2026-09-29"}

    def fetch(url, **_):
        ob = url.rsplit("/", 1)[-1]
        if by_ob[ob].instrument_id == "AVANZA_EM":
            return Resp({}, 503)
        return Resp({"isin": by_ob[ob].isin, "nav": 100.0, "navDate": nav_date["v"] + "T00:00:00"})

    t1 = datetime(2026, 10, 1, 5, 17, tzinfo=timezone.utc)
    r1 = observe(tmp_path, fetch=fetch, now=t1, sleep=lambda s: None)
    usa = next(r for r in r1 if r["instrument_id"] == "AVANZA_USA")
    assert usa["status"] == "OK_OLDER_NAV" and usa["is_new_nav_date"] == 1
    assert next(r for r in r1 if r["instrument_id"] == "AVANZA_EM")["status"].startswith("ERROR")
    nav_date["v"] = "2026-09-30"
    t2 = datetime(2026, 10, 1, 14, 17, tzinfo=timezone.utc)
    r2 = observe(tmp_path, fetch=fetch, now=t2, sleep=lambda s: None)
    usa2 = next(r for r in r2 if r["instrument_id"] == "AVANZA_USA")
    assert usa2["status"] == "OK" and usa2["first_seen_at"] == "2026-10-01T14:17:00Z"
    r3 = observe(tmp_path, fetch=fetch, now=datetime(2026, 10, 1, 17, 17, tzinfo=timezone.utc), sleep=lambda s: None)
    usa3 = next(r for r in r3 if r["instrument_id"] == "AVANZA_USA")
    assert usa3["is_new_nav_date"] == 0 and usa3["first_seen_at"] == "2026-10-01T14:17:00Z"
    rows = list(csv.DictReader((tmp_path / "observations.csv").open()))
    assert len(rows) == 3 * len(insts)
    fs = list(csv.DictReader((tmp_path / "first_seen.csv").open()))
    assert {"instrument_id": "AVANZA_USA", "nav_date": "2026-09-30", "first_seen_at_utc": "2026-10-01T14:17:00Z"} in fs
