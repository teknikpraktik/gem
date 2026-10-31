"""Load and validate data/catalog.yaml and data/investable_instruments.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml

REQUIRED_SERIES_FIELDS = (
    "id", "name", "provider", "provider_series_id", "source_url", "asset_class", "region", "currency",
    "frequency", "is_total_return", "start_date", "end_date", "license_notes", "retrieval_method",
    "proxy_for", "quality_status", "notes", "verification", "build_env", "fetch",
)
QUALITY_STATUSES = {"VERIFIED", "PROXY", "EXPERIMENTAL", "UNUSABLE", "LICENSE_RESTRICTED"}
VERIFICATION_LEVELS = {"VERIFIED FROM PRIMARY SOURCE", "VERIFIED FROM SECONDARY SOURCE", "ASSUMPTION", "UNRESOLVED"}
REQUIRED_INSTRUMENT_FIELDS = (
    "name", "isin", "provider", "category", "benchmark", "currency", "ongoing_charge", "launch_date",
    "cutoff_time", "settlement_notes", "source", "verified_at",
)


class CatalogError(ValueError):
    pass


def load_catalog(path: Path) -> dict[str, dict]:
    doc = yaml.safe_load(Path(path).read_text())
    out: dict[str, dict] = {}
    for e in doc["series"]:
        missing = [f for f in REQUIRED_SERIES_FIELDS if f not in e]
        if missing:
            raise CatalogError(f"{e.get('id')}: missing fields {missing}")
        if e["quality_status"] not in QUALITY_STATUSES:
            raise CatalogError(f"{e['id']}: bad quality_status {e['quality_status']}")
        if e["verification"] not in VERIFICATION_LEVELS:
            raise CatalogError(f"{e['id']}: bad verification {e['verification']}")
        if e["id"] in out:
            raise CatalogError(f"duplicate id {e['id']}")
        if "provider" not in e["fetch"]:
            raise CatalogError(f"{e['id']}: fetch.provider missing")
        out[e["id"]] = e
    return out


def load_instruments(path: Path) -> list[dict]:
    doc = yaml.safe_load(Path(path).read_text())
    items = doc["instruments"]
    for it in items:
        missing = [f for f in REQUIRED_INSTRUMENT_FIELDS if f not in it]
        if missing:
            raise CatalogError(f"{it.get('name')}: missing fields {missing}")
    return items
