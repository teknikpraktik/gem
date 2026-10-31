"""Strategy definitions.

The strategy layer is pure: it receives already-computed trailing returns and
returns a Signal. It knows nothing about data sources, currencies, files or
dates beyond the `as_of_date` label it echoes back. Same inputs + same
strategy version => same output (no randomness, no hidden state).

Models (kept strictly separate, see research/README.md):

* GEM_ORIGINAL   - Antonacci GEM in USD. US vs T-bill decides risk on/off,
                   then US vs ex-US picks the equity leg.
* GEM_SEK        - same decision structure, SEK legs, Swedish short-rate
                   hurdle and Swedish short-rate defensive asset. NOT GEM.
* REGIONAL_SEK   - best of USA/Europe/EM vs Swedish short-rate hurdle. NOT GEM.
* BUY_HOLD_*, STATIC_70_30 - fixed-weight benchmarks.

Tie rules are part of the specification and are unit tested:

* R_US <= R_HURDLE          -> defensive   (a tie goes to bonds)
* R_US >= R_EXUS            -> US          (a tie goes to US)
* REGIONAL: winner must be strictly > hurdle; ties between regions are broken
  by the fixed region order given at construction (first wins).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Mapping, Sequence

NO_SIGNAL = "NO_SIGNAL"
LOOKBACK_MONTHS = 12  # fixed by specification - never optimised


@dataclass(frozen=True)
class Signal:
    strategy_id: str
    strategy_version: str
    as_of_date: date
    target: str  # asset key, "MIXED" for fixed-weight portfolios, or NO_SIGNAL
    weights: Mapping[str, float]
    reason: str
    inputs: Mapping[str, float | None] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return self.target != NO_SIGNAL

    def to_dict(self) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "as_of_date": self.as_of_date.isoformat(),
            "target": self.target,
            "weights": dict(self.weights),
            "reason": self.reason,
            "inputs": dict(self.inputs),
        }


def _is_valid_number(x) -> bool:
    if x is None or isinstance(x, bool):
        return False
    try:
        return math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def _no_signal(sid, ver, as_of, reason, inputs) -> Signal:
    return Signal(sid, ver, as_of, NO_SIGNAL, {}, reason, dict(inputs))


class GemStrategy:
    """Dual momentum, Antonacci GEM decision structure.

    Asset keys are configurable so that the identical rule can be reused for
    GEM_SEK without code duplication; the *rule* is not configurable.
    """

    def __init__(
        self,
        strategy_id: str = "GEM_ORIGINAL",
        version: str = "1.0.0",
        us_asset: str = "US_EQUITIES",
        exus_asset: str = "EX_US_EQUITIES",
        defensive_asset: str = "US_AGG_BONDS",
    ):
        self.strategy_id = strategy_id
        self.version = version
        self.us_asset = us_asset
        self.exus_asset = exus_asset
        self.defensive_asset = defensive_asset

    @property
    def assets(self) -> tuple[str, ...]:
        return (self.us_asset, self.exus_asset, self.defensive_asset)

    def evaluate(
        self,
        as_of_date: date,
        us_return: float | None,
        exus_return: float | None,
        hurdle_return: float | None,
        *,
        stale_inputs: Iterable[str] = (),
    ) -> Signal:
        inputs = {"us_return": us_return, "exus_return": exus_return, "hurdle_return": hurdle_return}
        sid, ver = self.strategy_id, self.version
        stale = sorted(set(stale_inputs))
        if stale:
            return _no_signal(sid, ver, as_of_date, f"stale input(s): {', '.join(stale)}", inputs)
        missing = [k for k, v in inputs.items() if not _is_valid_number(v)]
        if missing:
            return _no_signal(sid, ver, as_of_date, f"missing input(s): {', '.join(missing)}", inputs)

        r_us, r_exus, r_h = float(us_return), float(exus_return), float(hurdle_return)
        if r_us <= r_h:
            target, reason = self.defensive_asset, "US momentum <= hurdle -> defensive"
        elif r_us >= r_exus:
            target, reason = self.us_asset, "US momentum > hurdle and >= ex-US -> US"
        else:
            target, reason = self.exus_asset, "US momentum > hurdle and ex-US > US -> ex-US"
        return Signal(sid, ver, as_of_date, target, {target: 1.0}, reason, inputs)


class RegionalMomentumStrategy:
    """Top-1 regional relative momentum with absolute-momentum filter.

    Experimental REGIONAL_SEK model. Not GEM.
    """

    def __init__(
        self,
        strategy_id: str = "REGIONAL_SEK",
        version: str = "1.0.0",
        regions: Sequence[str] = ("SE_USA_EQ", "SE_EUROPE_EQ", "SE_EM_EQ"),
        defensive_asset: str = "SE_SHORT_RATE",
    ):
        if len(set(regions)) != len(regions) or not regions:
            raise ValueError("regions must be non-empty and unique")
        self.strategy_id = strategy_id
        self.version = version
        self.regions = tuple(regions)
        self.defensive_asset = defensive_asset

    @property
    def assets(self) -> tuple[str, ...]:
        return self.regions + (self.defensive_asset,)

    def evaluate(
        self,
        as_of_date: date,
        region_returns: Mapping[str, float | None],
        hurdle_return: float | None,
        *,
        stale_inputs: Iterable[str] = (),
    ) -> Signal:
        inputs = {f"{r}_return": region_returns.get(r) for r in self.regions}
        inputs["hurdle_return"] = hurdle_return
        sid, ver = self.strategy_id, self.version
        stale = sorted(set(stale_inputs))
        if stale:
            return _no_signal(sid, ver, as_of_date, f"stale input(s): {', '.join(stale)}", inputs)
        missing = [k for k, v in inputs.items() if not _is_valid_number(v)]
        if missing:
            return _no_signal(sid, ver, as_of_date, f"missing input(s): {', '.join(missing)}", inputs)

        best = self.regions[0]
        for r in self.regions[1:]:  # strict '>' keeps the earlier region on ties
            if float(region_returns[r]) > float(region_returns[best]):
                best = r
        if float(region_returns[best]) > float(hurdle_return):
            return Signal(sid, ver, as_of_date, best, {best: 1.0}, f"{best} best and > hurdle", inputs)
        return Signal(
            sid, ver, as_of_date, self.defensive_asset, {self.defensive_asset: 1.0},
            f"best region {best} <= hurdle -> defensive", inputs,
        )


class FixedWeightStrategy:
    """Buy-and-hold (single asset) or static mix rebalanced to fixed weights.

    Rebalancing convention for multi-asset mixes: back to target weights at
    every period end (monthly). This is a fixed convention, not optimised.
    """

    def __init__(self, strategy_id: str, weights: Mapping[str, float], version: str = "1.0.0"):
        total = sum(weights.values())
        if abs(total - 1.0) > 1e-12 or any(w < 0 for w in weights.values()):
            raise ValueError(f"weights must be non-negative and sum to 1, got {total}")
        self.strategy_id = strategy_id
        self.version = version
        self.weights = dict(weights)

    @property
    def assets(self) -> tuple[str, ...]:
        return tuple(self.weights)

    def evaluate(self, as_of_date: date, available: Mapping[str, bool] | None = None) -> Signal:
        if available is not None:
            missing = [a for a in self.weights if not available.get(a, False)]
            if missing:
                return _no_signal(self.strategy_id, self.version, as_of_date,
                                  f"missing asset(s): {', '.join(missing)}", {})
        target = next(iter(self.weights)) if len(self.weights) == 1 else "MIXED"
        return Signal(self.strategy_id, self.version, as_of_date, target, dict(self.weights),
                      "fixed weights", {})
