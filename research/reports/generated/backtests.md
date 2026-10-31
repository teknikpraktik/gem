# Backtest results (generated)

All runs x execution conventions x cost scenarios. `NEXT_MONTH_CLOSE` is the primary, look-ahead-free convention; `IDEALIZED_CLOSE` is shown only for comparison with published backtests (it trades at the close that defines the signal).

Costs: `COST_0` = none, `COST_10BPS` = 10 bp per side on traded weight (a full switch costs 20 bp).

## BUY_HOLD_EXUS_PROXY_3P

Tier: `BENCHMARK`


| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1971-02-28 | 2016-12-31 | 9.89% | 17.21% | -57.37% | 0.36 | 0.52 | 0.17 | 0 | 0.00% | 551.00 | 78 | 2007-10-31..2014-04-30 | 337.0 | 1988-11-30..2016-12-31 | 1986 | 65.84% | 2008 | -45.24% | 760,053 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1971-02-28 | 2016-12-31 | 9.89% | 17.21% | -57.37% | 0.36 | 0.52 | 0.17 | 0 | 0.00% | 551.00 | 78 | 2007-10-31..2014-04-30 | 337.0 | 1988-11-30..2016-12-31 | 1986 | 65.84% | 2008 | -45.24% | 760,053 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 10.25% | 17.36% | -57.37% | 0.36 | 0.52 | 0.18 | 0 | 0.00% | 480.00 | 74 | 2007-10-31..2013-12-31 | 301.0 | 1988-11-30..2013-12-31 | 1986 | 65.84% | 2008 | -45.24% | 495,822 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 10.25% | 17.36% | -57.37% | 0.36 | 0.52 | 0.18 | 0 | 0.00% | 480.00 | 74 | 2007-10-31..2013-12-31 | 301.0 | 1988-11-30..2013-12-31 | 1986 | 65.84% | 2008 | -45.24% | 495,822 |

## BUY_HOLD_EXUS_STRICT_3P

Tier: `BENCHMARK`


| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1989-03-31 | 2016-12-31 | 4.91% | 17.25% | -57.37% | 0.19 | 0.27 | 0.09 | 0 | 0.00% | 334.00 | 78 | 2007-10-31..2014-04-30 | 334.0 | 1989-02-28..2016-12-31 | 2009 | 42.14% | 2008 | -45.24% | 37,960 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1989-03-31 | 2016-12-31 | 4.91% | 17.25% | -57.37% | 0.19 | 0.27 | 0.09 | 0 | 0.00% | 334.00 | 78 | 2007-10-31..2014-04-30 | 334.0 | 1989-02-28..2016-12-31 | 2009 | 42.14% | 2008 | -45.24% | 37,960 |

## BUY_HOLD_GLOBAL_SEK_FF_DEV_PROXY_V1__SE_3P

Tier: `BENCHMARK`

- Global buy & hold in SEK. Ken French Developed markets (incl. US, NO EM) as open proxy for MSCI ACWI.
- stop: stopped before 2026-10-31: no return for held asset(s) ['GLOBAL_EQ_SEK']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1990-08-31 | 2026-09-30 | 10.12% | 14.05% | -47.67% | 0.53 | 0.80 | 0.21 | 0 | 0.00% | 434.00 | 78 | 2000-08-31..2007-02-28 | n/a | n/a | 1993 | 43.51% | 2002 | -31.09% | 327,078 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1990-08-31 | 2026-09-30 | 10.12% | 14.05% | -47.67% | 0.53 | 0.80 | 0.21 | 0 | 0.00% | 434.00 | 78 | 2000-08-31..2007-02-28 | n/a | n/a | 1993 | 43.51% | 2002 | -31.09% | 327,078 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 0.0 | 1990-08-31 | 2016-12-31 | 8.83% | 14.30% | -47.67% | 0.38 | 0.57 | 0.19 | 0 | 0.00% | 317.00 | 78 | 2000-08-31..2007-02-28 | n/a | n/a | 1993 | 43.51% | 2002 | -31.09% | 93,408 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 10.0 | 1990-08-31 | 2016-12-31 | 8.83% | 14.30% | -47.67% | 0.38 | 0.57 | 0.19 | 0 | 0.00% | 317.00 | 78 | 2000-08-31..2007-02-28 | n/a | n/a | 1993 | 43.51% | 2002 | -31.09% | 93,408 |

## BUY_HOLD_GLOBAL_SEK_FF_DEV_PROXY_V1__SE_OPEN_SSVX

Tier: `BENCHMARK`

- Global buy & hold in SEK. Ken French Developed markets (incl. US, NO EM) as open proxy for MSCI ACWI.
- stop: stopped before 2026-10-31: no return for held asset(s) ['GLOBAL_EQ_SEK']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1990-08-31 | 2026-09-30 | 10.12% | 14.05% | -47.67% | 0.53 | 0.80 | 0.21 | 0 | 0.00% | 434.00 | 78 | 2000-08-31..2007-02-28 | n/a | n/a | 1993 | 43.51% | 2002 | -31.09% | 327,078 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1990-08-31 | 2026-09-30 | 10.12% | 14.05% | -47.67% | 0.53 | 0.80 | 0.21 | 0 | 0.00% | 434.00 | 78 | 2000-08-31..2007-02-28 | n/a | n/a | 1993 | 43.51% | 2002 | -31.09% | 327,078 |
| COMMON_SE_OPEN_SSVX | NEXT_MONTH_CLOSE | 0.0 | 1991-08-31 | 2026-09-30 | 10.28% | 13.72% | -47.67% | 0.57 | 0.88 | 0.22 | 0 | 0.00% | 422.00 | 78 | 2000-08-31..2007-02-28 | n/a | n/a | 1993 | 43.51% | 2002 | -31.09% | 312,567 |
| COMMON_SE_OPEN_SSVX | NEXT_MONTH_CLOSE | 10.0 | 1991-08-31 | 2026-09-30 | 10.28% | 13.72% | -47.67% | 0.57 | 0.88 | 0.22 | 0 | 0.00% | 422.00 | 78 | 2000-08-31..2007-02-28 | n/a | n/a | 1993 | 43.51% | 2002 | -31.09% | 312,567 |

