/**
 * Client-safe helpers (no server imports): imported by client components.
 */
export type DisplayStatus = "VALID" | "WAITING_FOR_DATA" | "NO_SIGNAL" | "DATA_ERROR" | "STALE_DATA";

/** Client-side: what to show when the device is offline or data is old. */
export function offlineDisplay(online: boolean, lastSyncedAt: string | null, payloadStatus: DisplayStatus) {
  if (online) return { banner: null as string | null, treatAsCurrent: payloadStatus === "VALID", label: payloadStatus };
  return {
    banner: `Offline · Senast synkroniserad ${lastSyncedAt ? new Date(lastSyncedAt).toLocaleString("sv-SE", { timeZone: "Europe/Stockholm" }) : "okänt"}`,
    treatAsCurrent: false,
    label: "OFFLINE_CACHED" as const,
  };
}
