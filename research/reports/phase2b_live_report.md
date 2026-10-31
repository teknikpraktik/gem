# Fas 2b: OMRX-verifiering och investerbar REGIONAL_SEK

Datum: 2026-10-31. Allt kört i GitHub Actions (workflow *GEM phase 2 research*), senast i
körningen bakom commit `a88de13`. Tester: 105 passed, 0 failed, 0 skipped. Refresh-körning
och cachekörning: identiska sha256 för samtliga resultatfiler.

Underlag: `generated/phase2.md` (§4a, §4b, §7), `generated/nav_implementation.json`,
`generated/live_signal.json`, `generated/runs_daily/REGIONAL_SEK_NAV_IMPL__*`,
`generated/nav_probe/`, `generated/nav_lag_observations.csv`.

## 1. OMRX-verifiering (FRED API, `FRED_API_KEY`)

**Serien `NASDAQOMRXTBILL`:**
* 2008-11-17 → 2026-10-29, daglig (bankdagar), 4 491 observationer.
* 193 tomma värden (`.` = helgdagar) i råsvaret.
* Inga inaktuella månadsslut.
* Ackumulerande indexnivå 3060 → 3477 (CAGR 0,71 %), med 90 negativa månader av 215
  (negativa räntor 2015–2021).
* Bedömning: lämplig som total-return-serie för svensk cash.

**Svensk cash: OMRX mot Riksbanksproxyn (SETB3MBENCH, `r_t = y_{t-1}/1200`),
2008-12 → 2026-10, månadsavkastning:**

| Mått | Värde |
|---|---:|
| Korrelation | 0,978 |
| Genomsnittlig absolut avvikelse | 0,015 %/mån |
| Maximal månadsavvikelse | 0,19 % (2008-12) |
| Tracking error | 0,09 %/år |
| CAGR OMRX / proxy | 0,71 % / 0,77 % |

**GEM_SEK med samma aktieben (Ken French USA och Developed ex US, Riksbankens USD/SEK),
2010-01 → 2026-09, 201 signalmånader:**

| Mått | OMRX (`GEM_SEK_FF_OMRX_VERIFIED_V1`) | Riksbanksproxy |
|---|---:|---:|
| CAGR, daglig B | 12,53 % | 12,54 % |
| Max DD, daglig B | −21,3 % | −21,3 % |
| CAGR, en månads fördröjning | 11,84 % | 11,85 % |
| Byten | 36 | 36 |
| **Signalöverensstämmelse** | **100 % (0 av 201 ändras)** | |

REGIONAL_SEK ger samma bild: 0 av 201 signaler ändras och CAGR skiljer 0,005 pp.

**Slutsats: Riksbanksproxyn är tillräckligt bra för historisk forskning före 2008.**
Hurdlen avgör aldrig en signal annorlunda i överlappet. Avvikelsen i defensiv avkastning
är försumbar.

## 2. Live-NAV-källor

Officiella vägar provades först, som probet visar:
* avanzafonder.se svarar med HTML utan NAV-data.
* investors.avanza.se: 404.
* Inget dokumenterat fondbolags-API hittades.

Kvar finns de JSON-endpoints som avanza.se själv använder (**UNDOCUMENTED_ENDPOINT**).
De fungerar anonymt från GitHub-runners och är isolerade bakom `FundNavProvider`
(`gem/nav.py`, `gem/data/avanza.py`).

| Fond | ISIN (bekräftad via avanza.se-sökning) | orderBookId | Benchmark (avanza.se primaryBenchmark) | Total avgift | Historik i data | Prissättning |
|---|---|---|---|---:|---|---|
| Avanza USA | SE0012741163 | 1025150 | Morningstar US TME PAB Sust NR SEK | 0,18 % | 2019-12 → | Dagligen |
| Avanza Europa | SE0013718699 | 1041067 | Morningstar Dev Eur TME PAB Sust NR SEK | 0,31 % | 2020-02-05 → | Dagligen |
| Avanza Emerging Markets | SE0012454338 | 944976 | (inget angivet) | 0,30 % | 2019-04 → | Dagligen, nästa bankdags kurs |
| Avanza Ränta Kort | SE0021021425 | 1684019 | (inget; mottagarfond Captor Perenne Short Term Bond A, SE0020552602) | 0,09 % | 2023-12-14 → | Dagligen |
| Avanza Global (benchmark) | SE0011527613 | 878733 | Morningstar DM TME PAB Sust NR SEK | 0,10 % | 2018-08-21 → | Dagligen |

Alla fonder är UCITS och i SEK.

