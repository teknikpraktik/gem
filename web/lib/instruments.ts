/**
 * Investable instruments for REGIONAL_SEK_LIVE (INVESTABLE_INSTRUMENT, never a
 * signal index). Facts mirror research/data/investable_instruments.yaml; ISIN and
 * orderBookId confirmed via avanza.se search (2026-10-31). Trading rules carry an
 * explicit verification status - "UNVERIFIED" is shown as such in the UI.
 */

import type { Instrument } from "./providers/types";

/**
 * Trading rules as instrument metadata. `cutoffTime` is "HH:MM" Europe/Stockholm on
 * Swedish banking days, or null when not verified - never a guess.
 * Status: VERIFIED (primary source, confirmed by the repo owner), VERIFIED_SEARCH_EXTRACT
 * (primary source read via search extract only), UNVERIFIED.
 */
export type VerificationStatus = "VERIFIED" | "VERIFIED_SEARCH_EXTRACT" | "UNVERIFIED";

export interface TradingRules {
  cutoffTime: string | null;
  cutoffStatus: VerificationStatus;
  /** Cut-off on the banking day before a holiday, if documented. */
  holidayEveCutoff: { time: string | null; status: VerificationStatus; note: string };
  navRule: string;
  settlement: string | null;
  source: string;
  verifiedAt: string;
}

export interface InstrumentInfo extends Instrument {
  shortName: string;
  benchmark: string;
  totalFeePct: number;
  firstNav: string;
  rules: TradingRules;
}

export const INSTRUMENTS: InstrumentInfo[] = [
  {
    instrumentId: "AVANZA_USA", name: "Avanza USA", shortName: "USA", isin: "SE0012741163", currency: "SEK",
    orderbookId: "1025150", role: "REGION_USA",
    benchmark: "Morningstar US TME PAB Sust NR SEK", totalFeePct: 0.18, firstNav: "2019-12",
    rules: { cutoffTime: "15:00", cutoffStatus: "VERIFIED_SEARCH_EXTRACT",
             holidayEveCutoff: { time: "12:00", status: "VERIFIED_SEARCH_EXTRACT", note: "dag före helgdag" },
             navRule: "Order före bryttid får dagens NAV", settlement: "Likvid inom 2 bankdagar",
             source: "Informationsbroschyr Avanza USA 2026 (sökutdrag)", verifiedAt: "2026-10-31" },
  },
  {
    instrumentId: "AVANZA_EUROPA", name: "Avanza Europa", shortName: "Europa", isin: "SE0013718699", currency: "SEK",
    orderbookId: "1041067", role: "REGION_EUROPE",
    benchmark: "Morningstar Dev Eur TME PAB Sust NR SEK", totalFeePct: 0.31, firstNav: "2020-02-05",
    rules: { cutoffTime: null, cutoffStatus: "UNVERIFIED",
             holidayEveCutoff: { time: null, status: "UNVERIFIED", note: "ej funnen" },
             navRule: "Kurs för den bankdag pengarna/begäran når fonden (broschyr)", settlement: null,
             source: "Informationsbroschyr Avanza Europa 2026-06-16: bryttid ej funnen i utdrag", verifiedAt: "2026-10-31" },
  },
  {
    instrumentId: "AVANZA_EM", name: "Avanza Emerging Markets", shortName: "Emerging Markets", isin: "SE0012454338", currency: "SEK",
    orderbookId: "944976", role: "REGION_EM",
    benchmark: "Ingen angiven (matarfond till Amundi Core MSCI Emerging Markets)", totalFeePct: 0.30, firstNav: "2019-04",
    rules: { cutoffTime: "12:00", cutoffStatus: "VERIFIED_SEARCH_EXTRACT",
             holidayEveCutoff: { time: null, status: "UNVERIFIED", note: "ej funnen" },
             navRule: "Nästa bankdags NAV; ingen NAV när kinesisk marknad är stängd (mätt: 5-8 bankdagars luckor)", settlement: "Likvid inom 2 bankdagar",
             source: "Informationsbroschyr Avanza Emerging Markets 2026 (sökutdrag) + mätta NAV-luckor", verifiedAt: "2026-10-31" },
  },
  {
    instrumentId: "AVANZA_RANTA_KORT", name: "Avanza Ränta Kort", shortName: "Ränta Kort", isin: "SE0021021425", currency: "SEK",
    orderbookId: "1684019", role: "DEFENSIVE",
    benchmark: "Inget (matarfond till Captor Perenne Short Term Bond A)", totalFeePct: 0.09, firstNav: "2023-12-14",
    rules: { cutoffTime: "15:00", cutoffStatus: "VERIFIED",
             holidayEveCutoff: { time: null, status: "UNVERIFIED",
                                 note: "motstridigt: 12:00 enligt fondens broschyr, 09:30 enligt Avanza 75-broschyren" },
             navRule: "Order före bryttid på bankdag får dagens NAV",
             settlement: "Kurs publiceras normalt inom 2 bankdagar", source: "Informationsbroschyr Avanza Ränta Kort 2026-04-28; bryttid 15:00 bekräftad av repoägaren 2026-10-31",
             verifiedAt: "2026-10-31" },
  },
];

export const BENCHMARK_INSTRUMENT: Instrument = {
  instrumentId: "AVANZA_GLOBAL", name: "Avanza Global", isin: "SE0011527613", currency: "SEK", orderbookId: "878733", role: "BENCHMARK",
};

export const SIGNAL_INSTRUMENTS = INSTRUMENTS.filter((i) => i.role !== "DEFENSIVE");

export function instrumentById(id: string | null | undefined): InstrumentInfo | undefined {
  return INSTRUMENTS.find((i) => i.instrumentId === id);
}
