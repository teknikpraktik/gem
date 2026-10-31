# Manuella dataexporter

Licensierade eller manuellt exporterade serier läggs i `research/data/manual/`
(checkas aldrig in). Varje CSV kräver en proveniensfil `<fil>.source.yaml`.
Importen vägras om schema eller proveniens inte stämmer (`providers.parse_local_csv`).

## CSV-schema (strikt)

```csv
date,value
2008-11-17,1000.00
2008-11-18,1000.12
```

* exakt kolumnerna `date,value`, i den ordningen
* ISO-datum `YYYY-MM-DD`, strikt stigande, inga dubbletter
* `value` = indexnivå eller NAV (positiv), inga tomma rader
* fond-NAV får inte innehålla datum före fondstart (`fetch.launch_date` i katalogen)

## Filer som pipelinen letar efter

| Fil | Catalog-id | Innehåll |
|---|---|---|
| `omrxtbill.csv` | `NASDAQ_OMRXTBILL_FULL` | OMRX Treasury Bill Index, full historik (Nasdaq) |
| `spx_tr.csv` | `SPX_TR_OFFICIAL` | S&P 500 Total Return (USD) |
| `msci_acwi_exus.csv` | `MSCI_ACWI_EXUS_OFFICIAL` | MSCI ACWI ex USA (USD; ange gross/net i sidecar) |
| `msci_acwi.csv` | `MSCI_ACWI_OFFICIAL` | MSCI ACWI (USD) |
| `us_agg.csv` | `BBG_US_AGG_OFFICIAL` | Bloomberg US Aggregate TR (USD) |
| `nav_SE0012741163.csv` | `AVZ_NAV_USA` | Avanza USA NAV (SEK) |
| `nav_SE0013718699.csv` | `AVZ_NAV_EUROPA` | Avanza Europa NAV |
| `nav_SE0012454338.csv` | `AVZ_NAV_EM` | Avanza Emerging Markets NAV |
| `nav_SE0021021425.csv` | `AVZ_NAV_RANTA_KORT` | Avanza Ränta Kort NAV |
| `nav_SE0011527613.csv` | `AVZ_NAV_GLOBAL` | Avanza Global NAV |

Se `example.csv.source.yaml` för proveniensfilens fält.
