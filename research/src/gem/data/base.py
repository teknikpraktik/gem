"""Raw data store with provenance.

Every download is cached byte-for-byte under data/raw/<provider>/<key>/ and
logged to data/manifests/retrievals.jsonl with:
  retrieved_at (UTC ISO), url, provider, key, sha256, bytes, status.

Reproducibility rule: by default the pipeline uses the most recent cached
file (no network). `refresh=True` downloads again; if the new bytes differ
from the previous cached version, the change is logged (see revisions.py) so
silent source revisions become visible.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import requests

USER_AGENT = "gem-research/0.1 (research; contact: repository owner)"


@dataclass(frozen=True)
class RawFile:
    path: Path
    url: str
    provider: str
    key: str
    sha256: str
    bytes: int
    retrieved_at: str
    status: str  # DOWNLOADED | CACHED | LOCAL

    def read(self) -> bytes:
        return self.path.read_bytes()


class FetchError(RuntimeError):
    pass


RETRY_STATUS = {429, 500, 502, 503, 504}


def _get_with_retry(url: str, headers: dict, timeout: int, attempts: int = 4, sleep=None):
    """GET with bounded retries on rate limiting / transient server errors.

    Honours Retry-After (seconds) when present, otherwise exponential backoff
    (2, 4, 8 s). TLS verification is never disabled.
    """
    import time as _time

    sleep = sleep or _time.sleep
    resp = None
    for i in range(attempts):
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code not in RETRY_STATUS or i == attempts - 1:
            return resp
        ra = resp.headers.get("Retry-After", "")
        wait = float(ra) if ra.replace(".", "", 1).isdigit() else 2 ** (i + 1)
        sleep(min(wait, 60))
    return resp


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)[:120]


class RawStore:
    def __init__(self, root: Path, manifest_dir: Path):
        self.root = Path(root)
        self.manifest_dir = Path(manifest_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = self.manifest_dir / "retrievals.jsonl"

    def _dir(self, provider: str, key: str) -> Path:
        return self.root / _safe(provider) / _safe(key)

    def latest_cached(self, provider: str, key: str) -> RawFile | None:
        d = self._dir(provider, key)
        if not d.exists():
            return None
        metas = sorted(d.glob("*.meta.json"))
        if not metas:
            return None
        m = json.loads(metas[-1].read_text())
        p = d / m["filename"]
        b = p.read_bytes()
        if _sha256(b) != m["sha256"]:
            raise FetchError(f"checksum mismatch in cache {p}")
        return RawFile(p, m["url"], provider, key, m["sha256"], len(b), m["retrieved_at"], "CACHED")

    def _log(self, rec: dict) -> None:
        with self.manifest.open("a") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")

    def fetch(self, provider: str, key: str, url: str, *, refresh: bool = False, offline: bool = False,
              timeout: int = 60, headers: dict | None = None) -> RawFile:
        cached = self.latest_cached(provider, key)
        if cached is not None and not refresh:
            return cached
        if offline:
            if cached is not None:
                return cached
            raise FetchError(f"offline and no cache for {provider}/{key}")
        h = {"User-Agent": USER_AGENT, **(headers or {})}
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            resp = _get_with_retry(url, h, timeout)
            resp.raise_for_status()
        except Exception as e:  # network policy, DNS, HTTP error ...
            self._log({"retrieved_at": now, "provider": provider, "key": key, "url": url,
                       "status": "FAILED", "error": str(e)[:300]})
            if cached is not None:
                return cached
            raise FetchError(f"{provider}/{key}: {e}") from e
        b = resp.content
        sha = _sha256(b)
        if cached is not None and cached.sha256 == sha:
            self._log({"retrieved_at": now, "provider": provider, "key": key, "url": url,
                       "status": "UNCHANGED", "sha256": sha, "bytes": len(b)})
            return cached
        d = self._dir(provider, key)
        d.mkdir(parents=True, exist_ok=True)
        ext = os.path.splitext(url.split("?")[0])[1][:6] or ".bin"
        stamp = now.replace(":", "").replace("-", "")
        fname = f"{stamp}_{sha[:12]}{ext}"
        (d / fname).write_bytes(b)
        meta = {"filename": fname, "url": url, "retrieved_at": now, "sha256": sha, "bytes": len(b),
                "previous_sha256": cached.sha256 if cached else None}
        (d / f"{stamp}_{sha[:12]}.meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))
        self._log({"retrieved_at": now, "provider": provider, "key": key, "url": url, "status": "DOWNLOADED",
                   "sha256": sha, "bytes": len(b), "previous_sha256": meta["previous_sha256"]})
        return RawFile(d / fname, url, provider, key, sha, len(b), now, "DOWNLOADED")

    def register_local(self, provider: str, key: str, path: Path) -> RawFile:
        """Manually supplied file (e.g. licensed MSCI/S&P/Nasdaq export)."""
        b = Path(path).read_bytes()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        rf = RawFile(Path(path), f"file://{Path(path).resolve()}", provider, key, _sha256(b), len(b), now, "LOCAL")
        self._log({**{k: str(v) for k, v in asdict(rf).items()}, "status": "LOCAL"})
        return rf
