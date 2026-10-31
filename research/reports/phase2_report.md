# Fas 2: härdad data och validering av den svenska modellen

Datum: 2026-10-31. Branch: `claude/gem-research-engine`.
Genererat underlag: [`generated/phase2.md`](generated/phase2.md), [`generated/phase2.json`](generated/phase2.json).

> **Definition of Done är inte uppfylld.** Ingen svensk strategi har körts på riktig
> historisk data. Orsaken är att byggmiljöns nätverkspolicy fortfarande nekar FRED,
> Riksbanken och Ken French (HTTP 403 vid CONNECT, se §2). Fasens status är därför
> **BLOCKED**, inte NO_GO: inget i resultaten talar emot modellerna, men inget talar för
> dem heller.

## 1. Executive summary

| Fråga | Svar |
|---|---|
| Fungerar GEM_SEK? | **Okänt – BLOCKED.** Motor, körningar, jämförelse mot GEM_ORIGINAL och exekveringsscenarier är implementerade och testade end-to-end på syntetisk data. Ingen svensk räntedata kunde hämtas. |
| Fungerar REGIONAL_SEK? | **Okänt – BLOCKED.** Samma läge, och dessutom saknas Ken French Europa/EM. |
| Går REGIONAL_SEK att implementera på Avanza? | **Strukturellt ja, kvantitativt okänt.** Alla fyra signalben har en billig Avanza-fond (USA, Europa, EM, Ränta Kort). Fonderna följer andra index än signalserierna, och Ränta Kort finns först från 2023. Implementationsgapet kan inte mätas utan fond-NAV. |
| Vilken modell bör PWA:n primärt visa? | **Ingen ännu.** När datan finns är REGIONAL_SEK den enda modellen som går att följa helt med Avanza-fonder och därmed förstahandskandidat, men det är ett strukturellt argument, inte ett resultat. |

Det som gjordes i fas 2:

* **Explicit tidsmodell** (`daily.py`). Varje byte får `signal_period_end`,
  `data_available_at`, `signal_generated_at`, `order_submitted_at`, `fund_cutoff`,
  `sell_nav_date`, `buy_nav_date` och `execution_date`. Tre scenarier: A
  `LOOKAHEAD_REFERENCE_ONLY`, B nästa handelsbara (huvudscenario) och C konservativt.
  Handelsregler (bryttid, NAV-förskjutning, likviddagar) konfigureras per fond från
  `investable_instruments.yaml`. En hel månads fördröjning är inte längre standard.
* **Valutakonvertering via SEK-nivå**: `TR_SEK(t) = TR_USD(t)·USDSEK(t)`, med
  avkastningen beräknad från SEK-nivån. Testat med exemplen 100→110 vid 10 SEK (+10 %)
  och 100→110 med 10→11 SEK (+21 %, inte 20 %).
* **Versionerade svenska körningar**: `GEM_SEK_OPEN_OMRX_V1`,
  `GEM_SEK_OPEN_SSVXSYNTH_V1`, `GEM_SEK_3P_SSVXSYNTH_V1`, `GEM_SEK_STRICT_V1`,
  `REGIONAL_SEK_FF_PROXY_OMRX_V1` och `REGIONAL_SEK_FF_PROXY_SSVXSYNTH_V1`.
  Jämförelsegrupper körs över exakt samma gemensamma fönster, med SEK-benchmarks
  (global buy-and-hold, 70/30, statisk 1/3-regionportfölj).
* **GEM_ORIGINAL mot GEM_SEK**: andel identiska signalmånader, år där skillnaderna
  koncentreras, övergångsmatris, samt CAGR- och MDD-skillnad med GEM_ORIGINAL omräknad
  till SEK för en svensk investerare.
* **Implementationsgap**: indexsignal mot samma signal genomförd i Avanza-fonder:
  tracking difference, avgift, signalavvikelse, exekveringsfördröjning, samt investerbar
  CAGR och MDD.
* **Strikt manuell import** (`date,value`, ISO-datum, stigande, positiv, med
  proveniensfil `.source.yaml`, och ingen data före fondstart) för OMRX-historik,
  licensierade index och Avanza-NAV. Mallar finns i `data/manual_templates/`.
* **Integrationstest** som kör hela fas 2-pipelinen på syntetisk data. Det hittade och
  rättade en verklig bugg (signaler före datans första handelsdag kraschade den dagliga
  motorn). 87 tester passerar.