## BUY_HOLD_US_AGG_PROXY_3P

Tier: `BENCHMARK`


| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1971-02-28 | 2016-12-31 | 7.40% | 5.33% | -12.74% | 0.47 | 0.72 | 0.58 | 0 | 0.00% | 551.00 | 16 | 1980-06-30..1981-10-31 | 507.0 | 1974-09-30..2016-12-31 | 1982 | 32.62% | 1994 | -2.92% | 264,935 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1971-02-28 | 2016-12-31 | 7.40% | 5.33% | -12.74% | 0.47 | 0.72 | 0.58 | 0 | 0.00% | 551.00 | 16 | 1980-06-30..1981-10-31 | 507.0 | 1974-09-30..2016-12-31 | 1982 | 32.62% | 1994 | -2.92% | 264,935 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 7.86% | 5.50% | -12.74% | 0.47 | 0.74 | 0.62 | 0 | 0.00% | 480.00 | 16 | 1980-06-30..1981-10-31 | 471.0 | 1974-09-30..2013-12-31 | 1982 | 32.62% | 1994 | -2.92% | 205,935 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 7.86% | 5.50% | -12.74% | 0.47 | 0.74 | 0.62 | 0 | 0.00% | 480.00 | 16 | 1980-06-30..1981-10-31 | 471.0 | 1974-09-30..2013-12-31 | 1982 | 32.62% | 1994 | -2.92% | 205,935 |

## BUY_HOLD_US_AGG_STRICT_3P

Tier: `BENCHMARK`


| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1989-03-31 | 2016-12-31 | 6.43% | 3.72% | -5.15% | 0.91 | 1.51 | 1.25 | 0 | 0.00% | 334.00 | 13 | 1999-01-31..2000-02-29 | 314.0 | 1990-10-31..2016-12-31 | 1995 | 18.47% | 1994 | -2.92% | 56,589 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1989-03-31 | 2016-12-31 | 6.43% | 3.72% | -5.15% | 0.91 | 1.51 | 1.25 | 0 | 0.00% | 334.00 | 13 | 1999-01-31..2000-02-29 | 314.0 | 1990-10-31..2016-12-31 | 1995 | 18.47% | 1994 | -2.92% | 56,589 |

## BUY_HOLD_US_PROXY_3P

Tier: `BENCHMARK`


| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1971-02-28 | 2016-12-31 | 10.37% | 15.12% | -50.95% | 0.41 | 0.61 | 0.20 | 0 | 0.00% | 551.00 | 73 | 2000-08-31..2006-09-30 | 0.0 | n/a | 1995 | 37.58% | 2008 | -37.00% | 927,490 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1971-02-28 | 2016-12-31 | 10.37% | 15.12% | -50.95% | 0.41 | 0.61 | 0.20 | 0 | 0.00% | 551.00 | 73 | 2000-08-31..2006-09-30 | 0.0 | n/a | 1995 | 37.58% | 2008 | -37.00% | 927,490 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 10.98% | 15.59% | -50.95% | 0.42 | 0.62 | 0.22 | 0 | 0.00% | 480.00 | 73 | 2000-08-31..2006-09-30 | 0.0 | n/a | 1995 | 37.58% | 2008 | -37.00% | 646,172 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 10.98% | 15.59% | -50.95% | 0.42 | 0.62 | 0.22 | 0 | 0.00% | 480.00 | 73 | 2000-08-31..2006-09-30 | 0.0 | n/a | 1995 | 37.58% | 2008 | -37.00% | 646,172 |

## BUY_HOLD_US_STRICT_3P

Tier: `BENCHMARK`


| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1989-03-31 | 2016-12-31 | 10.00% | 14.37% | -50.95% | 0.53 | 0.78 | 0.20 | 0 | 0.00% | 334.00 | 73 | 2000-08-31..2006-09-30 | 0.0 | n/a | 1995 | 37.58% | 2008 | -37.00% | 141,908 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1989-03-31 | 2016-12-31 | 10.00% | 14.37% | -50.95% | 0.53 | 0.78 | 0.20 | 0 | 0.00% | 334.00 | 73 | 2000-08-31..2006-09-30 | 0.0 | n/a | 1995 | 37.58% | 2008 | -37.00% | 141,908 |

## DIAG_EXUS_WORLD_ONLY

Tier: `DIAGNOSTIC`

