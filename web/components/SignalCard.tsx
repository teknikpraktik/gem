import { fmtDate, fmtDateTime, pct, regionLabel, STATUS_TEXT } from "@/lib/explain";
import { instrumentById } from "@/lib/instruments";
import type { SignalState } from "@/lib/status";
import StatusBadge from "./StatusBadge";

function OriginNote({ origin }: { origin: string }) {
  if (origin !== "research_pipeline") return null;
  return (
    <p className="small muted">
      Beräknad av forskningspipelinen (GitHub Actions) med samma regel. Ersätts av månadsjobbets snapshot när det har körts.
    </p>
  );
}

export default function SignalCard({ state }: { state: SignalState }) {
  const cur = state.status === "VALID" ? state.current : null;
  return (
    <>
      <section className="card hero" aria-labelledby="signal-h">
        <p className="eyebrow" id="signal-h">{state.strategyId} · aktuell signal</p>
        {cur ? (
          <>
            <p className="signal-region">{regionLabel(cur.selectedAsset).toUpperCase()}</p>
            <p className="signal-fund">{instrumentById(cur.selectedFund)?.name ?? cur.selectedFund} · 100 %</p>
            <div className="kv">
              <div><span>12 mån momentum (vald)</span><strong>{pct(cur.selectedAsset === "cash" ? cur.returns.cash : cur.returns[cur.selectedAsset as "usa"])}</strong></div>
              <div><span>Cash-tröskel (12 mån)</span><strong>{pct(cur.cashHurdle)}</strong></div>
              <div><span>Status</span><strong><StatusBadge status={state.status} /></strong></div>
              <div><span>Data till</span><strong>{fmtDate(cur.signalPeriod)}</strong></div>
              <div><span>Signal skapad</span><strong className="small">{fmtDateTime(cur.generatedAt)}</strong></div>
              <div><span>Strategiversion</span><strong className="small">{cur.strategyVersion}</strong></div>
            </div>
            <OriginNote origin={cur.origin} />
          </>
        ) : (
          <>
            <p className="signal-region"><StatusBadge status={state.status} /></p>
            <p>{STATUS_TEXT[state.status]?.body}</p>
            <p className="small muted">Förväntad period: {fmtDate(state.expectedPeriod)} · Detalj: {state.statusDetail}</p>
            {state.current && state.status === "NO_SIGNAL" ? <OriginNote origin={state.current.origin} /> : null}
          </>
        )}
      </section>
      {!cur && state.lastValid ? (
        <section className="card stale" aria-label="Senaste giltiga signal, inte aktuell">
          <p className="eyebrow">Senaste giltiga signal · inte aktuell</p>
          <p style={{ fontSize: 18, margin: "6px 0" }}>
            {instrumentById(state.lastValid.selectedFund)?.name ?? state.lastValid.selectedFund}
            <span className="tag">period {fmtDate(state.lastValid.signalPeriod)}</span>
          </p>
          <p className="small muted">Visas endast som referens. Nuvarande status: {state.status}.</p>
        </section>
      ) : null}
    </>
  );
}
