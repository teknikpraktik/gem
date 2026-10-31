/**
 * Freshness and provenance per data source and instrument.
 *
 * For every series used by the monthly signal: provider, instrument, latest
 * observation, latest observation inside the period, retrieval time, whether it
 * is fresh for the period and, if not, why. The pipeline uses the `state` to
 * decide between computing, waiting and failing closed.
 */
import { busdayCount, ISODate, lastBusinessDayOnOrBefore } from "./engine/dates";
import { MAX_STALE_BDAYS_NAV, MAX_STALE_BDAYS_YIELD } from "./engine/regional";

export type FreshnessState =
  | "FRESH"            // observation on the period's last business day
  | "CLOSED_PROVEN"    // last in-period observation within the tolerance and a later observation exists (fund was closed)
  | "NOT_YET_PUBLISHED" // last in-period observation within the tolerance, nothing later yet -> wait
  | "STALE"            // latest observation older than the tolerance allows and nothing later -> provider stale
  | "GAP_TOO_LONG"     // later observations exist but the in-period gap exceeds the tolerance -> engine gives NO_SIGNAL
  | "EMPTY"            // provider returned no observations
  | "TRUNCATED";       // no observation on/before the required history start -> provider returned cut-off history

export interface FreshnessEntry {
  provider: string;
  providerVersion: string;
  instrumentId: string; // instrument id or series id (SETB3MBENCH)
  kind: "NAV" | "YIELD";
  observations: number;
  firstObservation: ISODate | null;
  lastObservation: ISODate | null;
  lastObservationInPeriod: ISODate | null;
  retrievedAt: string | null;
  periodEnd: ISODate;
  requiredDate: ISODate; // last business day of the period
  requiredHistoryFrom: ISODate; // an observation on/before this date must exist (12-month start endpoint)
  toleranceBdays: number;
  state: FreshnessState;
  fresh: boolean;
  reason: string;
}

export function assessSeries(a: {
  provider: string; providerVersion: string; instrumentId: string; kind: "NAV" | "YIELD";
  dates: ISODate[]; retrievedAt: string | null; periodEnd: ISODate; requiredHistoryFrom: ISODate;
}): FreshnessEntry {
  const tol = a.kind === "NAV" ? MAX_STALE_BDAYS_NAV : MAX_STALE_BDAYS_YIELD;
  const req = lastBusinessDayOnOrBefore(a.periodEnd);
  const ds = [...a.dates].sort();
  const inPeriod = ds.filter((d) => d <= a.periodEnd).at(-1) ?? null;
  const last = ds.at(-1) ?? null;
  const later = ds.some((d) => d > a.periodEnd);
  const base = { provider: a.provider, providerVersion: a.providerVersion, instrumentId: a.instrumentId, kind: a.kind,
                 observations: ds.length, firstObservation: ds[0] ?? null, lastObservation: last, lastObservationInPeriod: inPeriod,
                 retrievedAt: a.retrievedAt, periodEnd: a.periodEnd, requiredDate: req, requiredHistoryFrom: a.requiredHistoryFrom,
                 toleranceBdays: tol };
  let state: FreshnessState;
  let reason: string;
  if (ds.length === 0) {
    state = "EMPTY"; reason = "provider returned no observations";
  } else if (ds[0] > a.requiredHistoryFrom) {
    state = "TRUNCATED"; reason = `first observation ${ds[0]} is after ${a.requiredHistoryFrom}: history needed for the 12-month window is missing`;
  } else if (inPeriod !== null && inPeriod >= req) {
    state = "FRESH"; reason = `observation for ${req} present`;
  } else {
    const lag = inPeriod === null ? Infinity : busdayCount(inPeriod, req);
    if (lag <= tol && later) {
      state = "CLOSED_PROVEN"; reason = `last in-period observation ${inPeriod} (${lag} bdays before ${req}); later observation ${last} proves a closure`;
    } else if (lag <= tol) {
      state = "NOT_YET_PUBLISHED"; reason = `observation for ${req} not published yet (last ${inPeriod}, ${lag} bdays before)`;
    } else if (later) {
      state = "GAP_TOO_LONG"; reason = `gap of ${lag === Infinity ? "all" : lag} bdays before ${req} exceeds ${tol} (later observation ${last} exists)`;
    } else {
      state = "STALE"; reason = `latest observation ${last ?? "none"} is more than ${tol} bdays before ${req} and nothing later: source looks stale`;
    }
  }
  return { ...base, state, fresh: state === "FRESH" || state === "CLOSED_PROVEN", reason };
}
