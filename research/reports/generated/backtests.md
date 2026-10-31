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
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1993-03-31 | 2026-09-30 | 10.04% | 13.34% | -47.50% | 0.60 | 0.90 | 0.21 | 0 | 0.00% | 403.00 | 76 | 2000-08-31..2006-12-31 | n/a | n/a | 1999 | 36.87% | 2002 | -31.44% | 248,625 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1993-03-31 | 2026-09-30 | 10.04% | 13.34% | -47.50% | 0.60 | 0.90 | 0.21 | 0 | 0.00% | 403.00 | 76 | 2000-08-31..2006-12-31 | n/a | n/a | 1999 | 36.87% | 2002 | -31.44% | 248,625 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2016-12-31 | 7.73% | 13.53% | -47.50% | 0.40 | 0.59 | 0.16 | 0 | 0.00% | 274.00 | 76 | 2000-08-31..2006-12-31 | n/a | n/a | 1999 | 36.87% | 2002 | -31.44% | 54,750 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2016-12-31 | 7.73% | 13.53% | -47.50% | 0.40 | 0.59 | 0.16 | 0 | 0.00% | 274.00 | 76 | 2000-08-31..2006-12-31 | n/a | n/a | 1999 | 36.87% | 2002 | -31.44% | 54,750 |

## BUY_HOLD_GLOBAL_SEK_FF_DEV_PROXY_V1__SE_FF_SSVX

Tier: `BENCHMARK`

- Global buy & hold in SEK. Ken French Developed markets (incl. US, NO EM) as open proxy for MSCI ACWI.
- stop: stopped before 2026-10-31: no return for held asset(s) ['GLOBAL_EQ_SEK']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1993-03-31 | 2026-09-30 | 10.04% | 13.34% | -47.50% | 0.60 | 0.90 | 0.21 | 0 | 0.00% | 403.00 | 76 | 2000-08-31..2006-12-31 | n/a | n/a | 1999 | 36.87% | 2002 | -31.44% | 248,625 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1993-03-31 | 2026-09-30 | 10.04% | 13.34% | -47.50% | 0.60 | 0.90 | 0.21 | 0 | 0.00% | 403.00 | 76 | 2000-08-31..2006-12-31 | n/a | n/a | 1999 | 36.87% | 2002 | -31.44% | 248,625 |
| COMMON_SE_FF_SSVX | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2026-09-30 | 9.48% | 13.35% | -47.50% | 0.57 | 0.85 | 0.20 | 0 | 0.00% | 391.00 | 76 | 2000-08-31..2006-12-31 | n/a | n/a | 1999 | 36.87% | 2002 | -31.44% | 191,014 |
| COMMON_SE_FF_SSVX | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2026-09-30 | 9.48% | 13.35% | -47.50% | 0.57 | 0.85 | 0.20 | 0 | 0.00% | 391.00 | 76 | 2000-08-31..2006-12-31 | n/a | n/a | 1999 | 36.87% | 2002 | -31.44% | 191,014 |

## BUY_HOLD_GLOBAL_SEK_FF_DEV_PROXY_V1__SE_OPEN_SSVX

Tier: `BENCHMARK`

- Global buy & hold in SEK. Ken French Developed markets (incl. US, NO EM) as open proxy for MSCI ACWI.
- stop: stopped before 2026-10-31: no return for held asset(s) ['GLOBAL_EQ_SEK']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1993-03-31 | 2026-09-30 | 10.04% | 13.34% | -47.50% | 0.60 | 0.90 | 0.21 | 0 | 0.00% | 403.00 | 76 | 2000-08-31..2006-12-31 | n/a | n/a | 1999 | 36.87% | 2002 | -31.44% | 248,625 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1993-03-31 | 2026-09-30 | 10.04% | 13.34% | -47.50% | 0.60 | 0.90 | 0.21 | 0 | 0.00% | 403.00 | 76 | 2000-08-31..2006-12-31 | n/a | n/a | 1999 | 36.87% | 2002 | -31.44% | 248,625 |

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

## GEM_ORIGINAL_FF_V1__SE_FF_SSVX

Tier: `EXTENDED_PROXY`

