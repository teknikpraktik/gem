# Svenska modeller och Avanza-implementering

Maskinläsbar fondlista: [`data/investable_instruments.yaml`](../data/investable_instruments.yaml).
Alla fondfakta kommer från sökutdrag ur Avanzas sidor och PDF:er, eller från
tredjepartssajter. `avanza.se` och `investors.avanza.se` gick inte att öppna från
byggmiljön, så varje fält ska verifieras igen mot aktuell informationsbroschyr innan
riktiga pengar används.

## 1. Kan de svenska modellerna backtestas trovärdigt?

**Inte ännu. Inget svenskt backtest har körts.** Motorn, FX-konverteringen och
körningsdefinitionerna (`GEM_SEK_3P`, `REGIONAL_SEK_FF`) finns och är testade, men den
svenska hurdle-/defensivserien kunde inte hämtas:

| Behov | Bästa källa | Status |
|---|---|---|
| Svensk hurdle 2008-11 → idag | FRED `NASDAQOMRXTBILL` | Blockerad i byggmiljön; öppen källa, fungerar troligen direkt när FRED är nåbart |
| Svensk hurdle före 2008-11 | Nasdaq OMRXTBILL (full historik) | Ingen dokumenterad öppen nedladdning; licens UNRESOLVED |
| Alternativ före 2008-11 | Riksbanken 3m SSVX → yield-transform | Serie-ID `SETB3MBENCH` är ett ASSUMPTION; resultatet är en syntetisk PROXY |
| USD/SEK | FRED H.10 (spegel) 1971 → idag | **Tillgänglig och validerad** |
| USA/ex-US i USD | Tredjepartsfilen (t.o.m. 2016-12) | Tillgänglig men slutar 2016 |
| Europa/EM-regioner | Ken French Europe/Emerging | Blockerad; filnamn ASSUMPTION |

Realistisk förväntan när datan finns:

* `GEM_SEK` med OMRXTBILL från FRED: trovärdigt från cirka 2009-12 (12 månader efter
  2008-11-17) till idag, men det kräver ett ex-US-ben efter 2016. Med
  `NASDAQNQGXUSLMN` (från 2001) och S&P 500 TR (licens) eller en öppen proxy blir det
  ungefär 16 år. Kort, och nästan bara en enda lång USA-ledd period.
* `GEM_SEK` 1990 → idag: kräver antingen Nasdaqs fulla OMRXTBILL-historik (licensfråga)
  eller en syntetisk SSVX-hurdle. Det senare kan göras seriöst eftersom transformationen
  är validerad för amerikanska växlar (0,14 % årlig tracking error), men det blir märkt
  PROXY.
* `REGIONAL_SEK`: Ken French Europa/EM börjar runt 1990. Med syntetisk svensk hurdle är
  cirka 1991 → idag möjligt som PROXY. Avanzas egna index (Morningstar TME PAB) saknar
  åtkomlig lång historik och kan bara användas för fondernas egen period.

Metodpunkt som avgörs av den svenska datan: i `GEM_SEK` påverkar valutan både signalen
och avkastningen. En stark krona sänker USA:s och ex-US:s SEK-momentum mot en svensk
hurdle, så modellen kan gå defensivt i lägen där original-GEM ligger kvar i aktier.
Det är en egen modell med eget beteende, och den ska inte bedömas mot GEM:s historik.

## 2. Avanza: vilken fond för vilken signal?

| Signal | Signalindex | Kandidatfond | Fondens index (enligt utdrag) | Avvikelse |
|---|---|---|---|---|
| GEM_ORIGINAL US | S&P 500 TR (USD) | Avanza USA (SE0012741163) | Morningstar US TME Paris Aligned Benchmark Sustainability Select | ESG/Paris-urval, cirka 330–500 bolag (källorna går isär), SEK. **Inte S&P 500.** |
| GEM_ORIGINAL ex-US | MSCI ACWI ex USA | **ingen Avanza-fond** | – | Avanza Global innehåller USA och saknar EM. Ex-US kräver en kombination (Europa + EM + Japan/Stillahavsområdet) eller en annan förvaltares globalfond ex USA. |
| GEM_ORIGINAL defensiv | US Aggregate (USD) | **ingen Avanza-fond** | – | Avanza Ränta Kort är svensk, kort och kreditexponerad, inte US Agg. |
| GEM_SEK US / ex-US | S&P 500 TR / ACWI ex USA i SEK | Avanza USA / ingen | se ovan | ex-US-problemet kvarstår |
| GEM_SEK, REGIONAL_SEK defensiv | OMRX T-bill | Avanza Ränta Kort (SE0021021425) | Inget jämförelseindex. Matarfond till Captor Perenne Short Term Bond (svenska AAA-bostadsobligationer, löptid < 1 år) | Säkerställda obligationer har spreadrisk som T-bills saknar. Hurdle och defensiv tillgång är olika saker. |
| REGIONAL_SEK USA | USA-index i SEK | Avanza USA | se ovan | se ovan |
| REGIONAL_SEK Europa | Europa-index i SEK | Avanza Europa (ISIN UNRESOLVED, start 2020-02-05) | Morningstar Developed Europe TME PAB Sustainability Select | ESG-urval, bara utvecklade marknader |
| REGIONAL_SEK EM | EM-index i SEK | Avanza Emerging Markets (SE0012454338, start 2019) | Matarfond till Amundi Core MSCI Emerging Markets | Matarstruktur; NR/GR UNRESOLVED |
| BUY_HOLD_GLOBAL | MSCI ACWI | Avanza Global (SE0011527613) | Morningstar Developed Markets TME PAB Sustainability Select (inte MSCI World sedan 2023/24) | Saknar EM. Inte ACWI. |

Avgifter (utdrag, ska verifieras): Avanza USA 0,18 % totalt, Europa förvaltningsavgift
0,16 %, Emerging Markets 0,30 % totalt, Global 0,05–0,11 % (källorna går isär), Ränta
Kort 0,09 % totalt.

Handel (utdrag): framåtprissättning; NAV publiceras dagen efter handelsdagen (T+1).
Generell stopptid 13.00 (10.00 halvdagar). Avanza Global 12.00 enligt 2024 års broschyr,
Avanza USA möjligen 15.00 (förvanskat utdrag). Fondspecifika tider och likviddagar för
sälj→köp är **UNRESOLVED**. `execution.FundOrderModel` modellerar detta när tiderna
verifierats. Med antagandet att köp läggs först när försäljningen likviderats blir
tiden utanför marknaden minst en bankdag per byte (testat).

## 3. Slutsatser för fas 2

1. **REGIONAL_SEK är den enda modell som går att implementera helt med Avanza-fonder.**
   Dess signalindex (regionala marknadsindex) skiljer sig dock från fondernas ESG/PAB-index.
   Tracking difference mellan signalindex och fond-NAV måste mätas när NAV-historik finns
   (bara från fondstart: 2019/2020).
2. GEM_ORIGINAL och GEM_SEK saknar en Avanza-fond för ex-US-benet. Det måste lösas med
   fonder från andra förvaltare (via Avanza-plattformen) eller accepteras som en
   avvikelse.
3. Ränta Kort som defensiv tillgång bär kreditrisk (bostadsobligationer). Det är
   acceptabelt för en svensk investerare men bör redovisas, och dess avkastning ska aldrig
   användas som hurdle.
4. Fond-NAV används aldrig bakåt före fondstart (`execution.assert_not_before_launch`).
