"use client";
import { useEffect, useState } from "react";
import { offlineDisplay, type DisplayStatus } from "@/lib/offline";

const KEY = "gem-signal-last-sync";

/** Remembers when this signal was last loaded online; shows an offline banner otherwise. */
export default function OfflineSync({ status, period, fund }: { status: DisplayStatus; period: string; fund: string | null }) {
  const [online, setOnline] = useState(true);
  const [synced, setSynced] = useState<string | null>(null);
  useEffect(() => {
    const on = () => setOnline(navigator.onLine);
    on();
    try {
      if (navigator.onLine) {
        const rec = { syncedAt: new Date().toISOString(), status, period, fund };
        localStorage.setItem(KEY, JSON.stringify(rec));
        setSynced(rec.syncedAt);
      } else {
        setSynced(JSON.parse(localStorage.getItem(KEY) ?? "null")?.syncedAt ?? null);
      }
    } catch {
      /* storage unavailable: banner still works */
    }
    window.addEventListener("online", on);
    window.addEventListener("offline", on);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", on);
    };
  }, [status, period, fund]);
  const d = offlineDisplay(online, synced, status);
  if (!d.banner) return null;
  return <div className="banner" role="alert">{d.banner}. Visad signal kan vara inaktuell och ska inte läsas som aktuell.</div>;
}
