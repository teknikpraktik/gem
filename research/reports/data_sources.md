# Datakällor – inventering

Status per 2026-10-31. Maskinläsbar version: [`data/catalog.yaml`](../data/catalog.yaml).
Observerad täckning för cachade serier: [`generated/data_quality.md`](generated/data_quality.md).

## Viktig förutsättning: byggmiljöns nätverk

Byggmiljön kunde **bara** nå `raw.githubusercontent.com`, PyPI och npm. Alla primärkällor
nekades av nätverkspolicyn (HTTP 403 vid CONNECT, loggat i
`data/manifests/retrievals.jsonl`): `fred.stlouisfed.org`, `api.stlouisfed.org`,
`mba.tuck.dartmouth.edu`, `api.riksbank.se`, `www.riksbank.se`, `www.msci.com`,
`www.avanza.se`, `www.spglobal.com`, `www.optimalmomentum.com`, `indexes.nasdaq.com`,
`www.scb.se`, `query1.finance.yahoo.com`, `stooq.com`, `data-api.ecb.europa.eu`.

Det får tre konsekvenser:

1. Providers för FRED, Ken French och Riksbanken är skrivna mot de dokumenterade
   formaten och testade mot format-fixtures, men har **aldrig körts mot de riktiga
   endpoints**.
2. Dokumentation (indexdefinitioner, fondfakta, API-format) har bara kunnat läsas via
   utdrag ur webbsökningsresultat, inte genom att öppna sidorna. Sådana fakta är märkta
   *search extract* och ska verifieras igen.
3. Backtesten bygger på en tredjepartskompilering från GitHub (se nedan).

För att köra de öppna nivåerna behöver miljön tillåta minst: `fred.stlouisfed.org`,
`mba.tuck.dartmouth.edu`, `api.riksbank.se`. Lokalt på en vanlig dator finns ingen sådan
begränsning; där räcker `python -m gem.research --refresh`.

## Sammanställning

| Role | Source | Series | Start | TR? | Currency | Quality | Byggmiljö |
|---|---|---|---|---|---|---|---|
| US equities (exakt) | S&P DJI | S&P 500 TR (SPXT) | UNRESOLVED | ja | USD | LICENSE_RESTRICTED | manuell fil |
| US equities (3P) | alexjansenhome/GEM ← Yahoo | `SP500TR` | 1988-01 | ja | USD | EXPERIMENTAL | nåbar |
| US equities (3P, skarv) | alexjansenhome/GEM ← Ibbotson | Large Company Stocks | 1970-01 | ja | USD | EXPERIMENTAL | nåbar |
| US equities (öppen proxy) | Ken French | Mkt-RF + RF (CRSP VW) | 1926-07 | ja | USD | PROXY | blockerad |
| US equities (korskontroll) | Shiller via datahub | S&P Composite + utdelning | 1871-01 → 2023-06 | ja* | USD | PROXY | nåbar |
| ex-US equities (exakt) | MSCI | ACWI ex USA | UNRESOLVED | ja | USD | LICENSE_RESTRICTED | manuell fil |
| ex-US equities (3P) | alexjansenhome/GEM ← MSCI | ACWI ex USA gross | 1987-12 | ja | USD | EXPERIMENTAL | nåbar |
| ex-US (3P, skarv före 1988) | alexjansenhome/GEM ← MSCI | World ex USA gross (utan EM) | 1969-12 | ja | USD | EXPERIMENTAL | nåbar |
| ex-US (modern öppen proxy) | FRED ← Nasdaq | NASDAQNQGXUSLMN (Global ex US LM NTR) | 2001-03 | ja | USD | PROXY | blockerad |
| ex-US (öppen proxy, utan EM) | Ken French | Developed ex US Mkt-RF + RF | 1990-07 | ja | USD | EXPERIMENTAL | blockerad |
| T-bill hurdle (yield) | FRED | DTB3 (daglig), TB3MS (månadssnitt) | 1954 / 1934 | **nej** (yield) | USD | PROXY | blockerad |
| T-bill hurdle (3P) | alexjansenhome/GEM ← FRED | "3 MONTH" TR byggd av TB3MS | 1969-12 | ja (syntetisk) | USD | EXPERIMENTAL | nåbar |
| T-bill (öppen, realiserad) | Ken French | RF (1-månadsväxel) | 1926-07 | ja | USD | PROXY | blockerad (snapshot t.o.m. 2018-11 via PyPI `arch`) |
| US Agg (exakt) | Bloomberg | US Aggregate TR (LBUSTRUU) | 1976-01 | ja | USD | LICENSE_RESTRICTED | manuell fil |
| US Agg (3P) | alexjansenhome/GEM ← Morningstar | "AGG" | 1975-12 | ja | USD | EXPERIMENTAL | nåbar |
| Obligationer (3P, skarv före 1976) | alexjansenhome/GEM ← Ibbotson | Intermediate-Term Govt | 1969-12 → 1999-12 | ja | USD | EXPERIMENTAL | nåbar |
| Obligationer (öppen, syntetisk) | FRED | GS5 → par-obligation | 1953 | syntetisk | USD | EXPERIMENTAL | blockerad |
| Svensk hurdle | FRED ← Nasdaq | NASDAQOMRXTBILL | 2008-11-17 | ja | SEK | VERIFIED (källa) | blockerad |
| Svensk hurdle, full historik | Nasdaq | OMRXTBILL | UNRESOLVED | ja | SEK | LICENSE_RESTRICTED | manuell fil |
| Svensk hurdle före 2008 | Riksbanken SWEA | SETB3MBENCH (id = ASSUMPTION) → yield-transform | UNRESOLVED | **nej** (yield) | SEK | PROXY | blockerad |
| USD/SEK | Riksbanken SWEA | SEKUSDPMI (SEK per USD) | UNRESOLVED | – | SEK/USD | VERIFIED | blockerad |
| USD/SEK | FRED H.10 via datahub-spegel | DEXSDUS (SEK per USD) | 1971-01-04 | – | SEK/USD | VERIFIED (spegel) | nåbar |
| Global benchmark | MSCI | ACWI | UNRESOLVED | ja | USD | LICENSE_RESTRICTED | manuell fil |