- GEM rule in USD on the same equity legs as GEM_SEK_FF_PROXY_SSVXSYNTH_V1; hurdle = Ken French RF. Defensive asset = US T-bills (FF RF) because no open US bond TR series is reachable without FRED - this changes returns in risk-off months, NOT the signals. Comparison partner only.

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1991-08-31 | 2026-09-30 | 10.53% | 12.83% | -23.16% | 0.65 | 1.01 | 0.45 | 52 | 147.87% | 7.96 | 45 | 2000-03-31..2003-12-31 | 211.0 | 2009-02-28..2026-09-30 | 1997 | 31.25% | 2000 | -21.01% | 338,516 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1991-08-31 | 2026-09-30 | 10.21% | 12.84% | -23.62% | 0.63 | 0.97 | 0.43 | 52 | 147.87% | 7.96 | 46 | 2000-03-31..2004-01-31 | 211.0 | 2009-02-28..2026-09-30 | 1997 | 31.25% | 2000 | -21.16% | 305,047 |
| FULL | IDEALIZED_CLOSE | 0.0 | 1991-07-31 | 2026-09-30 | 10.26% | 12.43% | -23.22% | 0.65 | 0.99 | 0.44 | 52 | 147.52% | 7.98 | 44 | 2000-03-31..2003-11-30 | 211.0 | 2009-02-28..2026-09-30 | 1997 | 31.25% | 2000 | -17.49% | 312,561 |
| FULL | IDEALIZED_CLOSE | 10.0 | 1991-07-31 | 2026-09-30 | 9.93% | 12.41% | -23.99% | 0.63 | 0.95 | 0.41 | 52 | 147.52% | 7.98 | 44 | 2000-03-31..2003-11-30 | 211.0 | 2009-02-28..2026-09-30 | 1997 | 31.25% | 2000 | -17.82% | 281,658 |
| COMMON_SE_FF_SSVX | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2026-09-30 | 10.26% | 12.76% | -23.16% | 0.64 | 0.98 | 0.44 | 51 | 156.52% | 7.52 | 45 | 2000-03-31..2003-12-31 | 211.0 | 2009-02-28..2026-09-30 | 1997 | 31.25% | 2000 | -21.01% | 241,133 |
| COMMON_SE_FF_SSVX | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2026-09-30 | 9.92% | 12.77% | -23.62% | 0.62 | 0.94 | 0.42 | 51 | 156.52% | 7.52 | 46 | 2000-03-31..2004-01-31 | 211.0 | 2009-02-28..2026-09-30 | 1997 | 31.25% | 2000 | -21.16% | 217,728 |
| COMMON_SE_FF_SSVX | IDEALIZED_CLOSE | 0.0 | 1994-03-31 | 2026-09-30 | 9.82% | 12.32% | -23.22% | 0.63 | 0.94 | 0.42 | 51 | 156.52% | 7.52 | 44 | 2000-03-31..2003-11-30 | 211.0 | 2009-02-28..2026-09-30 | 1997 | 31.25% | 2000 | -17.49% | 211,747 |
| COMMON_SE_FF_SSVX | IDEALIZED_CLOSE | 10.0 | 1994-03-31 | 2026-09-30 | 9.48% | 12.30% | -23.99% | 0.60 | 0.90 | 0.40 | 51 | 156.52% | 7.52 | 44 | 2000-03-31..2003-11-30 | 211.0 | 2009-02-28..2026-09-30 | 1997 | 31.25% | 2000 | -17.82% | 191,195 |

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
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2016-12-31 | 13.60% | 11.88% | -19.19% | 0.93 | 1.50 | 0.71 | 26 | 113.87% | 10.15 | 37 | 2000-03-31..2003-04-30 | 94.0 | 2009-02-28..2016-12-31 | 1997 | 33.36% | 2000 | -18.16% | 183,966 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2016-12-31 | 13.34% | 11.89% | -19.35% | 0.91 | 1.46 | 0.69 | 26 | 113.87% | 10.15 | 37 | 2000-03-31..2003-04-30 | 94.0 | 2009-02-28..2016-12-31 | 1997 | 33.36% | 2000 | -18.48% | 174,635 |
| COMMON_SE_3P | IDEALIZED_CLOSE | 0.0 | 1994-03-31 | 2016-12-31 | 13.00% | 11.87% | -18.96% | 0.89 | 1.41 | 0.69 | 26 | 113.87% | 10.15 | 37 | 2007-10-31..2010-11-30 | 94.0 | 2009-02-28..2016-12-31 | 1995 | 34.75% | 2000 | -16.81% | 162,776 |
| COMMON_SE_3P | IDEALIZED_CLOSE | 10.0 | 1994-03-31 | 2016-12-31 | 12.74% | 11.87% | -19.12% | 0.87 | 1.37 | 0.67 | 26 | 113.87% | 10.15 | 37 | 2007-10-31..2010-11-30 | 94.0 | 2009-02-28..2016-12-31 | 1995 | 34.48% | 2000 | -17.14% | 154,519 |

