"""Currency conversion.

Quote convention used internally: SEK_PER_USD (how many SEK one USD costs),
e.g. ~10.5 in 2024. This matches both:
  * Riksbank SWEA series SEKUSDPMI ("SEK per 1 USD"), and
  * Federal Reserve H.10 / FRED DEXSDUS ("Swedish Kronor to One U.S. Dollar").

USD -> SEK for an asset:
    value_SEK(t) = value_USD(t) * SEK_PER_USD(t)
    1 + R_SEK    = (1 + R_USD) * SEK_PER_USD(t1) / SEK_PER_USD(t0)

If a source quotes USD per SEK it must be inverted explicitly with
`invert_quote` before use. `check_sek_per_usd` guards against silently using
the wrong convention.
"""

from __future__ import annotations

import pandas as pd

# Plausibility band for SEK per USD since 1971 (historical range ~3.9 to ~11.5).
SEK_PER_USD_PLAUSIBLE = (3.0, 15.0)


def invert_quote(rate: pd.Series) -> pd.Series:
    if (rate <= 0).any():
        raise ValueError("non-positive FX rate")
    return 1.0 / rate


def check_sek_per_usd(rate: pd.Series) -> None:
    s = rate.dropna()
    lo, hi = SEK_PER_USD_PLAUSIBLE
    bad = s[(s < lo) | (s > hi)]
    if not bad.empty:
        raise ValueError(
            f"SEK_PER_USD outside plausible band {SEK_PER_USD_PLAUSIBLE}: first bad "
            f"{bad.index[0]} = {bad.iloc[0]} (wrong quote convention?)"
        )


def convert_return_usd_to_sek(r_usd: float, fx_start: float, fx_end: float) -> float:
    """(1+R_USD) * FX_end/FX_start - 1 with FX in SEK per USD."""
    return (1.0 + r_usd) * (fx_end / fx_start) - 1.0


def convert_index_usd_to_sek(usd_index: pd.Series, sek_per_usd: pd.Series) -> pd.Series:
    """Convert a USD month-end index into SEK. Both inputs month-end labelled.

    Months where either input is missing are NaN (no filling).
    """
    check_sek_per_usd(sek_per_usd)
    a, b = usd_index.align(sek_per_usd, join="outer")
    return (a * b).rename(f"{usd_index.name}_SEK" if usd_index.name else None)


def sek_returns_from_usd_index(usd_level: pd.Series, sek_per_usd: pd.Series) -> pd.Series:
    """Monthly SEK returns computed from the SEK INDEX LEVEL (never by adding %).

        TR_SEK(t) = TR_USD(t) * USDSEK(t)
        r_SEK(t)  = TR_SEK(t) / TR_SEK(t-1) - 1

    Both inputs month-end labelled. A missing level or FX value gives NaN.
    """
    check_sek_per_usd(sek_per_usd)
    a, b = usd_level.align(sek_per_usd, join="left")
    sek = a * b
    return (sek / sek.shift(1) - 1).rename(usd_level.name)