## 2. Data quality

Åtkomst i denna körning (`generated/phase2.md` §1):

| Host | Serier | OK | Fel |
|---|---:|---:|---|
| fred.stlouisfed.org | 6 | 0 | `Tunnel connection failed: 403 Forbidden` |
| api.riksbank.se | 4 | 0 | `Tunnel connection failed: 403 Forbidden` |
| mba.tuck.dartmouth.edu | 9 | 0 | `Tunnel connection failed: 403 Forbidden` |
| raw.githubusercontent.com | 13 | 13 | – |
| PyPI (`arch` 8.0.0) | 2 | 2 | – |
| manuella filer (`data/manual/`) | 10 | 0 | ej tillhandahållna |

Även `www.riksbank.se`, `indexes.nasdaq.com`, `www.avanza.se`, `investors.avanza.se`,
`www.msci.com`, `api.scb.se`, ECB, OECD och DBnomics är blockerade, och WebFetch löser
inte heller dessa namn. Inga GitHub-, PyPI- eller CRAN-speglar med svenska räntor eller
Ken French regionfiler hittades.

| Role | Series | Source | Period | Quality | TR status |
|---|---|---|---|---|---|
| Svensk cash (hurdle + defensiv) | `FRED_OMRXTBILL` (NASDAQOMRXTBILL) | FRED ← Nasdaq | 2008-11-17 → | VERIFIED (källa) – **ej hämtad** | TR-index |
| Svensk cash, full historik | `NASDAQ_OMRXTBILL_FULL` | Nasdaq (manuell export) | okänt basdatum → | LICENSE_RESTRICTED – **ej tillhandahållen** | TR-index |
| Svensk cash, syntetisk modell | `RB_SSVX_3M` (SETB3MBENCH) | Riksbanken | 1983-01-03 → | PROXY – **ej hämtad** | yield → syntetisk TR (`SE_CASH_SSVX_SYNTH_V1`) |
| Korskontroll | `RB_SSVX_1M` / `RB_SSVX_6M` (SETB1MBENCHC / SETB6MBENCH) | Riksbanken | – | PROXY – ej hämtad | yield |
| USD/SEK (modell) | `H10_SEK_PER_USD` (DEXSDUS) | FRED H.10 via GitHub-spegel | 1971-01 → 2026-10 | VERIFIED (spegel) – **hämtad** | – (SEK per USD) |
| USD/SEK (korskontroll) | `RB_SEK_PER_USD` (SEKUSDPMI) | Riksbanken | – | VERIFIED – ej hämtad | – |
| USA (öppen) | `FF_US_MKT_TR` (+ daglig) | Ken French | 1926-07 → | PROXY – ej hämtad | TR |
| ex-US (öppen) | `FRED_NASDAQ_GLOBAL_EXUS_LM_NTR` | FRED ← Nasdaq | 2001-03 → | PROXY – ej hämtad | net TR |
| Europa / EM | `FF_EUROPE_MKT_TR`, `FF_EMERGING_MKT_TR` (+ dagliga) | Ken French | ~1990 → | PROXY – ej hämtad; filnamn ASSUMPTION | TR |
| Global benchmark | `FF_DEVELOPED_MKT_TR` / `MSCI_ACWI_OFFICIAL` | Ken French / MSCI | 1990-07 → / – | PROXY / LICENSE_RESTRICTED – ej hämtad | TR |
| USA / ex-US (3P) | `AJ_SP500TR`, `AJ_MSCI_ACWI_EXUS_GR` | GitHub-kompilering | 1988 → 2016-12 | EXPERIMENTAL – hämtad | TR |
| Avanza-NAV (5 fonder) | `AVZ_NAV_*` | Avanza (manuell export) | fondstart → | EXPERIMENTAL – ej tillhandahållen | NAV (ackumulerande, ASSUMPTION) |

Verifieringar via sökutdrag i fas 2: `SETB3MBENCH` är 3-månaders statsskuldväxel med
data från 1983-01-03, och `SETB1MBENCHC` och `SETB6MBENCH` är 1- och 6-månaders
växel. Allt detta står på Riksbankens sida "Series for the API" (VERIFIED FROM PRIMARY
SOURCE, search extract). FRED:s OECD-serie `IR3TTS01SEM156N` verkar sluta 2023-12 och
används bara som korskontroll.