## GEM_SEK_3P_SSVXSYNTH_V1

Tier: `SWEDISH`

- NOT GEM. S&P 500 TR and MSCI ACWI ex USA (third-party copies) in SEK; Swedish cash = SE_CASH_SSVX_SYNTH_V1 (3m T-bill yield -> return, PROXY).
- stop: stopped before 2017-01-31: no return for held asset(s) ['SEK_US_EQ']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2016-12-31 | 11.58% | 11.47% | -19.69% | 0.76 | 1.30 | 0.59 | 37 | 162.04% | 7.21 | 58 | 2000-10-31..2005-08-31 | 93.0 | 2009-03-31..2016-12-31 | 1997 | 52.78% | 2000 | -8.46% | 121,943 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2016-12-31 | 11.21% | 11.46% | -20.33% | 0.74 | 1.25 | 0.55 | 37 | 162.04% | 7.21 | 58 | 2000-10-31..2005-08-31 | 93.0 | 2009-03-31..2016-12-31 | 1997 | 52.78% | 2000 | -8.83% | 113,237 |
| FULL | IDEALIZED_CLOSE | 0.0 | 1994-02-28 | 2016-12-31 | 12.14% | 11.54% | -20.59% | 0.80 | 1.39 | 0.59 | 37 | 161.45% | 7.24 | 55 | 2000-10-31..2005-05-31 | 93.0 | 2009-03-31..2016-12-31 | 1997 | 52.78% | 2000 | -8.20% | 138,268 |
| FULL | IDEALIZED_CLOSE | 10.0 | 1994-02-28 | 2016-12-31 | 11.78% | 11.53% | -21.22% | 0.77 | 1.34 | 0.56 | 37 | 161.45% | 7.24 | 56 | 2000-10-31..2005-06-30 | 93.0 | 2009-03-31..2016-12-31 | 1997 | 52.78% | 2001 | -8.70% | 128,396 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2016-12-31 | 11.58% | 11.47% | -19.69% | 0.76 | 1.30 | 0.59 | 37 | 162.04% | 7.21 | 58 | 2000-10-31..2005-08-31 | 93.0 | 2009-03-31..2016-12-31 | 1997 | 52.78% | 2000 | -8.46% | 121,943 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2016-12-31 | 11.21% | 11.46% | -20.33% | 0.74 | 1.25 | 0.55 | 37 | 162.04% | 7.21 | 58 | 2000-10-31..2005-08-31 | 93.0 | 2009-03-31..2016-12-31 | 1997 | 52.78% | 2000 | -8.83% | 113,237 |
| COMMON_SE_3P | IDEALIZED_CLOSE | 0.0 | 1994-03-31 | 2016-12-31 | 12.20% | 11.56% | -20.59% | 0.81 | 1.40 | 0.59 | 37 | 162.04% | 7.21 | 55 | 2000-10-31..2005-05-31 | 93.0 | 2009-03-31..2016-12-31 | 1997 | 52.78% | 2000 | -8.20% | 138,539 |
| COMMON_SE_3P | IDEALIZED_CLOSE | 10.0 | 1994-03-31 | 2016-12-31 | 11.84% | 11.55% | -21.22% | 0.78 | 1.34 | 0.56 | 37 | 162.04% | 7.21 | 56 | 2000-10-31..2005-06-30 | 93.0 | 2009-03-31..2016-12-31 | 1997 | 52.78% | 2001 | -8.70% | 128,648 |

## GEM_SEK_FF_PROXY_SSVXSYNTH_V1

Tier: `SWEDISH`

