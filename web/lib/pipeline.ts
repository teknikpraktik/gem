/**
 * Monthly signal pipeline (production). Called by the cron endpoint.
 *
 *   1. signal period = previous calendar month end (Stockholm date)
 *   2. if a final signal for (strategy, period, version) exists -> done (idempotent)
 *   3. fetch NAV windows around both 12-month endpoints + Riksbank yields
 *   4. validate (provider-level checks, no future-dated data)
 *   5. compute with the engine (port of the Python reference)
 *   6. classify:
 *      (freshness per series, lib/freshness.ts, is evaluated BEFORE the rule)
 *        provider failure / unexpected format,
 *          empty series, stale series (nothing
 *          near the month end and nothing later),
 *          truncated history                     -> DATA_ERROR (logged only, retried)
 *        last observation 1..tolerance bdays
 *          before the month's last business day,
 *          nothing later published yet           -> WAITING_FOR_DATA (logged only, retried)
 *        engine result VALID                    -> final, stored immutably with the exact input
 *        engine result NO_SIGNAL (e.g. fund
 *          closed longer than the tolerance and
 *          a later NAV proves it)                -> final NO_SIGNAL
 *   No fallback to an older signal, ever.
 */

import { buildEngineInput, codeVersion, dataAsOf, ENGINE_VERSION, EngineInputPayload, inputChecksum, REFERENCE_IMPLEMENTATION,
         runEngine } from "./audit";
import { addDays, ISODate, monthEndMinus, previousMonthEnd } from "./engine/dates";
import { EngineResult, Point, REGION_TO_INSTRUMENT, STRATEGY_ID, STRATEGY_VERSION } from "./engine/regional";
import { assessSeries, FreshnessEntry } from "./freshness";
import { INSTRUMENTS } from "./instruments";
import { NavPoint, NavProvider, ProviderError, YieldPoint, YieldProvider } from "./providers/types";
import { AttemptStatus, SignalRecord, SignalStore } from "./store/types";

export function stockholmDate(d: Date): ISODate {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Stockholm", year: "numeric", month: "2-digit", day: "2-digit" }).format(d);
}

export interface PipelineDeps {
  store: SignalStore;
  navProvider: NavProvider & { verifyInstrument?: (i: (typeof INSTRUMENTS)[number]) => Promise<unknown> };
  yieldProvider: YieldProvider;
  now: () => Date;
}

export interface PipelineResult {
  outcome: AttemptStatus;
  signalPeriod: ISODate;
  detail: string;
  record?: SignalRecord;
  inserted?: boolean;
}

const ASSET_OF_TARGET: Record<string, string> = {
  AVANZA_USA: "usa", AVANZA_EUROPA: "europe", AVANZA_EM: "em", AVANZA_RANTA_KORT: "cash",
};

function buildRecord(res: EngineResult, navs: Record<string, NavPoint[]>, yields: YieldPoint[], deps: PipelineDeps,
                     generatedAt: string, payload: EngineInputPayload, freshness: FreshnessEntry[]): SignalRecord {
  const inputs = Object.entries(REGION_TO_INSTRUMENT).map(([region, iid]) => {
    const e = res.endpoints[iid];
    return {
      instrumentId: iid,
      startDate: e?.start_date ?? null, startNav: e?.start_nav ?? null,
      endDate: e?.end_date ?? null, endNav: e?.end_nav ?? null,
      return12m: (res.returns as Record<string, number | null | undefined>)[region] ?? null,
    };
  });
  const lastYield = yields.filter((y) => y.date <= res.signal_period_end).at(-1);
  return {
    strategyId: STRATEGY_ID,
    strategyVersion: STRATEGY_VERSION,
    signalPeriod: res.signal_period_end,
    generatedAt,
    status: res.status,
    selectedAsset: res.target ? ASSET_OF_TARGET[res.target] ?? null : null,
    selectedFund: res.target,
    returns: { usa: res.returns.usa ?? null, europe: res.returns.europe ?? null, em: res.returns.em ?? null, cash: res.returns.cash ?? null },
    cashHurdle: res.returns.cash ?? null,
    reason: res.reason,
    inputDates: Object.fromEntries(inputs.map((i) => [i.instrumentId, { start: i.startDate, end: i.endDate }])),
    inputSources: {
      ...Object.fromEntries(Object.keys(navs).map((k) => [k, deps.navProvider.name])),
      SE_CASH_SSVX_SYNTH_V1: deps.yieldProvider.name,
    },
    dataQuality: {
      navQuality: deps.navProvider.quality,
      navRetrievedAt: Object.fromEntries(Object.entries(navs).map(([k, v]) => [k, v.at(-1)?.retrievedAt ?? null])),
      latestNavDate: Object.fromEntries(Object.entries(navs).map(([k, v]) => [k, v.at(-1)?.navDate ?? null])),
      lastYieldDateInPeriod: lastYield?.date ?? null,
      asOf: res.as_of,
      freshness,
    },
    providerVersions: { nav: deps.navProvider.version, yield: deps.yieldProvider.version },
    inputs,
    origin: "live",
    dataAsOf: dataAsOf(payload),
    inputDataChecksum: inputChecksum(payload),
    codeVersion: codeVersion(),
    engineVersion: ENGINE_VERSION,
    referenceImplementation: REFERENCE_IMPLEMENTATION,
    inputPayload: payload,
  };
}

