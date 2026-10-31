#!/usr/bin/env bash
# Fas 2 – full körning på riktig data. Körs från en maskin som når FRED, Riksbanken och
# Ken French (t.ex. din egen dator). Gör: nätverkskontroll -> tester -> refresh-körning ->
# cache-körning -> checksumjämförelse -> commit av rapporter och manifest (ingen push).
set -euo pipefail
cd "$(dirname "$0")/.."                       # research/
BRANCH=claude/gem-research-engine
[ "$(git branch --show-current)" = "$BRANCH" ] || { echo "Byt till $BRANCH först (git switch $BRANCH)"; exit 1; }

python3 -m venv .venv
. .venv/bin/activate
pip install -q --upgrade pip
pip install -q -e ".[test]" arch

echo "== 1. Nätverk (samma Python/requests som motorn) =="
python - <<'PY'
import requests, sys
urls = {
  "FRED":       "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQOMRXTBILL",
  "Riksbanken": "https://api.riksbank.se/swea/v1/Observations/SETB3MBENCH/2024-01-01/2024-01-31",
  "Ken French": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Europe_3_Factors_CSV.zip",
}
bad = 0
for k, u in urls.items():
    try:
        r = requests.get(u, timeout=30, headers={"User-Agent": "gem-research/0.1"})
        print(f"{k:11s} HTTP {r.status_code}  {len(r.content)} bytes  {r.headers.get('content-type','')}")
        bad += r.status_code != 200
    except Exception as e:
        print(f"{k:11s} FEL {type(e).__name__}: {str(e)[-150:]}"); bad += 1
sys.exit(1 if bad else 0)
PY

echo "== 2. Tester =="
python -m pytest -q -rs | tail -3

echo "== 3. Körning 1: refresh från källor =="
python -m gem.research --refresh
sha256sum reports/generated/summary.csv reports/generated/phase2.json > /tmp/gem_run1.sha
cat /tmp/gem_run1.sha

echo "== 4. Körning 2: endast cache =="
python -m gem.research --offline
sha256sum -c /tmp/gem_run1.sha && echo "REPRODUCERBART: identiska checksummor"

echo "== 5. Sammanfattning =="
sed -n '/## 1. Source access/,/Failed endpoints/p' reports/generated/phase2.md
sed -n '/## 4. GEM_ORIGINAL vs GEM_SEK/,$p' reports/generated/phase2.md | head -80

echo "== 6. Commit (rådata checkas inte in; manifest med checksummor gör det) =="
git add reports data/manifests
git commit -q -m "Phase 2: results on primary-source data (local run)" && echo "Klart. Granska och kör: git push"