\* Shiller använder månadsmedel av dagliga stängningskurser och interpolerad utdelning.
Mot S&P 500 TR vid månadsslut ger det 11,3 % årlig tracking error, så serien duger inte
till signaler, bara till korskontroll av nivåer och CAGR.

## Per behov

### USA equities – S&P 500 Total Return

* Det officiella indexet (S&P DJI) har inget öppet API och är licensierat.
  **LICENSE_RESTRICTED**, stöds via manuell export.
* FRED:s `SP500` är prisindex (inte TR) och har bara cirka 10 års historik.
  VERIFIED FROM SECONDARY SOURCE (datahub-README).
* FRED har `NASDAQNQUS500LCT` (Nasdaq US 500 Large Cap TR). Startdatum är oklart
  (2011 eller 2016 enligt motstridiga utdrag). UNRESOLVED.
* Tredjepartsfilens `SP500TR` (Yahoo ^SP500TR, 1988–2016) och Ibbotson Large Company
  (1970–2012) är identiska under överlappet (korrelation 1,0000, tracking error 0,01 %),
  vilket tyder på konsekvent ursprung.
* Ken French CRSP-marknaden är en bra långsiktig proxy (tracking error 2,4 % mot S&P 500
  TR, CAGR-skillnad 0,1 %-enheter) men är inte S&P 500.

### ex-USA equities – MSCI ACWI ex USA

* Definition: MSCI ACWI ex USA = utvecklade marknader utom USA plus tillväxtmarknader.
  Den gross-serie i tredjepartsfilen som är märkt MSCI har basvärde 100 per 1987-12-31.
  MSCI:s faktablad visar avkastning från 2000-12-29 (search extract). MSCI:s officiella
  basdatum för serien är UNRESOLVED.
* Licens: proprietär. MSCI:s end-of-day-verktyg tillåter visning och nedladdning för
  personligt bruk men inte vidaredistribution. **LICENSE_RESTRICTED**.
* Ingen öppen serie täcker exakt ACWI ex USA före 2001. Öppna alternativ:
  * `NASDAQNQGXUSLMN` (FRED, från 2001-03, DM+EM, annan indexleverantör): bästa moderna
    proxy, PROXY.
  * Ken French Developed ex US (från 1990-07): **saknar EM**, EXPERIMENTAL, och används
    bara i `GEM_PROXY_FF`.
* Före 1988 används MSCI World ex USA (utan EM). ACWI ex USA och World ex USA skiljer sig
  med 1,7 % årlig tracking error och 0,18 %-enheter CAGR 1988–2016.
* EAFE och Developed ex US har inte ersatt ACWI ex USA tyst någonstans. Varje sådan
  ersättning syns i run-ID och i noterna.

### US Treasury bills

* `DTB3`/`TB3MS` är **yield-serier** (diskontobasis), inga TR-index. Transformationen är
  dokumenterad och testad (metodik §3) och märkt PROXY.
* Ken French `RF` (Ibbotson/ICE 1-månadsväxel) är en realiserad avkastningsserie från
  1926. Den skiljer sig från 3m-TR med 0,16 % årlig tracking error 1970–2017.