- ex-US = MSCI World ex USA (developed only) for the whole period.
- Diagnostic only - not a model.

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| REF_1974_2013 | NEXT_MONTH_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 15.19% | 12.69% | -18.37% | 0.78 | 1.26 | 0.83 | 60 | 150.00% | 7.87 | 36 | 2000-03-31..2003-03-31 | 174.0 | 1987-11-30..2002-05-31 | 1986 | 65.84% | 2000 | -17.21% | 2,866,244 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 14.85% | 12.69% | -18.69% | 0.76 | 1.21 | 0.79 | 60 | 150.00% | 7.87 | 37 | 2007-10-31..2010-11-30 | 174.0 | 1987-11-30..2002-05-31 | 1986 | 65.84% | 2000 | -17.54% | 2,541,825 |
| REF_1974_2013 | IDEALIZED_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 16.27% | 12.40% | -18.21% | 0.87 | 1.46 | 0.89 | 60 | 150.00% | 7.87 | 37 | 2007-10-31..2010-11-30 | 124.0 | 1990-10-31..2001-02-28 | 1986 | 65.84% | 2000 | -16.19% | 4,159,862 |
| REF_1974_2013 | IDEALIZED_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 15.92% | 12.39% | -18.38% | 0.85 | 1.42 | 0.87 | 60 | 150.00% | 7.87 | 37 | 2007-10-31..2010-11-30 | 129.0 | 1990-10-31..2001-07-31 | 1986 | 65.84% | 2000 | -16.52% | 3,689,024 |

## DIAG_HURDLE_FF_RF_1M

Tier: `DIAGNOSTIC`

- Hurdle = Ken French RF (realised 1-month bill return) instead of 3m bill index.
- Diagnostic only - not a model.

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| REF_1974_2013 | NEXT_MONTH_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 15.68% | 12.69% | -19.19% | 0.82 | 1.34 | 0.82 | 56 | 140.00% | 8.42 | 37 | 2000-03-31..2003-04-30 | 174.0 | 1987-11-30..2002-05-31 | 1986 | 65.84% | 2000 | -18.16% | 3,388,246 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 15.35% | 12.69% | -19.35% | 0.80 | 1.30 | 0.79 | 56 | 140.00% | 8.42 | 37 | 2000-03-31..2003-04-30 | 175.0 | 1987-11-30..2002-06-30 | 1986 | 65.84% | 2000 | -18.48% | 3,028,902 |
| REF_1974_2013 | IDEALIZED_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 16.75% | 12.53% | -18.96% | 0.90 | 1.51 | 0.88 | 56 | 140.00% | 8.42 | 37 | 2007-10-31..2010-11-30 | 113.0 | 1974-09-30..1984-02-29 | 1986 | 65.84% | 2000 | -16.81% | 4,892,594 |
| REF_1974_2013 | IDEALIZED_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 16.42% | 12.52% | -19.12% | 0.88 | 1.47 | 0.86 | 56 | 140.00% | 8.42 | 37 | 2007-10-31..2010-11-30 | 113.0 | 1974-09-30..1984-02-29 | 1986 | 65.84% | 2000 | -17.14% | 4,373,705 |

## DIAG_HURDLE_TB3MS_PRIOR

Tier: `DIAGNOSTIC`

- Hurdle = TB3MS converted with our prior-month rule (r_t = y_{t-1}/1200).
- Diagnostic only - not a model.

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| REF_1974_2013 | NEXT_MONTH_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 15.68% | 12.69% | -19.19% | 0.81 | 1.32 | 0.82 | 56 | 140.00% | 8.42 | 37 | 2000-03-31..2003-04-30 | 174.0 | 1987-11-30..2002-05-31 | 1986 | 65.84% | 2000 | -18.16% | 3,388,246 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 15.35% | 12.69% | -19.35% | 0.79 | 1.28 | 0.79 | 56 | 140.00% | 8.42 | 37 | 2000-03-31..2003-04-30 | 175.0 | 1987-11-30..2002-06-30 | 1986 | 65.84% | 2000 | -18.48% | 3,028,902 |
| REF_1974_2013 | IDEALIZED_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 16.75% | 12.53% | -18.96% | 0.90 | 1.50 | 0.88 | 56 | 140.00% | 8.42 | 37 | 2007-10-31..2010-11-30 | 113.0 | 1974-09-30..1984-02-29 | 1986 | 65.84% | 2000 | -16.81% | 4,892,594 |
| REF_1974_2013 | IDEALIZED_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 16.42% | 12.52% | -19.12% | 0.87 | 1.46 | 0.86 | 56 | 140.00% | 8.42 | 37 | 2007-10-31..2010-11-30 | 113.0 | 1974-09-30..1984-02-29 | 1986 | 65.84% | 2000 | -17.14% | 4,373,705 |

## DIAG_US_MSCI_USA

Tier: `DIAGNOSTIC`

