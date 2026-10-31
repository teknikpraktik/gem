"""Source-specific URL builders and parsers.

Each provider turns (catalog entry, raw bytes) into a pandas Series of LEVELS
(index levels, yields in percent, or FX rates) indexed by observation date.
Return-type series (Ken French publishes monthly % returns) are converted to
a level index here so that downstream code only sees levels.

Providers marked PRIMARY have been implemented against the documented public
formats. In the build environment those hosts were blocked by network policy,
so their parsers are tested against format fixtures only (tests/fixtures);
see reports/data_sources.md for status.
"""

from __future__ import annotations

import io
import json
import zipfile
from typing import Callable

import numpy as np
import pandas as pd

from .base import FetchError, RawFile, RawStore

# --------------------------------------------------------------------------
# FRED (PRIMARY) - https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>
# No API key needed for this endpoint. Header column is "observation_date"
# (newer) or "DATE" (older); missing values are ".".
# --------------------------------------------------------------------------

def fred_url(entry: dict) -> str:
    return f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={entry['provider_series_id']}"


def parse_fred_csv(raw: bytes, entry: dict) -> pd.Series:
    df = pd.read_csv(io.BytesIO(raw), na_values=["."])
    date_col = df.columns[0]
    if date_col.upper() not in ("DATE", "OBSERVATION_DATE"):
        raise ValueError(f"unexpected FRED header {list(df.columns)}")
    sid = entry["provider_series_id"]
    col = sid if sid in df.columns else df.columns[1]
    s = pd.Series(pd.to_numeric(df[col], errors="coerce").values, index=pd.to_datetime(df[date_col]), name=entry["id"])
    return s.dropna()


# --------------------------------------------------------------------------
# Ken French Data Library (PRIMARY)
# https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/<FILE>_CSV.zip
# CSV inside the zip: free-text header lines, then a header row starting with
# a comma, then rows "YYYYMM, v1, v2, ...", then a blank line and further
# sections (annual factors etc.). Only the FIRST monthly block is used.
# Values are percent returns; -99.99 / -999 denote missing.
# --------------------------------------------------------------------------

def french_url(entry: dict) -> str:
    return f"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{entry['fetch']['file']}"


def parse_french_csv_text(text: str) -> pd.DataFrame:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    header = None
    rows = []
    for ln in lines:
        parts = [p.strip() for p in ln.split(",")]
        if header is None:
            if len(parts) > 1 and parts[0] == "" and any(parts[1:]):
                header = parts[1:]
            continue
        if len(parts) > 1 and len(parts[0]) in (6, 8) and parts[0].isdigit():
            rows.append(parts)
        elif rows:  # end of first monthly block
            break
    if header is None or not rows:
        raise ValueError("could not locate monthly block in Ken French file")
    if len(rows[0][0]) == 8:  # daily file
        idx = pd.to_datetime([r[0] for r in rows], format="%Y%m%d")
    else:
        idx = pd.to_datetime([r[0] for r in rows], format="%Y%m") + pd.offsets.MonthEnd(0)
    data = [[float(x) for x in r[1:len(header) + 1]] for r in rows]
    df = pd.DataFrame(data, index=idx, columns=header)
    return df.replace([-99.99, -999.0], np.nan)


def parse_french_zip(raw: bytes, entry: dict) -> pd.Series:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        text = z.read(name).decode("latin-1")
    df = parse_french_csv_text(text)
    return french_frame_to_level(df, entry)


def french_frame_to_level(df: pd.DataFrame, entry: dict) -> pd.Series:
    f = entry["fetch"]
    expr = f["returns"]  # e.g. "Mkt-RF + RF" or "RF"
    cols = [c.strip() for c in expr.split("+")]
    r = sum(df[c] for c in cols) / 100.0
    return returns_to_level(r, entry["id"])


def returns_to_level(r: pd.Series, name: str, base: float = 100.0) -> pd.Series:
    r = r.dropna()
    is_month_end = bool((r.index == r.index + pd.offsets.MonthEnd(0)).all())
    first = r.index[0] - (pd.offsets.MonthEnd(1) if is_month_end else pd.offsets.BDay(1))
    lvl = pd.concat([pd.Series([base], index=[first]), base * (1 + r).cumprod()])
    return lvl.rename(name)


# --------------------------------------------------------------------------
# Riksbank SWEA API (PRIMARY)
# https://api.riksbank.se/swea/v1/Observations/{seriesId}/{from}/{to}
# Returns JSON [{"date": "YYYY-MM-DD", "value": <number>}, ...].
# Anonymous access is rate limited; an optional key goes in the header
# Ocp-Apim-Subscription-Key (env RIKSBANK_API_KEY).
# --------------------------------------------------------------------------

def riksbank_url(entry: dict) -> str:
    f = entry.get("fetch", {})
    start = f.get("from", "1980-01-01")
    end = f.get("to", pd.Timestamp.today().strftime("%Y-%m-%d"))
    return f"https://api.riksbank.se/swea/v1/Observations/{entry['provider_series_id']}/{start}/{end}"


