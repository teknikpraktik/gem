# Reproduktion mot publicerad GEM

Genererade siffror: [`generated/reproduction_table.md`](generated/reproduction_table.md),
[`generated/summary.csv`](generated/summary.csv).

## Referens

Antonacci, *Dual Momentum Investing* (McGraw-Hill, 2014): GEM jan 1974–dec 2013, med
S&P 500 TR, MSCI ACWI ex USA, Barclays US Aggregate och T-bills. Siffrorna (CAGR 17,43 %,
standardavvikelse 12,64 %, max drawdown −22,72 %, Sharpe 0,87; jämförelseindex ACWI
8,85 % / −60,21 %) är hämtade från sekundärkällor som citerar boken (SVRN 2015,
Alpha Architect). Boken själv kunde inte läsas. **VERIFIED FROM SECONDARY SOURCE.**
Antal byten anges inte i någon åtkomlig källa (**UNRESOLVED**).

Kompletterande primäruppgift (Antonaccis egen blogg, search extract): "GEM was up 20% in
1973–74 while the S&P 500 was down over 40%".

## Vår körning

`GEM_ORIGINAL_PROXY_3P`, fönster 1974-01-31..2013-12-31, 0 kostnad, exakt GEM-regel och
12 månader, med tredjepartsdata (se `data_sources.md`). Skarvar: Ibbotson Large Co. →
S&P 500 TR (1988-02), MSCI World ex USA → ACWI ex USA (1988-01), Ibbotson IT Govt → US
Agg (1976-01), hurdle = 3m T-bill-TR byggd av TB3MS.

| Metric | Reference | Our result (IDEALIZED_CLOSE) | Difference | Our result (NEXT_MONTH_CLOSE) | Likely explanation |
|---|---:|---:|---:|---:|---|
| CAGR | 17,43 % | 16,80 % | −0,63 pp | 15,84 % | Andra dataserier (se nedan). Spannet för rimliga serieval är 16,27–17,02 %. Exekveringsfördröjningen kostar ytterligare ~1 pp. |
| Volatilitet | 12,64 % | 12,49 % | −0,15 pp | 12,66 % | Inom brus |
| Max drawdown | −22,72 % | −18,96 % | +3,76 pp | −19,19 % | MDD är en enskild episod. Vi har fem episoder mellan −15 och −19 % (1987, 1998, 2000, 2008, 2011). En enda månad i annan tillgång flyttar MDD flera pp. Referensens episod är okänd. |
| Sharpe | 0,87 | 0,90 | +0,03 | 0,82 | rf-definition (vår 3m-TR) och lägre MDD-episoder |
| Antal byten | UNRESOLVED | 56 (1,40/år) | n/a | 56 | – |
| Regim 1973–74 | "+20 %" | +21,3 % (1973 +14,7 %, 1974 +5,7 %) | ≈ | +22,7 % | Samma regimbild: obligationer från maj 1973 |

Stora regimskiften i vår körning (signalmånad → nytt innehav): obligationer 1973-04,
USA 1975-05, obligationer 1987-11 (efter kraschen, som träffade innehavet i ex-US med
−14,5 % i oktober), obligationer 1990-07, obligationer 2000-11 → aktier 2003-07,
obligationer 2008-01 → ex-US 2009-10. Se
`generated/runs/GEM_ORIGINAL_PROXY_3P__FULL__IDEALIZED_CLOSE__COST_0/regime_changes.csv`.
Mönstret (ute ur 1973–74, 2000–02 och 2008) stämmer med Antonaccis beskrivning.

## Diagnos: byt ett databen i taget (inte modeller)

IDEALIZED_CLOSE, 0 kostnad, 1974–2013:

| Diagnos | CAGR | MDD | Sharpe | Byten |
|---|---:|---:|---:|---:|
| Bas (`GEM_ORIGINAL_PROXY_3P`) | 16,80 % | −18,96 % | 0,90 | 56 |
| Hurdle = Ken French RF (1m, realiserad) | 16,75 % | −18,96 % | 0,90 | 56 |
| Hurdle = TB3MS med vår föregående-månadsregel | 16,75 % | −18,96 % | 0,90 | 56 |
| ex-US = World ex USA hela perioden | 16,27 % | −18,21 % | 0,87 | 60 |
| US = MSCI USA i stället för S&P 500 | 17,02 % | −17,84 % | 0,92 | 51 |

Tolkning:

* T-bill-definitionen spelar nästan ingen roll (±0,05 pp).
* Valet av ex-US- och US-index flyttar CAGR ±0,5 pp och antalet byten med ±5. Det är
  samma storleksordning som gapet till referensen.
* Ingen enskild orsak förklarar −0,63 pp. Den troligaste förklaringen är summan av
  (1) andra ex-US-data före 1988 (Antonaccis exakta pre-1988-serie är okänd),
  (2) obligationer 1974–75: vi har Ibbotson IT Govt där Antonacci hade Barclays-data
  tillbaka till 1973, och (3) gross- vs net-MSCI samt okänd MSCI-extraktionsdag.
  Datakällan för (1) och (2) kan inte avgöras utan bokens appendix (**UNRESOLVED**).
* Vi har **inte** justerat något för att närma oss 17,43 %.

## Slutsats

Reproduktionen lyckas i den mening som spelar roll: samma regel på näraliggande data ger
CAGR inom 0,6 pp, samma volatilitet och samma regimbild. Den lyckas inte exakt, och
max drawdown är systematiskt *bättre* än referensen. Det senare ska läsas som osäkerhet,
inte som förbättring. MDD för GEM bör i planeringen antas vara minst −23 % och kunna bli
värre.

Viktigare för en riktig tjänst: utan look-ahead vid stängningen (`NEXT_MONTH_CLOSE`)
faller CAGR till 15,84 %. Kostnader på 20 bp per byte drar ytterligare ~0,3 pp. Verklig
implementation hamnar mellan IDEALIZED och NEXT_MONTH.