- US = MSCI USA gross instead of Ibbotson/S&P 500 TR.
- Diagnostic only - not a model.

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| REF_1974_2013 | NEXT_MONTH_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 14.97% | 12.60% | -19.43% | 0.77 | 1.23 | 0.77 | 51 | 127.50% | 9.23 | 36 | 2000-03-31..2003-03-31 | 174.0 | 1987-11-30..2002-05-31 | 1986 | 65.84% | 2000 | -17.30% | 2,646,442 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 14.67% | 12.60% | -19.59% | 0.74 | 1.19 | 0.75 | 51 | 127.50% | 9.23 | 37 | 2000-03-31..2003-04-30 | 174.0 | 1987-11-30..2002-05-31 | 1986 | 65.84% | 2000 | -17.79% | 2,389,571 |
| REF_1974_2013 | IDEALIZED_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 17.02% | 12.40% | -17.84% | 0.92 | 1.56 | 0.95 | 51 | 127.50% | 9.23 | 37 | 2007-10-31..2010-11-30 | 93.0 | 1974-09-30..1982-06-30 | 1986 | 65.84% | 2000 | -8.63% | 5,372,011 |
| REF_1974_2013 | IDEALIZED_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 16.72% | 12.40% | -18.01% | 0.90 | 1.52 | 0.93 | 51 | 127.50% | 9.23 | 37 | 2007-10-31..2010-11-30 | 93.0 | 1974-09-30..1982-06-30 | 1986 | 65.84% | 2000 | -9.00% | 4,850,590 |

## GEM_ORIGINAL_PROXY_3P

Tier: `EXTENDED_PROXY`

- US: Ibbotson Large Co. TR to 1988-01, then S&P 500 TR.
- ex-US: MSCI World ex USA (developed only) to 1987-12, then MSCI ACWI ex USA.
- Bonds: Ibbotson Intermediate Government to 1975-12, then US Aggregate.
- All from the unverified third-party compilation.
- stop: stopped before 2017-01-31: no return for held asset(s) ['US_EQUITIES']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1971-02-28 | 2016-12-31 | 15.62% | 12.62% | -19.19% | 0.84 | 1.39 | 0.81 | 63 | 137.21% | 8.61 | 37 | 2000-03-31..2003-04-30 | 165.0 | 1987-11-30..2001-08-31 | 1986 | 65.84% | 2000 | -18.16% | 7,848,002 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1971-02-28 | 2016-12-31 | 15.31% | 12.61% | -19.35% | 0.82 | 1.35 | 0.79 | 63 | 137.21% | 8.61 | 37 | 2000-03-31..2003-04-30 | 174.0 | 1987-11-30..2002-05-31 | 1986 | 65.84% | 2000 | -18.48% | 6,918,042 |
| FULL | IDEALIZED_CLOSE | 0.0 | 1971-01-31 | 2016-12-31 | 16.39% | 12.54% | -18.96% | 0.90 | 1.53 | 0.86 | 63 | 136.96% | 8.62 | 37 | 2007-10-31..2010-11-30 | 113.0 | 1974-09-30..1984-02-29 | 1986 | 65.84% | 2000 | -16.81% | 10,758,792 |
| FULL | IDEALIZED_CLOSE | 10.0 | 1971-01-31 | 2016-12-31 | 16.07% | 12.53% | -19.12% | 0.88 | 1.49 | 0.84 | 63 | 136.96% | 8.62 | 37 | 2007-10-31..2010-11-30 | 113.0 | 1974-09-30..1984-02-29 | 1986 | 65.84% | 2000 | -17.14% | 9,483,914 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 15.84% | 12.66% | -19.19% | 0.82 | 1.35 | 0.83 | 56 | 140.00% | 8.42 | 37 | 2000-03-31..2003-04-30 | 165.0 | 1987-11-30..2001-08-31 | 1986 | 65.84% | 2000 | -18.16% | 3,585,032 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 15.52% | 12.65% | -19.35% | 0.80 | 1.31 | 0.80 | 56 | 140.00% | 8.42 | 37 | 2000-03-31..2003-04-30 | 174.0 | 1987-11-30..2002-05-31 | 1986 | 65.84% | 2000 | -18.48% | 3,204,817 |
| REF_1974_2013 | IDEALIZED_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 16.80% | 12.49% | -18.96% | 0.90 | 1.51 | 0.89 | 56 | 140.00% | 8.42 | 37 | 2007-10-31..2010-11-30 | 113.0 | 1974-09-30..1984-02-29 | 1986 | 65.84% | 2000 | -16.81% | 4,990,436 |
| REF_1974_2013 | IDEALIZED_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 16.48% | 12.49% | -19.12% | 0.88 | 1.47 | 0.86 | 56 | 140.00% | 8.42 | 37 | 2007-10-31..2010-11-30 | 113.0 | 1974-09-30..1984-02-29 | 1986 | 65.84% | 2000 | -17.14% | 4,461,171 |

## GEM_ORIGINAL_STRICT_3P

Tier: `STRICT_3P`