**Publiceringsfördröjning (mätt).** Lördag 2026-10-31 kl. 12:28–12:37 svensk tid var
senaste NAV-datum torsdag 2026-10-29 för alla fem fonder (två observationer i olika
körningar). Fredagens NAV var alltså inte publicerad ett dygn efter stängning. Det stämmer
med Avanzas uppgift att NAV publiceras bankdagen efter handelsdagen.

Slutsats: månadsslutets NAV finns tidigast **T+1 bankdag**, så signalen kan skapas
tidigast första bankdagen efter månadsskiftet. *Vilken tid* den bankdagen är inte mätt; om
det sker efter bryttiden blir det i praktiken scenario C.

`gem.navlag` loggar en observation per körning. En schemalagd mätning lades inte till
(se §7).

**Luckor i EM-NAV (mätt).** 2022-01-28→02-04 (5 bankdagar), 2025-01-22→02-03 (8),
2025-09-30→10-08 (6), 2026-02-11→02-23 (8). Mönstret sammanfaller med kinesiskt nyår och
Golden Week. Avanza EM tycks inte sätta NAV när kinesiska marknaden är stängd. Övriga
fonder saknar luckor.

## 3. REGIONAL_SEK: två nivåer, aldrig blandade

**A. Forskningsmodell (index).** Ken French USA/Europa/EM i SEK och Riksbankens cash,
1994-03 → 2026-09: CAGR 11,64 % (A) / 10,40 % (en månads fördröjning), max DD −27,1 % /
−39,4 %, mot global buy-and-hold 9,48 % / −47,5 %. Daglig B kan inte köras: det finns
ingen daglig EM-indexserie.

**B. Investerbar implementering (fond-NAV).**
* Signalen beräknas med samma funktion som live-signalen (`gem.live.regional_live_signal`):
  12 månaders NAV-avkastning punkt till punkt och hurdle från Riksbankens SSVX.
* Exekvering sker på NAV med fondernas regler:
  * USA 15:00, samma dag.
  * EM 12:00, nästa bankdags NAV.
  * Europa 15:00 och Ränta Kort 12:00 (båda ASSUMPTION).
  * Likvid T+2.
* Två varianter:
  * **HYBRID** (2021-04 → 2026-10, 67 mån): riktiga aktiefonder, syntetisk Riksbankscash
    som defensiv tillgång före Ränta Kort.
  * **PURE** (2024-01 → 2026-10, 34 mån): alla fyra riktiga fonder.

| Mått | Index, en månads fördröjning (samma månader) | Index A (samma månader) | **Avanza-fonder B (HYBRID)** | Avanza Global buy-and-hold |
|---|---:|---:|---:|---:|
| CAGR | 10,97 % | 12,26 % | **10,78 %** | 13,97 % |
| Volatilitet | 15,0 % | 14,6 % | 15,9 % | 12,8 % |
| Max DD (mån) | −20,0 % | −16,4 % | **−18,0 %** | −17,8 % |
| Sharpe (rf = 0) | 0,77 | 0,87 | **0,72** | 1,09 |
| Byten | 14 | 14 | 11 | 0 |

PURE (34 mån): fonder B 16,50 % / −18,0 % / 0,95 mot Avanza Global 16,12 % / −17,8 % / 1,23,
och 70/30 Global/Ränta Kort 12,19 % / −12,5 % / 1,32. 1/3-portföljen kan inte beräknas för
fönstret, eftersom EM-NAV saknas vid månadsslut januari och februari 2025.

**Exekveringsscenarier (HYBRID):**

| Scenario | CAGR | Max DD | Bankdagar signal→exekvering | Dagar utanför marknaden per byte |
|---|---:|---:|---:|---:|
| A publicerad close (LOOKAHEAD_REFERENCE_ONLY) | 11,51 % | −19,0 % | 0,3 | 0,2 |
| **B nästa handelsbara** | **10,78 %** | **−18,0 %** | 1,7 | 0,2 |
| C konservativ | 11,35 % | −16,7 % | 4,4 | 2,2 |

Med 11 byten styrs skillnaden mellan scenarierna av några få dagar runt bytena. C > B är
brus, inte en egenskap.

**Implementationsgap (index → fond):**

