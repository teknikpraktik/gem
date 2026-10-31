# Slutrapport fas 1: GEM-researchmotor

Datum: 2026-10-31. Kod: `research/`. Alla siffror kommer från `python -m gem.research`
(se `generated/summary.csv`); två körningar på samma cache ger identiskt resultat.

## 1. Executive summary

**Fungerar**

* Deterministisk strategimotor för `GEM_ORIGINAL`, `GEM_SEK`, `REGIONAL_SEK` och
  benchmarks. Regeln är enhetstestad inklusive likhetsfall, saknad och inaktuell data
  (65 tester).
* Generisk backtestmotor med explicita datum (signal → data tillgänglig → order →
  exekvering), två exekveringskonventioner, kostnader, `NO_SIGNAL` utan gissning och
  test som visar att framtida data inte påverkar historiska signaler.
* Datakatalog med 34 serier, proveniens, licens och kvalitetsstatus. Rå-cache med
  sha256 och hämtlogg.
* Ett historiskt GEM-backtest 1971–2016 som reproducerar Antonaccis publicerade
  1974–2013-resultat inom 0,6 pp CAGR med samma volatilitet och regimbild.
* Datakvalitetskontrollerna hittade ett verkligt fel i källdatan (transkriptionsfel i en
  T-bill-kolumn) och rekonstruerade hur en annan kolumn byggts.

**Fungerar inte (ännu)**

* Byggmiljön nådde inga primärkällor (FRED, Ken French, Riksbanken, MSCI, Avanza).
  Providers för dessa är skrivna och formattestade men **aldrig körda mot riktiga
  svar**.
* Alla körda GEM-backtest bygger på en tredjepartskompilering från GitHub med oklar
  proveniens och licens. Den slutar 2016-12.
* **Inget svenskt backtest** (`GEM_SEK`, `REGIONAL_SEK`) har körts: svensk räntedata
  saknas.
* `GEM_ORIGINAL_STRICT`, `GEM_PROXY_FF`, `BUY_HOLD_GLOBAL` och `STATIC_70_30` är
  blockerade. Orsak per serie finns i `generated/backtests.md`.

**Hur långt tillbaka**: med nuvarande data 1971-01 → 2016-12 (proxy) respektive
1989-02 → 2016-12 (exakta indexdefinitioner, tredjepartsdata). Med öppna primärkällor
bedöms 1927 → idag möjligt för US/T-bill-delen (Ken French), cirka 1991 → idag för
ex-US/regioner, och 2009 → idag för SEK-modeller med verifierad OMRX-hurdle.

## 2. Datakällor

| Role | Source | Series | Start | TR? | Currency | Quality |
|---|---|---|---|---|---|---|
| US equities | S&P DJI (licens) | S&P 500 TR | – | ja | USD | LICENSE_RESTRICTED (ej tillgänglig) |
| US equities (använd) | GitHub-kompilering ← Yahoo / Ibbotson | SP500TR / Large Co. | 1988 / 1970 | ja | USD | EXPERIMENTAL |
| ex-US equities | MSCI (licens) | ACWI ex USA | – | ja | USD | LICENSE_RESTRICTED (ej tillgänglig) |
| ex-US (använd) | GitHub-kompilering ← MSCI | ACWI ex USA gross / World ex USA (före 1988) | 1988 / 1970 | ja | USD | EXPERIMENTAL |
| T-bill hurdle (använd) | GitHub-kompilering ← FRED TB3MS | 3m-TR (syntetisk) | 1970 | syntetisk | USD | EXPERIMENTAL |
| T-bill (öppen) | FRED DTB3 / Ken French RF | yield / 1m-avkastning | 1954 / 1926 | nej / ja | USD | PROXY (blockerad) |
| US Agg (använd) | GitHub-kompilering ← Morningstar / Ibbotson IT Govt | AGG / IT Govt (före 1976) | 1976 / 1970 | ja | USD | EXPERIMENTAL |
| Svensk hurdle | FRED ← Nasdaq | NASDAQOMRXTBILL | 2008-11 | ja | SEK | VERIFIED-källa (blockerad) |
| Svensk hurdle före 2008 | Riksbanken | 3m SSVX (ID ej bekräftat) | ? | nej | SEK | PROXY (blockerad) |
| USD/SEK (använd) | FRED H.10 via datahub-spegel | DEXSDUS | 1971 | – | SEK/USD | VERIFIED (spegel) |
| USD/SEK | Riksbanken | SEKUSDPMI | ? | – | SEK/USD | VERIFIED (blockerad) |
| Global benchmark | MSCI (licens) | ACWI | – | ja | USD | LICENSE_RESTRICTED (ej tillgänglig) |