- NOT GEM. US = CRSP all US stocks (Ken French); ex-US = Ken French Developed ex US (NO emerging markets - deviation from ACWI ex USA); Swedish cash = SE_CASH_SSVX_SYNTH_V1 (Riksbank SETB3MBENCH yield -> return, PROXY); FX = Riksbank SEKUSDPMI.
- stop: stopped before 2026-10-31: no return for held asset(s) ['SEK_EXUS_EQ']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2026-09-30 | 11.30% | 12.33% | -20.03% | 0.75 | 1.22 | 0.56 | 65 | 199.49% | 5.92 | 37 | 2000-08-31..2003-09-30 | 210.0 | 2009-03-31..2026-09-30 | 1997 | 50.35% | 2000 | -11.65% | 326,981 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2026-09-30 | 10.85% | 12.34% | -20.04% | 0.71 | 1.16 | 0.54 | 65 | 199.49% | 5.92 | 46 | 2006-04-30..2010-02-28 | 210.0 | 2009-03-31..2026-09-30 | 1997 | 50.35% | 2000 | -11.82% | 287,083 |
| FULL | IDEALIZED_CLOSE | 0.0 | 1994-02-28 | 2026-09-30 | 11.71% | 12.29% | -16.79% | 0.78 | 1.28 | 0.70 | 65 | 198.98% | 5.94 | 57 | 2000-08-31..2005-05-31 | 210.0 | 2009-03-31..2026-09-30 | 1997 | 50.35% | 2000 | -6.63% | 372,532 |
| FULL | IDEALIZED_CLOSE | 10.0 | 1994-02-28 | 2026-09-30 | 11.27% | 12.28% | -16.95% | 0.75 | 1.23 | 0.66 | 65 | 198.98% | 5.94 | 57 | 2000-08-31..2005-05-31 | 210.0 | 2009-03-31..2026-09-30 | 1997 | 50.35% | 2000 | -6.81% | 327,076 |
| COMMON_SE_FF_SSVX | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2026-09-30 | 11.30% | 12.33% | -20.03% | 0.75 | 1.22 | 0.56 | 65 | 199.49% | 5.92 | 37 | 2000-08-31..2003-09-30 | 210.0 | 2009-03-31..2026-09-30 | 1997 | 50.35% | 2000 | -11.65% | 326,981 |
| COMMON_SE_FF_SSVX | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2026-09-30 | 10.85% | 12.34% | -20.04% | 0.71 | 1.16 | 0.54 | 65 | 199.49% | 5.92 | 46 | 2006-04-30..2010-02-28 | 210.0 | 2009-03-31..2026-09-30 | 1997 | 50.35% | 2000 | -11.82% | 287,083 |
| COMMON_SE_FF_SSVX | IDEALIZED_CLOSE | 0.0 | 1994-03-31 | 2026-09-30 | 11.73% | 12.31% | -16.79% | 0.78 | 1.29 | 0.70 | 65 | 199.49% | 5.92 | 57 | 2000-08-31..2005-05-31 | 210.0 | 2009-03-31..2026-09-30 | 1997 | 50.35% | 2000 | -6.63% | 370,922 |
| COMMON_SE_FF_SSVX | IDEALIZED_CLOSE | 10.0 | 1994-03-31 | 2026-09-30 | 11.28% | 12.30% | -16.95% | 0.75 | 1.23 | 0.67 | 65 | 199.49% | 5.92 | 57 | 2000-08-31..2005-05-31 | 210.0 | 2009-03-31..2026-09-30 | 1997 | 50.35% | 2000 | -6.81% | 325,662 |

## REGIONAL_SEK_FF_PROXY_SSVXSYNTH_V1

Tier: `SWEDISH`

