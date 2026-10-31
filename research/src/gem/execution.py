"""Execution conventions: when can a signal actually be traded?

Every backtest row carries five timestamps:

  signal_date          month-end whose data defines the signal
  data_available_date  when the last input value was published/knowable
  order_date           first moment an order can be placed
  execution_date       date whose closing price/NAV the trade gets
  execution_price      which price series is used (index level / fund NAV)

Two conventions are provided for MONTHLY INDEX backtests. They bracket what
is achievable in practice; neither is optimised.

IDEALIZED_CLOSE (lag 0)
    Signal computed from month-end close t and traded at the same close t.
    This is the convention used by most published GEM backtests. It contains
    a small look-ahead at the close (you cannot know the close before the
    close). Reported ONLY for reproduction against published numbers and
    always labelled as such.

NEXT_MONTH_CLOSE (lag 1)  <- primary, no look-ahead
    Signal from month-end t; the new position is established at the close of
    month-end t+1 and earns returns from month t+2. During month t+1 the old
    position is held. Conservative: real execution (1-3 trading days after
    t) lies between the two conventions.

With daily data, `FundOrderModel` models a forward-priced mutual fund
(e.g. Avanza funds): an order before the cut-off on trading day D gets NAV(D);
after the cut-off it gets NAV(next trading day). Cut-off times must come from
the fund's official documentation (see data/investable_instruments.yaml).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

import pandas as pd


@dataclass(frozen=True)
class MonthlyExecutionModel:
    name: str
    lag_months: int
    publication_lag_days: int = 0
    lookahead_free: bool = True
    description: str = ""

    def __post_init__(self):
        if self.lag_months < 0:
            raise ValueError("negative lag")

    def schedule(self, signal_date: pd.Timestamp) -> dict:
        sd = pd.Timestamp(signal_date)
        avail = sd + pd.Timedelta(days=self.publication_lag_days)
        exec_date = sd + pd.offsets.MonthEnd(self.lag_months) if self.lag_months else sd
        order_date = max(avail, exec_date) if self.lag_months else avail
        return {
            "signal_date": sd,
            "data_available_date": avail,
            "order_date": order_date,
            "execution_date": exec_date,
            # holding starts the month after execution
            "first_return_month": exec_date + pd.offsets.MonthEnd(1),
        }


IDEALIZED_CLOSE = MonthlyExecutionModel(
    "IDEALIZED_CLOSE", 0, 0, lookahead_free=False,
    description="Trade at the same month-end close that defines the signal (published-backtest convention; "
                "contains close look-ahead; reproduction only).",
)
NEXT_MONTH_CLOSE = MonthlyExecutionModel(
    "NEXT_MONTH_CLOSE", 1, 0, lookahead_free=True,
    description="Trade at the following month-end close; position earns from month t+2. Conservative bound.",
)


def next_business_day(d: date, holidays: frozenset[date] = frozenset()) -> date:
    n = d + timedelta(days=1)
    while n.weekday() >= 5 or n in holidays:
        n += timedelta(days=1)
    return n


def is_business_day(d: date, holidays: frozenset[date] = frozenset()) -> bool:
    return d.weekday() < 5 and d not in holidays


@dataclass(frozen=True)
class FundOrderModel:
    """Forward-priced fund order: which NAV date does an order get?"""

    cutoff: time
    holidays: frozenset = frozenset()

    def nav_date(self, order_ts: datetime) -> date:
        d = order_ts.date()
        if not is_business_day(d, self.holidays):
            return next_business_day(d, self.holidays)
        if order_ts.time() < self.cutoff:
            return d
        return next_business_day(d, self.holidays)

    def switch_dates(self, signal_month_end: date, data_ready: time = time(9, 0)) -> dict:
        """Sell fund A and buy fund B after a month-end signal.

        Conservative assumption: index closes for month-end t are known the
        next business day morning; the sell order is placed then, and the buy
        order only once the sell has settled into cash (sell NAV date + 1 business day,
        settlement lag is an ASSUMPTION until verified per fund).
        """
        first_bd = next_business_day(signal_month_end, self.holidays)
        sell_nav = self.nav_date(datetime.combine(first_bd, data_ready))
        buy_order_day = next_business_day(sell_nav, self.holidays)
        buy_nav = self.nav_date(datetime.combine(buy_order_day, data_ready))
        return {
            "signal_date": signal_month_end,
            "data_available_date": first_bd,
            "sell_nav_date": sell_nav,
            "buy_nav_date": buy_nav,
            "days_out_of_market": (buy_nav - sell_nav).days,
        }


def assert_not_before_launch(series: pd.Series, launch_date: date, name: str) -> None:
    """Hard guard: fund NAV / ETF prices must not exist before launch."""
    s = series.dropna()
    if not s.empty and s.index.min().date() < launch_date:
        raise ValueError(f"{name}: data at {s.index.min().date()} precedes launch {launch_date}")


def truncate_to_launch(series: pd.Series, launch_date: date) -> pd.Series:
    return series[series.index >= pd.Timestamp(launch_date)]
