/**
 * Monthly signal pipeline (production). Called by the cron endpoint.
 *
 *   1. signal period = previous calendar month end (Stockholm date)
 *   2. if a final signal for (strategy, period, version) exists -> done (idempotent)
 *   3. fetch NAV windows around both 12-month endpoints + Riksbank yields
 *   4. validate (provider-level checks, no future-dated data)
 *   5. compute with the engine (port of the Python reference)
 *   6. classify:
 *        VALID                                  -> final, stored immutably
 *        a fund's (or the yield's) last observation is
 *          before the month's last business day and
 *          nothing later is published yet         -> WAITING_FOR_DATA (logged only)
 *        month-end NAV missing although later
 *          NAVs exist (fund closed, e.g. EM on
 *          Chinese holidays)                     -> final NO_SIGNAL
 *        other missing inputs (history)          -> final NO_SIGNAL
 *        provider failure / unexpected format    -> DATA_ERROR (logged only)
 *   No fallback to an older signal, ever.
 */

import { addDays, ISODate, lastBusinessDayOnOrBefore, monthEndMinus, previousMonthEnd } from "./engine/dates";
import { computeRegionalSignal, EngineResult, Point, REGION_TO_INSTRUMENT, STRATEGY_ID, STRATEGY_VERSION } from "./engine/regional";
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
                     generatedAt: string): SignalRecord {
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
      engine: "web/lib/engine/regional.ts (conformance-tested against research/src/gem/live.py)",
    },
    providerVersions: { nav: deps.navProvider.version, yield: deps.yieldProvider.version },
    inputs,
    origin: "live",
  };
}

export async function runMonthlySignal(deps: PipelineDeps): Promise<PipelineResult> {
  const now = deps.now();
  const asOf = stockholmDate(now);
  const period = previousMonthEnd(asOf);
  const checkedAt = now.toISOString();
  const log = async (status: AttemptStatus, detail: string, sources: Record<string, string> = {}) =>
    deps.store.recordAttempt({ strategyId: STRATEGY_ID, signalPeriod: period, checkedAt, status, detail, sources });

  if (!deps.store.writable) {
    return { outcome: "DATA_ERROR", signalPeriod: period, detail: "store is read-only (DATABASE_URL not configured)" };
  }
  const existing = await deps.store.getSignal(STRATEGY_ID, period, STRATEGY_VERSION);
  if (existing) {
    await log("ALREADY_FINAL", `final ${existing.status} signal for ${period} already stored`);
    return { outcome: "ALREADY_FINAL", signalPeriod: period, detail: "already final", record: existing, inserted: false };
  }

  const start = monthEndMinus(period, 12);
  const navs: Record<string, NavPoint[]> = {};
  let yields: YieldPoint[];
  try {
    for (const inst of INSTRUMENTS.filter((i) => i.role !== "DEFENSIVE")) {
      if (deps.navProvider.verifyInstrument) await deps.navProvider.verifyInstrument(inst);
      const a = await deps.navProvider.history(inst, addDays(start, -20), addDays(start, 5));
      const b = await deps.navProvider.history(inst, addDays(period, -25), asOf);
      const pts = [...a, ...b];
      const future = pts.find((p) => p.navDate > asOf);
      if (future) throw new ProviderError(deps.navProvider.name, `NAV dated ${future.navDate} after as-of ${asOf} for ${inst.instrumentId}`);
      navs[inst.instrumentId] = pts;
    }
    yields = await deps.yieldProvider.ssvx3m(monthEndMinus(period, 14), asOf);
  } catch (e) {
    const msg = e instanceof ProviderError ? e.message : `unexpected error: ${(e as Error).message}`;
    await log("DATA_ERROR", msg);
    return { outcome: "DATA_ERROR", signalPeriod: period, detail: msg };
  }
  await deps.store.saveNavObservations(Object.values(navs).flat());

  // Month-end completeness BEFORE applying the rule. The engine tolerates a NAV up to
  // MAX_STALE_BDAYS_NAV before the month's last business day (fund closures, e.g. EM on
  // Chinese holidays). Live, such a gap is only final once a LATER NAV proves the fund
  // was closed; until then the month-end NAV may simply not be published yet.
  const lastBday = lastBusinessDayOnOrBefore(period);
  const sources0 = { nav: deps.navProvider.name, yield: deps.yieldProvider.name };
  for (const [iid, pts] of Object.entries(navs)) {
    const lastInPeriod = pts.filter((p) => p.navDate <= period).at(-1)?.navDate;
    if ((!lastInPeriod || lastInPeriod < lastBday) && !pts.some((p) => p.navDate > period)) {
      const detail = `${iid}: NAV for ${lastBday} not published yet (last ${lastInPeriod ?? "none"})`;
      await log("WAITING_FOR_DATA", detail, sources0);
      return { outcome: "WAITING_FOR_DATA", signalPeriod: period, detail };
    }
  }
  const lastYield = yields.filter((y) => y.date <= period).at(-1)?.date;
  if ((!lastYield || lastYield < lastBday) && !yields.some((y) => y.date > period)) {
    const detail = `SETB3MBENCH for ${lastBday} not published yet (last ${lastYield ?? "none"})`;
    await log("WAITING_FOR_DATA", detail, sources0);
    return { outcome: "WAITING_FOR_DATA", signalPeriod: period, detail };
  }

  const toPts = (xs: NavPoint[]): Point[] => xs.map((p) => ({ date: p.navDate, value: p.nav }));
  const res = computeRegionalSignal(asOf, Object.fromEntries(Object.entries(navs).map(([k, v]) => [k, toPts(v)])),
                                    yields.map((y) => ({ date: y.date, value: y.value })));
  const sources = { nav: deps.navProvider.name, yield: deps.yieldProvider.name };

  if (res.status === "NO_SIGNAL") {
    const iid = res.incomplete_instrument;
    if (iid && res.reason.startsWith("no NAV series")) {
      await log("DATA_ERROR", res.reason, sources);
      return { outcome: "DATA_ERROR", signalPeriod: period, detail: res.reason };
    }
    if (iid) {
      const publishedPastMonthEnd = (navs[iid] ?? []).some((p) => p.navDate > period);
      if (!publishedPastMonthEnd) {
        await log("WAITING_FOR_DATA", res.reason, sources);
        return { outcome: "WAITING_FOR_DATA", signalPeriod: period, detail: res.reason };
      }
    } else if (res.reason.includes("hurdle_return") && !yields.some((y) => y.date > period)) {
      await log("WAITING_FOR_DATA", res.reason, sources);
      return { outcome: "WAITING_FOR_DATA", signalPeriod: period, detail: res.reason };
    }
  }

  const record = buildRecord(res, navs, yields, deps, checkedAt);
  const { inserted, record: stored } = await deps.store.insertSignalIfAbsent(record);
  await log(stored.status, inserted ? `stored final ${stored.status}: ${stored.reason}` : "concurrent run already stored this period", sources);
  return { outcome: stored.status, signalPeriod: period, detail: stored.reason, record: stored, inserted };
}