- Same index definitions as GEM_ORIGINAL; values from an unverified third-party compilation (alexjansenhome/GEM). Not presented as verified GEM.
- stop: stopped before 2017-01-31: no return for held asset(s) ['US_EQUITIES']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1989-03-31 | 2016-12-31 | 13.41% | 12.10% | -19.19% | 0.86 | 1.39 | 0.70 | 30 | 107.78% | 10.77 | 37 | 2000-03-31..2003-04-30 | 149.0 | 1989-02-28..2001-07-31 | 1997 | 33.36% | 2000 | -18.16% | 331,784 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1989-03-31 | 2016-12-31 | 13.16% | 12.10% | -19.35% | 0.84 | 1.35 | 0.68 | 30 | 107.78% | 10.77 | 37 | 2000-03-31..2003-04-30 | 149.0 | 1989-02-28..2001-07-31 | 1997 | 33.36% | 2000 | -18.48% | 312,444 |
| FULL | IDEALIZED_CLOSE | 0.0 | 1989-02-28 | 2016-12-31 | 13.60% | 12.00% | -18.96% | 0.88 | 1.43 | 0.72 | 30 | 107.46% | 10.81 | 37 | 2007-10-31..2010-11-30 | 94.0 | 2009-02-28..2016-12-31 | 1995 | 34.75% | 2000 | -16.81% | 351,468 |
| FULL | IDEALIZED_CLOSE | 10.0 | 1989-02-28 | 2016-12-31 | 13.35% | 12.00% | -19.12% | 0.86 | 1.40 | 0.70 | 30 | 107.46% | 10.81 | 37 | 2007-10-31..2010-11-30 | 94.0 | 2009-02-28..2016-12-31 | 1995 | 34.48% | 2000 | -17.14% | 330,980 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 0.0 | 1990-08-31 | 2016-12-31 | 13.41% | 12.02% | -19.19% | 0.89 | 1.42 | 0.70 | 29 | 109.78% | 10.57 | 37 | 2000-03-31..2003-04-30 | 129.0 | 1990-10-31..2001-07-31 | 1997 | 33.36% | 2000 | -18.16% | 277,488 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 10.0 | 1990-08-31 | 2016-12-31 | 13.16% | 12.03% | -19.35% | 0.87 | 1.39 | 0.68 | 29 | 109.78% | 10.57 | 37 | 2000-03-31..2003-04-30 | 129.0 | 1990-10-31..2001-07-31 | 1997 | 33.36% | 2000 | -18.48% | 261,837 |
| COMMON_SE_3P | IDEALIZED_CLOSE | 0.0 | 1990-08-31 | 2016-12-31 | 13.47% | 11.91% | -18.96% | 0.90 | 1.46 | 0.71 | 28 | 105.99% | 10.93 | 37 | 2007-10-31..2010-11-30 | 94.0 | 2009-02-28..2016-12-31 | 1995 | 34.75% | 2000 | -16.81% | 281,715 |
| COMMON_SE_3P | IDEALIZED_CLOSE | 10.0 | 1990-08-31 | 2016-12-31 | 13.23% | 11.91% | -19.12% | 0.88 | 1.42 | 0.69 | 28 | 105.99% | 10.93 | 37 | 2007-10-31..2010-11-30 | 94.0 | 2009-02-28..2016-12-31 | 1995 | 34.48% | 2000 | -17.14% | 266,358 |

## GEM_SEK_3P_SSVXSYNTH_V1

Tier: `SWEDISH`

- NOT GEM. S&P 500 TR and MSCI ACWI ex USA (third-party copies) in SEK; Swedish cash = SE_CASH_SSVX_SYNTH_V1 (3m T-bill yield -> return, PROXY).
- stop: stopped before 2017-01-31: no return for held asset(s) ['SEK_US_EQ']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1989-03-31 | 2016-12-31 | 12.70% | 11.58% | -18.81% | 0.71 | 1.22 | 0.68 | 49 | 176.05% | 6.68 | 60 | 2000-08-31..2005-08-31 | n/a | n/a | 1997 | 55.15% | 2000 | -9.12% | 279,088 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1989-03-31 | 2016-12-31 | 12.31% | 11.57% | -19.62% | 0.68 | 1.16 | 0.63 | 49 | 176.05% | 6.68 | 60 | 2000-08-31..2005-08-31 | n/a | n/a | 1997 | 55.15% | 2000 | -9.48% | 253,010 |
| FULL | IDEALIZED_CLOSE | 0.0 | 1989-02-28 | 2016-12-31 | 13.03% | 11.64% | -21.15% | 0.73 | 1.25 | 0.62 | 49 | 175.52% | 6.70 | 42 | 2000-08-31..2004-02-29 | n/a | n/a | 1997 | 55.15% | 2000 | -8.86% | 305,408 |
| FULL | IDEALIZED_CLOSE | 10.0 | 1989-02-28 | 2016-12-31 | 12.63% | 11.63% | -21.94% | 0.70 | 1.20 | 0.58 | 49 | 175.52% | 6.70 | 57 | 2000-08-31..2005-05-31 | n/a | n/a | 1997 | 55.15% | 2001 | -9.11% | 276,871 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 0.0 | 1990-08-31 | 2016-12-31 | 12.69% | 11.40% | -18.81% | 0.76 | 1.30 | 0.67 | 45 | 170.35% | 6.89 | 60 | 2000-08-31..2005-08-31 | 93.0 | 2009-03-31..2016-12-31 | 1997 | 55.15% | 2000 | -9.12% | 234,716 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 10.0 | 1990-08-31 | 2016-12-31 | 12.31% | 11.39% | -19.62% | 0.73 | 1.25 | 0.63 | 45 | 170.35% | 6.89 | 60 | 2000-08-31..2005-08-31 | 93.0 | 2009-03-31..2016-12-31 | 1997 | 55.15% | 2000 | -9.48% | 214,495 |
| COMMON_SE_3P | IDEALIZED_CLOSE | 0.0 | 1990-08-31 | 2016-12-31 | 13.25% | 11.60% | -21.15% | 0.79 | 1.38 | 0.63 | 45 | 170.35% | 6.89 | 42 | 2000-08-31..2004-02-29 | 93.0 | 2009-03-31..2016-12-31 | 1997 | 55.15% | 2000 | -8.86% | 267,750 |
| COMMON_SE_3P | IDEALIZED_CLOSE | 10.0 | 1990-08-31 | 2016-12-31 | 12.87% | 11.59% | -21.94% | 0.76 | 1.32 | 0.59 | 45 | 170.35% | 6.89 | 57 | 2000-08-31..2005-05-31 | 93.0 | 2009-03-31..2016-12-31 | 1997 | 55.15% | 2001 | -9.11% | 244,683 |

