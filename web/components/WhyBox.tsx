import { pct } from "@/lib/explain";
import type { SignalRecord } from "@/lib/store/types";

const ROWS: { key: "usa" | "europe" | "em" | "cash"; label: string }[] = [
  { key: "usa", label: "USA" }, { key: "europe", label: "Europa" }, { key: "em", label: "Emerging Markets" }, { key: "cash", label: "Cash (tröskel)" },
];

export default function WhyBox({ signal, explanation }: { signal: SignalRecord; explanation: string[] }) {
  const vals = ROWS.map((r) => signal.returns[r.key]).filter((v): v is number => typeof v === "number");
  const maxAbs = Math.max(0.01, ...vals.map((v) => Math.abs(v)));
  return (
    <section className="card" aria-labelledby="why-h">
      <h2 id="why-h" style={{ marginTop: 0 }}>Varför?</h2>
      <p className="small muted">12-månaders avkastning per region (fond-NAV, SEK) och svensk kort ränta, per {signal.signalPeriod}.</p>
      {ROWS.map((r) => {
        const v = signal.returns[r.key];
        const sel = r.key === signal.selectedAsset;
        const w = typeof v === "number" ? (Math.abs(v) / maxAbs) * 100 : 0;
        return (
          <div className="why-row" key={r.key}>
            <span>{r.label}{sel ? <span className="tag">vald</span> : null}</span>
            <span className="why-bar" aria-hidden="true"><i className={sel ? "sel" : ""} style={{ left: 0, width: `${w}%` }} /></span>
            <span className="val">{pct(v)}</span>
          </div>
        );
      })}
      {explanation.map((t) => <p key={t}>{t}</p>)}
      <p className="small muted">Regel: högst 12-månadersavkastning av USA, Europa och EM väljs om den överstiger cash-tröskeln; annars Avanza Ränta Kort. 100 % i en fond. Inga optimerade parametrar.</p>
    </section>
  );
}
