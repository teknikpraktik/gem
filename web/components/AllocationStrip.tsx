import { fmtDate } from "@/lib/explain";

/** One cell per month, colored by the selected fund (categorical identity, fixed order). */
const FUNDS: { id: string; label: string; v: string }[] = [
  { id: "AVANZA_USA", label: "Avanza USA", v: "var(--series-1)" },
  { id: "AVANZA_EUROPA", label: "Avanza Europa", v: "var(--series-2)" },
  { id: "AVANZA_EM", label: "Avanza Emerging Markets", v: "var(--series-3)" },
  { id: "AVANZA_RANTA_KORT", label: "Avanza Ränta Kort", v: "var(--series-4)" },
];

export default function AllocationStrip({ rows }: { rows: { signalPeriod: string; selectedFund: string | null; status: string }[] }) {
  const data = [...rows].sort((a, b) => (a.signalPeriod < b.signalPeriod ? -1 : 1));
  const n = data.length;
  const W = 900, H = 46, gap = 2;
  const w = n ? (W - gap * (n - 1)) / n : W;
  const years = data.filter((d, i) => i === 0 || d.signalPeriod.slice(0, 4) !== data[i - 1].signalPeriod.slice(0, 4));
  return (
    <figure style={{ margin: "8px 0 0" }}>
      <div className="legend">
        {FUNDS.map((f) => <span key={f.id} style={{ ["--c" as string]: f.v }}>{f.label}</span>)}
        <span style={{ ["--c" as string]: "transparent" }}>Ingen signal (tom ruta)</span>
      </div>
      <svg className="chart" viewBox={`0 0 ${W} ${H + 18}`} role="img" aria-label="Vald fond per månad">
        {data.map((d, i) => {
          const f = FUNDS.find((x) => x.id === d.selectedFund);
          return (
            <rect key={d.signalPeriod} x={i * (w + gap)} y={0} width={Math.max(w, 1)} height={H} rx={2}
              fill={f ? f.v : "none"} stroke={f ? "none" : "var(--border)"}>
              <title>{`${fmtDate(d.signalPeriod)}: ${f ? f.label : d.status}`}</title>
            </rect>
          );
        })}
        {years.map((d) => {
          const i = data.indexOf(d);
          return <text key={d.signalPeriod} x={i * (w + gap)} y={H + 14}>{d.signalPeriod.slice(0, 4)}</text>;
        })}
      </svg>
      <figcaption className="small muted">Varje ruta är en signalmånad. Hovra för detaljer; tabellen nedan visar samma data.</figcaption>
    </figure>
  );
}
