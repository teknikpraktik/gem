import type { NavPoint } from "../providers/types";
import { AttemptRecord, SignalRecord, SignalStore, signalKey } from "./types";

function deepFreeze<T>(o: T): T {
  if (o && typeof o === "object") {
    Object.freeze(o);
    for (const v of Object.values(o as Record<string, unknown>)) deepFreeze(v);
  }
  return o;
}

/** In-memory store (tests, local dev). Same immutability contract as Postgres. */
export class MemoryStore implements SignalStore {
  readonly kind: string = "memory";
  readonly writable: boolean = true;
  private signals = new Map<string, SignalRecord>();
  private attempts: AttemptRecord[] = [];
  private navs = new Map<string, NavPoint>(); // key instrument|date|source

  constructor(seed: SignalRecord[] = []) {
    for (const s of seed) this.signals.set(signalKey(s), deepFreeze(structuredClone(s)));
  }

  async getSignal(strategyId: string, period: string, version: string) {
    return this.signals.get(signalKey({ strategyId, signalPeriod: period, strategyVersion: version })) ?? null;
  }

  async insertSignalIfAbsent(rec: SignalRecord) {
    const k = signalKey(rec);
    const existing = this.signals.get(k);
    if (existing) return { inserted: false, record: existing };
    const frozen = deepFreeze(structuredClone(rec));
    this.signals.set(k, frozen);
    return { inserted: true, record: frozen };
  }

  async listSignals(strategyId: string, limit = 240) {
    return [...this.signals.values()]
      .filter((s) => s.strategyId === strategyId)
      .sort((a, b) => (a.signalPeriod < b.signalPeriod ? 1 : -1))
      .slice(0, limit);
  }

  async latestValid(strategyId: string) {
    return (await this.listSignals(strategyId)).find((s) => s.status === "VALID") ?? null;
  }

  async recordAttempt(a: AttemptRecord) {
    this.attempts.push(structuredClone(a));
  }

  async latestAttempt(strategyId: string, period: string) {
    const xs = this.attempts.filter((a) => a.strategyId === strategyId && a.signalPeriod === period);
    return xs.length ? xs[xs.length - 1] : null;
  }

  allAttempts() {
    return [...this.attempts];
  }

  async saveNavObservations(points: NavPoint[]) {
    for (const p of points) {
      const k = `${p.instrumentId}|${p.navDate}|${p.source}`;
      if (!this.navs.has(k)) this.navs.set(k, structuredClone(p));
    }
  }

  async latestNavs() {
    const out: Record<string, NavPoint> = {};
    for (const p of this.navs.values()) {
      const cur = out[p.instrumentId];
      if (!cur || p.navDate > cur.navDate) out[p.instrumentId] = p;
    }
    return out;
  }
}
