# Fas 2: datavalidering (GitHub Actions)

Körningar: [41184283853](https://github.com/teknikpraktik/gem/actions/runs/41184283853) (första) och
körningen bakom commit `8337710` (andra). Genererat underlag: `generated/connectivity.md`,
`generated/data_quality.md`, `generated/raw_samples/`, `generated/diagnostics/`, `data/manifests/retrievals.jsonl`.

## Åtkomst från GitHub-hosted runner (ubuntu-latest)

| Källa | Endpoint | Resultat |
|---|---|---|
| Riksbanken SWEA | `/swea/v1/Series`, `/Observations/{id}/{from}/{to}` | **HTTP 200** |
| Ken French | `data_library.html`, `ftp/*.zip` | **HTTP 200** |
| FRED fredgraph.csv | `fred.stlouisfed.org/graph/fredgraph.csv?id=…` | **ingen respons** (curl 000 efter <1 s, `requests`: read timeout 60 s) |
| FRED officiellt API | `api.stlouisfed.org/fred/series?…` | **HTTP 400 utan nyckel = nåbart**. Fungerar med secret `FRED_API_KEY` (stöd finns, nyckeln maskeras i loggar). |

Slutsats: FRED:s CSV-endpoint svarar inte moln-IP:er. Det dokumenterade API:t är rätt väg, men
kräver en gratis nyckel som bara repo-ägaren kan skapa. Ingen User-Agent-förfalskning har använts.

## Dataklasser i fas 2-resultaten

| Klass | Serier |
|---|---|
| PRIMARY_SOURCE_VERIFIED | `RB_SEK_PER_USD` (Riksbanken SEKUSDPMI, SEK per USD, 1993-01 →) |
| PROXY | `RB_SSVX_3M` → `SE_CASH_SSVX_SYNTH_V1` (räntenotering transformerad till avkastning); Ken French `FF_US_MKT_TR`, `FF_DEV_EXUS_MKT_TR`, `FF_EUROPE_MKT_TR`, `FF_EMERGING_MKT_TR`, `FF_DEVELOPED_MKT_TR`, `FF_RF`, dagliga US/Europe/Dev-ex-US |
| THIRD_PARTY | alexjansenhome-kompileringen (endast `*_3P`-körningar), H.10-spegeln (endast korsvalidering), `arch`-snapshot (endast korsvalidering) |
| SYNTHETIC_TEST_ONLY | endast `tests/test_pipeline_integration.py`, aldrig i rapporter |

Varje `result.json` har ett `provenance`-block (strategiversion, serier, leverantör,
`retrieved_at`, sha256, dataperiod, kvalitet, klass). De svenska huvudkörningarna
(`SE_FF_SSVX`-gruppen) har svagaste klass **PROXY** och innehåller ingen tredjepartsdata.

## Kontroller per serie (urval; fullständigt i `generated/data_quality.md`)

| Serie | Period | Fynd | Åtgärd |
|---|---|---|---|
| Riksbanken `SETB3MBENCH` | 1983-01-03 → 2026-10 | Format `[{"date","value"}]`, procent. Nivåhopp sep–okt 1992 (+3,1 / −5,2 pp) | Verkliga (räntekrisen 1992). Behålls, fylls inte. |
| Riksbanken `SETB1MBENCHC` | 1983 → | Stale månadsslut 2001-12 | Bara korskontroll |
| Riksbanken `SETB6MBENCH` | 1984 → | Stale 2018-08, en saknad månad | Bara korskontroll |
| Riksbanken `SEKUSDPMI` | 1993-01 → 2026-10 | SEK per USD (3–15-vakten passerar). Inga luckor eller stale värden. | Används för all USD→SEK |
| SEKUSDPMI vs H.10 | 1993–2026 | Nivåskillnad i snitt 0,44 %, max 2,52 % (2011-11-30) | Tidsskillnad: Stockholmsfixing på förmiddagen, NY-notering kl 12. Den 30 nov 2011 föll dollarn på centralbankernas gemensamma åtgärd mellan de två noteringarna. CAGR-skillnad 0,01 pp. |
| Ken French Europe/Developed/Dev ex US | 1990-07 → 2026-09 | Filhuvud "created using the … Bloomberg database"; procent, −99.99 = saknas | Parsern hanterar formatet; inga luckor |
| Ken French Emerging (månad) | 1989-07 → 2026-09 | −27,2 % i okt 2008 (verklig) | – |
| Ken French Emerging (dag) | – | **404 – filen finns inte** | Katalogiserad UNUSABLE. REGIONAL_SEK saknar daglig EM och kan inte köras i scenario B/C. |
| Ken French US (dag) | 1926-07 → 2026-09 | – | Används i scenario B/C |

Senaste Ken French-observation: 2026-09. Biblioteket uppdateras månadsvis med cirka en
månads fördröjning. Det spelar ingen roll för backtestet, men det avgör den live-signal som
diskuteras i rapporten.

## Svensk cash: räntenotering ≠ avkastningsindex

`SE_CASH_SSVX_SYNTH_V1`:

* Månadsvis: `r_t = y_{t-1}/1200`, där y är SSVX 3m vid månadsslut (senaste notering i
  månaden, stale-kontroll 5 bankdagar).
* Dagligen (scenario B/C): `L(d1) = L(d0)·(1 + y(d0)/100·(d1−d0)/365)`. Föregående
  noterings ränta används, och luckor över 7 dagar bryter serien.
* Antaganden: enkel ränta, ACT/365 (växelkonventionen är ACT/360; skillnaden är cirka 1,4 %
  av räntenivån), inga kursrörelser under innehavstiden, ingen kreditrisk.

**Jämförelse mot OMRX: BLOCKED** (FRED kräver API-nyckel). Analysen (korrelation,
genomsnittlig avvikelse, maximal månadsavvikelse, antal ändrade GEM-signaler) körs
automatiskt när `FRED_API_KEY` finns.

## Reproducerbarhet

Refresh-körning och cachekörning på runnern gav identiska sha256 för samtliga
resultatfiler (378 resp. fler i andra körningen; se `generated/checksums.sha256`,
`generated/reproducibility.md`). Tester på runnern: 91 passed, 0 failed, 0 skipped.
