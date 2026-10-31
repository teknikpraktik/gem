import type { ISODate } from "../engine/dates";
import type { EngineInputPayload } from "../audit";
import type { FreshnessEntry } from "../freshness";
import type { NavPoint } from "../providers/types";

/** Final, immutable monthly signal (one per strategy + period + version). */
export interface SignalRecord {
  strategyId: string;
  strategyVersion: string;
  signalPeriod: ISODate; // month end the signal is based on
  generatedAt: string;
  status: "VALID" | "NO_SIGNAL";
  selectedAsset: string | null; // "usa" | "europe" | "em" | "cash"
  selectedFund: string | null; // instrument id
  returns: { usa: number | null; europe: number | null; em: number | null; cash: number | null };
  cashHurdle: number | null;
  reason: string;
  inputDates: Record<string, { start: ISODate | null; end: ISODate | null }>;
  inputSources: Record<string, string>;
  dataQuality: Record<string, unknown>;
  providerVersions: Record<string, string>;
  inputs: SignalInput[];
  origin: "live" | "research_pipeline";
  // ---- audit trail (migration 002) ----
  /** Latest observation date contained in the engine input. */
  dataAsOf: ISODate | null;
  /** "sha256:<hex>" over the canonical JSON of the exact engine input (lib/audit.ts). */
  inputDataChecksum: string | null;
  /** Git SHA of the code that produced the snapshot ("unknown" if not available). */
  codeVersion: string;
  engineVersion: string;
  referenceImplementation: string;
  /** Exact engine input; null for research-pipeline bootstrap records. */
  inputPayload: EngineInputPayload | null;
}

export interface SignalInput {
  instrumentId: string;
  startDate: ISODate | null;
  startNav: number | null;
  endDate: ISODate | null;
  endNav: number | null;
  return12m: number | null;
}

export type AttemptStatus = "VALID" | "NO_SIGNAL" | "WAITING_FOR_DATA" | "DATA_ERROR" | "ALREADY_FINAL";

/** Every pipeline run is logged (data_source_status), final or not. */
export interface AttemptRecord {
  strategyId: string;
  signalPeriod: ISODate;
  checkedAt: string;
  status: AttemptStatus;
  detail: string;
  sources: Record<string, string>;
  /** Freshness/provenance per series at the time of the attempt (empty if not fetched). */
  freshness?: FreshnessEntry[];
}

export interface SignalStore {
  readonly kind: string;
  readonly writable: boolean;
  getSignal(strategyId: string, period: ISODate, version: string): Promise<SignalRecord | null>;
  /** Idempotent: inserts only if (strategy, period, version) is absent; never overwrites. */
  insertSignalIfAbsent(rec: SignalRecord): Promise<{ inserted: boolean; record: SignalRecord }>;
  listSignals(strategyId: string, limit?: number): Promise<SignalRecord[]>;
  latestValid(strategyId: string): Promise<SignalRecord | null>;
  recordAttempt(a: AttemptRecord): Promise<void>;
  latestAttempt(strategyId: string, period: ISODate): Promise<AttemptRecord | null>;
  saveNavObservations(points: NavPoint[]): Promise<void>;
  latestNavs(): Promise<Record<string, NavPoint>>;
}

export class ImmutableSignalError extends Error {
  constructor(key: string) {
    super(`signal ${key} already exists and is immutable`);
    this.name = "ImmutableSignalError";
  }
}

export function signalKey(r: Pick<SignalRecord, "strategyId" | "signalPeriod" | "strategyVersion">): string {
  return `${r.strategyId}|${r.signalPeriod}|${r.strategyVersion}`;
}