- NOT GEM. Regions = Ken French US (CRSP all US stocks), Developed Europe and Emerging markets portfolios (value-weighted, USD -> SEK with Riksbank SEKUSDPMI); Swedish cash = SE_CASH_SSVX_SYNTH_V1 (PROXY).
- stop: stopped before 2026-10-31: no return for held asset(s) ['SE_EM_EQ']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2026-09-30 | 10.40% | 15.17% | -39.36% | 0.58 | 0.87 | 0.26 | 81 | 248.59% | 4.77 | 63 | 2000-03-31..2005-06-30 | 210.0 | 2009-03-31..2026-09-30 | 2005 | 58.67% | 2008 | -20.72% | 251,411 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2026-09-30 | 9.85% | 15.16% | -40.80% | 0.55 | 0.82 | 0.24 | 81 | 248.59% | 4.77 | 65 | 2000-03-31..2005-08-31 | 210.0 | 2009-03-31..2026-09-30 | 2005 | 57.72% | 2008 | -21.20% | 213,775 |
| FULL | IDEALIZED_CLOSE | 0.0 | 1994-02-28 | 2026-09-30 | 11.60% | 14.52% | -27.09% | 0.67 | 1.04 | 0.43 | 81 | 247.96% | 4.78 | 64 | 2007-10-31..2013-02-28 | 210.0 | 2009-03-31..2026-09-30 | 2005 | 63.99% | 2008 | -22.51% | 360,379 |
| FULL | IDEALIZED_CLOSE | 10.0 | 1994-02-28 | 2026-09-30 | 11.05% | 14.51% | -27.38% | 0.64 | 0.99 | 0.40 | 81 | 247.96% | 4.78 | 64 | 2007-10-31..2013-02-28 | 210.0 | 2009-03-31..2026-09-30 | 2005 | 63.34% | 2008 | -22.97% | 306,432 |
| COMMON_SE_FF_SSVX | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2026-09-30 | 10.40% | 15.17% | -39.36% | 0.58 | 0.87 | 0.26 | 81 | 248.59% | 4.77 | 63 | 2000-03-31..2005-06-30 | 210.0 | 2009-03-31..2026-09-30 | 2005 | 58.67% | 2008 | -20.72% | 251,411 |
| COMMON_SE_FF_SSVX | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2026-09-30 | 9.85% | 15.16% | -40.80% | 0.55 | 0.82 | 0.24 | 81 | 248.59% | 4.77 | 65 | 2000-03-31..2005-08-31 | 210.0 | 2009-03-31..2026-09-30 | 2005 | 57.72% | 2008 | -21.20% | 213,775 |
| COMMON_SE_FF_SSVX | IDEALIZED_CLOSE | 0.0 | 1994-03-31 | 2026-09-30 | 11.64% | 14.53% | -27.09% | 0.67 | 1.05 | 0.43 | 81 | 248.59% | 4.77 | 64 | 2007-10-31..2013-02-28 | 210.0 | 2009-03-31..2026-09-30 | 2005 | 63.99% | 2008 | -22.51% | 361,975 |
| COMMON_SE_FF_SSVX | IDEALIZED_CLOSE | 10.0 | 1994-03-31 | 2026-09-30 | 11.09% | 14.52% | -27.38% | 0.64 | 0.99 | 0.40 | 81 | 248.59% | 4.77 | 64 | 2007-10-31..2013-02-28 | 210.0 | 2009-03-31..2026-09-30 | 2005 | 63.34% | 2008 | -22.97% | 307,788 |

## STATIC_70_30_SEK_FF_DEV_PROXY_V1__SE_3P

Tier: `BENCHMARK`

- 70 % global equity (FF Developed, SEK) / 30 % Swedish short rate, monthly rebalanced. The 30 % leg is Swedish cash, not bonds - the defensive asset a Swedish investor actually uses here.
- stop: stopped before 2026-10-31: no return for held asset(s) ['GLOBAL_EQ_SEK']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1993-03-31 | 2026-09-30 | 7.93% | 9.33% | -33.75% | 0.60 | 0.90 | 0.23 | 0 | 7.74% | 403.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1999 | 26.02% | 2002 | -21.88% | 129,669 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1993-03-31 | 2026-09-30 | 7.91% | 9.33% | -33.79% | 0.60 | 0.90 | 0.23 | 0 | 7.74% | 403.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1999 | 26.00% | 2002 | -21.90% | 128,997 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2016-12-31 | 6.47% | 9.45% | -33.75% | 0.40 | 0.59 | 0.19 | 0 | 7.81% | 274.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1999 | 26.02% | 2002 | -21.88% | 41,865 |
| COMMON_SE_3P | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2016-12-31 | 6.46% | 9.45% | -33.79% | 0.40 | 0.58 | 0.19 | 0 | 7.81% | 274.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1999 | 26.00% | 2002 | -21.90% | 41,716 |

## STATIC_70_30_SEK_FF_DEV_PROXY_V1__SE_FF_SSVX

Tier: `BENCHMARK`