Detaljer, länkar och verifieringsnivåer: `data_sources.md`.

## 3. GEM reproduction

Referens: Antonacci (2014), 1974–2013. Siffrorna är citerade via sekundärkällor.

| Metric | Reference | Vår (IDEALIZED) | Diff | Vår (NEXT_MONTH, utan look-ahead) |
|---|---:|---:|---:|---:|
| CAGR | 17,43 % | 16,80 % | −0,63 pp | 15,84 % |
| Volatilitet | 12,64 % | 12,49 % | −0,15 pp | 12,66 % |
| Max drawdown | −22,72 % | −18,96 % | +3,76 pp | −19,19 % |
| Sharpe | 0,87 | 0,90 | +0,03 | 0,82 |
| Byten | ? | 56 (1,4/år) | – | 56 |
| 1973–74 | "+20 %" | +21,3 % | ≈ | +22,7 % |

Byte av ett databen i taget ger CAGR 16,27–17,02 %. Gapet ligger alltså inom
osäkerheten från val av dataserier, men kan inte fördelas exakt på orsaker utan bokens
dataappendix. Inget har justerats mot referensen. Detaljer: `reproduction.md`.

Övriga GEM-resultat (0 kostnad, NEXT_MONTH_CLOSE):

| Körning | Period | CAGR | Vol | MDD | Sharpe | Byten/år | S&P 500 TR samma period |
|---|---|---:|---:|---:|---:|---:|---|
| GEM_ORIGINAL_STRICT_3P | 1989-03 → 2016-12 | 13,41 % | 12,10 % | −19,19 % | 0,86 | 1,08 | 10,00 %, MDD −50,95 % |
| GEM_ORIGINAL_PROXY_3P | 1971-02 → 2016-12 | 15,62 % | 12,62 % | −19,19 % | 0,84 | 1,37 | 10,37 %, MDD −50,95 % |

Kostnad 10 bp/sida: −0,2 till −0,3 pp CAGR. Exekveringskonvention: −0,2 till −1,0 pp.
Längsta relativa underprestation mot S&P 500: 94 månader (2009-02 → 2016-12,
IDEALIZED, STRICT_3P) och upp till 165 månader beroende på konvention och period.

## 4. Swedish models

Ingen svensk modell kan backtestas trovärdigt i dag, eftersom svensk hurdle-/räntedata
saknas. När FRED är nåbart blir `GEM_SEK` med verifierad OMRX-hurdle möjlig från cirka
2009-12 (kort historik, i stort sett en USA-ledd regim). 1990 → idag kräver Nasdaqs
fulla OMRX-historik (licens UNRESOLVED) eller en syntetisk SSVX-hurdle märkt PROXY.
`REGIONAL_SEK` kan med Ken French-regioner och syntetisk hurdle sannolikt gå från cirka
1991 som PROXY. USD/SEK-delen är klar och validerad. Se `swedish_and_avanza.md`.

## 5. Avanza implementation

| Signal | Fond | Anmärkning |
|---|---|---|
| USA | Avanza USA (SE0012741163) | Följer Morningstar US TME PAB Sustainability Select, inte S&P 500 |
| Europa | Avanza Europa (start 2020-02-05) | Morningstar Developed Europe TME PAB |
| EM | Avanza Emerging Markets (SE0012454338, 2019) | Matarfond till Amundi MSCI EM |
| Defensiv SEK | Avanza Ränta Kort (SE0021021425, 2023) | Säkerställda obligationer, inget jämförelseindex, inte T-bills |
| Global (benchmark) | Avanza Global (SE0011527613) | Utvecklade marknader, ingen EM, inte MSCI World/ACWI |
| GEM ex-US | **saknas** | Ingen Avanza-fond motsvarar ACWI ex USA |
| GEM US Agg | **saknas** | – |

Alla fondfakta kommer från sökutdrag och måste verifieras mot aktuella broschyrer.
`REGIONAL_SEK` är den enda modellen som kan genomföras helt med Avanza-fonder.

## 6. Methodological limitations

