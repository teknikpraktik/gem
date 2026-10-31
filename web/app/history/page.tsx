import AllocationStrip from "@/components/AllocationStrip";
import { getHistory } from "@/lib/api";
import { fmtDate, pct } from "@/lib/explain";
import { instrumentById } from "@/lib/instruments";

export const dynamic = "force-dynamic";

export default async function History() {
  const rows = await getHistory();
  return (
    <>
      <h1>Signalhistorik</h1>
      <p className="muted">
        REGIONAL_SEK på Avanza-fondernas NAV. Månader före att live-jobbet startade är beräknade av forskningspipelinen med samma regel
        (märkta <em>research</em>); live-snapshots ersätter dem för samma period.
      </p>
      <section className="card"><AllocationStrip rows={rows} /></section>
      <section className="card">
        <div className="table-scroll">
          <table>
            <thead>
              <tr><th>Månad</th><th>Signal</th><th>Föregående</th><th>Byte</th><th className="num">USA</th><th className="num">Europa</th>
                <th className="num">EM</th><th className="num">Cash</th><th>Status</th><th>Källa</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.signalPeriod}>
                  <td>{fmtDate(r.signalPeriod)}</td>
                  <td>{instrumentById(r.selectedFund)?.shortName ?? "–"}</td>
                  <td>{instrumentById(r.previousFund)?.shortName ?? "–"}</td>
                  <td>{r.switched ? "ja" : "nej"}</td>
                  <td className="num">{pct(r.returns.usa)}</td>
                  <td className="num">{pct(r.returns.europe)}</td>
                  <td className="num">{pct(r.returns.em)}</td>
                  <td className="num">{pct(r.returns.cash)}</td>
                  <td title={r.reason}>{r.status}</td>
                  <td className="small">{r.origin === "live" ? "live" : "research"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
