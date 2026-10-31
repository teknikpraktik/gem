import LineChart, { Series } from "@/components/LineChart";
import MetricsTable, { MetricRow } from "@/components/MetricsTable";
import { getBacktest } from "@/lib/api";
import { pctPlain } from "@/lib/explain";

export const dynamic = "force-static";

type M = MetricRow["m"] & Record<string, unknown>;

function cumulative(rets: [string, number | null][]) {
  let v = 1;
  const out: { t: string; v: number }[] = [];
  for (const [t, r] of rets) {
    if (r === null) continue;
    v *= 1 + r;
    out.push({ t, v: v - 1 });
  }
  return out;
}

function drawdown(rets: [string, number | null][]) {
  let v = 1, peak = 1;
  return rets.filter(([, r]) => r !== null).map(([t, r]) => {
    v *= 1 + (r as number);
    peak = Math.max(peak, v);
    return { t, v: v / peak - 1 };
  });
}

export default function Backtest() {
  const b = getBacktest();
  const inv = b.investable;
  const benchOf = (vn: string, k: string): MetricRow => {
    const m = (inv.benchmarks_same_window as Record<string, Record<string, M & { status?: string }>>)[vn]?.[k];
    return m && !m.status ? { name: "", m } : { name: "", missing: "kan inte beräknas för perioden (saknad NAV vid månadsslut, t.ex. EM jan–feb 2025, eller Ränta Kort före 2023-12)" };
  };
  const sc = (vn: string, s: string) => (inv.variants as Record<string, { scenarios: Record<string, { metrics: M }> }>)[vn].scenarios[s].metrics;
  const hybridRows: MetricRow[] = [
    { name: "REGIONAL_SEK – Avanza-fonder (B, nästa handelsbara)", note: "Huvudresultat: verkliga NAV, fondernas bryttider", m: sc("HYBRID_SYNTH_CASH", "B_NEXT_TRADABLE") },
    { name: "REGIONAL_SEK – konservativ (C)", note: "+1 bankdag, köp efter likvid", m: sc("HYBRID_SYNTH_CASH", "C_CONSERVATIVE") },
    { name: "REGIONAL_SEK – publicerad close (A)", note: "LOOKAHEAD_REFERENCE_ONLY – inte genomförbar", m: sc("HYBRID_SYNTH_CASH", "A_PUBLISHED_CLOSE") },
    { ...benchOf("HYBRID_SYNTH_CASH", "BUY_HOLD_AVANZA_GLOBAL"), name: "Global buy-and-hold (Avanza Global)" },
    { ...benchOf("HYBRID_SYNTH_CASH", "STATIC_70_30_AVANZA_GLOBAL_RANTA_KORT"), name: "70/30 Avanza Global / Ränta Kort" },
    { ...benchOf("HYBRID_SYNTH_CASH", "STATIC_REGIONAL_EQUAL_AVANZA"), name: "Regional 1/3 + 1/3 + 1/3" },
  ];
  const pureRows: MetricRow[] = [
    { name: "REGIONAL_SEK – alla fyra Avanza-fonder (B)", m: sc("PURE_AVANZA_FUNDS", "B_NEXT_TRADABLE") },
    { ...benchOf("PURE_AVANZA_FUNDS", "BUY_HOLD_AVANZA_GLOBAL"), name: "Global buy-and-hold (Avanza Global)" },
    { ...benchOf("PURE_AVANZA_FUNDS", "STATIC_70_30_AVANZA_GLOBAL_RANTA_KORT"), name: "70/30 Avanza Global / Ränta Kort" },
    { ...benchOf("PURE_AVANZA_FUNDS", "STATIC_REGIONAL_EQUAL_AVANZA"), name: "Regional 1/3 + 1/3 + 1/3" },
  ];
  const rl = b.research_long as Record<string, M | string | null>;
  const longRows: MetricRow[] = [
    { name: "REGIONAL_SEK – indexmodell, en månads fördröjning", note: "konservativ gräns", m: rl.REGIONAL_SEK_ONE_MONTH_DELAY as M },
    { name: "REGIONAL_SEK – indexmodell, publicerad close", note: "LOOKAHEAD_REFERENCE_ONLY", m: rl.REGIONAL_SEK_LOOKAHEAD_REFERENCE as M },
    { name: "Global buy-and-hold (Ken French Developed, SEK)", m: rl.BUY_HOLD_GLOBAL as M },
    { name: "70/30 global / svensk kort ränta", m: rl.STATIC_70_30 as M },
    { name: "Regional 1/3 + 1/3 + 1/3", m: rl.STATIC_REGIONAL_EQUAL as M },
  ];
  const curve = inv.equity_curve_hybrid_b_monthly_returns as [string, number | null][];
  const benchCurves = inv.benchmark_monthly_returns as Record<string, Record<string, number | null>>;
  const series: Series[] = [{ name: "REGIONAL_SEK, Avanza-fonder (B)", color: "var(--series-1)", points: cumulative(curve) }];
  const glob = benchCurves?.BUY_HOLD_AVANZA_GLOBAL;
  if (glob) {
    const months = new Set(curve.map(([t]) => t));
    series.push({ name: "Avanza Global", color: "var(--series-2)",
      points: cumulative(Object.entries(glob).filter(([t]) => months.has(t)).sort() as [string, number | null][]) });
  }
  const strat = sc("HYBRID_SYNTH_CASH", "B_NEXT_TRADABLE");
  const gm = benchOf("HYBRID_SYNTH_CASH", "BUY_HOLD_AVANZA_GLOBAL").m;
  return (
    <>
      <h1>Backtest</h1>
      <div className="banner">Historisk avkastning är inte en prognos. Den investerbara perioden med riktiga Avanza-fonder är kort ({String(strat.months)} månader, {String(strat.number_of_switches)} byten) – skillnader på några procentenheter per år kan vara slump.</div>
      <section className="card">
        <h2 style={{ marginTop: 0 }}>Jämförelse under investerbar period</h2>
        <p>REGIONAL_SEK med Avanza-fonder: <strong>{pctPlain(strat.cagr, 2)}</strong> per år. Avanza Global: <strong>{pctPlain(gm?.cagr, 2)}</strong> per år.
          Modellen har inte slagit global buy-and-hold under den moderna investerbara perioden. Den är ett momentum- och risksystem, avsett att minska exponeringen under längre negativa marknadsregimer – inte en metod för högre avkastning.</p>
      </section>
      <section className="card">
        <h2 style={{ marginTop: 0 }}>Investerbar implementering, 2021–2026</h2>
        <p className="small muted">Signal och exekvering på verkliga NAV för Avanza USA, Europa och Emerging Markets; defensivt läge med syntetisk svensk kort ränta (Riksbanken) innan Avanza Ränta Kort fanns (2023-12).</p>
        <MetricsTable rows={hybridRows} sharpeNote="Sharpe med riskfri ränta = 0. Byten = antal fondbyten." />
        <LineChart series={series} valueFormat="pct0" ariaLabel="Ackumulerad avkastning" />
        <h3>Drawdown – REGIONAL_SEK (B)</h3>
        <LineChart series={[{ name: "Drawdown från tidigare topp", color: "var(--series-1)", points: drawdown(curve) }]} height={150}
          valueFormat="pct1" ariaLabel="Drawdown" />
      </section>
      <section className="card">
        <h2 style={{ marginTop: 0 }}>Endast verkliga Avanza-fonder, 2024–2026</h2>
        <MetricsTable rows={pureRows} sharpeNote="Mycket kort period (34 månader). Sharpe med riskfri ränta = 0." />
      </section>
      <section className="card research">
        <h2 style={{ marginTop: 0 }}>Lång forskningsmodell, 1994–2026 (inte investerbar)</h2>
        <p className="small muted">{String(rl.description ?? "")} Ingen daglig EM-data finns, så endast månadskonventioner. Visar historiskt beteende i björnmarknader (2000–2002, 2008).</p>
        <MetricsTable rows={longRows} sharpeNote="Sharpe mot svensk kort ränta. Indexserier ≠ fonder: tracking difference −0,6 till −1,4 pp/år." />
      </section>
      <p className="small muted">Källa: forskningspipelinen i GitHub Actions (commit {b.research_commit}, exporterad {b.exported_at}).</p>
    </>
  );
}
