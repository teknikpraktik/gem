/**
 * Deterministic, rule-based explanations and formatting (no AI, no free text).
 */

import { instrumentById } from "./instruments";
import type { SignalRecord } from "./store/types";

const REGION_LABEL: Record<string, string> = { usa: "USA", europe: "Europa", em: "Emerging Markets", cash: "Svensk kort ränta" };

export function pct(x: number | null | undefined, digits = 1): string {
  if (x === null || x === undefined || !Number.isFinite(x)) return "–";
  const s = (x * 100).toFixed(digits).replace(".", ",").replace("-", "−");
  return `${x > 0 ? "+" : ""}${s} %`;
}

export function pctPlain(x: number | null | undefined, digits = 1): string {
  if (x === null || x === undefined || !Number.isFinite(x)) return "–";
  return `${(x * 100).toFixed(digits).replace(".", ",").replace("-", "−")} %`;
}

export function fmtDate(d: string | null | undefined): string {
  if (!d) return "–";
  const dt = new Date(`${d.slice(0, 10)}T12:00:00Z`);
  return dt.toLocaleDateString("sv-SE", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

export function fmtDateTime(ts: string | null | undefined): string {
  if (!ts) return "–";
  return new Date(ts).toLocaleString("sv-SE", { timeZone: "Europe/Stockholm", dateStyle: "medium", timeStyle: "short" });
}

export function regionLabel(asset: string | null): string {
  return asset ? REGION_LABEL[asset] ?? asset : "–";
}

/** Rule explanation derived only from the stored numbers. */
export function explainSignal(s: SignalRecord): string[] {
  const r = s.returns;
  if (s.status !== "VALID") {
    return [`Regeln kunde inte tillämpas för perioden: ${s.reason}.`, "Ingen ny allokering anges för perioden."];
  }
  const regions = (["usa", "europe", "em"] as const).map((k) => ({ k, v: r[k] as number }));
  const best = regions.reduce((a, b) => (b.v > a.v ? b : a));
  const fund = instrumentById(s.selectedFund)?.name ?? s.selectedFund;
  if (s.selectedAsset === "cash") {
    return [
      `${REGION_LABEL[best.k]} har högst 12-månadersavkastning (${pct(best.v)}) men ligger inte över cash-tröskeln (${pct(r.cash)}).`,
      `Regeln väljer därför det defensiva alternativet: ${fund}.`,
    ];
  }
  return [
    `${REGION_LABEL[best.k]} har högst 12-månadersavkastning (${pct(best.v)}) av de tre regionerna och ligger över cash-tröskeln (${pct(r.cash)}).`,
    `Regeln väljer därför ${fund} med 100 % allokering.`,
  ];
}

export const STATUS_TEXT: Record<string, { title: string; body: string }> = {
  VALID: { title: "VALID", body: "Signalen är beräknad på komplett data för perioden." },
  WAITING_FOR_DATA: { title: "WAITING_FOR_DATA", body: "Månadens slutkurser (NAV) är inte publicerade eller inte behandlade ännu. Ingen ny signal finns för perioden." },
  NO_SIGNAL: { title: "NO_SIGNAL", body: "Regeln kunde inte tillämpas för perioden (t.ex. saknad månadsslutskurs). Ingen ny allokering anges." },
  DATA_ERROR: { title: "DATA_ERROR", body: "Datakällan gav fel eller oväntat format. Ingen signal har beräknats; en tidigare signal visas inte som aktuell." },
  STALE_DATA: { title: "STALE_DATA", body: "Månadens signal borde ha funnits men saknas. Data är inaktuell." },
};