- 70 % global equity (FF Developed, SEK) / 30 % Swedish short rate, monthly rebalanced. The 30 % leg is Swedish cash, not bonds - the defensive asset a Swedish investor actually uses here.
- stop: stopped before 2026-10-31: no return for held asset(s) ['GLOBAL_EQ_SEK']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1993-03-31 | 2026-09-30 | 7.93% | 9.33% | -33.75% | 0.60 | 0.90 | 0.23 | 0 | 7.74% | 403.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1999 | 26.02% | 2002 | -21.88% | 129,669 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1993-03-31 | 2026-09-30 | 7.91% | 9.33% | -33.79% | 0.60 | 0.90 | 0.23 | 0 | 7.74% | 403.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1999 | 26.00% | 2002 | -21.90% | 128,997 |
| COMMON_SE_FF_SSVX | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2026-09-30 | 7.49% | 9.33% | -33.75% | 0.57 | 0.85 | 0.22 | 0 | 7.75% | 391.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1999 | 26.02% | 2002 | -21.88% | 105,067 |
| COMMON_SE_FF_SSVX | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2026-09-30 | 7.47% | 9.33% | -33.79% | 0.57 | 0.85 | 0.22 | 0 | 7.75% | 391.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1999 | 26.00% | 2002 | -21.90% | 104,538 |

## STATIC_70_30_SEK_FF_DEV_PROXY_V1__SE_OPEN_SSVX

Tier: `BENCHMARK`

- 70 % global equity (FF Developed, SEK) / 30 % Swedish short rate, monthly rebalanced. The 30 % leg is Swedish cash, not bonds - the defensive asset a Swedish investor actually uses here.
- stop: stopped before 2026-10-31: no return for held asset(s) ['GLOBAL_EQ_SEK']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1993-03-31 | 2026-09-30 | 7.93% | 9.33% | -33.75% | 0.60 | 0.90 | 0.23 | 0 | 7.74% | 403.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1999 | 26.02% | 2002 | -21.88% | 129,669 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1993-03-31 | 2026-09-30 | 7.91% | 9.33% | -33.79% | 0.60 | 0.90 | 0.23 | 0 | 7.74% | 403.00 | 68 | 2007-05-31..2013-01-31 | n/a | n/a | 1999 | 26.00% | 2002 | -21.90% | 128,997 |

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

## STATIC_REGIONAL_EQUAL_SEK_FF_V1__SE_FF_SSVX

Tier: `BENCHMARK`

- Static 1/3-1/3-1/3 regional portfolio in SEK, monthly rebalanced. Equal weights are the parameter-free choice, not optimised.
- stop: stopped before 2026-10-31: no return for held asset(s) ['SE_USA_EQ', 'SE_EUROPE_EQ', 'SE_EM_EQ']

| window | execution | cost_per_side_bps | start_date | end_date | cagr | volatility | max_drawdown | sharpe | sortino | calmar | number_of_switches | annual_turnover | average_holding_period_months | longest_drawdown_months | longest_drawdown_span | longest_underperformance_vs_benchmark_months | longest_underperformance_span | best_year | best_year_return | worst_year | worst_year_return | end_value |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FULL | NEXT_MONTH_CLOSE | 0.0 | 1993-03-31 | 2026-09-30 | 10.39% | 14.18% | -44.41% | 0.59 | 0.87 | 0.23 | 0 | 9.72% | 403.00 | 65 | 2007-10-31..2013-03-31 | n/a | n/a | 1999 | 43.30% | 2008 | -34.79% | 276,120 |
| FULL | NEXT_MONTH_CLOSE | 10.0 | 1993-03-31 | 2026-09-30 | 10.36% | 14.18% | -44.44% | 0.59 | 0.87 | 0.23 | 0 | 9.72% | 403.00 | 65 | 2007-10-31..2013-03-31 | n/a | n/a | 1999 | 43.27% | 2008 | -34.81% | 274,323 |
| COMMON_SE_FF_SSVX | NEXT_MONTH_CLOSE | 0.0 | 1994-03-31 | 2026-09-30 | 9.54% | 14.14% | -44.41% | 0.55 | 0.80 | 0.21 | 0 | 9.60% | 391.00 | 65 | 2007-10-31..2013-03-31 | n/a | n/a | 1999 | 43.30% | 2008 | -34.79% | 194,744 |
| COMMON_SE_FF_SSVX | NEXT_MONTH_CLOSE | 10.0 | 1994-03-31 | 2026-09-30 | 9.52% | 14.14% | -44.44% | 0.55 | 0.80 | 0.21 | 0 | 9.60% | 391.00 | 65 | 2007-10-31..2013-03-31 | n/a | n/a | 1999 | 43.27% | 2008 | -34.81% | 193,529 |

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