OMRX-frågor som fortfarande är olösta: basdatum, om serien är ackumulerande (FRED
anger den som "Index", Nasdaqs metodik beskriver en portfölj som rullas, vilket
indikerar TR, men det är inte bekräftat), användningsvillkor för Nasdaqs fulla historik
och om automatiserad åtkomst är tillåten. Importvägen finns för det fall en manuell
export är tillåten.

Syntetisk cash-modell `SE_CASH_SSVX_SYNTH_V1`: SSVX 3m vid månadsslut,
`r_t = y_{t-1}/1200`. Samma transformation träffade ett amerikanskt T-bill-TR-index med
0,14 % årlig tracking error i fas 1. Jämförelsen mot OMRX från 2008-11 körs automatiskt
när båda finns (`OMRX T-bill index vs SE_CASH_SSVX_SYNTH`). Dagräkning (ACT/360 mot
ACT/365) och diskont- mot enkel ränta är dokumenterade approximationer.

## 3. GEM_ORIGINAL vs GEM_SEK

| Metric | Original | SEK |
|---|---:|---:|
| CAGR | BLOCKED | BLOCKED |
| Volatility | BLOCKED | BLOCKED |
| Max DD | BLOCKED | BLOCKED |
| Sharpe | BLOCKED | BLOCKED |
| Switches | BLOCKED | BLOCKED |
| Signal agreement % | BLOCKED | |

Alla fyra jämförelsepar är blockerade. `GEM_SEK_3P_SSVXSYNTH_V1` saknar `RB_SSVX_3M`;
`GEM_SEK_OPEN_*` och `GEM_ORIGINAL_OPEN_V1` saknar data från FRED och Ken French;
`GEM_SEK_STRICT_V1` saknar licensierade exporter. Analysen (identiska och olika
månader, år, övergångar, ΔCAGR och ΔMDD i SEK) är implementerad och verifierad i
integrationstestet.

Förväntat beteende, vilket är en hypotes och inte ett resultat: GEM_SEK skiljer sig
från GEM_ORIGINAL främst när kronan rör sig kraftigt. En stark krona sänker USA:s och
ex-US:s 12m-avkastning i SEK och kan ge defensiv signal där originalet ligger kvar i
aktier, och tvärtom. Ett skifte mellan USA och ex-US påverkas däremot inte av valutan,
eftersom båda räknas om med samma USD/SEK. Skillnaderna bör därför ligga nästan helt i
övergångarna mot och från det defensiva läget.

## 4. REGIONAL_SEK

**BLOCKED.** `REGIONAL_SEK_FF_PROXY_OMRX_V1` (från cirka 2009-11) och
`REGIONAL_SEK_FF_PROXY_SSVXSYNTH_V1` (från cirka 1991) saknar Ken French
USA/Europa/EM och svensk cash.

Vad serierna representerar när de hämtas (dokumenterat i katalogen):

* USA: CRSP, alla amerikanska aktier, värdeviktat (`Mkt-RF + RF`), inte S&P 500.
* Europa: Ken French utvecklade europeiska marknader, värdeviktat, USD.
* EM: Ken French tillväxtmarknader, värdeviktat, USD.
* Alla räknas om till SEK med H.10 SEK per USD via SEK-nivå.

Fast specifikation: 12 månader, top-1, vinnaren måste vara strikt större än hurdle,
lika värden avgörs av ordningen USA, Europa, EM. Inget är optimerat. Bättre officiella
serier kan läggas in som ett nytt run-ID utan att strategimotorn ändras.

## 5. Benchmarks

**BLOCKED** i alla svenska grupper. Definierade och körklara över gruppens gemensamma
fönster:

| Benchmark | Definition |
|---|---|
| `BUY_HOLD_GLOBAL_SEK_FF_DEV_PROXY_V1` | Ken French Developed (inkl. USA, utan EM) i SEK – öppen proxy för MSCI ACWI |
| `STATIC_70_30_SEK_FF_DEV_PROXY_V1` | 70 % global (SEK) / 30 % svensk cash, månadsombalansering |
| `STATIC_REGIONAL_EQUAL_SEK_FF_V1` | 1/3 USA, 1/3 Europa, 1/3 EM i SEK, månadsombalansering (parameterfritt val) |
| `BUY_HOLD_GLOBAL_SEK_ACWI_V1`, `STATIC_70_30_SEK_ACWI_V1` | samma med MSCI ACWI (licensierad export) |