## REGIONAL_SEK_FF_PROXY_SSVXSYNTH_V1

Tier: `SWEDISH`

- NOT GEM. As REGIONAL_SEK_FF_PROXY_OMRX_V1 with synthetic SSVX cash (PROXY, longer history).
- stop: stopped before 2026-10-31: no return for held asset(s) ['SE_EM_EQ']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1991-08-31 | 2026-09-30 | 11.62% | 15.75% | -38.15% | 0.60 | 0.93 | 0.30 | 85 | 241.71% | 4.91 | 64 | 2000-02-29..2005-06-30 | 210.0 | 2009-03-31..2026-09-30 | 1993 | 93.94% | 1994 | -21.02% | 478,161 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1991-08-31 | 2026-09-30 | 11.09% | 15.74% | -39.62% | 0.56 | 0.87 | 0.28 | 85 | 241.71% | 4.91 | 64 | 2000-02-29..2005-06-30 | 210.0 | 2009-03-31..2026-09-30 | 1993 | 93.17% | 1994 | -21.02% | 403,339 |
| FULL | IDEALIZED_CLOSE | 0.0 | 1991-07-31 | 2026-09-30 | 13.72% | 14.87% | -24.18% | 0.75 | 1.21 | 0.57 | 85 | 241.13% | 4.92 | 48 | 2000-02-29..2004-02-29 | 210.0 | 2009-03-31..2026-09-30 | 1993 | 101.30% | 2000 | -14.50% | 928,300 |
| FULL | IDEALIZED_CLOSE | 10.0 | 1991-07-31 | 2026-09-30 | 13.17% | 14.86% | -25.68% | 0.72 | 1.16 | 0.51 | 85 | 241.13% | 4.92 | 58 | 2000-02-29..2004-12-31 | 210.0 | 2009-03-31..2026-09-30 | 1993 | 100.90% | 2011 | -14.87% | 783,040 |
| COMMON_SE_OPEN_SSVX | NEXT_MONTH_CLOSE | 0.0 | 1991-08-31 | 2026-09-30 | 11.62% | 15.75% | -38.15% | 0.60 | 0.93 | 0.30 | 85 | 241.71% | 4.91 | 64 | 2000-02-29..2005-06-30 | 210.0 | 2009-03-31..2026-09-30 | 1993 | 93.94% | 1994 | -21.02% | 478,161 |
| COMMON_SE_OPEN_SSVX | NEXT_MONTH_CLOSE | 10.0 | 1991-08-31 | 2026-09-30 | 11.09% | 15.74% | -39.62% | 0.56 | 0.87 | 0.28 | 85 | 241.71% | 4.91 | 64 | 2000-02-29..2005-06-30 | 210.0 | 2009-03-31..2026-09-30 | 1993 | 93.17% | 1994 | -21.02% | 403,339 |
| COMMON_SE_OPEN_SSVX | IDEALIZED_CLOSE | 0.0 | 1991-08-31 | 2026-09-30 | 13.68% | 14.89% | -24.18% | 0.75 | 1.21 | 0.57 | 85 | 241.71% | 4.91 | 48 | 2000-02-29..2004-02-29 | 210.0 | 2009-03-31..2026-09-30 | 1993 | 101.30% | 2000 | -14.50% | 908,128 |
| COMMON_SE_OPEN_SSVX | IDEALIZED_CLOSE | 10.0 | 1991-08-31 | 2026-09-30 | 13.13% | 14.88% | -25.68% | 0.71 | 1.15 | 0.51 | 85 | 241.71% | 4.91 | 58 | 2000-02-29..2004-12-31 | 210.0 | 2009-03-31..2026-09-30 | 1993 | 100.90% | 2011 | -14.87% | 766,025 |

## STATIC_70_30_SEK_FF_DEV_PROXY_V1__SE_3P

Tier: `BENCHMARK`

- 70 % global equity (FF Developed, SEK) / 30 % Swedish short rate, monthly rebalanced. The 30 % leg is Swedish cash, not bonds - the defensive asset a Swedish investor actually uses here.
- stop: stopped before 2026-10-31: no return for held asset(s) ['GLOBAL_EQ_SEK']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1990-08-31 | 2026-09-30 | 8.23% | 9.83% | -33.83% | 0.53 | 0.80 | 0.24 | 0 | 7.93% | 434.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1993 | 32.43% | 2002 | -21.59% | 174,810 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1990-08-31 | 2026-09-30 | 8.22% | 9.83% | -33.87% | 0.53 | 0.80 | 0.24 | 0 | 7.93% | 434.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1993 | 32.40% | 2002 | -21.61% | 173,811 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 0.0 | 1990-08-31 | 2016-12-31 | 7.61% | 10.01% | -33.83% | 0.38 | 0.57 | 0.22 | 0 | 8.01% | 317.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1993 | 32.43% | 2002 | -21.59% | 69,396 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 10.0 | 1990-08-31 | 2016-12-31 | 7.59% | 10.01% | -33.87% | 0.38 | 0.56 | 0.22 | 0 | 8.01% | 317.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1993 | 32.40% | 2002 | -21.61% | 69,103 |

