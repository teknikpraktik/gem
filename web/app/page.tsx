import DataStatus from "@/components/DataStatus";
import OfflineSync from "@/components/OfflineSync";
import SignalCard from "@/components/SignalCard";
import WhyBox from "@/components/WhyBox";
import { getSignalPayload } from "@/lib/api";
import { fmtDate } from "@/lib/explain";
import backtest from "@/data/backtest.json";

export const dynamic = "force-dynamic";

export default async function Home() {
  const p = await getSignalPayload();
  const s = p.state;
  const hyb = backtest.investable.variants.HYBRID_SYNTH_CASH;
  const strat = hyb.scenarios.B_NEXT_TRADABLE.metrics;
  const glob = (backtest.investable.benchmarks_same_window.HYBRID_SYNTH_CASH as Record<string, { cagr?: number }>).BUY_HOLD_AVANZA_GLOBAL;
  return (
    <>
      <OfflineSync status={s.status} period={s.expectedPeriod} fund={s.current?.selectedFund ?? null} />
      <h1>Vad säger modellen just nu?</h1>
      <SignalCard state={s} />
      {s.status === "VALID" && s.current ? <WhyBox signal={s.current} explanation={p.explanation} /> : null}
      <DataStatus p={p} />
      <section className="card" aria-labelledby="about-h">
        <h2 id="about-h" style={{ marginTop: 0 }}>Om modellen</h2>
        <p>Modellen är ett regelbaserat momentum- och risksystem. Historiskt har den framför allt varit tänkt att minska exponeringen under längre negativa marknadsregimer.</p>
        <p>Den har inte slagit global buy-and-hold under den moderna investerbara perioden: med Avanza-fonder {fmtDate(strat.start_date)}–{fmtDate(strat.end_date)} gav REGIONAL_SEK {((strat.cagr ?? 0) * 100).toFixed(2).replace(".", ",")} % per år mot {((glob?.cagr ?? 0) * 100).toFixed(2).replace(".", ",")} % för Avanza Global.</p>
        <p className="small muted">Signalen är information, inte en uppmaning. Ingen automatisk handel sker. Se <a href="/backtest">backtest</a> för fullständiga siffror.</p>
      </section>
    </>
  );
}
