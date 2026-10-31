"""Explicit-time execution model on DAILY total-return levels.

Every monthly signal becomes one trade record with:

  signal_period_end    month-end whose closes define the signal
  data_available_at    when the last input close is knowable (scenario)
  signal_generated_at  when the signal is computed (= data_available_at)
  order_submitted_at   when the order(s) reach the fund/broker
  fund_cutoff          cut-off time of the instrument being sold
  sell_nav_date        NAV/close date the sale is executed at
  buy_nav_date         NAV/close date the purchase is executed at
  execution_date       = buy_nav_date (new position fully established)

Between sell_nav_date and buy_nav_date the portfolio is in cash earning 0 %
(conservative; SEK cash interest over 1-3 days is immaterial and ignored).

Scenarios (fixed definitions, never tuned):

  A PUBLISHED_CLOSE   label LOOKAHEAD_REFERENCE_ONLY. Sell and buy at the
                      close of the last trading day of the signal month.
  B NEXT_TRADABLE     main scenario. Closes of period end are known the next
                      business day at 08:00; orders submitted 09:00 that day;
                      each leg gets the NAV its TradingRules imply; buy order
                      submitted when the sale NAV is struck (proceeds treated as
                      available for a new fund order at Avanza - ASSUMPTION,
                      see TradingRules.buy_waits_for_settlement).
  C CONSERVATIVE      one extra business day before ordering, and the buy
                      order waits until the sale has SETTLED (settlement_bdays).

Index validation uses DEFAULT_INDEX_RULES (cut-off 15:00, same-day close,
T+2 settlement). Fund implementations use per-fund rules from
data/investable_instruments.yaml.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, time

import numpy as np
import pandas as pd

from .metrics import annual_returns, compute_metrics, drawdown_curve
from .strategies import Signal


@dataclass(frozen=True)
class TradingRules:
    cutoff: time = time(15, 0)
    nav_lag_bdays: int = 0          # 0: order before cut-off on D -> NAV(D); 1 -> NAV(D+1)
    settlement_bdays: int = 2       # sale proceeds settle D_nav + n business days
    source: str = "DEFAULT"


DEFAULT_INDEX_RULES = TradingRules(source="index validation default")


@dataclass(frozen=True)
class ExecutionScenario:
    name: str
    label: str
    lookahead_free: bool
    published_close: bool = False
    data_available_bdays: int = 1
    data_time: time = time(8, 0)
    extra_delay_bdays: int = 0
    order_time: time = time(9, 0)
    buy_waits_for_settlement: bool = False


SCENARIO_A = ExecutionScenario("A_PUBLISHED_CLOSE", "LOOKAHEAD_REFERENCE_ONLY", False, published_close=True)
SCENARIO_B = ExecutionScenario("B_NEXT_TRADABLE", "MAIN", True)
SCENARIO_C = ExecutionScenario("C_CONSERVATIVE", "CONSERVATIVE", True, extra_delay_bdays=1,
                               buy_waits_for_settlement=True)
SCENARIOS = (SCENARIO_A, SCENARIO_B, SCENARIO_C)


class Calendar:
    """Business-day calendar taken from the dates present in the data."""

    def __init__(self, days: pd.DatetimeIndex):
        self.days = pd.DatetimeIndex(sorted(set(pd.DatetimeIndex(days).normalize())))

    def last_on_or_before(self, d) -> pd.Timestamp:
        i = self.days.searchsorted(pd.Timestamp(d), side="right") - 1
        if i < 0:
            raise IndexError(f"no trading day on/before {d}")
        return self.days[i]

    def first_after(self, d) -> pd.Timestamp:
        i = self.days.searchsorted(pd.Timestamp(d), side="right")
        if i >= len(self.days):
            raise IndexError(f"no trading day after {d}")
        return self.days[i]

    def first_on_or_after(self, d) -> pd.Timestamp:
        i = self.days.searchsorted(pd.Timestamp(d), side="left")
        if i >= len(self.days):
            raise IndexError(f"no trading day on/after {d}")
        return self.days[i]

    def add(self, d, n: int) -> pd.Timestamp:
        i = self.days.get_loc(self.first_on_or_after(d)) + n
        if i >= len(self.days):
            raise IndexError("calendar exhausted")
        return self.days[i]


def nav_date_for_order(cal: Calendar, order_at: datetime, rules: TradingRules) -> pd.Timestamp:
    d = pd.Timestamp(order_at.date())
    if d not in cal.days:
        base = cal.first_on_or_after(d)
    elif order_at.time() < rules.cutoff:
        base = d
    else:
        base = cal.first_after(d)
    return cal.add(base, rules.nav_lag_bdays)


def schedule_switch(cal: Calendar, period_end, scenario: ExecutionScenario,
                    sell_rules: TradingRules, buy_rules: TradingRules) -> dict:
    pe = pd.Timestamp(period_end)
    if scenario.published_close:
        d = cal.last_on_or_before(pe)
        close = datetime.combine(d.date(), time(17, 30))
        return {"signal_period_end": pe, "data_available_at": close, "signal_generated_at": close,
                "order_submitted_at": close, "fund_cutoff": sell_rules.cutoff, "sell_nav_date": d,
                "buy_nav_date": d, "execution_date": d}
    avail_day = cal.add(cal.first_after(pe), scenario.data_available_bdays - 1)
    data_at = datetime.combine(avail_day.date(), scenario.data_time)
    order_day = cal.add(avail_day, scenario.extra_delay_bdays)
    order_at = datetime.combine(order_day.date(), scenario.order_time)
    sell_nav = nav_date_for_order(cal, order_at, sell_rules)
    if scenario.buy_waits_for_settlement:
        buy_order_day = cal.add(sell_nav, sell_rules.settlement_bdays)
    else:
        buy_order_day = sell_nav  # buy submitted when the sale is struck (ASSUMPTION B)
    buy_order_at = max(order_at, datetime.combine(buy_order_day.date(), scenario.order_time))
    buy_nav = max(nav_date_for_order(cal, buy_order_at, buy_rules), sell_nav)
    return {"signal_period_end": pe, "data_available_at": data_at, "signal_generated_at": data_at,
            "order_submitted_at": order_at, "fund_cutoff": sell_rules.cutoff, "sell_nav_date": sell_nav,
            "buy_nav_date": buy_nav, "execution_date": buy_nav}


@dataclass
class DailyResult:
    run_id: str
    scenario: str
    label: str
    lookahead_free: bool
    daily: pd.DataFrame
    monthly_returns: pd.Series
    trades: pd.DataFrame
    metrics: dict
    notes: list = field(default_factory=list)


def run_daily_backtest(run_id: str, signals: list[Signal], levels: pd.DataFrame, scenario: ExecutionScenario,
                       rules: dict[str, TradingRules] | None = None, *, cost_per_side_bps: float = 0.0,
                       rf_monthly: pd.Series | None = None, benchmark_monthly: pd.Series | None = None,
                       start=None, end=None, start_value: float = 10_000.0) -> DailyResult:
    """Single-asset (100 %) strategies on daily TR levels with explicit trade timing."""
    rules = rules or {}
    lv = levels.sort_index()
    cal = Calendar(lv.index)
    valid = lv.notna()
    px = lv.ffill()  # valuation on another market's holiday = unchanged price (no look-ahead)

    def r_of(a):
        return rules.get(a, DEFAULT_INDEX_RULES)

    def first_valid_nav(a, d):
        while not bool(valid.at[d, a]):
            d = cal.first_after(d)
        return d

    trades, plan = [], []
    holding = None
    first_day = cal.days[0]
    usable = [s for s in signals if s.is_valid and pd.Timestamp(s.as_of_date) >= first_day]
    if start is not None:
        st = pd.Timestamp(start)
        before = [s for s in usable if pd.Timestamp(s.as_of_date) < st]
        usable = before[-1:] + [s for s in usable if pd.Timestamp(s.as_of_date) >= st]
    for s in usable:
        if not s.is_valid or s.target == holding:
            continue
        try:
            sell_r = r_of(holding) if holding else DEFAULT_INDEX_RULES
            sch = schedule_switch(cal, s.as_of_date, scenario, sell_r, r_of(s.target))
        except IndexError:
            break
        if holding:
            sch["sell_nav_date"] = first_valid_nav(holding, sch["sell_nav_date"])
        sch["buy_nav_date"] = first_valid_nav(s.target, max(sch["buy_nav_date"], sch["sell_nav_date"]))
        sch["execution_date"] = sch["buy_nav_date"]
        sch.update({"from": holding, "to": s.target})
        plan.append(sch)
        holding = s.target
    # discard switches whose sell happens before the previous buy completed (keep order)
    days = cal.days
    if start is not None:
        days = days[days >= pd.Timestamp(start)]
    if end is not None:
        days = days[days <= pd.Timestamp(end)]
    v = None
    pos = None  # asset or "CASH"
    k = 0
    rows = []
    prev_day = None
    for d in days:
        # mark to market
        if v is not None and pos not in (None, "CASH"):
            v *= float(px.at[d, pos] / px.at[prev_day, pos])
        # execute trades scheduled for today (at the close)
        while k < len(plan) and plan[k]["sell_nav_date"] <= d:
            p = plan[k]
            if v is None:  # initial purchase
                if p["buy_nav_date"] <= d:
                    v, pos = start_value, p["to"]
                    trades.append({**p, "cost": 0.0})
                    k += 1
                    continue
                break
            if pos == p["from"] and p["sell_nav_date"] <= d:
                v *= 1 - cost_per_side_bps / 1e4
                pos = "CASH"
            if p["buy_nav_date"] <= d:
                v *= 1 - cost_per_side_bps / 1e4
                pos = p["to"]
                trades.append({**p, "cost": 2 * cost_per_side_bps / 1e4})
                k += 1
            else:
                break
        if v is not None:
            rows.append({"date": d, "value": v, "position": pos})
        prev_day = d
    daily = pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame(columns=["value", "position"])
    if daily.empty:
        return DailyResult(run_id, scenario.name, scenario.label, scenario.lookahead_free, daily,
                           pd.Series(dtype=float), pd.DataFrame(trades), {"months": 0})
    me = daily["value"].groupby(daily.index + pd.offsets.MonthEnd(0)).last()
    first_month_start = daily["value"].iloc[0]
    mret = me / me.shift(1) - 1
    mret.iloc[0] = me.iloc[0] / first_month_start - 1
    mret = mret.iloc[1:]  # drop the partial first month
    pos_m = daily["position"].groupby(daily.index + pd.offsets.MonthEnd(0)).last().reindex(mret.index)
    metrics = compute_metrics(mret, rf=rf_monthly, benchmark=benchmark_monthly, targets=pos_m,
                              start_value=start_value)
    tr = pd.DataFrame(trades)
    metrics["number_of_trades"] = int(len(tr) - 1) if len(tr) else 0
    if len(tr):
        out_days = [(cal.days.get_loc(b) - cal.days.get_loc(s)) for s, b in zip(tr["sell_nav_date"], tr["buy_nav_date"])]
        metrics["avg_bdays_out_of_market_per_switch"] = float(np.mean(out_days[1:])) if len(out_days) > 1 else 0.0
        lag = [(cal.days.get_loc(e) - cal.days.get_loc(cal.last_on_or_before(p)))
               for p, e in zip(tr["signal_period_end"], tr["execution_date"])]
        metrics["avg_bdays_signal_to_execution"] = float(np.mean(lag))
    return DailyResult(run_id, scenario.name, scenario.label, scenario.lookahead_free, daily, mret, tr, metrics)