def parse_riksbank_json(raw: bytes, entry: dict) -> pd.Series:
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError(f"unexpected Riksbank payload: {str(data)[:200]}")
    s = pd.Series({pd.Timestamp(d["date"]): d["value"] for d in data}, name=entry["id"], dtype=float)
    return s.sort_index().dropna()


# --------------------------------------------------------------------------
# Manual local CSV (for licensed exports: MSCI, S&P DJI, Bloomberg, Nasdaq).
# Expected columns: date,value  (ISO dates).  Placed by the user under
# data/manual/<file>; never downloaded automatically.
# --------------------------------------------------------------------------

SIDECAR_FIELDS = ("source", "source_url", "exported_at", "exported_by", "licence_terms", "series_definition")


class ManualImportError(ValueError):
    pass


def validate_sidecar(csv_path) -> dict:
    """Manual (licensed) exports must carry provenance in <file>.source.yaml."""
    from pathlib import Path

    import yaml

    side = Path(str(csv_path) + ".source.yaml")
    if not side.exists():
        raise ManualImportError(f"missing provenance sidecar {side.name}")
    meta = yaml.safe_load(side.read_text()) or {}
    missing = [f for f in SIDECAR_FIELDS if not meta.get(f)]
    if missing:
        raise ManualImportError(f"{side.name}: missing fields {missing}")
    return meta


def parse_local_csv(raw: bytes, entry: dict) -> pd.Series:
    """Strict schema: columns date,value; ISO dates; strictly increasing; no
    duplicates; finite positive values (index levels / NAV). Anything else is
    refused - no repair. Data before fetch.launch_date is refused."""
    f = entry.get("fetch", {})
    df = pd.read_csv(io.BytesIO(raw), dtype=str)
    dc, vc = f.get("date_column", "date"), f.get("value_column", "value")
    if list(df.columns[:2]) != [dc, vc]:
        raise ManualImportError(f"{entry['id']}: expected columns [{dc},{vc}], got {list(df.columns)}")
    try:
        dates = pd.to_datetime(df[dc], format="%Y-%m-%d")
    except Exception as e:  # noqa: BLE001
        raise ManualImportError(f"{entry['id']}: dates must be ISO YYYY-MM-DD ({e})") from e
    vals = pd.to_numeric(df[vc], errors="coerce")
    if vals.isna().any():
        raise ManualImportError(f"{entry['id']}: non-numeric/missing value at row {int(vals.isna().idxmax()) + 2}")
    if dates.duplicated().any():
        raise ManualImportError(f"{entry['id']}: duplicate dates")
    if not dates.is_monotonic_increasing:
        raise ManualImportError(f"{entry['id']}: dates not strictly increasing")
    if entry.get("asset_class") not in ("money_market_yield", "bond_yield") and (vals <= 0).any():
        raise ManualImportError(f"{entry['id']}: non-positive level")
    s = pd.Series(vals.values, index=pd.DatetimeIndex(dates), name=entry["id"])
    if f.get("launch_date"):
        launch = pd.Timestamp(str(f["launch_date"]))
        if s.index.min() < launch:
            raise ManualImportError(f"{entry['id']}: data at {s.index.min().date()} precedes launch {launch.date()}")
    return s


# --------------------------------------------------------------------------
# SECONDARY MIRRORS on raw.githubusercontent.com (reachable in build env)
# --------------------------------------------------------------------------

def parse_shiller_tr(raw: bytes, entry: dict) -> pd.Series:
    """datasets/s-and-p-500 (Shiller data + FRED SP500 after 2023-06).

    TR index: r_t = (P_t + D_t/12) / P_{t-1} - 1, with D the annualised
    dividend. P is the MONTHLY AVERAGE of daily closes (not month end) and D
    is interpolated from quarterly totals. Rows after Shiller's last month
    have Dividend == 0 (price only) and are DROPPED, never used as TR.
    """
    df = pd.read_csv(io.BytesIO(raw), parse_dates=["Date"])
    df = df[df["Dividend"] > 0]
    p, d = df["SP500"].values, df["Dividend"].values
    r = pd.Series((p[1:] + d[1:] / 12.0) / p[:-1] - 1.0,
                  index=pd.DatetimeIndex(df["Date"].values[1:]) + pd.offsets.MonthEnd(0))
    return returns_to_level(r, entry["id"])


def parse_h10_mirror(raw: bytes, entry: dict) -> pd.Series:
    """datasets/exchange-rates daily.csv (mirror of FRED H.10, e.g. DEXSDUS)."""
    df = pd.read_csv(io.BytesIO(raw), parse_dates=["Date"])
    df = df[df["Country"] == entry["fetch"]["country"]]
    vcol = "Exchange rate" if "Exchange rate" in df.columns else "Value"  # header changed over time
    s = pd.Series(pd.to_numeric(df[vcol], errors="coerce").values, index=pd.DatetimeIndex(df["Date"]), name=entry["id"])
    s = s[s > 0].dropna().sort_index()
    return s[~s.index.duplicated(keep="last")]