## STATIC_70_30_SEK_FF_DEV_PROXY_V1__SE_OPEN_SSVX

Tier: `BENCHMARK`

- 70 % global equity (FF Developed, SEK) / 30 % Swedish short rate, monthly rebalanced. The 30 % leg is Swedish cash, not bonds - the defensive asset a Swedish investor actually uses here.
- stop: stopped before 2026-10-31: no return for held asset(s) ['GLOBAL_EQ_SEK']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1990-08-31 | 2026-09-30 | 8.23% | 9.83% | -33.83% | 0.53 | 0.80 | 0.24 | 0 | 7.93% | 434.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1993 | 32.43% | 2002 | -21.59% | 174,810 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1990-08-31 | 2026-09-30 | 8.22% | 9.83% | -33.87% | 0.53 | 0.80 | 0.24 | 0 | 7.93% | 434.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1993 | 32.40% | 2002 | -21.61% | 173,811 |
| COMMON_SE_OPEN_SSVX | NEXT_MONTH_CLOSE | 0.0 | 1991-08-31 | 2026-09-30 | 8.24% | 9.60% | -33.83% | 0.57 | 0.88 | 0.24 | 0 | 7.81% | 422.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1993 | 32.43% | 2002 | -21.59% | 162,033 |
| COMMON_SE_OPEN_SSVX | NEXT_MONTH_CLOSE | 10.0 | 1991-08-31 | 2026-09-30 | 8.23% | 9.60% | -33.87% | 0.57 | 0.87 | 0.24 | 0 | 7.81% | 422.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1993 | 32.40% | 2002 | -21.61% | 161,146 |

## STATIC_70_30_US_PROXY_3P

Tier: `BENCHMARK`

- Benchmark on the same third-party data as the GEM run. US equity, not global: no MSCI ACWI series was available.

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1971-02-28 | 2016-12-31 | 9.73% | 11.01% | -37.62% | 0.46 | 0.70 | 0.26 | 0 | 8.18% | 551.00 | 57 | 2000-08-31..2005-05-31 | 507.0 | 1974-09-30..2016-12-31 | 1995 | 31.61% | 2008 | -26.03% | 711,531 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1971-02-28 | 2016-12-31 | 9.72% | 11.01% | -37.64% | 0.46 | 0.69 | 0.26 | 0 | 8.18% | 551.00 | 58 | 2000-08-31..2005-06-30 | 507.0 | 1974-09-30..2016-12-31 | 1995 | 31.60% | 2008 | -26.05% | 706,204 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 0.0 | 1974-01-31 | 2013-12-31 | 10.31% | 11.37% | -37.62% | 0.47 | 0.71 | 0.27 | 0 | 8.42% | 480.00 | 57 | 2000-08-31..2005-05-31 | 471.0 | 1974-09-30..2013-12-31 | 1995 | 31.61% | 2008 | -26.03% | 507,431 |
| REF_1974_2013 | NEXT_MONTH_CLOSE | 10.0 | 1974-01-31 | 2013-12-31 | 10.30% | 11.37% | -37.64% | 0.47 | 0.71 | 0.27 | 0 | 8.42% | 480.00 | 58 | 2000-08-31..2005-06-30 | 471.0 | 1974-09-30..2013-12-31 | 1995 | 31.60% | 2008 | -26.05% | 504,024 |

## STATIC_70_30_US_STRICT_3P

Tier: `BENCHMARK`

- Benchmark on the same third-party data as the GEM run. US equity, not global: no MSCI ACWI series was available.

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1989-03-31 | 2016-12-31 | 9.16% | 10.24% | -37.62% | 0.62 | 0.93 | 0.24 | 0 | 8.07% | 334.00 | 57 | 2000-08-31..2005-05-31 | 218.0 | 1990-10-31..2008-12-31 | 1995 | 31.61% | 2008 | -26.03% | 114,583 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1989-03-31 | 2016-12-31 | 9.14% | 10.24% | -37.64% | 0.62 | 0.93 | 0.24 | 0 | 8.07% | 334.00 | 58 | 2000-08-31..2005-06-30 | 219.0 | 1990-10-31..2009-01-31 | 1995 | 31.60% | 2008 | -26.05% | 114,070 |

## STATIC_REGIONAL_EQUAL_SEK_FF_V1__SE_OPEN_SSVX

Tier: `BENCHMARK`

- Static 1/3-1/3-1/3 regional portfolio in SEK, monthly rebalanced. Equal weights are the parameter-free choice, not optimised.
- stop: stopped before 2026-10-31: no return for held asset(s) ['SE_USA_EQ', 'SE_EUROPE_EQ', 'SE_EM_EQ']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1990-08-31 | 2026-09-30 | 10.85% | 14.82% | -44.65% | 0.56 | 0.83 | 0.24 | 0 | 9.87% | 434.00 | 64 | 2007-10-31..2013-02-28 | n/a | n/a | 1993 | 64.85% | 2008 | -33.63% | 415,517 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1990-08-31 | 2026-09-30 | 10.83% | 14.82% | -44.68% | 0.56 | 0.83 | 0.24 | 0 | 9.87% | 434.00 | 64 | 2007-10-31..2013-02-28 | n/a | n/a | 1993 | 64.82% | 2008 | -33.65% | 412,561 |
| COMMON_SE_OPEN_SSVX | NEXT_MONTH_CLOSE | 0.0 | 1991-08-31 | 2026-09-30 | 10.98% | 14.59% | -44.65% | 0.59 | 0.89 | 0.25 | 0 | 9.80% | 422.00 | 64 | 2007-10-31..2013-02-28 | n/a | n/a | 1993 | 64.85% | 2008 | -33.63% | 390,246 |
| COMMON_SE_OPEN_SSVX | NEXT_MONTH_CLOSE | 10.0 | 1991-08-31 | 2026-09-30 | 10.96% | 14.59% | -44.68% | 0.59 | 0.89 | 0.25 | 0 | 9.80% | 422.00 | 64 | 2007-10-31..2013-02-28 | n/a | n/a | 1993 | 64.82% | 2008 | -33.65% | 387,566 |

