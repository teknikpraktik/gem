# Metodik

Alla definitioner nedan är implementerade i koden som anges och täcks av tester i `tests/`.

## 1. Månadsslut (`returns.to_month_end`)

* Månadens etikett = sista kalenderdagen.
* Värde = sista giltiga observation (ej NaN, ej 0-platshållare) inom kalendermånaden.
* **Stale**: om observationen ligger mer än 5 bankdagar (mån–fre, ingen helgkalender)
  före månadens sista bankdag sätts månadsvärdet till NaN och flaggas. Exempel som
  fångades: tredjepartsfilens sista rad 2017-05-12 (maj 2017 → stale).
* Månader utan observation finns kvar som NaN så att luckor syns.
* Dubbletter i tidsindex → fel (serien används inte).

## 2. Avkastning

* Månadsavkastning `r_t = P_t / P_{t-1} - 1` på ett komplett månadsrutnät; en lucka ger
  NaN, aldrig en tvåmånadersavkastning (`returns.simple_returns`).
* 12-månadersavkastning `P_t / P_{t-12} - 1` kräver att alla 13 nivåer finns
  (`returns.trailing_return`). Nivåkedjor bryts vid luckor (`panel.chain_levels`).
* Skarvade serier: avkastningen från serie A används t.o.m. skarvmånaden, därefter serie
  B. 12m-momentum över skarven använder den kedjade avkastningen.
* Valuta: `1 + R_SEK = (1 + R_USD) · FX_t / FX_{t-1}` med FX = SEK per USD vid månadsslut
  (`fx.py`, `panel.leg_returns`). En plausibilitetsvakt (3–15 SEK/USD) stoppar fel
  kvoteringskonvention.

## 3. Yield → avkastning (endast för märkta proxyer)

`returns.yield_to_monthly_return`, standard `simple_prior`:

```
r_t = y_{t-1} / 100 / 12
```

Antaganden: en växel köpt vid slutet av månad t-1 ger 1/12 av årsräntan under månad t;
diskontobasis vs. obligationsekvivalent yield och kursrörelser under månaden ignoreras.
Validering mot ett T-bill-TR-index (tredjepartsfilen) 1970–2017: årlig tracking error
0,14 %, CAGR-skillnad −0,01 %-enheter (`reports/generated/data_quality.md`). Riksbankens
SSVX-ränta används **aldrig** direkt som totalavkastningsindex, bara efter denna
transformation och då märkt som proxy.

Syntetisk obligation (`returns.par_bond_monthly_return`, endast `GEM_PROXY_FF`): en
par-obligation köpt till y_{t-1} omvärderas till y_t med löptid M − 1/12, plus en månads
kupong. Märkt EXPERIMENTAL.

## 4. Signal och exekvering (`execution.py`, `backtest.py`)

Varje signalrad lagrar `signal_date`, `data_available_date`, `order_date`,
`execution_date` och `first_return_month`.

| Konvention | Handel | Första avkastningsmånad | Look-ahead | Användning |
|---|---|---|---|---|
| `NEXT_MONTH_CLOSE` (primär) | stängning vid nästa månadsslut t+1 | t+2 | nej | huvudresultat |
| `IDEALIZED_CLOSE` | samma stängning t som definierar signalen | t+1 | ja (stängningen) | endast jämförelse mot publicerade backtests |

Verklig handel sker 1–3 bankdagar efter t, alltså mellan de två konventionerna.
Konventionerna är inte optimerade; de är de två ytterlägena som månadsdata medger.

För framtida fondimplementering finns `FundOrderModel` (cut-off, framåtprissättning,
sälj→köp med tid utanför marknaden). Cut-off-tider är **ej verifierade** (se
`data/investable_instruments.yaml`).

`NO_SIGNAL` (saknad/inaktuell input) ändrar aldrig positionen och loggas. Saknar en
hållen tillgång avkastning en månad stoppas backtestet och orsaken lagras (`stop_reason`).

## 5. Kostnader

* `COST_0`: inga kostnader (jämförbart med publicerade indexbacktests).
* `COST_10BPS`: 10 bp per sida på handlad vikt, alltså 20 bp per fullt byte. Första köpet
  belastas inte (samma för alla strategier). Ett illustrativt scenario, inte kalibrerat
  mot Avanza. Fondavgifter, tracking difference, valutaväxling och ISK ingår inte ännu.

## 6. Mått (`metrics.py`)

| Mått | Definition |
|---|---|
| CAGR | (V_slut/V_start)^(12/n) − 1 |
| Volatilitet | stdav(månad, ddof=1)·√12 |
| Sharpe | medel(r − rf)·12 / (stdav(r − rf)·√12), rf = körningens T-bill-/hurdle-serie |
| Sortino | medel(r − rf)·12 / (√medel(min(r − rf, 0)²)·√12) |
| Max drawdown | min(V/löpande max(V) − 1), startvärdet inräknat |
| Calmar | CAGR / \|MDD\| |
| Byten | antal månader där målet skiljer sig från föregående månad |
| Turnover/år | Σ\|Δw\|/2 per år (fullt byte = 100 %) |
| Snittinnehav | månader / (byten + 1) |
| Längsta drawdown | längsta följd av månader under tidigare topp (med start-/slutdatum) |
| Längsta underprestation | längsta följd av månader då strategi/benchmark-förmögenhetskvoten ligger under sin tidigare topp |
| Bästa/sämsta år | endast hela kalenderår |

## 7. Reproducerbarhet

* Rådata cachas byte-för-byte med sha256 (`data/raw/…/*.meta.json`) och loggas i
  `data/manifests/retrievals.jsonl`. Standardkörning använder cache. Två körningar på
  samma cache ger identisk `summary.csv` (kontrollerat med sha256).
* `--refresh` laddar ned igen. Ändrade bytes sparas som ny version med `previous_sha256`
  så att revisioner hos källan syns.
* Ingen slump, inget dolt tillstånd. Strategiversion lagras i varje signal.

## 8. Ingen parameteroptimering

Fönstret är 12 månader och testas inte mot alternativ. Skarvdatum är där den önskade
serien börjar. De fyra `DIAG_*`-körningarna byter **ett** databen i taget enbart för att
förklara avvikelsen mot referensen. De är inga kandidatmodeller och påverkar inte
huvudmodellerna.
