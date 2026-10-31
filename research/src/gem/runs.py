"""Backtest run definitions.

A run binds a strategy (pure rule) to concrete catalog series. Runs are
grouped in tiers:

  STRICT          exact GEM index definitions, verified/licensed sources
  STRICT_3P       exact GEM index definitions, third-party copies (unverified)
  EXTENDED_PROXY  longer history with documented splices/proxies
  SWEDISH         SEK models (GEM_SEK, REGIONAL_SEK)
  BENCHMARK       buy & hold / static mixes

Nothing here is tuned: the lookback is fixed at 12 months in the strategy
module, and splice dates are where the preferred series begins.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .strategies import FixedWeightStrategy, GemStrategy, RegionalMomentumStrategy


@dataclass(frozen=True)
class Leg:
    """A return source for one asset key.

    segments: ((series_id, last_month_inclusive_or_None), ...). Returns of the
    first series are used up to and including its end month, then the next.
    transform: "level" (TR index) or "yield_to_return" (annual % yield).
    fx_to_sek: series id of SEK-per-USD FX to convert a USD leg to SEK.
    """

    segments: tuple[tuple[str, str | None], ...]
    transform: str = "level"
    fx_to_sek: str | None = None

    @property
    def series_ids(self) -> list[str]:
        ids = [s for s, _ in self.segments]
        if self.fx_to_sek:
            ids.append(self.fx_to_sek)
        return ids


def single(sid: str, **kw) -> Leg:
    return Leg(((sid, None),), **kw)


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    tier: str
    strategy: object
    legs: dict  # asset key -> Leg
    roles: dict  # strategy input -> asset key (momentum of that asset's leg)
    rf_asset: str | None
    benchmark_asset: str | None = None
    windows: tuple[tuple[str, str | None, str | None], ...] = (("FULL", None, None),)
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def series_ids(self) -> set[str]:
        return {sid for leg in self.legs.values() for sid in leg.series_ids}


GEM = GemStrategy("GEM_ORIGINAL", "1.0.0")
REF_WINDOW = ("REF_1974_2013", "1974-01-31", "2013-12-31")

# Splices for the third-party EXTENDED_PROXY run (dates = start of preferred series)
US_EQ_PROXY_3P = Leg((("AJ_IBBOTSON_LARGE", "1988-01-31"), ("AJ_SP500TR", None)))
EXUS_PROXY_3P = Leg((("AJ_MSCI_WORLD_EXUS_GR", "1987-12-31"), ("AJ_MSCI_ACWI_EXUS_GR", None)))
BONDS_PROXY_3P = Leg((("AJ_IBBOTSON_IT_GOVT", "1975-12-31"), ("AJ_US_AGG", None)))


def all_runs() -> list[RunSpec]:
    gem_roles = {"us": "US_EQUITIES", "exus": "EX_US_EQUITIES", "hurdle": "US_TBILL"}
    runs = [
        # ---------------- STRICT (needs licensed exports; blocked in build env) ----------
        RunSpec(
            "GEM_ORIGINAL_STRICT", "STRICT", GEM,
            legs={"US_EQUITIES": single("SPX_TR_OFFICIAL"),
                  "EX_US_EQUITIES": single("MSCI_ACWI_EXUS_OFFICIAL"),
                  "US_AGG_BONDS": single("BBG_US_AGG_OFFICIAL"),
                  "US_TBILL": single("FRED_DTB3", transform="yield_to_return")},
            roles=gem_roles, rf_asset="US_TBILL", benchmark_asset="US_EQUITIES",
            windows=(("FULL", None, None), REF_WINDOW),
            notes=("Exact GEM definitions from official/licensed sources.",
                   "T-bill leg: DTB3 month-end yield -> next-month return (documented transformation)."),
        ),
        # ---------------- STRICT_3P -----------------------------------------------------
        RunSpec(
            "GEM_ORIGINAL_STRICT_3P", "STRICT_3P", GEM,
            legs={"US_EQUITIES": single("AJ_SP500TR"),
                  "EX_US_EQUITIES": single("AJ_MSCI_ACWI_EXUS_GR"),
                  "US_AGG_BONDS": single("AJ_US_AGG"),
                  "US_TBILL": single("AJ_TBILL_3M_TR")},
            roles=gem_roles, rf_asset="US_TBILL", benchmark_asset="US_EQUITIES",
            notes=("Same index definitions as GEM_ORIGINAL; values from an unverified third-party "
                   "compilation (alexjansenhome/GEM). Not presented as verified GEM.",),
        ),
        # ---------------- EXTENDED_PROXY -------------------------------------------------
        RunSpec(
            "GEM_ORIGINAL_PROXY_3P", "EXTENDED_PROXY", GEM,
            legs={"US_EQUITIES": US_EQ_PROXY_3P, "EX_US_EQUITIES": EXUS_PROXY_3P,
                  "US_AGG_BONDS": BONDS_PROXY_3P, "US_TBILL": single("AJ_TBILL_3M_TR")},
            roles=gem_roles, rf_asset="US_TBILL", benchmark_asset="US_EQUITIES",
            windows=(("FULL", None, None), REF_WINDOW),
            notes=("US: Ibbotson Large Co. TR to 1988-01, then S&P 500 TR.",
                   "ex-US: MSCI World ex USA (developed only) to 1987-12, then MSCI ACWI ex USA.",
                   "Bonds: Ibbotson Intermediate Government to 1975-12, then US Aggregate.",
                   "All from the unverified third-party compilation."),
        ),
        RunSpec(
            "GEM_PROXY_FF", "EXTENDED_PROXY", GemStrategy("GEM_PROXY_FF", "1.0.0"),
            legs={"US_EQUITIES": single("FF_US_MKT_TR"),
                  "EX_US_EQUITIES": single("FF_DEV_EXUS_MKT_TR"),
                  "US_AGG_BONDS": single("FRED_GS5", transform="par_bond_5y"),
                  "US_TBILL": single("FF_RF")},
            roles=gem_roles, rf_asset="US_TBILL", benchmark_asset="US_EQUITIES",
            notes=("Open-data proxy: CRSP US market, Developed ex US (no EM), synthetic 5y Treasury "
                   "par bond from GS5, 1-month T-bill. NOT GEM_ORIGINAL.",),
        ),
        # ---------------- SWEDISH ---------------------------------------------------------
        RunSpec(
            "GEM_SEK_3P", "SWEDISH",
            GemStrategy("GEM_SEK", "1.0.0", us_asset="SEK_US_EQ", exus_asset="SEK_EXUS_EQ",
                        defensive_asset="SE_SHORT_RATE"),
            legs={"SEK_US_EQ": Leg((("AJ_SP500TR", None),), fx_to_sek="H10_SEK_PER_USD"),
                  "SEK_EXUS_EQ": Leg((("AJ_MSCI_ACWI_EXUS_GR", None),), fx_to_sek="H10_SEK_PER_USD"),
                  "SE_SHORT_RATE": Leg((("RB_SSVX_3M", "2008-11-30"), ("FRED_OMRXTBILL", None)),
                                       transform="mixed_ssvx_omrx")},
            roles={"us": "SEK_US_EQ", "exus": "SEK_EXUS_EQ", "hurdle": "SE_SHORT_RATE"},
            rf_asset="SE_SHORT_RATE", benchmark_asset="SEK_US_EQ",
            notes=("Separate research model, NOT GEM. Swedish hurdle = synthetic SSVX TR until "
                   "2008-11, OMRX T-bill index after.",),
        ),
        RunSpec(
            "REGIONAL_SEK_FF", "SWEDISH",
            RegionalMomentumStrategy("REGIONAL_SEK", "1.0.0",
                                     regions=("SE_USA_EQ", "SE_EUROPE_EQ", "SE_EM_EQ"),
                                     defensive_asset="SE_SHORT_RATE"),
            legs={"SE_USA_EQ": Leg((("FF_US_MKT_TR", None),), fx_to_sek="H10_SEK_PER_USD"),
                  "SE_EUROPE_EQ": Leg((("FF_EUROPE_MKT_TR", None),), fx_to_sek="H10_SEK_PER_USD"),
                  "SE_EM_EQ": Leg((("FF_EMERGING_MKT_TR", None),), fx_to_sek="H10_SEK_PER_USD"),
                  "SE_SHORT_RATE": Leg((("RB_SSVX_3M", "2008-11-30"), ("FRED_OMRXTBILL", None)),
                                       transform="mixed_ssvx_omrx")},
            roles={"SE_USA_EQ": "SE_USA_EQ", "SE_EUROPE_EQ": "SE_EUROPE_EQ", "SE_EM_EQ": "SE_EM_EQ",
                   "hurdle": "SE_SHORT_RATE"},
            rf_asset="SE_SHORT_RATE", benchmark_asset="SE_USA_EQ",
            notes=("Experimental, NOT GEM. Regional signals from Ken French region portfolios in SEK.",),
        ),
        # ---------------- BENCHMARKS -----------------------------------------------------
        RunSpec(
            "BUY_HOLD_GLOBAL", "BENCHMARK", FixedWeightStrategy("BUY_HOLD_GLOBAL", {"GLOBAL_EQ": 1.0}),
            legs={"GLOBAL_EQ": single("MSCI_ACWI_OFFICIAL"), "US_TBILL": single("FRED_DTB3", transform="yield_to_return")},
            roles={"GLOBAL_EQ": "GLOBAL_EQ"}, rf_asset="US_TBILL",
            notes=("MSCI ACWI buy and hold.",),
        ),
        RunSpec(
            "STATIC_70_30", "BENCHMARK",
            FixedWeightStrategy("STATIC_70_30", {"GLOBAL_EQ": 0.7, "US_AGG_BONDS": 0.3}),
            legs={"GLOBAL_EQ": single("MSCI_ACWI_OFFICIAL"), "US_AGG_BONDS": single("BBG_US_AGG_OFFICIAL"),
                  "US_TBILL": single("FRED_DTB3", transform="yield_to_return")},
            roles={"GLOBAL_EQ": "GLOBAL_EQ", "US_AGG_BONDS": "US_AGG_BONDS"}, rf_asset="US_TBILL",
            notes=("70% MSCI ACWI / 30% US Aggregate, rebalanced monthly (fixed convention).",),
        ),
    ]
    # third-party benchmarks aligned with the 3P GEM runs
    for suffix, legs in (("STRICT_3P", {"US_EQUITIES": single("AJ_SP500TR"),
                                        "EX_US_EQUITIES": single("AJ_MSCI_ACWI_EXUS_GR"),
                                        "US_AGG_BONDS": single("AJ_US_AGG")}),
                         ("PROXY_3P", {"US_EQUITIES": US_EQ_PROXY_3P, "EX_US_EQUITIES": EXUS_PROXY_3P,
                                       "US_AGG_BONDS": BONDS_PROXY_3P})):
        legs = {**legs, "US_TBILL": single("AJ_TBILL_3M_TR")}
        windows = (("FULL", None, None), REF_WINDOW) if suffix == "PROXY_3P" else (("FULL", None, None),)
        for sid, w in (("BUY_HOLD_US", {"US_EQUITIES": 1.0}),
                       ("BUY_HOLD_EXUS", {"EX_US_EQUITIES": 1.0}),
                       ("BUY_HOLD_US_AGG", {"US_AGG_BONDS": 1.0}),
                       ("STATIC_70_30_US", {"US_EQUITIES": 0.7, "US_AGG_BONDS": 0.3})):
            runs.append(RunSpec(
                f"{sid}_{suffix}", "BENCHMARK", FixedWeightStrategy(sid, w),
                legs=legs, roles={a: a for a in w}, rf_asset="US_TBILL", benchmark_asset="US_EQUITIES",
                windows=windows,
                notes=("Benchmark on the same third-party data as the GEM run. US equity, not global: "
                       "no MSCI ACWI series was available.",) if "70_30" in sid else (),
            ))
    runs.extend(diagnostic_runs())
    return runs


def diagnostic_runs() -> list[RunSpec]:
    """Reproduction diagnostics: swap ONE leg of GEM_ORIGINAL_PROXY_3P at a time.

    Purpose: explain the gap to the published figures. These are NOT
    candidate models and must never be used to change the main models.
    Evaluated on the reference window only.
    """
    gem_roles = {"us": "US_EQUITIES", "exus": "EX_US_EQUITIES", "hurdle": "US_TBILL"}
    base = {"US_EQUITIES": US_EQ_PROXY_3P, "EX_US_EQUITIES": EXUS_PROXY_3P,
            "US_AGG_BONDS": BONDS_PROXY_3P, "US_TBILL": single("AJ_TBILL_3M_TR")}
    swaps = {
        "DIAG_HURDLE_FF_RF_1M": ("US_TBILL", single("ARCH_FF_RF"),
                                 "Hurdle = Ken French RF (realised 1-month bill return) instead of 3m bill index."),
        "DIAG_HURDLE_TB3MS_PRIOR": ("US_TBILL", single("AJ_TB3MS_YIELD"),
                                    "Hurdle = TB3MS converted with our prior-month rule (r_t = y_{t-1}/1200)."),
        "DIAG_EXUS_WORLD_ONLY": ("EX_US_EQUITIES", single("AJ_MSCI_WORLD_EXUS_GR"),
                                 "ex-US = MSCI World ex USA (developed only) for the whole period."),
        "DIAG_US_MSCI_USA": ("US_EQUITIES", single("AJ_MSCI_USA_GR"),
                             "US = MSCI USA gross instead of Ibbotson/S&P 500 TR."),
    }
    out = []
    for rid, (asset, leg, note) in swaps.items():
        legs = dict(base)
        legs[asset] = leg
        out.append(RunSpec(rid, "DIAGNOSTIC", GemStrategy(f"GEM_ORIGINAL", "1.0.0"), legs=legs, roles=gem_roles,
                           rf_asset="US_TBILL", benchmark_asset="US_EQUITIES",
                           windows=(REF_WINDOW,), notes=(note, "Diagnostic only - not a model.")))
    return out
