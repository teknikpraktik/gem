"""Probe candidate NAV sources for the Avanza funds and store the REAL responses.

    python -m gem.navprobe            # writes reports/generated/nav_probe/

Purpose: decide, from actual responses (not guesses), which source can feed the
FundNavProvider. Candidates are tried in the priority order of the phase-3 brief:
official Avanza / Avanza Fonder pages first, then Morningstar pages, and only
last the undocumented www.avanza.se JSON endpoints (used by avanza.se itself;
not an official API - OPTIONAL provider only). Requests are few, sequential
and unauthenticated; nothing is retried aggressively.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

UA = "gem-research/0.1 (research; NAV source probe)"
ROOT = Path(__file__).resolve().parents[2]

# orderbook ids seen in official avanza.se fund URLs (phase 1/2 search extracts)
FUNDS = {
    "AVANZA_USA": {"isin": "SE0012741163", "orderbook": "1025150", "slug": "avanza-usa"},
    "AVANZA_EUROPA": {"isin": "SE0013718699", "orderbook": None, "slug": "avanza-europa"},
    "AVANZA_EM": {"isin": "SE0012454338", "orderbook": "944976", "slug": "avanza-emerging-markets"},
    "AVANZA_RANTA_KORT": {"isin": "SE0021021425", "orderbook": "1684019", "slug": "avanza-ranta-kort"},
    "AVANZA_GLOBAL": {"isin": "SE0011527613", "orderbook": None, "slug": "avanza-global"},
}

A = "https://www.avanza.se"


def candidates(fid: str, f: dict) -> list[tuple[str, str, str, dict | None]]:
    """(label, method, url, json_body)"""
    out = [
        ("avanza_fonder_site", "GET", "https://www.avanzafonder.se/", None),
        ("investors_avanza_fonder", "GET", "https://investors.avanza.se/sv/om-avanza/avanza-fonder/", None),
        ("search_filtered", "POST", f"{A}/_api/search/filtered-search",
         {"query": f["isin"], "searchFilter": {"types": ["FUND"]}, "pagination": {"from": 0, "size": 5}}),
        ("search_global", "GET", f"{A}/_api/search/global-search?query={f['isin']}", None),
    ]
    ob = f["orderbook"]
    if ob:
        today = f"{datetime.now(timezone.utc):%Y-%m-%d}"
        out += [
            ("fund_page_html", "GET", f"{A}/fonder/om-fonden.html/{ob}/{f['slug']}", None),
            ("fund_guide", "GET", f"{A}/_api/fund-guide/guide/{ob}", None),
            ("price_chart_stock_all_day", "GET", f"{A}/_api/price-chart/stock/{ob}?timePeriod=all_time&resolution=day", None),
            ("price_chart_fund_all", "GET", f"{A}/_api/price-chart/fund/{ob}?timePeriod=all_time", None),
            ("fund_guide_chart_all", "GET", f"{A}/_api/fund-guide/chart/{ob}/all_time", None),
            ("fund_guide_chart_range_raw", "GET", f"{A}/_api/fund-guide/chart/{ob}/2015-01-01/{today}?raw=true", None),
            ("fund_guide_chart_range", "GET", f"{A}/_api/fund-guide/chart/{ob}/2015-01-01/{today}", None),
            ("fund_guide_chart_recent_raw", "GET", f"{A}/_api/fund-guide/chart/{ob}/2026-09-01/{today}?raw=true", None),
        ]
    return out


def find_orderbook(doc, isin: str):
    """Walk a search response and return the id of the hit whose isin matches (schema-agnostic)."""
    stack = [doc]
    while stack:
        x = stack.pop()
        if isinstance(x, dict):
            if str(x.get("isin", "")).upper() == isin:
                for k in ("orderBookId", "orderbookId", "orderbook_id", "id"):
                    if x.get(k):
                        return str(x[k])
            stack.extend(x.values())
        elif isinstance(x, list):
            stack.extend(x)
    return None


def summarize(resp: requests.Response) -> dict:
    ct = resp.headers.get("content-type", "")
    info = {"status": resp.status_code, "content_type": ct, "bytes": len(resp.content),
            "final_url": resp.url}
    if "json" in ct:
        try:
            doc = resp.json()
            if isinstance(doc, dict):
                info["json_keys"] = sorted(doc.keys())[:60]
                for k in ("nav", "navDate", "isin", "name", "startDate", "currency", "orderbookId"):
                    if k in doc:
                        info[k] = doc[k]
                for k, v in doc.items():
                    if isinstance(v, list) and v:
                        info[f"list:{k}"] = {"len": len(v), "first": v[0], "last": v[-1]}
            elif isinstance(doc, list):
                info["json_list_len"] = len(doc)
                info["first"] = doc[0] if doc else None
        except ValueError:
            pass
    return info


def main() -> int:
    out = ROOT / "reports" / "generated" / "nav_probe"
    out.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/json, text/html;q=0.9"})
    rows = []
    seen = set()
    for fid, f in FUNDS.items():
        if not f["orderbook"]:
            try:
                r = s.post(f"{A}/_api/search/filtered-search", timeout=30,
                           json={"query": f["isin"], "searchFilter": {"types": ["FUND"]}, "pagination": {"from": 0, "size": 5}})
                f["orderbook"] = find_orderbook(r.json(), f["isin"])
                print(f"{fid:18s} orderbook resolved via search: {f['orderbook']}")
            except Exception as e:  # noqa: BLE001
                print(f"{fid:18s} orderbook search failed: {e}")
            time.sleep(1.0)
        for label, method, url, body in candidates(fid, f):
            if url in seen and label in ("avanza_fonder_site", "investors_avanza_fonder"):
                continue
            seen.add(url)
            t = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            try:
                r = s.request(method, url, json=body, timeout=30)
                info = summarize(r)
                (out / f"{fid}__{label}.txt").write_text(
                    f"retrieved_at: {t}\n{method} {url}\nbody: {json.dumps(body)}\n"
                    f"{json.dumps(info, indent=1, default=str)}\n---\n{r.text[:6000]}\n")
            except Exception as e:  # noqa: BLE001
                info = {"status": "ERROR", "error": f"{type(e).__name__}: {str(e)[:200]}"}
            rows.append({"fund": fid, "label": label, "url": url, "retrieved_at": t, **info})
            print(f"{fid:18s} {label:28s} {info.get('status')} {info.get('content_type', '')[:30]} {info.get('bytes', '')}")
            time.sleep(1.0)
    (out / "summary.json").write_text(json.dumps(rows, indent=1, default=str))
    lines = ["# NAV source probe (generated)", "", "| fund | candidate | status | content-type | bytes | nav | navDate |",
             "|---|---|---|---|---:|---|---|"]
    for r in rows:
        lines.append(f"| {r['fund']} | {r['label']} | {r.get('status')} | {str(r.get('content_type', ''))[:30]} | "
                     f"{r.get('bytes', '')} | {r.get('nav', '')} | {r.get('navDate', '')} |")
    (out / "summary.md").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
