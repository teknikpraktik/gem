import { readFileSync } from "node:fs";
import { join } from "node:path";
import { PGlite } from "@electric-sql/pglite";
import { beforeEach, describe, expect, it } from "vitest";
import { STRATEGY_ID, STRATEGY_VERSION } from "@/lib/engine/regional";
import { runMonthlySignal } from "@/lib/pipeline";
import { PostgresStore } from "@/lib/store/postgres";
import { FakeNavProvider, FakeYieldProvider, NOW } from "./helpers";

let db: PGlite;
let store: PostgresStore;

beforeEach(async () => {
  db = new PGlite();
  await db.exec(readFileSync(join(__dirname, "..", "db", "schema.sql"), "utf8"));
  store = new PostgresStore(async (t, p) => (await db.query(t, p)).rows as Record<string, unknown>[]);
});

const deps = () => ({ store, navProvider: new FakeNavProvider(), yieldProvider: new FakeYieldProvider(), now: () => NOW });

describe("PostgresStore on real Postgres (PGlite) with db/schema.sql", () => {
  it("round-trips a snapshot with its inputs", async () => {
    const r = await runMonthlySignal(deps());
    expect(r.outcome).toBe("VALID");
    const got = await store.getSignal(STRATEGY_ID, "2026-09-30", STRATEGY_VERSION);
    expect(got!.selectedFund).toBe("AVANZA_EM");
    expect(got!.inputs).toHaveLength(3);
    expect(got!.inputs.find((i) => i.instrumentId === "AVANZA_EM")!.endDate).toBe("2026-09-30");
    expect(got!.returns.em).toBeCloseTo(r.record!.returns.em!, 12);
    expect((await store.latestValid(STRATEGY_ID))!.signalPeriod).toBe("2026-09-30");
    expect((await store.latestAttempt(STRATEGY_ID, "2026-09-30"))!.status).toBe("VALID");
    expect(Object.keys(await store.latestNavs())).toContain("AVANZA_EM");
  });

  it("idempotent cron: second run ALREADY_FINAL, one row", async () => {
    await runMonthlySignal(deps());
    expect((await runMonthlySignal(deps())).outcome).toBe("ALREADY_FINAL");
    const n = await db.query<{ n: number }>("SELECT count(*)::int AS n FROM signals");
    expect(n.rows[0].n).toBe(1);
  });

  it("duplicate insert is a no-op (unique strategy+period+version)", async () => {
    const r = await runMonthlySignal(deps());
    const dup = await store.insertSignalIfAbsent({ ...r.record!, selectedFund: "AVANZA_USA", reason: "tampered" });
    expect(dup.inserted).toBe(false);
    expect(dup.record.selectedFund).toBe("AVANZA_EM");
    const n = await db.query<{ n: number }>("SELECT count(*)::int AS n FROM signal_inputs");
    expect(n.rows[0].n).toBe(3);
  });

  it("database trigger forbids UPDATE and DELETE of snapshots and inputs", async () => {
    await runMonthlySignal(deps());
    await expect(db.query("UPDATE signals SET selected_fund = 'AVANZA_USA'")).rejects.toThrow(/immutable/i);
    await expect(db.query("DELETE FROM signals")).rejects.toThrow(/immutable/i);
    await expect(db.query("UPDATE signal_inputs SET end_nav = 1")).rejects.toThrow(/immutable/i);
    await expect(db.query("DELETE FROM signal_inputs")).rejects.toThrow(/immutable/i);
  });

  it("schema rejects non-final statuses as snapshots", async () => {
    await expect(db.query(
      `INSERT INTO signals (strategy_id, strategy_version, signal_period, generated_at, status, returns, reason,
         input_dates, input_sources, data_quality, provider_versions)
       VALUES ('REGIONAL_SEK','1.0.0','2026-08-31',now(),'WAITING_FOR_DATA','{}','x','{}','{}','{}','{}')`)).rejects.toThrow();
  });
});
