import MetricsTable, { MetricRow } from "@/components/MetricsTable";
import { getResearch } from "@/lib/api";
import { pctPlain } from "@/lib/explain";

export const dynamic = "force-static";

type M = NonNullable<MetricRow["m"]>;

export default function Research() {
  const r = getResearch() as unknown as {
    gem_sek: { window: string; monthly: Record<string, M>; daily_a: M; daily_b: M; daily_c: M;
               agreement_vs_original: { months: number; identical: number; different: number; agreement_pct: number;
                 differences_absolute_momentum: number; differences_relative_momentum: number; top_years: number[] };
               ranking_invariance: { months: number; ranking_mismatches: number } };
    omrx_validation: { series: Record<string, unknown> | null; omrx_daily_b: M; proxy_daily_b: M;
                       hurdle_sensitivity: Record<string, { window: string; months: number; signals_changed: number; signal_agreement_pct: number }> };
    gem_original_reproduction: { reference: { cagr: number; volatility: number; max_drawdown: number; sharpe: number; source: string };
                                 ours: (M & { execution: string })[]; data_note: string };
    research_commit: string; exported_at: string;
  };
  const g = r.gem_sek;
  const ag = g.agreement_vs_original;
  const rows: MetricRow[] = [
    { name: "GEM_SEK – daglig, nästa handelsbara (B)", m: g.daily_b },
    { name: "GEM_SEK – daglig, konservativ (C)", m: g.daily_c },
    { name: "GEM_SEK – publicerad close (A)", note: "LOOKAHEAD_REFERENCE_ONLY", m: g.daily_a },
    { name: "GEM_ORIGINAL-regel, samma ben (USD), en månads fördröjning", note: "defensivt: US T-bills (ingen öppen obligationsserie)", m: g.monthly.GEM_ORIGINAL_FF_ONE_MONTH_DELAY },
  ];
  const hs = Object.entries(r.omrx_validation.hurdle_sensitivity);
  const ref = r.gem_original_reproduction.reference;
  const s = r.omrx_validation.series as { first_observation?: string; last_observation?: string; observations?: number; cagr?: number } | null;
  return (
    <>
      <div className="banner research" role="note">RESEARCH MODEL · NOT LIVE SIGNAL</div>
      <h1>Research</h1>
      <p className="muted">Modellerna här är forsknings- och referensmodeller. De visas för transparens och får inte läsas som köp- eller säljsignaler. Den enda live-signalen är REGIONAL_SEK på startsidan.</p>

      <section className="card research">
        <p className="eyebrow">Research model · not live signal</p>
        <h2 style={{ marginTop: 4 }}>GEM_SEK, {g.window}</h2>
        <p className="small muted">Antonaccis GEM-regel i SEK: USA (Ken French CRSP) mot Developed ex US (utan EM) och svensk kort ränta (Riksbanken). Proxydata; saknar Avanza-fond för ex-US-benet och används därför inte live.</p>
        <MetricsTable rows={rows} sharpeNote="Sharpe mot svensk kort ränta (GEM_SEK) respektive US T-bills (original)." />
        <h3>Jämförelse med original-GEM (samma period och ben)</h3>
        <ul>
          <li>Signalöverensstämmelse: <strong>{pctPlain(ag.agreement_pct, 1)}</strong> ({ag.identical} av {ag.months} månader).</li>
          <li>Alla {ag.different} skillnader kommer från absolut momentum (risk på/av); {ag.differences_relative_momentum} från valet USA/ex-US. Kontroll: valutaomräkningen ändrade rankingen USA/ex-US i {g.ranking_invariance.ranking_mismatches} av {g.ranking_invariance.months} månader.</li>
          <li>Skillnaderna koncentreras till: {ag.top_years.join(", ")}.</li>
        </ul>
      </section>

      <section className="card research">
        <p className="eyebrow">Research model · not live signal</p>
        <h2 style={{ marginTop: 4 }}>OMRX-validering av svensk cash-proxy</h2>
        <p>OMRX Treasury Bill Index (FRED API, {s?.first_observation} – {s?.last_observation}, {s?.observations} observationer) jämfört med Riksbankens 3-månaders statsskuldväxel omräknad till avkastning:</p>
        <ul>
          {hs.map(([k, v]) => (
            <li key={k}><strong>{pctPlain(v.signal_agreement_pct, 0)} signalöverensstämmelse</strong> ({v.months - v.signals_changed} av {v.months} månader) för {k.split(" vs ")[0].startsWith("REGIONAL") ? "REGIONAL_SEK" : "GEM_SEK"}.</li>
          ))}
          <li>GEM_SEK med OMRX: CAGR {pctPlain(r.omrx_validation.omrx_daily_b?.cagr, 2)}, med Riksbanksproxy: {pctPlain(r.omrx_validation.proxy_daily_b?.cagr, 2)} (daglig B, samma period).</li>
        </ul>
        <p className="small muted">Slutsats: Riksbanksproxyn är tillräckligt bra för historisk forskning före 2008, då OMRX inte finns öppet.</p>
      </section>

      <section className="card research">
        <p className="eyebrow">Research model · not live signal</p>
        <h2 style={{ marginTop: 4 }}>GEM_ORIGINAL – reproduktion 1974–2013</h2>
        <div className="table-scroll">
          <table>
            <thead><tr><th></th><th className="num">CAGR</th><th className="num">Volatilitet</th><th className="num">Max DD</th><th className="num">Sharpe</th></tr></thead>
            <tbody>
              <tr><td>Referens ({ref.source})</td><td className="num">{pctPlain(ref.cagr, 2)}</td><td className="num">{pctPlain(ref.volatility, 2)}</td><td className="num">{pctPlain(ref.max_drawdown, 2)}</td><td className="num">{ref.sharpe.toFixed(2).replace(".", ",")}</td></tr>
              {r.gem_original_reproduction.ours.map((o) => (
                <tr key={o.execution}><td>Vår körning ({o.execution === "IDEALIZED_CLOSE" ? "publicerad close, LOOKAHEAD_REFERENCE_ONLY" : "en månads fördröjning"})</td>
                  <td className="num">{pctPlain(o.cagr, 2)}</td><td className="num">{pctPlain(o.volatility, 2)}</td><td className="num">{pctPlain(o.max_drawdown, 2)}</td><td className="num">{(o.sharpe ?? 0).toFixed(2).replace(".", ",")}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="small muted">{r.gem_original_reproduction.data_note}</p>
      </section>

      <section className="card research">
        <p className="eyebrow">Research model · not live signal</p>
        <h2 style={{ marginTop: 4 }}>Lång regional forskningsmodell</h2>
        <p>REGIONAL_SEK på Ken French-regionindex 1994–2026 visas under <a href="/backtest">Backtest</a>. Den bygger på indexserier, inte fonder, och är bara ungefärligt jämförbar med live-signalen (82 % samma signal där båda finns).</p>
      </section>
      <p className="small muted">Källa: forskningspipelinen (commit {r.research_commit}, exporterad {r.exported_at}).</p>
    </>
  );
}