def parse_aj_compilation(raw: bytes, entry: dict) -> pd.Series:
    """alexjansenhome/GEM msci_all_gross.csv (third-party compilation, 1969-2017).

    Old-Mac CR line endings, 3 header rows, US m/d/yy dates, thousands
    separators. Zero is used as a 'no data' placeholder and is mapped to NaN.
    """
    text = raw.decode("latin-1").replace("\r\n", "\n").replace("\r", "\n")
    df = pd.read_csv(io.StringIO(text), skiprows=2, thousands=",", index_col=0)
    df.index = pd.to_datetime(df.index, format="%m/%d/%y")
    df.columns = [c.strip() for c in df.columns]
    s = pd.to_numeric(df[entry["fetch"]["column"]], errors="coerce")
    s = s.where(s != 0).dropna()
    return s.rename(entry["id"])


def parse_arch_french(raw: bytes, entry: dict) -> pd.Series:
    """Ken French factors as bundled in the `arch` PyPI package (ends 2018-11)."""
    df = pd.read_csv(io.BytesIO(raw), compression="gzip" if raw[:2] == b"\x1f\x8b" else None)
    dates = pd.to_datetime(df.iloc[:, 0].astype(int).astype(str), format="%Y%m") + pd.offsets.MonthEnd(0)
    df.index = dates
    return french_frame_to_level(df, entry)


def arch_french_bytes() -> tuple[bytes, str]:
    import importlib.metadata as md
    import importlib.resources as res

    import arch.data.frenchdata as fd  # noqa: F401

    pkg = res.files("arch.data.frenchdata")
    cand = [p for p in pkg.iterdir() if p.name.startswith("frenchdata.csv")]
    if not cand:
        raise FetchError("arch package does not contain frenchdata.csv*")
    return cand[0].read_bytes(), f"pypi://arch=={md.version('arch')}/arch/data/frenchdata/{cand[0].name}"


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------

PARSERS: dict[str, Callable[[bytes, dict], pd.Series]] = {
    "fred": parse_fred_csv,
    "french": parse_french_zip,
    "riksbank": parse_riksbank_json,
    "local_csv": parse_local_csv,
    "github_shiller": parse_shiller_tr,
    "github_h10": parse_h10_mirror,
    "github_aj": parse_aj_compilation,
    "pypi_arch_french": parse_arch_french,
}


def entry_url(entry: dict) -> str | None:
    p = entry["fetch"]["provider"]
    if p == "fred":
        return fred_url(entry)
    if p == "french":
        return french_url(entry)
    if p == "riksbank":
        return riksbank_url(entry)
    if p.startswith("github_"):
        return entry["fetch"]["url"]
    return None


def fetch_raw(entry: dict, store: RawStore, *, refresh: bool, offline: bool, manual_dir=None) -> RawFile:
    import os
    from pathlib import Path

    p = entry["fetch"]["provider"]
    if p == "local_csv":
        path = Path(manual_dir or "data/manual") / entry["fetch"]["file"]
        if not path.exists():
            raise FetchError(f"manual file not supplied: {path}")
        if entry["fetch"].get("require_sidecar"):
            validate_sidecar(path)
        return store.register_local(p, entry["id"], path)
    if p == "pypi_arch_french":
        cached = store.latest_cached(p, "frenchdata")
        if cached and not refresh:
            return cached
        try:
            b, src = arch_french_bytes()
        except Exception as e:
            if cached:
                return cached
            raise FetchError(f"arch package unavailable: {e}") from e
        return _store_bytes(store, p, "frenchdata", src, b)
    url = entry_url(entry)
    headers = {}
    if p == "riksbank" and os.environ.get("RIKSBANK_API_KEY"):
        headers["Ocp-Apim-Subscription-Key"] = os.environ["RIKSBANK_API_KEY"]
    key = entry["fetch"].get("cache_key", entry["id"])
    return store.fetch(p, key, url, refresh=refresh, offline=offline, headers=headers)


def _store_bytes(store: RawStore, provider: str, key: str, src: str, b: bytes) -> RawFile:
    """Store bytes that did not come over HTTP (e.g. from an installed package)."""
    import hashlib
    from datetime import datetime, timezone

    sha = hashlib.sha256(b).hexdigest()
    cached = store.latest_cached(provider, key)
    if cached and cached.sha256 == sha:
        return cached
    d = store._dir(provider, key)
    d.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    stamp = now.replace(":", "").replace("-", "")
    fname = f"{stamp}_{sha[:12]}.bin"
    (d / fname).write_bytes(b)
    (d / f"{stamp}_{sha[:12]}.meta.json").write_text(json.dumps(
        {"filename": fname, "url": src, "retrieved_at": now, "sha256": sha, "bytes": len(b),
         "previous_sha256": cached.sha256 if cached else None}, indent=2, sort_keys=True))
    store._log({"retrieved_at": now, "provider": provider, "key": key, "url": src, "status": "DOWNLOADED",
                "sha256": sha, "bytes": len(b)})
    return RawFile(d / fname, src, provider, key, sha, len(b), now, "DOWNLOADED")


def parse(entry: dict, raw: RawFile) -> pd.Series:
    return PARSERS[entry["fetch"]["provider"]](raw.read(), entry)
