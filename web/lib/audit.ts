/**
 * Audit trail for signal snapshots.
 *
 * Every live snapshot stores the EXACT engine input (EngineInputPayload), its
 * SHA-256 checksum over a canonical JSON encoding, the code version (git SHA)
 * and the engine/reference versions. `verifySnapshot` recomputes the checksum
 * and re-runs the engine on the stored input, so any signal can be reproduced
 * and checked after the fact.
 */
import { createHash } from "node:crypto";
import type { ISODate } from "./engine/dates";
import { computeRegionalSignal, EngineResult, Point } from "./engine/regional";

export const ENGINE_VERSION = "web/lib/engine/regional.ts@regional-sek-v1.0.0";
export const REFERENCE_IMPLEMENTATION = "research/src/gem/live.py::regional_live_signal";

/** Exactly what the engine received. Arrays are [date, value], sorted by date. */
export interface EngineInputPayload {
  asOf: ISODate;
  navs: Record<string, [ISODate, number][]>;
  yields: [ISODate, number][];
}

export function buildEngineInput(asOf: ISODate, navs: Record<string, Point[]>, yields: Point[]): EngineInputPayload {
  const enc = (xs: Point[]): [ISODate, number][] =>
    [...xs].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0)).map((p) => [p.date, p.value]);
  return { asOf, navs: Object.fromEntries(Object.keys(navs).sort().map((k) => [k, enc(navs[k])])), yields: enc(yields) };
}

/** Canonical JSON: object keys sorted recursively, no whitespace, shortest round-trip numbers. */
export function canonicalJson(v: unknown): string {
  if (v === null || typeof v !== "object") {
    if (typeof v === "number" && !Number.isFinite(v)) throw new Error("non-finite number in audit payload");
    return JSON.stringify(v);
  }
  if (Array.isArray(v)) return `[${v.map(canonicalJson).join(",")}]`;
  const o = v as Record<string, unknown>;
  return `{${Object.keys(o).sort().filter((k) => o[k] !== undefined).map((k) => `${JSON.stringify(k)}:${canonicalJson(o[k])}`).join(",")}}`;
}

export function inputChecksum(p: EngineInputPayload): string {
  return `sha256:${createHash("sha256").update(canonicalJson(p)).digest("hex")}`;
}

/** Latest observation date contained in the input (what the data is "as of"). */
export function dataAsOf(p: EngineInputPayload): ISODate | null {
  let m: ISODate | null = null;
  for (const xs of [...Object.values(p.navs), p.yields]) for (const [d] of xs) if (d <= p.asOf && (m === null || d > m)) m = d;
  return m;
}

/** Git SHA of the deployed code (Vercel sets VERCEL_GIT_COMMIT_SHA), else GIT_SHA, else "unknown". */
export function codeVersion(env: Record<string, string | undefined> = process.env): string {
  return env.VERCEL_GIT_COMMIT_SHA || env.GIT_SHA || "unknown";
}

export function runEngine(p: EngineInputPayload): EngineResult {
  const pts = (xs: [ISODate, number][]): Point[] => xs.map(([date, value]) => ({ date, value }));
  return computeRegionalSignal(p.asOf, Object.fromEntries(Object.entries(p.navs).map(([k, v]) => [k, pts(v)])), pts(p.yields));
}

export interface VerificationResult {
  checksumMatches: boolean;
  recomputedChecksum: string;
  decisionMatches: boolean;
  recomputed: Pick<EngineResult, "status" | "target" | "reason" | "returns">;
}

/** Re-derive a stored snapshot from its stored input. */
export function verifySnapshot(rec: { inputDataChecksum: string | null; status: string; selectedFund: string | null;
                                      reason: string; returns: Record<string, number | null> },
                               payload: EngineInputPayload): VerificationResult {
  const recomputedChecksum = inputChecksum(payload);
  const r = runEngine(payload);
  const sameReturns = (["usa", "europe", "em", "cash"] as const).every((k) =>
    ((r.returns as Record<string, number | null | undefined>)[k] ?? null) === (rec.returns[k] ?? null));
  return {
    checksumMatches: recomputedChecksum === rec.inputDataChecksum,
    recomputedChecksum,
    decisionMatches: r.status === rec.status && r.target === rec.selectedFund && r.reason === rec.reason && sameReturns,
    recomputed: { status: r.status, target: r.target, reason: r.reason, returns: r.returns },
  };
}
