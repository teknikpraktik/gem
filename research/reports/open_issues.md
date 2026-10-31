# Olösta frågor

Prioritet: **P1** blockerar GO, **P2** behövs före riktiga pengar, **P3** förbättring.

## Data och åtkomst

| # | Prio | Fråga | Status / nästa steg |
|---|---|---|---|
| 1 | P1 | Byggmiljön når inte FRED, Ken French eller Riksbanken | Tillåt `fred.stlouisfed.org`, `mba.tuck.dartmouth.edu`, `api.riksbank.se` i miljöns nätverksinställningar, eller kör `python -m gem.research --refresh` lokalt. Providers är otestade mot riktiga svar. |
| 2 | P1 | Ingen svensk hurdle-serie har hämtats | `NASDAQOMRXTBILL` (FRED, från 2008-11-17) är förstahandsval. Pre-2008: Nasdaqs fulla historik (licens?) eller syntetisk SSVX. |
| 3 | – | Riksbankens serie-ID för 3m SSVX | **Löst i fas 2**: `SETB3MBENCH` (från 1983-01-03), även `SETB1MBENCHC`, `SETB6MBENCH` – Riksbankens seriesida (sökutdrag). |
| 4 | P1 | Licens för S&P 500 TR, MSCI ACWI ex USA, MSCI ACWI, Bloomberg US Agg | Behövs för `GEM_ORIGINAL_STRICT` och benchmarkarna. Alternativ: dokumenterade öppna proxyer (`GEM_PROXY_FF`, Nasdaq-serier på FRED) med uttalad avvikelse. För en publik tjänst krävs sannolikt licens för att visa indexvärden. |
| 5 | P2 | Tredjepartsfilen (alexjansenhome/GEM) har okänd proveniens och slutar 2016-12 | Ersätt med primärdata. En kolumn hade transkriptionsfel (UNUSABLE). |
| 6 | P2 | MSCI ACWI ex USA: gross eller net, officiellt basdatum | UNRESOLVED |
| 7 | P2 | `NASDAQNQUS500LCT` startdatum (2011 eller 2016) och om FRED trunkerar Nasdaq-historik | Kontrollera på FRED |
| 8 | P2 | Ken French: exakta filnamn för Europe/Emerging, EM-startdatum | Filnamn är antaganden |
| 9 | P3 | ICE BofA-villkor på FRED (endast internt bruk) | Används inte |
| 10 | P3 | KPI (SCB) för reala mått | Inte implementerat |

## Metod

| # | Prio | Fråga | Status |
|---|---|---|---|
| 11 | P1 | Referensens antal byten och exakta pre-1988-ex-US-serie och 1974–75-obligationsdata | Kräver bokens appendix. Gapet på −0,63 pp i CAGR kan därför inte fördelas på orsaker. |
| 12 | P2 | Referensens MDD-episod (−22,72 %) | Okänd. Vår MDD är −19 % (2000). Planera för minst −23 %. |
| 13 | P2 | Exekvering med dagsdata (T+1–T+3) i stället för två månadsgränser | Kräver dagliga TR-serier. Motorn har konventionen klar för fonder (`FundOrderModel`). |
| 14 | P2 | Kostnadsscenario 10 bp/sida är illustrativt | Kalibrera mot Avanza: courtage 0 för fonder, men spread/valutaväxling för utländska fonder, tid utanför marknaden, fondavgift och tracking difference. |
| 15 | P2 | Lång relativ underprestation mot S&P 500 | 94–165 månader beroende på konvention (t.ex. 2009-02 → 2016-12). Påverkar hur tjänsten ska kommunicera förväntningar. |
| 16 | P3 | ISK-modellering | Utanför fas 1 |

## Avanza

| # | Prio | Fråga |
|---|---|---|
| 17 | P1 | Ingen Avanza-fond för GEM:s ex-US-ben (ACWI ex USA) eller för US Agg |
| 18 | P2 | Verifiera ISIN (Europa nu SE0013718699, sekundärkälla), startdatum (Global 2018-08-27; USA dec 2019; Ränta Kort exakt dag), avgifter (Global: 0,05–0,11 %), stopptider per fond, likviddagar sälj→köp |
| 19 | P2 | Mät tracking difference: fond-NAV mot signalindex (Morningstar PAB-index mot S&P/MSCI-regionindex) från fondstart |
| 20 | P2 | Ränta Kort (säkerställda obligationer) mot OMRX T-bill: skillnad i avkastning och risk |
| 21 | P3 | Odokumenterade Avanza-endpoints som valfri NAV-provider (inte byggd, får aldrig bli kritisk) |

## Tillägg fas 2

| # | Prio | Fråga |
|---|---|---|
| 22 | P1 | Nätverket blockerar fortfarande FRED, Riksbanken och Ken French (403) – ingen svensk körning möjlig |
| 23 | P1 | OMRX: basdatum, ackumulerande eller inte, villkor för Nasdaqs fulla historik |
| 24 | P2 | Scenario B antar att köporder kan läggas när försäljningens NAV satts (utan att vänta på likvid) – verifiera mot Avanza |
| 25 | P2 | Ken French filnamn för Europa/EM (månad och dag) |
| 26 | P2 | Bryttider för Avanza Europa och Ränta Kort, total avgift för Europa och Global |
| 27 | P2 | Fonderna antas vara ackumulerande andelsklasser |
| 28 | P3 | Svensk obligationsserie för en äkta 70/30 i SEK (nu 30 % svensk cash) |
