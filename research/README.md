# GEM research engine (fas 1)

Forskningsmotor för en framtida svensk tjänst med månadsvis signal baserad på
Global Equities Momentum (GEM). **Ingen frontend, ingen handel, inga konton.**

Slutsatser och beslut: fas 1 [`reports/final_report.md`](reports/final_report.md),
fas 2 [`reports/phase2_report.md`](reports/phase2_report.md), fas 2b (OMRX-verifiering och
investerbar REGIONAL_SEK på Avanza-NAV) [`reports/phase2b_live_report.md`](reports/phase2b_live_report.md).

Forskningskörningen sker i GitHub Actions: workflow **GEM phase 2 research**
(`.github/workflows/gem-phase2-research.yml`), startas under *Actions → GEM phase 2 research →
Run workflow*. Valfria secrets: `FRED_API_KEY`, `RIKSBANK_API_KEY`.

## Snabbstart

```bash
cd research
pip install -e '.[test]'           # pandas, numpy, PyYAML, requests, pytest
pip install arch                   # valfritt: Ken French-snapshot för korsvalidering
python -m pytest                   # 105 tester (inkl. end-to-end på syntetisk data)
python -m gem.research             # hämta/cacha -> validera -> backtesta -> rapporter
python -m gem.research --offline   # bara cache, ingen nätverkstrafik
python -m gem.research --refresh   # ladda ned allt nåbart igen (revisioner loggas)
```

Licensierade serier (S&P 500 TR, MSCI ACWI ex USA, MSCI ACWI, Bloomberg US Agg,
OMRX full historik) läggs manuellt som `data/manual/<fil>.csv` med kolumnerna
`date,value`. Filnamn anges i `data/catalog.yaml` (`fetch.file`). De hämtas aldrig
automatiskt och checkas aldrig in.

## Modeller (strikt separerade)

| Strategy ID | Vad | Status |
|---|---|---|
| `GEM_ORIGINAL` | Antonacci GEM i USD: S&P 500 TR, MSCI ACWI ex USA, 3m T-bills, US Agg | Motor klar. Körd på tredjepartsdata (`*_3P`). Strikt körning blockerad (licensdata saknas). |
| `GEM_PROXY_FF` | Öppna proxyer (CRSP US, FF Developed ex US, syntetisk 5y-obligation, FF RF) | Motor klar, data blockerad i byggmiljön |
| `GEM_SEK` | Samma regel, SEK-ben, svensk kort ränta som hurdle/defensiv. **Inte GEM.** Run-ID: `GEM_SEK_OPEN_OMRX_V1`, `GEM_SEK_OPEN_SSVXSYNTH_V1`, `GEM_SEK_3P_SSVXSYNTH_V1`, `GEM_SEK_STRICT_V1` | Implementerad, BLOCKED (svensk räntedata) |
| `REGIONAL_SEK` | Bästa av USA/Europa/EM i SEK mot svensk hurdle. **Inte GEM.** Run-ID: `REGIONAL_SEK_FF_PROXY_OMRX_V1`, `REGIONAL_SEK_FF_PROXY_SSVXSYNTH_V1` | Implementerad, BLOCKED |
| `BUY_HOLD_GLOBAL`, `STATIC_70_30` | Benchmarks (MSCI ACWI, 70/30 ACWI/Agg) | Blockerade (MSCI ACWI saknas) |
| `BUY_HOLD_US/EXUS/US_AGG`, `STATIC_70_30_US` | Benchmarks på samma tredjepartsdata som GEM | Körda |

Regeln ändras aldrig: 12 månaders fönster (`strategies.LOOKBACK_MONTHS`), 100 % i en
tillgång, `R_US <= R_TBILL` → obligationer, `R_US >= R_EXUS` → USA, annars ex-US.

## Struktur

```text
research/
  src/gem/
    strategies.py   ren beslutslogik (ingen datakunskap)
    returns.py      månadsslut, avkastning, 12m-avkastning, yield->avkastning
    fx.py           USD->SEK (SEK per USD), konventionsvakt
    execution.py    månadskonventioner, fond-cutoff, fondstartsvakt
    daily.py        explicit tidsmodell på dagsdata: scenario A/B/C, handelsregler per fond
    analysis.py     signalöverensstämmelse GEM_ORIGINAL vs GEM_SEK
    implementation.py  implementationsgap + investerbar REGIONAL_SEK på fond-NAV
    nav.py          FundNavProvider-interface (manuell export, Avanza-endpoint)
    live.py         live-signal REGIONAL_SEK (ren funktion, samma kod i backtest)
    navprobe.py     probe av NAV-källor;  navlag.py  mätning av NAV-publicering
    data/avanza.py  avanza.se fund-guide JSON (UNDOCUMENTED_ENDPOINT)
    backtest.py     generisk månadsmotor, kostnader, NO_SIGNAL-hantering
    metrics.py      CAGR, vol, Sharpe, Sortino, Calmar, drawdowns, turnover ...
    validation.py   datakvalitet + korsvalidering mellan källor
    panel.py        katalogserier -> avkastnings-/momentumpaneler, skarvar, FX
    runs.py         körningsdefinitioner per nivå (STRICT, STRICT_3P, EXTENDED_PROXY, SWEDISH, BENCHMARK, DIAGNOSTIC)
    research.py     pipeline (python -m gem.research)
    reporting.py    genererade rapporter
    data/base.py    rå-cache med sha256 + manifest
    data/providers.py  FRED, Ken French, Riksbanken, lokal CSV, GitHub-speglar
  data/
    catalog.yaml                 alla serier, proveniens, kvalitet, licens
    investable_instruments.yaml  Avanza-fonder (forskning, ej handel)
    manifests/retrievals.jsonl   hämtlogg (retrieved_at, url, sha256, status)
    raw/ processed/ manual/      ej incheckade
  reports/
    final_report.md  methodology.md  data_sources.md  reproduction.md
    swedish_and_avanza.md  open_issues.md
    generated/       skrivs av pipelinen – redigera inte för hand
  tests/
```

## Datapolicy

* Ingen serie används om den inte finns i `data/catalog.yaml`.
* Inga luckor fylls. Saknad/inaktuell data → `NO_SIGNAL`, och backtestet stoppar om en
  hållen tillgång saknar avkastning.
* Fond-NAV används aldrig före fondstart (`execution.assert_not_before_launch`).
* Tredjeparts-/proxydata märks i run-ID (`_3P`, `_PROXY`, `_FF`) och i rapporterna.