export async function runMonthlySignal(deps: PipelineDeps): Promise<PipelineResult> {
  const now = deps.now();
  const asOf = stockholmDate(now);
  const period = previousMonthEnd(asOf);
  const checkedAt = now.toISOString();
  const log = async (status: AttemptStatus, detail: string, sources: Record<string, string> = {}, freshness: FreshnessEntry[] = []) =>
    deps.store.recordAttempt({ strategyId: STRATEGY_ID, signalPeriod: period, checkedAt, status, detail, sources, freshness });

  if (!deps.store.writable) {
    return { outcome: "DATA_ERROR", signalPeriod: period, detail: "store is read-only (DATABASE_URL not configured)" };
  }
  const existing = await deps.store.getSignal(STRATEGY_ID, period, STRATEGY_VERSION);
  if (existing) {
    await log("ALREADY_FINAL", `final ${existing.status} signal for ${period} already stored`);
    return { outcome: "ALREADY_FINAL", signalPeriod: period, detail: "already final", record: existing, inserted: false };
  }

  // 1. fetch (provider errors -> DATA_ERROR, never a fallback)
  const start = monthEndMinus(period, 12);
  const navs: Record<string, NavPoint[]> = {};
  let yields: YieldPoint[];
  try {
    for (const inst of INSTRUMENTS.filter((i) => i.role !== "DEFENSIVE")) {
      if (deps.navProvider.verifyInstrument) await deps.navProvider.verifyInstrument(inst);
      const a = await deps.navProvider.history(inst, addDays(start, -20), addDays(start, 5));
      const b = await deps.navProvider.history(inst, addDays(period, -25), asOf);
      const pts = [...new Map([...a, ...b].map((p) => [p.navDate, p])).values()]
        .sort((x, y) => (x.navDate < y.navDate ? -1 : 1));
      const future = pts.find((p) => p.navDate > asOf);
      if (future) throw new ProviderError(deps.navProvider.name, `NAV dated ${future.navDate} after as-of ${asOf} for ${inst.instrumentId}`);
      navs[inst.instrumentId] = pts;
    }
    yields = await deps.yieldProvider.ssvx3m(monthEndMinus(period, 14), asOf);
    const fy = yields.find((y) => y.date > asOf);
    if (fy) throw new ProviderError(deps.yieldProvider.name, `yield dated ${fy.date} after as-of ${asOf}`);
  } catch (e) {
    const msg = e instanceof ProviderError ? e.message : `unexpected error: ${(e as Error).message}`;
    await log("DATA_ERROR", msg);
    return { outcome: "DATA_ERROR", signalPeriod: period, detail: msg };
  }
  await deps.store.saveNavObservations(Object.values(navs).flat());
  const sources = { nav: deps.navProvider.name, yield: deps.yieldProvider.name };

  // 2. freshness / provenance per series, BEFORE the rule is applied
  const freshness: FreshnessEntry[] = [
    ...Object.entries(navs).map(([iid, pts]) => assessSeries({
      provider: deps.navProvider.name, providerVersion: deps.navProvider.version, instrumentId: iid, kind: "NAV",
      dates: pts.map((p) => p.navDate), retrievedAt: pts.at(-1)?.retrievedAt ?? null, periodEnd: period, requiredHistoryFrom: start })),
    assessSeries({
      provider: deps.yieldProvider.name, providerVersion: deps.yieldProvider.version, instrumentId: "SETB3MBENCH", kind: "YIELD",
      dates: yields.map((y) => y.date), retrievedAt: yields.at(-1)?.retrievedAt ?? null, periodEnd: period, requiredHistoryFrom: start }),
  ];
  const failed = freshness.filter((f) => f.state === "EMPTY" || f.state === "STALE" || f.state === "TRUNCATED");
  if (failed.length) {
    const detail = failed.map((f) => `${f.instrumentId}: ${f.state} - ${f.reason}`).join("; ");
    await log("DATA_ERROR", detail, sources, freshness);
    return { outcome: "DATA_ERROR", signalPeriod: period, detail };
  }
  const pending = freshness.filter((f) => f.state === "NOT_YET_PUBLISHED");
  if (pending.length) {
    const detail = pending.map((f) => `${f.instrumentId}: ${f.reason}`).join("; ");
    await log("WAITING_FOR_DATA", detail, sources, freshness);
    return { outcome: "WAITING_FOR_DATA", signalPeriod: period, detail };
  }

  // 3. apply the rule on exactly the recorded input
  const toPts = (xs: NavPoint[]): Point[] => xs.map((p) => ({ date: p.navDate, value: p.nav }));
  const payload = buildEngineInput(asOf, Object.fromEntries(Object.entries(navs).map(([k, v]) => [k, toPts(v)])),
                                   yields.map((y) => ({ date: y.date, value: y.value })));
  const res = runEngine(payload);
  if (res.status === "NO_SIGNAL" && res.reason.startsWith("no NAV series")) {
    // unreachable after the EMPTY check; kept as a fail-closed guard
    await log("DATA_ERROR", res.reason, sources, freshness);
    return { outcome: "DATA_ERROR", signalPeriod: period, detail: res.reason };
  }

  const record = buildRecord(res, navs, yields, deps, checkedAt, payload, freshness);
  const { inserted, record: stored } = await deps.store.insertSignalIfAbsent(record);
  await log(stored.status, inserted ? `stored final ${stored.status}: ${stored.reason}` : "concurrent run already stored this period",
            sources, freshness);
  return { outcome: stored.status, signalPeriod: period, detail: stored.reason, record: stored, inserted };
}
