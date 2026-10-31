/**
 * Read-time status of the live signal. The UI shows exactly this; it never
 * promotes an older signal to "current".
 *
 *   VALID            final VALID signal exists for the expected period
 *   NO_SIGNAL        final NO_SIGNAL for the expected period (rule could not be applied)
 *   WAITING_FOR_DATA expected period not final yet, still within the publication window
 *   STALE_DATA       expected period not final and the publication window has passed
 *   DATA_ERROR       latest attempt for the expected period failed (provider/format)
 */

import { busdayCount, ISODate, lastBusinessDayOnOrBefore, previousMonthEnd } from "./engine/dates";
import { STRATEGY_ID, STRATEGY_VERSION } from "./engine/regional";
import { stockholmDate } from "./pipeline";
import type { AttemptRecord, SignalRecord, SignalStore } from "./store/types";

export type DisplayStatus = "VALID" | "WAITING_FOR_DATA" | "NO_SIGNAL" | "DATA_ERROR" | "STALE_DATA";

/** Business days after the period's last business day before a missing signal counts as stale. */
export const STALE_AFTER_BDAYS = 6;

export interface SignalState {
  strategyId: string;
  strategyVersion: string;
  asOf: ISODate;
  expectedPeriod: ISODate;
  status: DisplayStatus;
  /** Signal for the expected period - only when status is VALID or NO_SIGNAL. */
  current: SignalRecord | null;
  /** Most recent VALID signal for an EARLIER period - never to be shown as current. */
  lastValid: SignalRecord | null;
  lastAttempt: AttemptRecord | null;
  statusDetail: string;
}

export function deriveStatus(now: Date, forPeriod: SignalRecord | null, latestValid: SignalRecord | null,
                             lastAttempt: AttemptRecord | null): SignalState {
  const asOf = stockholmDate(now);
  const expectedPeriod = previousMonthEnd(asOf);
  let status: DisplayStatus;
  let statusDetail: string;
  if (forPeriod) {
    status = forPeriod.status;
    statusDetail = forPeriod.reason;
  } else if (lastAttempt?.status === "DATA_ERROR") {
    status = "DATA_ERROR";
    statusDetail = lastAttempt.detail;
  } else if (busdayCount(lastBusinessDayOnOrBefore(expectedPeriod), asOf) > STALE_AFTER_BDAYS) {
    status = "STALE_DATA";
    statusDetail = lastAttempt?.detail ?? "no signal generated for the expected period";
  } else {
    status = "WAITING_FOR_DATA";
    statusDetail = lastAttempt?.detail ?? "month-end NAVs not yet processed";
  }
  const current = forPeriod;
  const lastValid = latestValid && latestValid.signalPeriod !== expectedPeriod ? latestValid : null;
  return { strategyId: STRATEGY_ID, strategyVersion: STRATEGY_VERSION, asOf, expectedPeriod, status, current,
           lastValid: status === "VALID" ? null : lastValid, lastAttempt, statusDetail };
}

export async function loadSignalState(store: SignalStore, now: Date): Promise<SignalState> {
  const expected = previousMonthEnd(stockholmDate(now));
  const [forPeriod, latestValid, lastAttempt] = await Promise.all([
    store.getSignal(STRATEGY_ID, expected, STRATEGY_VERSION),
    store.latestValid(STRATEGY_ID),
    store.latestAttempt(STRATEGY_ID, expected),
  ]);
  return deriveStatus(now, forPeriod, latestValid, lastAttempt);
}

/** Client-side: what to show when the device is offline or data is old. */
export function offlineDisplay(online: boolean, lastSyncedAt: string | null, payloadStatus: DisplayStatus) {
  if (online) return { banner: null as string | null, treatAsCurrent: payloadStatus === "VALID", label: payloadStatus };
  return {
    banner: `Offline · Senast synkroniserad ${lastSyncedAt ? new Date(lastSyncedAt).toLocaleString("sv-SE", { timeZone: "Europe/Stockholm" }) : "okänt"}`,
    treatAsCurrent: false,
    label: "OFFLINE_CACHED" as const,
  };
}
