/**
 * Runtime dependencies (store + providers). Tests replace them via setDepsForTests.
 *
 * Without DATABASE_URL the app runs READ-ONLY on the bootstrap snapshot produced by
 * the research pipeline (web/data/bootstrap_signal.json), clearly labelled as such;
 * the cron endpoint then refuses to run.
 */

import bootstrap from "@/data/bootstrap_signal.json";
import { STRATEGY_ID, STRATEGY_VERSION } from "./engine/regional";
import { AvanzaNavProvider } from "./providers/avanza";
import { RiksbankYieldProvider } from "./providers/riksbank";
import type { NavProvider, YieldProvider } from "./providers/types";
import { MemoryStore } from "./store/memory";
import { PostgresStore } from "./store/postgres";
import type { SignalRecord, SignalStore } from "./store/types";

export interface Deps {
  store: SignalStore;
  navProvider: NavProvider & { verifyInstrument?: AvanzaNavProvider["verifyInstrument"] };
  yieldProvider: YieldProvider;
  now: () => Date;
}

const ASSET: Record<string, string> = { AVANZA_USA: "usa", AVANZA_EUROPA: "europe", AVANZA_EM: "em", AVANZA_RANTA_KORT: "cash" };

/** The research pipeline's latest signal, converted to a SignalRecord with origin "research_pipeline". */
export function bootstrapRecord(): SignalRecord | null {
  const s = (bootstrap as { signal?: Record<string, unknown>; exported_at?: string; research_commit?: string }).signal;
  if (!s || (s.status !== "VALID" && s.status !== "NO_SIGNAL")) return null;
  const returns = s.returns as SignalRecord["returns"];
  const navDates = (s.nav_dates ?? {}) as Record<string, string | null>;
  return {
    strategyId: STRATEGY_ID,
    // research exports before the explicit version tag carried the bare semver "1.0.0" of the same rule
    strategyVersion: s.strategy_version === "1.0.0" || s.strategy_version === undefined ? STRATEGY_VERSION : String(s.strategy_version),
    signalPeriod: String(s.signal_period_end),
    generatedAt: String((bootstrap as { exported_at?: string }).exported_at ?? ""),
    status: s.status as SignalRecord["status"],
    selectedAsset: s.target ? ASSET[String(s.target)] ?? null : null,
    selectedFund: (s.target as string) ?? null,
    returns,
    cashHurdle: returns?.cash ?? null,
    reason: String(s.reason ?? ""),
    inputDates: Object.fromEntries(Object.entries(navDates).map(([k, v]) => [k, { start: null, end: v }])),
    inputSources: (s.sources ?? {}) as Record<string, string>,
    dataQuality: { note: "bootstrap snapshot from the research pipeline (GitHub Actions); replaced by live cron snapshots",
                   researchCommit: (bootstrap as { research_commit?: string }).research_commit },
    providerVersions: { engine: "research/src/gem/live.py" },
    inputs: [],
    origin: "research_pipeline",
    dataAsOf: Object.values(navDates).filter((d): d is string => !!d).sort().at(-1) ?? null,
    inputDataChecksum: null, // the research pipeline does not record the exact live input; labelled as bootstrap
    codeVersion: String((bootstrap as { research_commit?: string }).research_commit ?? "unknown"),
    engineVersion: "research/src/gem/live.py",
    referenceImplementation: "research/src/gem/live.py::regional_live_signal",
    inputPayload: null,
  };
}

class ReadOnlyStore extends MemoryStore {
  override readonly writable = false;
  override readonly kind = "bootstrap (read-only, DATABASE_URL not set)";
}

let override: Partial<Deps> | null = null;
let cachedStore: SignalStore | null = null;

export function setDepsForTests(d: Partial<Deps> | null) {
  override = d;
}

export function getDeps(): Deps {
  if (!cachedStore) {
    const url = process.env.DATABASE_URL;
    if (url) cachedStore = new PostgresStore(url);
    else {
      const b = bootstrapRecord();
      cachedStore = new ReadOnlyStore(b ? [b] : []);
    }
  }
  return {
    store: override?.store ?? cachedStore,
    navProvider: override?.navProvider ?? new AvanzaNavProvider(),
    yieldProvider: override?.yieldProvider ?? new RiksbankYieldProvider(),
    now: override?.now ?? (() => new Date()),
  };
}