1. Backtesten bygger på okontrollerad tredjepartsdata (handsammanställd; ett
   transkriptionsfel hittat) som slutar 2016.
2. Skarvar: ex-US är World ex USA (utan EM) före 1988, obligationer är IT Govt före
   1976, US-aktier är Ibbotson före 1988.
3. T-bill-hurdlen är syntetisk, byggd av en yield-serie (samma månads snittränta).
4. Månadsdata medger bara två exekveringsgränser (stängning t respektive t+1). Verklig
   handel med fond-NAV, stopptider och likviddagar är inte simulerad mot riktig data.
5. Kostnaderna är illustrativa; fondavgift, tracking difference, valutaväxling och ISK
   ingår inte.
6. Referensvärdena är citerade via sekundärkällor; antal byten och MDD-episod är okända.
7. Fondfakta och flera API-detaljer är bara verifierade via sökutdrag.
8. Global benchmark (MSCI ACWI) saknas. `STATIC_70_30_US` använder US-aktier och är
   inte den efterfrågade globala 70/30.
9. Ingen out-of-sample-period efter 2016 med denna data. Sekundärkällor rapporterar
   svagare GEM-resultat efter publiceringen (bl.a. att ex-US-benet kostat 1,4–3,2 pp/år
   2008–2026 enligt quanterlab.com). Det är inte verifierat här.

## 7. Recommendation

```text
GO_WITH_LIMITATIONS
```

Motivering: motorn är klar, deterministisk och testad. Regeln reproducerar publicerad
GEM på näraliggande data utan justering. Arkitekturen separerar signalindex,
investeringsinstrument och exekvering. Det som saknas är data och verifiering, inte
modellarbete.

Begränsningar som är villkor för fas 2:

* Ingen svensk signal (`GEM_SEK`, `REGIONAL_SEK`) får visas för användare innan dess
  backtest körts på primärdata (öppna frågor 1–3).
* `GEM_ORIGINAL` får inte presenteras som verifierad förrän `GEM_ORIGINAL_STRICT`
  eller en dokumenterad öppen motsvarighet har körts på primärdata fram till idag.
* Licensfrågan för indexvärden (S&P, MSCI, Bloomberg, Nasdaq) måste avgöras innan en
  publik tjänst visar indexdata.

**Starkaste motargumentet** mot att gå vidare: produkten är en svensk signal, och just
den delen har noll backtest. En 0,6 pp-reproduktion av amerikansk GEM på data som slutar
2016 säger lite om hur `GEM_SEK` eller `REGIONAL_SEK` beter sig efter valuta, med en
svensk hurdle och med fonder som följer ESG/PAB-index. Den kortaste verifierbara svenska
historiken (2009→) innehåller dessutom i stort sett en enda regim. Om man väger
korrekthet över allt annat är NO_GO för de svenska modellerna ett försvarbart utfall.
Därför är GO villkorat ovan och gäller motorn och GEM_ORIGINAL-spåret, inte en svensk
signal.

## 8. Nästa steg (förslag fas 2 – inte implementerat)

1. **Datahärdning (först):** öppna nätverket eller kör lokalt; verifiera FRED-, Ken
   French- och Riksbanksproviders mot riktiga svar; bekräfta SSVX-serie-ID; ta beslut om
   licenser (eller dokumenterade öppna proxyer); ersätt tredjepartsfilen.
2. **Svenska backtest:** `GEM_SEK` och `REGIONAL_SEK` på nivåerna STRICT (OMRX från
   2008-11) och PROXY (syntetisk SSVX från cirka 1990), med samma rapportpaket.
3. **Daglig exekvering:** dagliga TR-serier, T+1/T+2-exekvering och fond-NAV-modell med
   verifierade stopptider; tid utanför marknaden vid byte.
4. **Instrumentvalidering:** hämta Avanza-fondernas NAV från fondstart (officiell källa;
   odokumenterade endpoints bara som valfri provider), mät tracking difference mot
   signalindex, och avgör hur ex-US-benet ska implementeras.
5. **Kostnads- och ISK-modell:** fondavgifter, valutaväxling, schablonskatt (enkel).
6. **Signaltjänst utan UI:** schemalagd månadskörning som skriver en versionerad signal
   (JSON) med full proveniens och `NO_SIGNAL`-hantering. Det blir backend för den
   senare PWA:n.