Avvikelse från uppdragstexten: 30 %-delen i 70/30 är svensk kort ränta, inte
obligationer. Det är den defensiva tillgång modellerna faktiskt använder; en svensk
obligationsserie (t.ex. OMRX Bond) finns inte i katalogen.

## 6. Execution sensitivity

| Scenario | Definition | Status |
|---|---|---|
| A `A_PUBLISHED_CLOSE` | sälj och köp till stängningen sista handelsdagen i signalmånaden – **LOOKAHEAD_REFERENCE_ONLY** | implementerat |
| B `B_NEXT_TRADABLE` (huvud) | stängningar kända 08:00 nästa bankdag, order 09:00, NAV enligt fondens regler; köp läggs när försäljningens NAV satts | implementerat |
| C `C_CONSERVATIVE` | +1 bankdag före order; köp först när försäljningen likviderats (T+2) | implementerat |

Utfall på riktig data: **BLOCKED.** Scenarierna kräver dagliga TR-serier, och ingen
daglig aktie- eller räntenivå är nåbar.

Det enda belägg som finns kommer från fas 1 (GEM_ORIGINAL, tredjepartsdata, månadsdata,
1974–2013): stängningen t gav 16,80 % CAGR och en hel månads fördröjning gav 15,84 %.
B och C bör hamna nära A eftersom fördröjningen är 1–4 bankdagar, inte 21. Det får inte
behandlas som ett resultat förrän det har körts.

På syntetisk data bekräftar integrationstestet att fördröjningen ökar strikt från A
(0 dagar) till B (1 bankdag) till C (4 bankdagar, varav 2 utanför marknaden per byte).

## 7. Avanza implementation

| Signal | Signalindex | Investerbar fond | ISIN | Start | Index fonden följer | Avgift | Bryttid / NAV | Avvikelser |
|---|---|---|---|---|---|---|---|---|
| USA | CRSP US (FF) i SEK | Avanza USA | SE0012741163 | dec 2019 | Morningstar US TME PAB Sustainability Select | 0,18 % | 15:00, samma dag (T+1-publ.) | ESG/PAB-urval, inte totalmarknad |
| Europa | FF Europe i SEK | Avanza Europa | SE0013718699 | 2020-02-05 | Morningstar Developed Europe TME PAB | förv. 0,16 % (total ?) | 15:00 (ASSUMPTION) | ESG-urval |
| EM | FF Emerging i SEK | Avanza Emerging Markets | SE0012454338 | 2019 | Amundi Core MSCI EM (matarfond) | 0,30 % | 12:00, **nästa bankdags NAV** | matarfond, annan EM-konstruktion |
| Defensiv | OMRX T-bill | Avanza Ränta Kort | SE0021021425 | 2023 | inget jämförelseindex; Captor Perenne Short Term Bond | 0,09 % | okänd (12:00 ASSUMPTION) | säkerställda obligationer, kreditrisk; finns bara från 2023 |
| Global benchmark | FF Developed / MSCI ACWI | Avanza Global | SE0011527613 | 2018-08-27 | Morningstar Developed Markets TME PAB | 0,05–0,11 % (oklart) | 12:00 (2024) | ingen EM |

Gemensamt (sökutdrag ur 2026 års broschyrer): handel varje svensk bankdag,
framåtprissättning, NAV publiceras T+1, likvid inom två bankdagar. Inga belägg för
valutasäkring i någon fond (UNRESOLVED).

Konsekvenser för implementering:

1. Ett byte till eller från EM tar minst en extra bankdag (nästa dags NAV). C-scenariot
   modellerar dessutom likviddagar utanför marknaden.
2. REGIONAL_SEK kan bara följas helt med Avanza-fonder från 2023 (Ränta Kort). Före dess
   saknar det defensiva benet fond.
3. GEM_ORIGINAL och GEM_SEK saknar fortfarande en Avanza-fond för ex-US.
4. Implementationsgapet (tracking difference, signalavvikelse när momentum räknas på
   fond-NAV, investerbar CAGR och MDD) beräknas automatiskt när `data/manual/nav_<ISIN>.csv`
   finns. **BLOCKED** nu.

## 8. Methodological limitations

1. **Inga svenska resultat.** Allt i §3–§6 är implementerat men inte kört på riktig
   data.
2. Primärproviders (FRED, Riksbanken, Ken French) har fortfarande aldrig fått ett
   riktigt svar. Formatfixtures och integrationstest minskar risken men tar inte bort
   den. Första riktiga körningen kan avslöja formatfel.
