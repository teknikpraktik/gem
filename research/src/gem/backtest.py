"""Generic monthly backtest engine.

Data flow (no look-ahead by construction):

  1. Signals are generated for each month-end t using ONLY momentum values
     labelled <= t (`generate_signals`). The momentum panel itself is built
     from trailing returns ending at t.
  2. The execution model maps signal date t -> first month whose return the
     new position earns (t+1 for IDEALIZED_CLOSE, t+2 for NEXT_MONTH_CLOSE).
  3. For every return month M the position is the most recent valid signal
     whose first_return_month <= M. NO_SIGNAL never changes the position (no
     trade, no guess); it is logged.
  4. If a held asset has no return for month M the backtest STOPS at M-1 and
     records why. Nothing is interpolated.

Costs: cost_per_side_bps is charged on sum(|target_w - drifted_w|) at each
trade. The initial purchase is not charged (same for all strategies).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping

import numpy as np
import pandas as pd

from .execution import MonthlyExecutionModel
from .metrics import annual_returns, compute_metrics, drawdown_curve, equity_curve
from .strategies import NO_SIGNAL, FixedWeightStrategy, GemStrategy, RegionalMomentumStrategy, Signal


def generate_signals(
    strategy,
    momentum: pd.DataFrame,
    roles: Mapping[str, str],
    stale: pd.DataFrame | None = None,
) -> list[Signal]:
    """Evaluate a strategy at every month-end of `momentum`.

    roles maps strategy input names to momentum columns:
      GemStrategy:              {"us": col, "exus": col, "hurdle": col}
      RegionalMomentumStrategy: {<region asset key>: col, ..., "hurdle": col}
      FixedWeightStrategy:      {<asset key>: col} (column = availability proxy)
    """
    sigs: list[Signal] = []
    for t in momentum.index:
        row = momentum.loc[t]
        st_cols = set()
        if stale is not None and t in stale.index:
            st_cols = {c for c in roles.values() if c in stale.columns and bool(stale.at[t, c])}
        stale_roles = [k for k, c in roles.items() if c in st_cols]

        def val(col):
            v = row.get(col, np.nan)
            return None if pd.isna(v) else float(v)

        d = t.date()
        if isinstance(strategy, GemStrategy):
            s = strategy.evaluate(d, val(roles["us"]), val(roles["exus"]), val(roles["hurdle"]),
                                  stale_inputs=stale_roles)
        elif isinstance(strategy, RegionalMomentumStrategy):
            regs = {r: val(roles[r]) for r in strategy.regions}
            s = strategy.evaluate(d, regs, val(roles["hurdle"]), stale_inputs=stale_roles)
        elif isinstance(strategy, FixedWeightStrategy):
            s = strategy.evaluate(d, {a: val(roles[a]) is not None for a in strategy.weights})
        else:
            raise TypeError(type(strategy))
        sigs.append(s)
    return sigs


@dataclass
class BacktestResult:
    run_id: str
    strategy_id: str
    strategy_version: str
    execution: str
    lookahead_free: bool
    cost_per_side_bps: float
    data_tier: str
    monthly: pd.DataFrame  # one row per return month
    signals: pd.DataFrame  # one row per signal date
    metrics: dict
    notes: list[str] = field(default_factory=list)
    stop_reason: str | None = None

    @property
    def returns(self) -> pd.Series:
        return self.monthly["net_return"]

    def annual(self) -> pd.DataFrame:
        return annual_returns(self.returns)

    def export(self, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        m = self.monthly.copy()
        m.index = m.index.strftime("%Y-%m-%d")
        m.to_csv(out_dir / "monthly.csv", float_format="%.10g")
        s = self.signals.copy()
        s.to_csv(out_dir / "signals.csv", index=False, float_format="%.10g")
        self.annual().to_csv(out_dir / "annual.csv", float_format="%.10g")
        meta = {
            "run_id": self.run_id,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "execution": self.execution,
            "lookahead_free": self.lookahead_free,
            "cost_per_side_bps": self.cost_per_side_bps,
            "data_tier": self.data_tier,
            "stop_reason": self.stop_reason,
            "notes": self.notes,
            "metrics": self.metrics,
            "provenance": getattr(self, "provenance", None),
        }
        (out_dir / "result.json").write_text(json.dumps(meta, indent=2, default=str, sort_keys=True))


def run_backtest(
    run_id: str,
    strategy,
    signals: list[Signal],
    asset_returns: pd.DataFrame,
    execution: MonthlyExecutionModel,
    *,
    cost_per_side_bps: float = 0.0,
    rf: pd.Series | None = None,
    benchmark: pd.Series | None = None,
    data_tier: str = "UNSPECIFIED",
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
    start_value: float = 10_000.0,
    notes: list[str] | None = None,
) -> BacktestResult:
    # --- schedule signals -------------------------------------------------
    sig_rows = []
    effective: dict[pd.Timestamp, Signal] = {}
    for s in signals:
        sched = execution.schedule(pd.Timestamp(s.as_of_date))
        row = {**{k: v.date() if hasattr(v, "date") else v for k, v in sched.items()},
               "target": s.target, "reason": s.reason,
               **{f"in_{k}": v for k, v in s.inputs.items()}}
        sig_rows.append(row)
        if s.is_valid:
            effective[sched["first_return_month"]] = s
    sig_df = pd.DataFrame(sig_rows)

    months = asset_returns.index.sort_values()
    if start is not None:
        months = months[months >= start]
    if end is not None:
        months = months[months <= end]

    rows = []
    current: Signal | None = None
    drifted: dict[str, float] | None = None
    eff_keys = sorted(effective)
    k = 0
    stop_reason = None
    for m in months:
        while k < len(eff_keys) and eff_keys[k] <= m:
            current = effective[eff_keys[k]]
            k += 1
        if current is None:
            continue  # not invested yet
        target_w = dict(current.weights)
        r = asset_returns.loc[m]
        missing = [a for a, w in target_w.items() if w > 0 and (a not in r.index or pd.isna(r[a]))]
        if missing:
            stop_reason = f"stopped before {m.date()}: no return for held asset(s) {missing}"
            break
        if drifted is None:
            traded = 0.0  # initial purchase - not charged
        else:
            keys = set(target_w) | set(drifted)
            traded = sum(abs(target_w.get(a, 0.0) - drifted.get(a, 0.0)) for a in keys)
        cost = traded * cost_per_side_bps / 1e4
        gross = sum(w * float(r[a]) for a, w in target_w.items() if w > 0)
        net = (1 - cost) * (1 + gross) - 1
        # drift weights to end of month
        denom = 1 + gross
        drifted = {a: w * (1 + float(r[a])) / denom for a, w in target_w.items() if w > 0}
        rows.append({
            "month": m,
            "signal_date": current.as_of_date,
            "target": current.target,
            "weights": json.dumps(target_w, sort_keys=True),
            "gross_return": gross,
            "turnover": traded,
            "cost": cost,
            "net_return": net,
        })

    monthly = pd.DataFrame(rows).set_index("month") if rows else pd.DataFrame(
        columns=["signal_date", "target", "weights", "gross_return", "turnover", "cost", "net_return"])
    if rows:
        eq = equity_curve(monthly["net_return"], start_value)
        monthly["equity"] = eq.iloc[1:].values
        monthly["drawdown"] = drawdown_curve(eq).iloc[1:].values
        wdf = pd.DataFrame([json.loads(w) for w in monthly["weights"]], index=monthly.index).fillna(0.0)
        metrics = compute_metrics(monthly["net_return"], rf=rf, benchmark=benchmark, weights=wdf,
                                  turnover=monthly["turnover"], targets=monthly["target"],
                                  start_value=start_value)
    else:
        metrics = {"months": 0}
    metrics["no_signal_count"] = int((sig_df["target"] == NO_SIGNAL).sum()) if len(sig_df) else 0
    return BacktestResult(
        run_id=run_id,
        strategy_id=strategy.strategy_id,
        strategy_version=strategy.version,
        execution=execution.name,
        lookahead_free=execution.lookahead_free,
        cost_per_side_bps=cost_per_side_bps,
        data_tier=data_tier,
        monthly=monthly,
        signals=sig_df,
        metrics=metrics,
        notes=list(notes or []),
        stop_reason=stop_reason,
    )