## Blocked runs

Runs that could not be executed because required series were unavailable. Nothing was substituted.

### BUY_HOLD_GLOBAL_SEK_ACWI_V1 (`BENCHMARK`)
- `MSCI_ACWI_OFFICIAL`: manual file not supplied: /home/runner/work/gem/gem/research/data/manual/msci_acwi.csv
- `NASDAQ_OMRXTBILL_FULL`: manual file not supplied: /home/runner/work/gem/gem/research/data/manual/omrxtbill.csv

### BUY_HOLD_GLOBAL_SEK_FF_DEV_PROXY_V1__SE_OPEN_OMRX (`BENCHMARK`)
- `FRED_OMRXTBILL`: offline and no cache for fred/FRED_OMRXTBILL

### GEM_ORIGINAL_OPEN_V1__SE_OPEN_OMRX (`EXTENDED_PROXY`)
- `FRED_GS5`: offline and no cache for fred/FRED_GS5
- `FRED_NASDAQ_GLOBAL_EXUS_LM_NTR`: offline and no cache for fred/FRED_NASDAQ_GLOBAL_EXUS_LM_NTR

### GEM_ORIGINAL_OPEN_V1__SE_OPEN_SSVX (`EXTENDED_PROXY`)
- `FRED_GS5`: offline and no cache for fred/FRED_GS5
- `FRED_NASDAQ_GLOBAL_EXUS_LM_NTR`: offline and no cache for fred/FRED_NASDAQ_GLOBAL_EXUS_LM_NTR

### GEM_ORIGINAL_STRICT (`STRICT`)
- `BBG_US_AGG_OFFICIAL`: manual file not supplied: /home/runner/work/gem/gem/research/data/manual/us_agg.csv
- `FRED_DTB3`: offline and no cache for fred/FRED_DTB3
- `MSCI_ACWI_EXUS_OFFICIAL`: manual file not supplied: /home/runner/work/gem/gem/research/data/manual/msci_acwi_exus.csv
- `SPX_TR_OFFICIAL`: manual file not supplied: /home/runner/work/gem/gem/research/data/manual/spx_tr.csv

### GEM_PROXY_FF (`EXTENDED_PROXY`)
- `FRED_GS5`: offline and no cache for fred/FRED_GS5

### GEM_SEK_OPEN_OMRX_V1 (`SWEDISH`)
- `FRED_NASDAQ_GLOBAL_EXUS_LM_NTR`: offline and no cache for fred/FRED_NASDAQ_GLOBAL_EXUS_LM_NTR
- `FRED_OMRXTBILL`: offline and no cache for fred/FRED_OMRXTBILL

### GEM_SEK_OPEN_SSVXSYNTH_V1 (`SWEDISH`)
- `FRED_NASDAQ_GLOBAL_EXUS_LM_NTR`: offline and no cache for fred/FRED_NASDAQ_GLOBAL_EXUS_LM_NTR

### GEM_SEK_STRICT_V1 (`SWEDISH`)
- `MSCI_ACWI_EXUS_OFFICIAL`: manual file not supplied: /home/runner/work/gem/gem/research/data/manual/msci_acwi_exus.csv
- `MSCI_ACWI_OFFICIAL`: manual file not supplied: /home/runner/work/gem/gem/research/data/manual/msci_acwi.csv
- `NASDAQ_OMRXTBILL_FULL`: manual file not supplied: /home/runner/work/gem/gem/research/data/manual/omrxtbill.csv
- `SPX_TR_OFFICIAL`: manual file not supplied: /home/runner/work/gem/gem/research/data/manual/spx_tr.csv

### REGIONAL_SEK_FF_PROXY_OMRX_V1 (`SWEDISH`)
- `FRED_OMRXTBILL`: offline and no cache for fred/FRED_OMRXTBILL

### STATIC_70_30_SEK_ACWI_V1 (`BENCHMARK`)
- `MSCI_ACWI_OFFICIAL`: manual file not supplied: /home/runner/work/gem/gem/research/data/manual/msci_acwi.csv
- `NASDAQ_OMRXTBILL_FULL`: manual file not supplied: /home/runner/work/gem/gem/research/data/manual/omrxtbill.csv

### STATIC_70_30_SEK_FF_DEV_PROXY_V1__SE_OPEN_OMRX (`BENCHMARK`)
- `FRED_OMRXTBILL`: offline and no cache for fred/FRED_OMRXTBILL

### STATIC_REGIONAL_EQUAL_SEK_FF_V1__SE_OPEN_OMRX (`BENCHMARK`)
- `FRED_OMRXTBILL`: offline and no cache for fred/FRED_OMRXTBILL

