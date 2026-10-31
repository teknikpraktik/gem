"""Measure Avanza fund NAV publication lag (one observation per call).

    python -m gem.navlag OUT.csv

Appends one row per fund: observed_at_utc, observed_at_stockholm, instrument_id,
isin, nav_date, nav, bdays_nav_date_to_observation, status. Repeated calls around
a month end bound the time at which the month-end NAV becomes available.
NOT scheduled by this repository; scheduling is a decision for the repo owner.
Source: avanza.se fund-guide JSON (UNDOCUMENTED_ENDPOINT).
"""

from __future__ import annotations

import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import requests

from .data.avanza import guide_url
from .nav import load_instruments

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ["observed_at_utc", "observed_at_stockholm", "instrument_id", "isin", "nav_date", "nav",
          "bdays_nav_date_to_observation", "status"]


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    out = Path(argv[0]) if argv else ROOT / "reports" / "generated" / "nav_lag_observations.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    insts = load_instruments(ROOT / "data" / "investable_instruments.yaml")
    new = not out.exists()
    with out.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for iid, inst in sorted(insts.items()):
            now = datetime.now(timezone.utc)
            sto = now.astimezone(ZoneInfo("Europe/Stockholm"))
            row = {"observed_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "observed_at_stockholm": sto.isoformat(),
                   "instrument_id": iid, "isin": inst.isin}
            try:
                r = requests.get(guide_url(inst.orderbook_id), timeout=30,
                                 headers={"User-Agent": "gem-research/0.1 (NAV publication lag measurement)"})
                g = r.json()
                nd = g["navDate"][:10]
                row.update({"nav_date": nd, "nav": g["nav"], "status": "OK",
                            "bdays_nav_date_to_observation": int(np.busday_count(nd, sto.date().isoformat()))})
            except Exception as e:  # noqa: BLE001 - logged, never fatal
                row.update({"status": f"ERROR {type(e).__name__}: {str(e)[:80]}"})
            w.writerow(row)
            print(row)
            time.sleep(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