* Tredjepartsfilens "3 MONTH"-kolumn är rekonstruerad: avkastningen = **samma månads**
  TB3MS / 1200 (korrelation 0,9997). Inget look-ahead för en månadsslutssignal, men en
  tidsapproximation.
* BIL (ETF) används inte. Det finns inget behov, och den får inte användas före sin start.

### US aggregate bonds

* Bloomberg US Aggregate är licensierat. Ingen fri lång TR-serie hittades.
  FRED:s ICE BofA-index omfattar bara företagsobligationer och har restriktiva villkor
  (endast internt bruk).
* Tredjepartsfilens "AGG" (Morningstar, 1976–2016) används. Före 1976: Ibbotson
  Intermediate Government, vilket är samma förlängning som Antonacci anger att han
  använde (search extract, optimalmomentum.com). Agg mot IT Govt 1976–1999: 1,9 % årlig
  tracking error.
* AGG (ETF, start 2003) används inte.

### Sverige

| Serie | Källa | ID | Status |
|---|---|---|---|
| OMRX Treasury Bill Index | FRED / Nasdaq | `NASDAQOMRXTBILL` | Från 2008-11-17 på FRED (search extract). Längre historik bara från Nasdaq; licensen är UNRESOLVED. |
| 3m statsskuldväxel | Riksbanken SWEA | `SETB3MBENCH` | **ASSUMPTION**: bekräfta via `/swea/v1/Series`. Yield, får inte användas som TR. |
| USD/SEK | Riksbanken SWEA | `SEKUSDPMI` | VERIFIED FROM PRIMARY SOURCE (API-FAQ, search extract): "hur många SEK för en enhet", alltså SEK per USD. |
| USD/SEK | FRED H.10 | `DEXSDUS` | SEK per USD, från 1971-01-04. Datahub-spegeln används nu. Den hade bytt kolumnnamn (`Value` → `Exchange rate`), vilket parsern hanterar. Inga orimliga hopp utöver devalveringarna 1982-10 (+18,7 %) och 1992-11 (+17,8 %), som är verkliga regimskiften. |
| KPI | SCB | PR0101 (KPI totalt) | Inte implementerat, behövs inte i fas 1. |

USD/SEK-konvention: hela koden använder SEK per USD. `fx.check_sek_per_usd` stoppar
värden utanför 3–15 (skulle fånga en inverterad USD-per-SEK-serie). Testat i
`tests/test_returns_fx_execution.py`.

## Tredjepartskompileringen (alexjansenhome/GEM)

`msci_all_gross.csv` (1969-12 → 2017-05) samlar MSCI-, Yahoo-, Morningstar-, Ibbotson-
och FRED-serier i en fil. Vem som sammanställt den och när, samt exakta indexvarianter,
är odokumenterat. Kvalitetskontrollerna fann:

* **Transkriptionsfel**: Ibbotson 30-dagars T-bill tappade första siffran i nov 1990, nov
  1991 och nov 1992 (0,366 i stället för 10,366). Kolumnen är märkt **UNUSABLE** och
  används inte. Felet tyder på att filen satts ihop för hand.
* Sista raden 2017-05-12 är ett halvt månadsvärde och flaggas stale.
* Ibbotson-data (SBBI) och Bloomberg/Morningstar-data är proprietära; filens
  vidaredistribution är oklar. Rådata cachas lokalt och checkas inte in, och inte heller
  månadsserier för benchmarkkörningar.

Därför används filen bara på nivåerna `STRICT_3P` och `EXTENDED_PROXY`, aldrig som
"verifierad GEM".

## Länkar (primärkällor, endast lästa via sökutdrag)

* FRED TB3MS / DTB3 / DEXSDUS / NASDAQOMRXTBILL / NASDAQNQGXUSLMN:
  <https://fred.stlouisfed.org/series/DTB3>, <https://fred.stlouisfed.org/series/NASDAQOMRXTBILL>,
  <https://fred.stlouisfed.org/series/NASDAQNQGXUSLMN>
* Ken French Data Library: <https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html>
* Riksbanken API-FAQ: <https://www.riksbank.se/en-gb/statistics/interest-rates-and-exchange-rates/retrieving-interest-rates-and-exchange-rates-via-api/faq--the-api-for-interest-rates-and-exchange-rates/>
* OMRX-metodik: <https://indexes.nasdaq.com/docs/Methodology_OMRX.pdf>, historik:
  <https://indexes.nasdaq.com/Index/History/OMRXTBILL>
* MSCI end-of-day: <https://www.msci.com/end-of-day-history>
* ICE-villkor på FRED: <https://fred.stlouisfed.org/data/BAMLCC0A0CMTRIV>
* Speglar: <https://github.com/datasets/exchange-rates>, <https://github.com/datasets/s-and-p-500>,
  <https://github.com/alexjansenhome/GEM>
