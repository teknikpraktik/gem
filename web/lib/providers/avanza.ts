/**
 * Avanza fund NAV provider - JSON endpoints used by avanza.se itself.
 *
 * QUALITY: UNDOCUMENTED_ENDPOINT. Not an official API; works anonymously today
 * (verified 2026-10-31) and may change without notice. Isolated behind
 * NavProvider. Any unexpected shape -> ProviderError -> status DATA_ERROR; a
 * stale or old signal is never presented as new.
 *
 * Wire format (verified, research/reports/generated/nav_probe/):
 *   GET /_api/fund-guide/guide/{orderBookId}  -> { isin, name, currency, nav, navDate, ... }
 *   GET /_api/fund-guide/chart/{id}/{from}/{to}?raw=true
 *        -> { dataSerie: [{ x: epoch ms at 00:00 Europe/Stockholm, y: NAV | null }] }
 *   Windows up to ~2 months return DAILY points; longer windows are downsampled
 *   to monthly points, so this provider requests windows of <= 40 days and
 *   rejects any response whose median spacing is not daily.
 */

import { addDays, ISODate, toUTC } from "../engine/dates";
import { Instrument, NavPoint, NavProvider, ProviderError, validateNavPoints } from "./types";

const BASE = "https://www.avanza.se";
const SOURCE = "avanza_fund_guide";
const WINDOW_DAYS = 40;

export type Fetcher = (url: string, init?: RequestInit) => Promise<Response>;

/** Per-request timeout. A hanging provider must fail (DATA_ERROR), not stall the cron. */
export const PROVIDER_TIMEOUT_MS = 15_000;

export function describeFetchError(e: unknown): string {
  const n = (e as { name?: string })?.name;
  return n === "TimeoutError" || n === "AbortError" ? "timeout" : `network error: ${(e as Error)?.message ?? String(e)}`;
}

function stockholmDate(epochMs: number): ISODate {
  // en-CA formats as YYYY-MM-DD
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Stockholm", year: "numeric", month: "2-digit", day: "2-digit" })
    .format(new Date(epochMs));
}

export function parseChart(body: unknown, inst: Instrument, retrievedAt: string): NavPoint[] {
  if (!body || typeof body !== "object" || !Array.isArray((body as { dataSerie?: unknown }).dataSerie)) {
    throw new ProviderError(SOURCE, `unexpected chart payload for ${inst.instrumentId}`, JSON.stringify(body).slice(0, 200));
  }
  const pts: NavPoint[] = [];
  for (const p of (body as { dataSerie: { x: unknown; y: unknown }[] }).dataSerie) {
    if (!p || typeof p !== "object" || !("x" in p) || !("y" in p)) {
      // a MISSING field is a schema change; only an explicit null means "no NAV that day"
      throw new ProviderError(SOURCE, `chart point without x/y for ${inst.instrumentId} (schema change?)`, p);
    }
    if (p.y === null) continue; // null before launch / no NAV that day
    if (typeof p.x !== "number" || typeof p.y !== "number") {
      throw new ProviderError(SOURCE, `non-numeric chart point for ${inst.instrumentId}`, p);
    }
    pts.push({ instrumentId: inst.instrumentId, isin: inst.isin, navDate: stockholmDate(p.x), nav: p.y,
               currency: inst.currency, retrievedAt, source: SOURCE, quality: "UNDOCUMENTED_ENDPOINT" });
  }
  return pts;
}

export function medianSpacingDays(points: NavPoint[]): number {
  if (points.length < 2) return 1;
  const d = points.slice(1).map((p, i) => (toUTC(p.navDate) - toUTC(points[i].navDate)) / 86_400_000).sort((a, b) => a - b);
  return d[Math.floor(d.length / 2)];
}

export class AvanzaNavProvider implements NavProvider {
  readonly name = SOURCE;
  readonly version = "avanza_fund_guide/1";
  readonly quality = "UNDOCUMENTED_ENDPOINT" as const;

  constructor(private readonly fetcher: Fetcher = fetch, private readonly now: () => Date = () => new Date(),
              private readonly timeoutMs = PROVIDER_TIMEOUT_MS) {}

  private async getJson(url: string): Promise<unknown> {
    let res: Response;
    try {
      res = await this.fetcher(url, {
        headers: { Accept: "application/json", "User-Agent": "gem-signal-monitor/1 (no trading)" },
        cache: "no-store",
        signal: AbortSignal.timeout(this.timeoutMs),
      });
    } catch (e) {
      throw new ProviderError(SOURCE, `${describeFetchError(e)} for ${url}`);
    }
    if (!res.ok) throw new ProviderError(SOURCE, `HTTP ${res.status} for ${url}`);
    let text: string;
    try {
      text = await res.text();
    } catch (e) {
      throw new ProviderError(SOURCE, `${describeFetchError(e)} reading body of ${url}`);
    }
    if (!text.trim()) throw new ProviderError(SOURCE, `empty response from ${url}`);
    try {
      return JSON.parse(text);
    } catch {
      throw new ProviderError(SOURCE, `invalid JSON from ${url}`);
    }
  }

  /** Confirms the endpoint still describes the expected instrument (detects silent changes). */
  async verifyInstrument(inst: Instrument): Promise<{ navDate: ISODate; nav: number }> {
    const g = (await this.getJson(`${BASE}/_api/fund-guide/guide/${inst.orderbookId}`)) as Record<string, unknown>;
    if (g?.isin !== inst.isin) throw new ProviderError(SOURCE, `guide ISIN ${String(g?.isin)} != ${inst.isin}`);
    if (g?.currency !== inst.currency) throw new ProviderError(SOURCE, `guide currency ${String(g?.currency)} != ${inst.currency}`);
    if (typeof g.nav !== "number" || typeof g.navDate !== "string") throw new ProviderError(SOURCE, "guide nav/navDate missing");
    return { navDate: g.navDate.slice(0, 10), nav: g.nav };
  }

  async history(inst: Instrument, from: ISODate, to: ISODate): Promise<NavPoint[]> {
    const all: NavPoint[] = [];
    for (let a = from; a <= to; a = addDays(a, WINDOW_DAYS)) {
      const b = addDays(a, WINDOW_DAYS - 1) < to ? addDays(a, WINDOW_DAYS - 1) : to;
      const retrievedAt = this.now().toISOString();
      const pts = parseChart(await this.getJson(`${BASE}/_api/fund-guide/chart/${inst.orderbookId}/${a}/${b}?raw=true`), inst, retrievedAt);
      if (pts.length >= 3 && medianSpacingDays(pts) > 3) {
        throw new ProviderError(SOURCE, `chart window ${a}..${b} for ${inst.instrumentId} is not daily (format change?)`);
      }
      all.push(...pts.filter((p) => p.navDate >= from && p.navDate <= to));
    }
    const dedup = new Map(all.map((p) => [p.navDate, p]));
    return validateNavPoints([...dedup.values()], inst, SOURCE);
  }
}
