"""Observe when Avanza fund NAVs are actually published (OBSERVATION ONLY).

    python -m gem.navobserver OUT_DIR

Each call appends one row per instrument to OUT_DIR/observations.csv:
    observed_at_utc, observed_at_stockholm, instrument_id, isin, expected_nav_date,
    nav_date, nav, first_seen_at, is_new_nav_date, bdays_expected_to_observation,
    source, status
and rewrites OUT_DIR/first_seen.csv (first time each (instrument, nav_date) was seen).

expected_nav_date = the latest Monday-Friday date strictly before the Stockholm
observation date (the NAV that could at the earliest be published by now; Swedish
holidays are not modelled, so a holiday shows up as a late NAV - read it as such).

Requests: one guide request per instrument per call (5), 1 s apart. The scheduled
workflow (.github/workflows/nav-observer.yml) runs a few times per day around month
ends only. Nothing here affects signals or trades; the data is used to calibrate the
live cron window and the STALE_DATA threshold.
Source: avanza.se fund-guide JSON (UNDOCUMENTED_ENDPOINT).
"""

from __future__ import annotations

import csv
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import requests

from .data.avanza import guide_url
from .nav import load_instruments

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "avanza_fund_guide (UNDOCUMENTED_ENDPOINT)"
FIELDS = ["observed_at_utc", "observed_at_stockholm", "instrument_id", "isin", "expected_nav_date", "nav_date", "nav",
          "first_seen_at", "is_new_nav_date", "bdays_expected_to_observation", "source", "status"]


def expected_nav_date(today: date) -> date:
    d = today - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def load_first_seen(obs: Path) -> dict[tuple[str, str], str]:
    seen: dict[tuple[str, str], str] = {}
    if obs.exists():
        with obs.open() as fh:
            for r in csv.DictReader(fh):
                if str(r.get("status", "")).startswith("OK") and r.get("nav_date"):
                    seen.setdefault((r["instrument_id"], r["nav_date"]), r["observed_at_utc"])
    return seen


def observe(out_dir: Path, fetch=requests.get, now: datetime | None = None, sleep=time.sleep) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    obs = out_dir / "observations.csv"
    seen = load_first_seen(obs)
    insts = load_instruments(ROOT / "data" / "investable_instruments.yaml")
    rows = []
    for iid, inst in sorted(insts.items()):
        t = now or datetime.now(timezone.utc)
        sto = t.astimezone(ZoneInfo("Europe/Stockholm"))
        exp = expected_nav_date(sto.date())
        row = {"observed_at_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "observed_at_stockholm": sto.isoformat(timespec="seconds"),
               "instrument_id": iid, "isin": inst.isin, "expected_nav_date": exp.isoformat(), "source": SOURCE}
        try:
            r = fetch(guide_url(inst.orderbook_id), timeout=30,
                      headers={"User-Agent": "gem-research/0.1 (NAV publication observation, no trading)"})
            r.raise_for_status()
            g = r.json()
            if g.get("isin") != inst.isin:
                raise ValueError(f"ISIN mismatch {g.get('isin')} != {inst.isin}")
            nd = str(g["navDate"])[:10]
            key = (iid, nd)
            new = key not in seen
            if new:
                seen[key] = row["observed_at_utc"]
            row.update({"nav_date": nd, "nav": g["nav"], "first_seen_at": seen[key], "is_new_nav_date": int(new),
                        "bdays_expected_to_observation": int(np.busday_count(exp.isoformat(), sto.date().isoformat())),
                        "status": "OK" if nd >= exp.isoformat() else "OK_OLDER_NAV"})
        except Exception as e:  # noqa: BLE001 - logged, never fatal
            row.update({"status": f"ERROR {type(e).__name__}: {str(e)[:80]}"})
        rows.append(row)
        sleep(1)
    new_file = not obs.exists()
    with obs.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerows(rows)
    with (out_dir / "first_seen.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["instrument_id", "nav_date", "first_seen_at_utc"])
        for (iid, nd), ts in sorted(seen.items()):
            w.writerow([iid, nd, ts])
    return rows


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    out = Path(argv[0]) if argv else ROOT / "reports" / "generated" / "nav_observer"
    for r in observe(out):
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
