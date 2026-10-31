/**
 * Data-provider interfaces. Strategy/engine and UI code depend ONLY on these
 * types, never on a provider's wire format, so a provider can be replaced
 * (official feed, licensed vendor) without touching strategy or UI code.
 */

import type { ISODate } from "../engine/dates";

export type ProviderQuality = "OFFICIAL" | "UNDOCUMENTED_ENDPOINT" | "MANUAL_EXPORT" | "FIXTURE";

export interface Instrument {
  instrumentId: string;
  name: string;
  isin: string;
  currency: string;
  orderbookId: string;
  role: "REGION_USA" | "REGION_EUROPE" | "REGION_EM" | "DEFENSIVE" | "BENCHMARK";
}

export interface NavPoint {
  instrumentId: string;
  isin: string;
  navDate: ISODate;
  nav: number;
  currency: string;
  retrievedAt: string; // ISO timestamp
  source: string; // e.g. "avanza_fund_guide"
  quality: ProviderQuality;
}

export interface YieldPoint {
  date: ISODate;
  value: number; // percent
  retrievedAt: string;
  source: string;
}

/** Raised for any failure that means the source cannot be trusted right now. */
export class ProviderError extends Error {
  constructor(
    public readonly source: string,
    message: string,
    public readonly detail?: unknown,
  ) {
    super(`${source}: ${message}`);
    this.name = "ProviderError";
  }
}

export interface NavProvider {
  readonly name: string;
  readonly version: string;
  readonly quality: ProviderQuality;
  /** Daily NAV points with from <= navDate <= to (inclusive), sorted, validated. */
  history(inst: Instrument, from: ISODate, to: ISODate): Promise<NavPoint[]>;
}

export interface YieldProvider {
  readonly name: string;
  readonly version: string;
  /** Daily Swedish 3m T-bill yields (percent), from <= date <= to. */
  ssvx3m(from: ISODate, to: ISODate): Promise<YieldPoint[]>;
}

/** Shared validation: refuses bad data, never repairs it. */
export function validateNavPoints(points: NavPoint[], inst: Instrument, source: string): NavPoint[] {
  const seen = new Set<string>();
  for (const p of points) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(p.navDate)) throw new ProviderError(source, `bad date ${p.navDate}`);
    if (!(Number.isFinite(p.nav) && p.nav > 0)) throw new ProviderError(source, `non-positive NAV ${p.nav} on ${p.navDate}`);
    if (seen.has(p.navDate)) throw new ProviderError(source, `duplicate NAV date ${p.navDate} for ${inst.instrumentId}`);
    seen.add(p.navDate);
  }
  const sorted = [...points].sort((a, b) => (a.navDate < b.navDate ? -1 : 1));
  for (let i = 1; i < sorted.length; i++) {
    const move = Math.abs(sorted[i].nav / sorted[i - 1].nav - 1);
    if (move > 0.25) throw new ProviderError(source, `NAV move ${(move * 100).toFixed(1)} % on ${sorted[i].navDate} for ${inst.instrumentId} (split/error?)`);
  }
  return sorted;
}
