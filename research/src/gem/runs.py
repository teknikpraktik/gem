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
    group: str | None = None          # runs in a group are compared over their COMMON window
    daily_legs: dict | None = None    # asset key -> Leg on DAILY series (enables scenarios A/B/C)
    sek_fx_for_comparison: str | None = None  # convert a USD strategy's returns to SEK for comparison

    @property
    def series_ids(self) -> set[str]:
        ids = {sid for leg in self.legs.values() for sid in leg.series_ids}
        if self.sek_fx_for_comparison:
            ids.add(self.sek_fx_for_comparison)
        return ids

    @property
    def daily_series_ids(self) -> set[str]:
        return {sid for leg in (self.daily_legs or {}).values() for sid in leg.series_ids}


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
            windows=(("FULL", None, None), REF_WINDOW), group="SE_STRICT", sek_fx_for_comparison=FX,
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
            group="SE_3P", sek_fx_for_comparison=FX,
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
    runs.extend(swedish_runs())
    runs.extend(diagnostic_runs())
    return runs


# ------------------------------------------------------------------------------------------
# Phase 2: Swedish models. Every data combination is its own versioned run id.
# ------------------------------------------------------------------------------------------

# USD/SEK for ALL Swedish runs = Riksbank SEKUSDPMI (primary source, SEK per USD, from 1993).
# The H.10 GitHub mirror is third-party and is kept only for cross-validation.
FX = "RB_SEK_PER_USD"
FX_DAILY = "RB_SEK_PER_USD"
SE_CASH_OMRX = single("FRED_OMRXTBILL")          # VERIFIED TR index, from 2008-11-17
SE_CASH_OMRX_FULL = single("NASDAQ_OMRXTBILL_FULL")  # manual licensed export
SE_CASH_SSVX = single("RB_SSVX_3M")              # SE_CASH_SSVX_SYNTH_V1 (yield -> return), PROXY

GEM_SEK = GemStrategy("GEM_SEK", "1.0.0", us_asset="SEK_US_EQ", exus_asset="SEK_EXUS_EQ",
                      defensive_asset="SE_SHORT_RATE")
GEM_SEK_ROLES = {"us": "SEK_US_EQ", "exus": "SEK_EXUS_EQ", "hurdle": "SE_SHORT_RATE"}
REGIONAL = RegionalMomentumStrategy("REGIONAL_SEK", "1.0.0", regions=("SE_USA_EQ", "SE_EUROPE_EQ", "SE_EM_EQ"),
                                    defensive_asset="SE_SHORT_RATE")
REG_ROLES = {"SE_USA_EQ": "SE_USA_EQ", "SE_EUROPE_EQ": "SE_EUROPE_EQ", "SE_EM_EQ": "SE_EM_EQ",
             "hurdle": "SE_SHORT_RATE"}


def sek(sid: str, fx: str = FX) -> Leg:
    return Leg(((sid, None),), fx_to_sek=fx)


# Global buy-and-hold in SEK, used as the benchmark for "longest underperformance" (never traded).
BENCH_OPEN = Leg((("FF_DEVELOPED_MKT_TR", None),), fx_to_sek=FX)


