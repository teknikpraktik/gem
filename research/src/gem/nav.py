"""Fund NAV providers (investable instruments) - source-agnostic.

A provider returns NAV history/latest NAV for an INVESTABLE_INSTRUMENT. Strategy
and live-signal code only see `NavPoint` / `pd.Series` and never a provider's
wire format, so a provider can be swapped (official feed, licensed vendor,
manual export, or - last resort - an undocumented avanza.se endpoint).

Every NavPoint carries: instrument_id, isin, nav_date, nav, currency,
retrieved_at, source, quality.
"""

from __future__ import annotations

import abc
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

QUALITY_OFFICIAL = "OFFICIAL"                  # documented feed from the fund company / exchange
QUALITY_MANUAL_OFFICIAL = "MANUAL_OFFICIAL_EXPORT"
QUALITY_UNDOCUMENTED = "UNDOCUMENTED_ENDPOINT"  # works today, may change without notice


@dataclass(frozen=True)
class Instrument:
    instrument_id: str
    name: str
    isin: str
    currency: str
    launch_date: date | None
    orderbook_id: str | None = None


@dataclass(frozen=True)
class NavPoint:
    instrument_id: str
    isin: str
    nav_date: date
    nav: float
    currency: str
    retrieved_at: str
    source: str
    quality: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["nav_date"] = self.nav_date.isoformat()
        return d


class NavError(RuntimeError):
    pass


class FundNavProvider(abc.ABC):
    name: str = "abstract"
    quality: str = QUALITY_UNDOCUMENTED

    @abc.abstractmethod
    def historical_nav(self, inst: Instrument) -> pd.Series:
        """Daily NAV (index = nav_date, values = NAV in inst.currency), sorted, no NaN."""

    def latest_nav(self, inst: Instrument) -> NavPoint:
        s = self.historical_nav(inst)
        if s.empty:
            raise NavError(f"{self.name}: no NAV for {inst.instrument_id}")
        return NavPoint(inst.instrument_id, inst.isin, s.index[-1].date(), float(s.iloc[-1]), inst.currency,
                        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), self.name, self.quality)


def validate_nav_series(s: pd.Series, inst: Instrument) -> pd.Series:
    """Hard checks shared by all providers. Refuses, never repairs."""
    if s.index.has_duplicates:
        raise NavError(f"{inst.instrument_id}: duplicate NAV dates")
    s = s.sort_index()
    if (s <= 0).any() or s.isna().any():
        raise NavError(f"{inst.instrument_id}: non-positive or missing NAV")
    if inst.launch_date is not None and s.index.min().date() < inst.launch_date:
        raise NavError(f"{inst.instrument_id}: NAV dated {s.index.min().date()} before launch {inst.launch_date}")
    r = s.pct_change().abs()
    if (r > 0.25).any():
        raise NavError(f"{inst.instrument_id}: daily NAV move > 25 % on {r.idxmax().date()} (split/error?)")
    return s


class ManualCsvNavProvider(FundNavProvider):
    """data/manual/nav_<ISIN>.csv (strict date,value schema + .source.yaml sidecar)."""

    name = "manual_csv"
    quality = QUALITY_MANUAL_OFFICIAL

    def __init__(self, manual_dir: Path):
        self.dir = Path(manual_dir)

    def historical_nav(self, inst: Instrument) -> pd.Series:
        from .data.providers import parse_local_csv, validate_sidecar

        p = self.dir / f"nav_{inst.isin}.csv"
        if not p.exists():
            raise NavError(f"manual NAV file missing: {p.name}")
        validate_sidecar(p)
        entry = {"id": inst.instrument_id, "asset_class": "fund_nav",
                 "fetch": {"launch_date": str(inst.launch_date) if inst.launch_date else None}}
        return validate_nav_series(parse_local_csv(p.read_bytes(), entry), inst)


def load_instruments(path: Path) -> dict[str, Instrument]:
    doc = yaml.safe_load(Path(path).read_text())
    out = {}
    for it in doc["instruments"]:
        iid = it.get("instrument_id")
        if not iid:
            continue
        ld = it.get("launch_date_iso")
        out[iid] = Instrument(iid, it["name"], it["isin"], it.get("nav_currency", "SEK"),
                              date.fromisoformat(ld) if ld else None, str(it.get("orderbook_id") or "") or None)
    return out