3. Ken French-filnamnen för Europa och EM (månads- och dagsfiler) är antaganden.
4. Syntetisk svensk cash är en yield-transformation (PROXY). OMRX finns öppet bara från
   2008-11. En verifierad GEM_SEK med öppen data blir därför högst cirka 17 år lång och
   domineras av en lång USA-ledd regim.
5. Regionserierna (Ken French) är inte de index Avanza-fonderna följer
   (Morningstar PAB/ESG, MSCI EM). Signal och implementering kommer att skilja sig.
6. Ränta Kort har kreditrisk som OMRX-hurdlen saknar.
7. Fondfakta kommer från sökutdrag; flera bryttider är ASSUMPTION.
8. Antagandet i scenario B att köpordern kan läggas när försäljningens NAV satts, utan
   att vänta på likvid, är overifierat. Scenario C täcker det motsatta fallet.
9. Ackumulerande andelsklasser antas för alla fonder.
10. GEM_ORIGINAL-resultaten från fas 1 bygger fortfarande på en tredjepartsfil som
    slutar 2016.

## 9. Recommendation

| Komponent | Status | Motivering |
|---|---|---|
| ENGINE | **GO_WITH_LIMITATIONS** | Strategi-, backtest- och tidsmotor, FX, manuell import och rapportering är testade (87 tester, inklusive end-to-end). Begränsning: primärproviders är overifierade mot riktiga svar. |
| GEM_ORIGINAL | **GO_WITH_LIMITATIONS** (endast research) | Reproducerad inom 0,6 pp på tredjepartsdata 1974–2013 (fas 1). Ingen data efter 2016, inga dagliga scenarier. |
| GEM_SEK | **BLOCKED** | Ingen svensk räntedata; inget backtest. |
| REGIONAL_SEK | **BLOCKED** | Ingen svensk räntedata och inga regionserier; implementationsgap omätt. |
| PWA | **NO_GO** | Ingen svensk strategi uppfyller DoD. |
| LIVE_MONTHLY_SIGNAL | **BLOCKED** | Ingen aktuell aktie- eller räntedata nås (bara USD/SEK är aktuell). En signal för november 2026 kan inte beräknas i den här miljön. |

**Starkaste motargumentet** mot att låta allt vänta på datan: GEM_ORIGINAL är
reproducerad och skulle kunna visas som research redan nu. Men den har ingen data efter
2016 i miljön, kan inte ge en aktuell signal och är inte den svenska produkten. Att visa
den vore att bygga UI på det enda som inte är produktens kärna.

Det omvända argumentet, att fas 2 borde sägas NO_GO, håller inte heller. Inget
resultat talar emot modellerna. Det enda som hindrar är tillgången till data, och den
går att lösa på minuter.

**Vad som låser upp fasen.** Datan går att få på något av två sätt:

* Tillåt `fred.stlouisfed.org`, `api.riksbank.se` och `mba.tuck.dartmouth.edu` under
  Network access i miljöinställningarna
  (<https://code.claude.com/docs/en/cloud-environments#network-access>).
* Kör lokalt: `cd research && pip install -e '.[test]' && python -m gem.research --refresh`.

Det ger utan kodändring: `GEM_SEK_OPEN_OMRX_V1` (cirka 2009-11 →),
`GEM_SEK_OPEN_SSVXSYNTH_V1` (cirka 2002 →), båda REGIONAL_SEK-varianterna (cirka 2009 →
respektive cirka 1991 →), alla SEK-benchmarks, signalöverensstämmelse och scenario A/B/C.

För implementationsgapet krävs dessutom Avanza-NAV som manuell export, enligt
`data/manual_templates/README.md`.

## 10. PWA gate

```text
BUILD_PWA = NO
```

Ingen strategi får visas som riktig signal. GEM_ORIGINAL får som mest visas som
historisk research med tydlig märkning (tredjepartsdata, slutar 2016). Gaten prövas igen
när minst en av `GEM_SEK_OPEN_OMRX_V1`, `GEM_SEK_OPEN_SSVXSYNTH_V1`,
`REGIONAL_SEK_FF_PROXY_OMRX_V1` eller `REGIONAL_SEK_FF_PROXY_SSVXSYNTH_V1` har körts på
primärdata, jämförts med benchmark i scenario B och fått sin Avanza-mappning bekräftad
mot primärkälla.
