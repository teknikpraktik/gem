import { addDays, ISODate, toUTC, weekday } from "@/lib/engine/dates";
import type { Instrument, NavPoint, NavProvider, YieldPoint, YieldProvider } from "@/lib/providers/types";
import { ProviderError } from "@/lib/providers/types";

/** Annual log growth per instrument; EM strongest by default -> signal AVANZA_EM. */
export const DEFAULT_GROWTH: Record<string, number> = { AVANZA_USA: 0.10, AVANZA_EUROPA: 0.05, AVANZA_EM: 0.20, AVANZA_RANTA_KORT: 0.02 };

export interface FakeNavOptions {
  growth?: Record<string, number>;
  /** last NAV date published (inclusive) */
  publishedThrough?: ISODate;
  /** dates without NAV per instrument (fund closed) */
  gaps?: Record<string, (d: ISODate) => boolean>;
  fail?: Error;
}

export class FakeNavProvider implements NavProvider {
  readonly name = "fake_nav";
  readonly version = "fake/1";
  readonly quality = "FIXTURE" as const;
  calls = 0;
  constructor(private readonly o: FakeNavOptions = {}) {}
  async history(inst: Instrument, from: ISODate, to: ISODate): Promise<NavPoint[]> {
    this.calls++;
    if (this.o.fail) throw this.o.fail;
    const g = (this.o.growth ?? DEFAULT_GROWTH)[inst.instrumentId] ?? 0;
    const out: NavPoint[] = [];
    for (let d = from; d <= to; d = addDays(d, 1)) {
      if (weekday(d) >= 5) continue;
      if (this.o.publishedThrough && d > this.o.publishedThrough) continue;
      if (this.o.gaps?.[inst.instrumentId]?.(d)) continue;
      const years = (toUTC(d) - toUTC("2020-01-01")) / (365.25 * 86_400_000);
      out.push({ instrumentId: inst.instrumentId, isin: inst.isin, navDate: d, nav: 100 * Math.exp(g * years), currency: "SEK",
                 retrievedAt: "2026-10-02T08:00:00.000Z", source: this.name, quality: this.quality });
    }
    return out;
  }
}

export class FakeYieldProvider implements YieldProvider {
  readonly name = "fake_yield";
  readonly version = "fake/1";
  constructor(private readonly level = 2.0, private readonly through?: ISODate, private readonly fail?: Error) {}
  async ssvx3m(from: ISODate, to: ISODate): Promise<YieldPoint[]> {
    if (this.fail) throw this.fail;
    const out: YieldPoint[] = [];
    for (let d = from; d <= to; d = addDays(d, 1)) {
      if (weekday(d) >= 5 || (this.through && d > this.through)) continue;
      out.push({ date: d, value: this.level, retrievedAt: "2026-10-02T08:00:00.000Z", source: this.name });
    }
    return out;
  }
}

export const providerDown = () => new ProviderError("fake_nav", "HTTP 503 for https://example.invalid");

/** 2026-10-02 10:00 Stockholm: signal period 2026-09-30 (Wednesday). */
export const NOW = new Date("2026-10-02T08:00:00Z");
