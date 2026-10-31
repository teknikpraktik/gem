import { fmtDate, pctPlain } from "@/lib/explain";

export interface MetricRow {
  name: string;
  note?: string;
  m?: { start_date?: string; end_date?: string; cagr?: number | null; max_drawdown?: number | null; sharpe?: number | null;
        volatility?: number | null; number_of_switches?: number | null; number_of_trades?: number | null } | null;
  missing?: string;
}

const n2 = (x: number | null | undefined) => (x === null || x === undefined ? "–" : x.toFixed(2).replace(".", ","));

export default function MetricsTable({ rows, sharpeNote }: { rows: MetricRow[]; sharpeNote: string }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr><th>Strategi</th><th>Period</th><th className="num">CAGR</th><th className="num">Max DD</th><th className="num">Sharpe</th>
            <th className="num">Volatilitet</th><th className="num">Byten</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.name}>
              <td>{r.name}{r.note ? <div className="small muted">{r.note}</div> : null}</td>
              {r.m ? (
                <>
                  <td className="small">{fmtDate(r.m.start_date)} – {fmtDate(r.m.end_date)}</td>
                  <td className="num">{pctPlain(r.m.cagr, 2)}</td>
                  <td className="num">{pctPlain(r.m.max_drawdown, 1)}</td>
                  <td className="num">{n2(r.m.sharpe)}</td>
                  <td className="num">{pctPlain(r.m.volatility, 1)}</td>
                  <td className="num">{r.m.number_of_switches ?? r.m.number_of_trades ?? 0}</td>
                </>
              ) : (
                <td colSpan={6} className="small muted">{r.missing ?? "kan inte beräknas"}</td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="small muted">{sharpeNote}</p>
    </div>
  );
}