| Komponent | Värde |
|---|---|
| Total CAGR-skillnad mot index (samma månader) | −0,2 pp mot en månads fördröjning, −1,5 pp mot A |
| Tracking difference fond mot indexben | USA −0,60 pp/år (TE 4,1 %), Europa −1,41 pp (TE 4,6 %), EM −1,36 pp (TE 3,7 %) |
| Fondavgifter (ingår i NAV) | 0,18 / 0,31 / 0,30 / 0,09 % |
| Signalöverensstämmelse index mot NAV | 81,8 % (54/66); 11 av 12 skillnader är regionval, 1 är risk-on/off |
| Var skillnaderna ligger | främst 2025: NAV-modellen väljer EM där indexmodellen väljer USA eller Europa (Avanza EM ≈ MSCI EM ≠ Ken French Emerging) |
| Exekveringsfördröjning B | i snitt 1,7 bankdagar från signalmånadens slut |
| NO_SIGNAL | 2 av 68 månader (2025-01 inaktuell EM-NAV; 2026-01 inaktuell startpunkt för 12 mån) |

## 4. Live-signal (prototyp)

`generated/live_signal.json`, beräknad 2026-10-30 på data till och med 2026-10-29:

```json
{"strategy": "REGIONAL_SEK", "signal_period_end": "2026-09-30", "status": "VALID",
 "target": "AVANZA_EM",
 "returns": {"usa": 0.218, "europe": 0.161, "em": 0.355, "cash": 0.019}}
```

Oktobers signal kan inte beräknas förrän månadsslutets NAV (fredag 30 oktober)
publicerats, väntat måndag 2 november. Funktionen svarar korrekt med september som senaste
kompletta månad.

## 5. Live readiness

| Fond | Status | Begränsning |
|---|---|---|
| Avanza USA | READY_WITH_LIMITATIONS | odokumenterad endpoint; bryttid 15:00 från broschyrutdrag |
| Avanza Europa | READY_WITH_LIMITATIONS | odokumenterad endpoint; bryttid antagen 15:00 |
| Avanza Emerging Markets | READY_WITH_LIMITATIONS | NAV saknas 5–8 bankdagar vid kinesiska helgdagar; nästa bankdags kurs |
| Avanza Ränta Kort | READY_WITH_LIMITATIONS | finns först från 2023-12-14; bryttid antagen; säkerställda obligationer (kreditrisk); används aldrig som hurdle |

## 6. PWA-gate (kriterier från uppdraget)

| # | Kriterium | Utfall |
|---|---|---|
| 1 | OMRX avslöjar inget fundamentalt problem med GEM_SEK-proxyn | **uppfyllt**: 100 % samma signaler |
| 2 | REGIONAL_SEK kan beräknas från aktuell NAV inom rimlig tid efter månadsslut | **uppfyllt med begränsning**: T+1 bankdag (klockslag ej mätt); EM-luckor kan ge NO_SIGNAL (2 av 68 mån) |
| 3 | Realistiskt NEXT_TRADABLE-resultat | **uppfyllt**: 10,78 % / −18,0 % med fondernas regler |
| 4 | Acceptabelt implementationsgap mot indexmodellen | **uppfyllt**: −0,2 till −1,5 pp/år; tracking difference −0,6 till −1,4 pp/år |
| 5 | Live-signalen är reproducerbar | **uppfyllt**: ren funktion, samma kod i backtest och live, identiska checksummor |
| 6 | Ingen kritisk datakälla kräver manuellt arbete varje månad | **uppfyllt med begränsning**: helt automatiskt, men via en odokumenterad Avanza-endpoint |

## 7. Begränsningar som påverkar tolkningen

1. **Under den investerbara perioden slog REGIONAL_SEK inte Avanza Global.** Den gav
   −3,2 pp/år med samma drawdown (−18,0 % mot −17,8 %) och lägre Sharpe. Den kända
   nyttan, lägre drawdown, kommer helt från forskningsperioden före 2009.
2. **Mycket korta urval:** 67 månader och 11 byten (HYBRID), 34 månader och 6 byten
   (PURE). Skillnader under cirka 2 pp/år kan inte skiljas från brus.
3. **Live-signalen bygger på fond-NAV, forskningsmodellen på Ken French-index.** De är
   överens 82 % av månaderna. Forskningsmodellens 30-åriga historik gäller därför bara
   ungefärligt för live-modellen.
4. **NAV-källan är odokumenterad.** Den kan ändras utan förvarning. Bytet kräver bara en ny
   `FundNavProvider`.
5. **Publiceringstiden på T+1 är mätt vid ett tillfälle, en lördag.** En schemalagd mätning
   runt några månadsskiften behövs. Jag lade inte till ett schemalagt workflow, eftersom
   det skapar återkommande körningar i ditt repo; det beslutet är ditt.
6. **Bryttider för Europa och Ränta Kort** är antaganden från broschyrutdrag.
