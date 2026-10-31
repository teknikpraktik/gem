/**
 * Payload builders shared by API routes and server-rendered pages (one source of truth).
 * Nothing here implements an investment rule; it only reads stored signals.
 */

import backtest from "@/data/backtest.json";
import history from "@/data/history.json";
import research from "@/data/research.json";
import { STRATEGY_ID, STRATEGY_VERSION } from "./engine/regional";
import { Deps, getDeps } from "./deps";
import { explainSignal } from "./explain";
import { INSTRUMENTS } from "./instruments";
import { loadSignalState, SignalState } from "./status";

export const DISCLAIMER =
  "Regelbaserad signalmonitor för forskning och beslutsstöd. Ingen investeringsrådgivning och ingen automatisk handel. " +
  "Historisk avkastning är ingen prognos.";

export interface SignalPayload {
  state: SignalState;
  explanation: string[];
  latestNavs: Record<string, { navDate: string; nav: number; retrievedAt: string; source: string; quality: string }>;
  store: string;
  serverTime: string;
  disclaimer: string;
}

export async function getSignalPayload(deps: Deps = getDeps()): Promise<SignalPayload> {
  const now = deps.now();
  const state = await loadSignalState(deps.store, now);
  const latestNavs = await deps.store.latestNavs();
  return {
    state,
    explanation: state.current ? explainSignal(state.current) : [],
    latestNavs: Object.fromEntries(Object.entries(latestNavs).map(([k, p]) => [k, { navDate: p.navDate, nav: p.nav,
      retrievedAt: p.retrievedAt, source: p.source, quality: p.quality }])),
    store: deps.store.kind,
    serverTime: now.toISOString(),
    disclaimer: DISCLAIMER,
  };
}

export interface HistoryRow {
  signalPeriod: string;
  status: string;
  selectedFund: string | null;
  previousFund: string | null;
  switched: boolean;
  returns: Record<string, number | null>;
  reason: string;
  origin: "live" | "research_pipeline";
}

/** Live snapshots override research backfill for the same period. */
export async function getHistory(deps: Deps = getDeps()): Promise<HistoryRow[]> {
  const live = await deps.store.listSignals(STRATEGY_ID, 600);
  const byPeriod = new Map<string, HistoryRow>();
  for (const s of (history as { signals: HistoryRow[] }).signals) byPeriod.set(s.signalPeriod, { ...s });
  for (const s of live.filter((x) => x.strategyVersion === STRATEGY_VERSION)) {
    byPeriod.set(s.signalPeriod, { signalPeriod: s.signalPeriod, status: s.status, selectedFund: s.selectedFund, previousFund: null,
      switched: false, returns: s.returns, reason: s.reason, origin: s.origin });
  }
  const rows = [...byPeriod.values()].sort((a, b) => (a.signalPeriod < b.signalPeriod ? -1 : 1));
  let prev: string | null = null;
  for (const r of rows) {
    r.previousFund = prev;
    r.switched = Boolean(r.selectedFund && prev && r.selectedFund !== prev);
    if (r.selectedFund) prev = r.selectedFund;
  }
  return rows.reverse();
}

export async function getStatus(deps: Deps = getDeps()) {
  const p = await getSignalPayload(deps);
  return {
    strategy: STRATEGY_ID,
    strategyVersion: STRATEGY_VERSION,
    expectedPeriod: p.state.expectedPeriod,
    status: p.state.status,
    statusDetail: p.state.statusDetail,
    lastAttempt: p.state.lastAttempt,
    signalGeneratedAt: p.state.current?.generatedAt ?? null,
    signalOrigin: p.state.current?.origin ?? null,
    latestNavs: p.latestNavs,
    providers: {
      nav: { name: deps.navProvider.name, version: deps.navProvider.version, quality: deps.navProvider.quality },
      yield: { name: deps.yieldProvider.name, version: deps.yieldProvider.version, quality: "OFFICIAL" },
    },
    instruments: INSTRUMENTS.map((i) => ({ instrumentId: i.instrumentId, name: i.name, isin: i.isin, rules: i.rules })),
    store: p.store,
    serverTime: p.serverTime,
  };
}

export function getBacktest() {
  return backtest;
}

export function getResearch() {
  return research;
}