def swedish_runs() -> list[RunSpec]:
    out = []
    # ---- SE_3P: third-party US/ex-US (1988-2016) + synthetic Swedish cash ----------------
    out.append(RunSpec(
        "GEM_SEK_3P_SSVXSYNTH_V1", "SWEDISH", GEM_SEK,
        legs={"SEK_US_EQ": sek("AJ_SP500TR"), "SEK_EXUS_EQ": sek("AJ_MSCI_ACWI_EXUS_GR"),
              "SE_SHORT_RATE": SE_CASH_SSVX, "BENCH_GLOBAL_SEK": BENCH_OPEN},
        roles=GEM_SEK_ROLES, rf_asset="SE_SHORT_RATE", benchmark_asset="BENCH_GLOBAL_SEK", group="SE_3P",
        notes=("NOT GEM. S&P 500 TR and MSCI ACWI ex USA (third-party copies) in SEK; Swedish cash = "
               "SE_CASH_SSVX_SYNTH_V1 (3m T-bill yield -> return, PROXY).",)))
    # ---- SE_OPEN: open primary sources, monthly, to today --------------------------------
    open_eq = {"SEK_US_EQ": sek("FF_US_MKT_TR"), "SEK_EXUS_EQ": sek("FRED_NASDAQ_GLOBAL_EXUS_LM_NTR")}
    open_eq_daily = {"SEK_US_EQ": sek("FF_US_MKT_TR_DAILY", FX_DAILY),
                     "SEK_EXUS_EQ": sek("FRED_NASDAQ_GLOBAL_EXUS_LM_NTR", FX_DAILY)}
    out.append(RunSpec(
        "GEM_SEK_OPEN_OMRX_V1", "SWEDISH", GEM_SEK, legs={**open_eq, "SE_SHORT_RATE": SE_CASH_OMRX, "BENCH_GLOBAL_SEK": BENCH_OPEN},
        roles=GEM_SEK_ROLES, rf_asset="SE_SHORT_RATE", benchmark_asset="BENCH_GLOBAL_SEK", group="SE_OPEN_OMRX",
        daily_legs={**open_eq_daily, "SE_SHORT_RATE": SE_CASH_OMRX},
        notes=("NOT GEM. US = CRSP US market (Ken French), ex-US = Nasdaq Global ex US LM NTR (FRED, DM+EM), "
               "Swedish cash = OMRX Treasury Bill Index (FRED, VERIFIED, from 2008-11-17).",)))
    out.append(RunSpec(
        "GEM_SEK_OPEN_SSVXSYNTH_V1", "SWEDISH", GEM_SEK, legs={**open_eq, "SE_SHORT_RATE": SE_CASH_SSVX, "BENCH_GLOBAL_SEK": BENCH_OPEN},
        roles=GEM_SEK_ROLES, rf_asset="SE_SHORT_RATE", benchmark_asset="BENCH_GLOBAL_SEK", group="SE_OPEN_SSVX",
        notes=("NOT GEM. As GEM_SEK_OPEN_OMRX_V1 but Swedish cash = synthetic SSVX model (PROXY, longer).",)))
    for grp in ("SE_OPEN_OMRX", "SE_OPEN_SSVX"):
        out.append(RunSpec(
            f"GEM_ORIGINAL_OPEN_V1__{grp}", "EXTENDED_PROXY", GemStrategy("GEM_ORIGINAL", "1.0.0"),
            legs={"US_EQUITIES": single("FF_US_MKT_TR"), "EX_US_EQUITIES": single("FRED_NASDAQ_GLOBAL_EXUS_LM_NTR"),
                  "US_AGG_BONDS": single("FRED_GS5"), "US_TBILL": single("FF_RF")},
            roles={"us": "US_EQUITIES", "exus": "EX_US_EQUITIES", "hurdle": "US_TBILL"},
            rf_asset="US_TBILL", benchmark_asset="US_EQUITIES", group=grp, sek_fx_for_comparison=FX,
            notes=("GEM rule on the same open equity legs as GEM_SEK_OPEN_* (USD); bonds = synthetic 5y "
                   "Treasury from GS5 (EXPERIMENTAL); hurdle = Ken French RF. Comparison partner only.",)))
    # ---- SE_FF_SSVX: only primary/open sources that are reachable (Ken French + Riksbank) ----
    ff_eq = {"SEK_US_EQ": sek("FF_US_MKT_TR"), "SEK_EXUS_EQ": sek("FF_DEV_EXUS_MKT_TR")}
    out.append(RunSpec(
        "GEM_SEK_FF_PROXY_SSVXSYNTH_V1", "SWEDISH", GEM_SEK,
        legs={**ff_eq, "SE_SHORT_RATE": SE_CASH_SSVX, "BENCH_GLOBAL_SEK": BENCH_OPEN},
        roles=GEM_SEK_ROLES, rf_asset="SE_SHORT_RATE", benchmark_asset="BENCH_GLOBAL_SEK", group="SE_FF_SSVX",
        daily_legs={"SEK_US_EQ": sek("FF_US_MKT_TR_DAILY", FX_DAILY),
                    "SEK_EXUS_EQ": sek("FF_DEV_EXUS_MKT_TR_DAILY", FX_DAILY), "SE_SHORT_RATE": SE_CASH_SSVX},
        notes=("NOT GEM. US = CRSP all US stocks (Ken French); ex-US = Ken French Developed ex US "
               "(NO emerging markets - deviation from ACWI ex USA); Swedish cash = SE_CASH_SSVX_SYNTH_V1 "
               "(Riksbank SETB3MBENCH yield -> return, PROXY); FX = Riksbank SEKUSDPMI.",)))
    out.append(RunSpec(
        "GEM_ORIGINAL_FF_V1__SE_FF_SSVX", "EXTENDED_PROXY",
        GemStrategy("GEM_ORIGINAL", "1.0.0", defensive_asset="US_TBILL_DEF"),
        legs={"US_EQUITIES": single("FF_US_MKT_TR"), "EX_US_EQUITIES": single("FF_DEV_EXUS_MKT_TR"),
              "US_TBILL_DEF": single("FF_RF"), "US_TBILL": single("FF_RF")},
        roles={"us": "US_EQUITIES", "exus": "EX_US_EQUITIES", "hurdle": "US_TBILL"},
        rf_asset="US_TBILL", benchmark_asset="US_EQUITIES", group="SE_FF_SSVX", sek_fx_for_comparison=FX,
        notes=("GEM rule in USD on the same equity legs as GEM_SEK_FF_PROXY_SSVXSYNTH_V1; hurdle = Ken French RF. "
               "Defensive asset = US T-bills (FF RF) because no open US bond TR series is reachable without FRED - "
               "this changes returns in risk-off months, NOT the signals. Comparison partner only.",)))
    # ---- REGIONAL_SEK -------------------------------------------------------------------
    reg_legs = {"SE_USA_EQ": sek("FF_US_MKT_TR"), "SE_EUROPE_EQ": sek("FF_EUROPE_MKT_TR"),
                "SE_EM_EQ": sek("FF_EMERGING_MKT_TR")}
    reg_daily = {"SE_USA_EQ": sek("FF_US_MKT_TR_DAILY", FX_DAILY), "SE_EUROPE_EQ": sek("FF_EUROPE_MKT_TR_DAILY", FX_DAILY),
                 "SE_EM_EQ": sek("FF_EMERGING_MKT_TR_DAILY", FX_DAILY)}
    out.append(RunSpec(
        "REGIONAL_SEK_FF_PROXY_OMRX_V1", "SWEDISH", REGIONAL, legs={**reg_legs, "SE_SHORT_RATE": SE_CASH_OMRX, "BENCH_GLOBAL_SEK": BENCH_OPEN},
        roles=REG_ROLES, rf_asset="SE_SHORT_RATE", benchmark_asset="BENCH_GLOBAL_SEK", group="SE_OPEN_OMRX",
        daily_legs={**reg_daily, "SE_SHORT_RATE": SE_CASH_OMRX},
        notes=("NOT GEM. Regions = Ken French US (CRSP all US stocks), Europe (developed Europe) and Emerging "
               "market portfolios, value-weighted, USD converted to SEK; cash = OMRX T-bill (VERIFIED).",)))
    out.append(RunSpec(
        "REGIONAL_SEK_FF_PROXY_SSVXSYNTH_V1", "SWEDISH", REGIONAL, legs={**reg_legs, "SE_SHORT_RATE": SE_CASH_SSVX, "BENCH_GLOBAL_SEK": BENCH_OPEN},
        roles=REG_ROLES, rf_asset="SE_SHORT_RATE", benchmark_asset="BENCH_GLOBAL_SEK", group="SE_FF_SSVX",
        daily_legs={**reg_daily, "SE_SHORT_RATE": SE_CASH_SSVX},
        notes=("NOT GEM. Regions = Ken French US (CRSP all US stocks), Developed Europe and Emerging markets "
               "portfolios (value-weighted, USD -> SEK with Riksbank SEKUSDPMI); Swedish cash = SE_CASH_SSVX_SYNTH_V1 "
               "(PROXY).",)))
    # ---- SE_STRICT: licensed exports ----------------------------------------------------
    out.append(RunSpec(
        "GEM_SEK_STRICT_V1", "SWEDISH", GEM_SEK,
        legs={"SEK_US_EQ": sek("SPX_TR_OFFICIAL"), "SEK_EXUS_EQ": sek("MSCI_ACWI_EXUS_OFFICIAL"),
              "SE_SHORT_RATE": SE_CASH_OMRX_FULL, "BENCH_GLOBAL_SEK": sek("MSCI_ACWI_OFFICIAL")},
        roles=GEM_SEK_ROLES, rf_asset="SE_SHORT_RATE", benchmark_asset="BENCH_GLOBAL_SEK", group="SE_STRICT",
        notes=("NOT GEM. Official S&P 500 TR and MSCI ACWI ex USA in SEK; cash = full OMRX history (manual).",)))
    # ---- SEK benchmarks (each group) ------------------------------------------------------
    for grp, cash in (("SE_OPEN_OMRX", SE_CASH_OMRX), ("SE_OPEN_SSVX", SE_CASH_SSVX), ("SE_3P", SE_CASH_SSVX),
                      ("SE_FF_SSVX", SE_CASH_SSVX)):
        out.append(RunSpec(
            f"BUY_HOLD_GLOBAL_SEK_FF_DEV_PROXY_V1__{grp}", "BENCHMARK",
            FixedWeightStrategy("BUY_HOLD_GLOBAL", {"GLOBAL_EQ_SEK": 1.0}),
            legs={"GLOBAL_EQ_SEK": sek("FF_DEVELOPED_MKT_TR"), "SE_SHORT_RATE": cash},
            roles={"GLOBAL_EQ_SEK": "GLOBAL_EQ_SEK"}, rf_asset="SE_SHORT_RATE", group=grp,
            notes=("Global buy & hold in SEK. Ken French Developed markets (incl. US, NO EM) as open proxy for "
                   "MSCI ACWI.",)))
        out.append(RunSpec(
            f"STATIC_70_30_SEK_FF_DEV_PROXY_V1__{grp}", "BENCHMARK",
            FixedWeightStrategy("STATIC_70_30", {"GLOBAL_EQ_SEK": 0.7, "SE_SHORT_RATE": 0.3}),
            legs={"GLOBAL_EQ_SEK": sek("FF_DEVELOPED_MKT_TR"), "SE_SHORT_RATE": cash},
            roles={"GLOBAL_EQ_SEK": "GLOBAL_EQ_SEK", "SE_SHORT_RATE": "SE_SHORT_RATE"},
            rf_asset="SE_SHORT_RATE", group=grp,
            notes=("70 % global equity (FF Developed, SEK) / 30 % Swedish short rate, monthly rebalanced. The 30 % "
                   "leg is Swedish cash, not bonds - the defensive asset a Swedish investor actually uses here.",)))
    for grp, cash in (("SE_OPEN_OMRX", SE_CASH_OMRX), ("SE_FF_SSVX", SE_CASH_SSVX)):
        out.append(RunSpec(
            f"STATIC_REGIONAL_EQUAL_SEK_FF_V1__{grp}", "BENCHMARK",
            FixedWeightStrategy("STATIC_REGIONAL_EQUAL", {"SE_USA_EQ": 1 / 3, "SE_EUROPE_EQ": 1 / 3,
                                                          "SE_EM_EQ": 1 - 2 / 3}),
            legs={**reg_legs, "SE_SHORT_RATE": cash},
            roles={"SE_USA_EQ": "SE_USA_EQ", "SE_EUROPE_EQ": "SE_EUROPE_EQ", "SE_EM_EQ": "SE_EM_EQ"},
            rf_asset="SE_SHORT_RATE", group=grp,
            notes=("Static 1/3-1/3-1/3 regional portfolio in SEK, monthly rebalanced. Equal weights are the "
                   "parameter-free choice, not optimised.",)))
    out.append(RunSpec(
        "BUY_HOLD_GLOBAL_SEK_ACWI_V1", "BENCHMARK", FixedWeightStrategy("BUY_HOLD_GLOBAL", {"GLOBAL_EQ_SEK": 1.0}),
        legs={"GLOBAL_EQ_SEK": sek("MSCI_ACWI_OFFICIAL"), "SE_SHORT_RATE": SE_CASH_OMRX_FULL},
        roles={"GLOBAL_EQ_SEK": "GLOBAL_EQ_SEK"}, rf_asset="SE_SHORT_RATE", group="SE_STRICT",
        notes=("MSCI ACWI in SEK (licensed export).",)))
    out.append(RunSpec(
        "STATIC_70_30_SEK_ACWI_V1", "BENCHMARK",
        FixedWeightStrategy("STATIC_70_30", {"GLOBAL_EQ_SEK": 0.7, "SE_SHORT_RATE": 0.3}),
        legs={"GLOBAL_EQ_SEK": sek("MSCI_ACWI_OFFICIAL"), "SE_SHORT_RATE": SE_CASH_OMRX_FULL},
        roles={"GLOBAL_EQ_SEK": "GLOBAL_EQ_SEK", "SE_SHORT_RATE": "SE_SHORT_RATE"}, rf_asset="SE_SHORT_RATE",
        group="SE_STRICT", notes=("70 % MSCI ACWI (SEK) / 30 % OMRX T-bill.",)))
    return out


# GEM_ORIGINAL vs GEM_SEK pairs for the signal-agreement analysis
AGREEMENT_PAIRS = (
    ("GEM_ORIGINAL_FF_V1__SE_FF_SSVX", "GEM_SEK_FF_PROXY_SSVXSYNTH_V1"),
    ("GEM_ORIGINAL_STRICT_3P", "GEM_SEK_3P_SSVXSYNTH_V1"),
    ("GEM_ORIGINAL_OPEN_V1__SE_OPEN_OMRX", "GEM_SEK_OPEN_OMRX_V1"),
    ("GEM_ORIGINAL_OPEN_V1__SE_OPEN_SSVX", "GEM_SEK_OPEN_SSVXSYNTH_V1"),
    ("GEM_ORIGINAL_STRICT", "GEM_SEK_STRICT_V1"),
)
ROLE_OF_ASSET = {"US_EQUITIES": "US", "EX_US_EQUITIES": "EX_US", "US_AGG_BONDS": "DEFENSIVE", "US_TBILL_DEF": "DEFENSIVE",
                 "SEK_US_EQ": "US", "SEK_EXUS_EQ": "EX_US", "SE_SHORT_RATE": "DEFENSIVE"}


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
