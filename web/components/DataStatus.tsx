import { fmtDate, fmtDateTime } from "@/lib/explain";
import { INSTRUMENTS } from "@/lib/instruments";
import type { SignalPayload } from "@/lib/api";

export default function DataStatus({ p }: { p: SignalPayload }) {
  const cur = p.state.current;
  return (
    <section className="card" aria-labelledby="data-h">
      <h2 id="data-h" style={{ marginTop: 0 }}>Datastatus</h2>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Fond</th><th>Senaste NAV</th><th className="num">NAV</th><th>NAV i signalen</th><th className="hide-sm">Källa</th></tr></thead>
          <tbody>
            {INSTRUMENTS.map((i) => {
              const n = p.latestNavs[i.instrumentId];
              const used = cur?.inputDates?.[i.instrumentId]?.end ?? null;
              return (
                <tr key={i.instrumentId}>
                  <td>{i.name}</td>
                  <td className="date">{n ? fmtDate(n.navDate) : "–"}</td>
                  <td className="num">{n ? n.nav.toFixed(2).replace(".", ",") : "–"}</td>
                  <td>{used ? fmtDate(used) : i.role === "DEFENSIVE" ? "används ej i momentum" : "–"}</td>
                  <td className="small hide-sm">{n ? `${n.source} (${n.quality})` : "–"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="kv">
        <div><span>Förväntad signalperiod</span><strong className="small">{fmtDate(p.state.expectedPeriod)}</strong></div>
        <div><span>Data hämtad (senaste körning)</span><strong className="small">{fmtDateTime(p.state.lastAttempt?.checkedAt)}</strong></div>
        <div><span>Signal skapad</span><strong className="small">{fmtDateTime(cur?.generatedAt)}</strong></div>
        <div><span>Senaste körningens status</span><strong className="small">{p.state.lastAttempt?.status ?? "ingen körning för perioden"}</strong></div>
        <div><span>Strategiversion</span><strong className="small">{p.state.strategyVersion}</strong></div>
        <div><span>Lagring</span><strong className="small">{p.store}</strong></div>
      </div>
      <p className="small muted">
        NAV-källa: avanza.se fund-guide (odokumenterad endpoint, UNDOCUMENTED_ENDPOINT – utbytbar). Cash-tröskel: Riksbanken SWEA
        (SETB3MBENCH, officiell). Månadsslutets NAV publiceras tidigast bankdagen efter.
      </p>
    </section>
  );
}
