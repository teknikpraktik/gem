/**
 * Riksbank SWEA API - Swedish 3-month Treasury bill yield (SETB3MBENCH).
 * Official, documented API. Optional key: env RIKSBANK_API_KEY
 * (header Ocp-Apim-Subscription-Key) for higher rate limits.
 *
 * GET https://api.riksbank.se/swea/v1/Observations/SETB3MBENCH/{from}/{to}
 *   -> [{ "date": "YYYY-MM-DD", "value": number }]
 * The yield is a QUOTE, not a total-return index; the engine converts it with
 * the documented SE_CASH_SSVX_SYNTH_V1 rule (validated against OMRX: 100 %
 * identical signals over 2010-2026).
 */

import type { ISODate } from "../engine/dates";
import { describeFetchError, Fetcher, PROVIDER_TIMEOUT_MS } from "./avanza";
import { ProviderError, YieldPoint, YieldProvider } from "./types";

const SOURCE = "riksbank_swea";
export const SSVX_3M_SERIES = "SETB3MBENCH";

export class RiksbankYieldProvider implements YieldProvider {
  readonly name = SOURCE;
  readonly version = "riksbank_swea/v1";

  constructor(private readonly fetcher: Fetcher = fetch, private readonly apiKey = process.env.RIKSBANK_API_KEY,
              private readonly now: () => Date = () => new Date(), private readonly timeoutMs = PROVIDER_TIMEOUT_MS) {}

  async ssvx3m(from: ISODate, to: ISODate): Promise<YieldPoint[]> {
    const url = `https://api.riksbank.se/swea/v1/Observations/${SSVX_3M_SERIES}/${from}/${to}`;
    const headers: Record<string, string> = { Accept: "application/json" };
    if (this.apiKey) headers["Ocp-Apim-Subscription-Key"] = this.apiKey;
    let res: Response;
    try {
      res = await this.fetcher(url, { headers, cache: "no-store", signal: AbortSignal.timeout(this.timeoutMs) });
    } catch (e) {
      throw new ProviderError(SOURCE, describeFetchError(e));
    }
    if (!res.ok) throw new ProviderError(SOURCE, `HTTP ${res.status}`);
    let text: string;
    try {
      text = await res.text();
    } catch (e) {
      throw new ProviderError(SOURCE, `${describeFetchError(e)} reading body`);
    }
    if (!text.trim()) throw new ProviderError(SOURCE, "empty response");
    let body: unknown;
    try {
      body = JSON.parse(text);
    } catch {
      throw new ProviderError(SOURCE, "invalid JSON");
    }
    if (!Array.isArray(body)) throw new ProviderError(SOURCE, "unexpected payload", JSON.stringify(body).slice(0, 200));
    const retrievedAt = this.now().toISOString();
    const out: YieldPoint[] = [];
    for (const o of body as { date?: unknown; value?: unknown }[]) {
      if (!o || typeof o !== "object" || !("date" in o) || !("value" in o)) {
        throw new ProviderError(SOURCE, "observation without date/value (schema change?)", o);
      }
      if (typeof o.date !== "string" || !/^\d{4}-\d{2}-\d{2}/.test(o.date)) throw new ProviderError(SOURCE, "bad date field", o);
      if (o.value === null) continue; // explicit null = no observation that day
      if (typeof o.value !== "number" || !Number.isFinite(o.value)) throw new ProviderError(SOURCE, "bad value field", o);
      out.push({ date: o.date.slice(0, 10), value: o.value, retrievedAt, source: SOURCE });
    }
    return out.sort((a, b) => (a.date < b.date ? -1 : 1));
  }
}
