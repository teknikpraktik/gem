import { PGlite } from "@electric-sql/pglite";
import { beforeEach, describe, expect, it } from "vitest";
// @ts-expect-error - plain ESM module shared with scripts/migrate.mjs
import { loadMigrations, migrate, MIGRATIONS_DIR } from "@/db/migrations.mjs";
import { inputChecksum, verifySnapshot } from "@/lib/audit";
import { STRATEGY_ID, STRATEGY_VERSION } from "@/lib/engine/regional";
import { runMonthlySignal } from "@/lib/pipeline";
import { PostgresStore } from "@/lib/store/postgres";
import { FakeNavProvider, FakeYieldProvider, NOW } from "./helpers";

let db: PGlite;
let store: PostgresStore;
const q = async (t: string, p: unknown[] = []) => (await db.query(t, p)).rows as Record<string, unknown>[];

beforeEach(async () => {
  db = new PGlite();
  await migrate(q);
  store = new PostgresStore(q);
});

const deps = () => ({ store, navProvider: new FakeNavProvider(), yieldProvider: new FakeYieldProvider(), now: () => NOW });
const count = async (table: string) => Number((await q(`SELECT count(*)::int AS n FROM ${table}`))[0].n);

describe("migrations", () => {
  it("apply in order, are recorded with checksums and are idempotent", async () => {
    const rows = await q("SELECT version, sha256 FROM schema_migrations ORDER BY version");
    const files = loadMigrations() as { version: string; sha256: string }[];
    expect(rows.map((r) => r.version)).toEqual(files.map((f) => f.version));
    expect(rows.map((r) => r.sha256)).toEqual(files.map((f) => f.sha256));
    expect(files.map((f) => f.version)).toEqual(["001_init", "002_audit_provenance"]);
    expect(await migrate(q)).toEqual([]); // second run: nothing to do
  });

  it("refuses to run when an applied migration file was changed", async () => {
    await q("UPDATE schema_migrations SET sha256 = 'x' WHERE version = '001_init'");
    await expect(migrate(q)).rejects.toThrow(/changed after it was applied/);
    expect(MIGRATIONS_DIR).toMatch(/migrations/);
  });
});

describe("PostgresStore on Postgres (PGlite) with db/migrations", () => {
  it("INSERT works and round-trips the snapshot incl. provenance and exact input", async () => {
    const r = await runMonthlySignal({ ...deps() });
    expect(r.outcome).toBe("VALID");
    const got = (await store.getSignal(STRATEGY_ID, "2026-09-30", STRATEGY_VERSION))!;
    expect(got.strategyVersion).toBe("regional-sek-v1.0.0");
    expect(got.selectedFund).toBe("AVANZA_EM");
    expect(got.inputs).toHaveLength(3);
    expect(got.dataAsOf).toBe("2026-10-02"); // fake provider publishes through the as-of day
    expect(got.inputDataChecksum).toMatch(/^sha256:[0-9a-f]{64}$/);
    expect(got.codeVersion).toBeTruthy();
    expect(got.engineVersion).toContain("regional-sek-v1.0.0");
    expect(got.inputPayload).not.toBeNull();
    expect(inputChecksum(got.inputPayload!)).toBe(got.inputDataChecksum); // jsonb round trip keeps the checksum
    const v = verifySnapshot(got, got.inputPayload!);
    expect(v.checksumMatches).toBe(true);
    expect(v.decisionMatches).toBe(true);
    expect(got.returns.em).toBe(r.record!.returns.em);
    expect((await store.latestAttempt(STRATEGY_ID, "2026-09-30"))!.freshness!.length).toBe(4);
  });

  it("duplicate signal (same strategy + period + version) is rejected; idempotent cron", async () => {
    const r = await runMonthlySignal(deps());
    const dup = await store.insertSignalIfAbsent({ ...r.record!, selectedFund: "AVANZA_USA", reason: "tampered" });
    expect(dup.inserted).toBe(false);
    expect(dup.record.selectedFund).toBe("AVANZA_EM");
    expect((await runMonthlySignal(deps())).outcome).toBe("ALREADY_FINAL");
    expect(await count("signals")).toBe(1);
    expect(await count("signal_inputs")).toBe(3);
    expect(await count("signal_input_snapshots")).toBe(1);
    // a raw INSERT bypassing the store hits the unique constraint
    await expect(q(`INSERT INTO signals (strategy_id, strategy_version, signal_period, generated_at, status, returns, reason,
      input_dates, input_sources, data_quality, provider_versions, origin)
      SELECT strategy_id, strategy_version, signal_period, now(), status, returns, 'dup', input_dates, input_sources, data_quality,
             provider_versions, 'research_pipeline' FROM signals`)).rejects.toThrow(/signals_unique_period|duplicate key/);
  });

  it("UPDATE and DELETE are rejected on signals, inputs, input snapshots and the run log", async () => {
    await runMonthlySignal(deps());
    for (const t of ["signals", "signal_inputs", "signal_input_snapshots", "data_source_status"]) {
      await expect(q(`UPDATE ${t} SET ${t === "signals" ? "reason" : t === "signal_inputs" ? "end_nav" : t === "data_source_status" ? "detail" : "payload"} = ${t === "signal_inputs" ? "1" : t === "signal_input_snapshots" ? "'{}'::jsonb" : "'x'"}`))
        .rejects.toThrow(/immutable/i);
      await expect(q(`DELETE FROM ${t}`)).rejects.toThrow(/immutable/i);
    }
    expect(await count("signals")).toBe(1);
  });

  it("a live snapshot without provenance is rejected by the schema", async () => {
    await expect(q(`INSERT INTO signals (strategy_id, strategy_version, signal_period, generated_at, status, returns, reason,
      input_dates, input_sources, data_quality, provider_versions, origin)
      VALUES ('REGIONAL_SEK','regional-sek-v1.0.0','2026-08-31',now(),'VALID','{}','x','{}','{}','{}','{}','live')`))
      .rejects.toThrow(/signals_audit_required/);
    await expect(q(`INSERT INTO signals (strategy_id, strategy_version, signal_period, generated_at, status, returns, reason,
      input_dates, input_sources, data_quality, provider_versions, origin, data_as_of, input_data_checksum, code_version,
      engine_version, reference_implementation)
      VALUES ('REGIONAL_SEK','regional-sek-v1.0.0','2026-08-31',now(),'VALID','{}','x','{}','{}','{}','{}','live','2026-09-01',
              'md5:abc','sha','e','r')`)).rejects.toThrow(/signals_audit_required/);
  });

  it("non-final statuses and unknown strategy versions are rejected", async () => {
    await expect(q(`INSERT INTO signals (strategy_id, strategy_version, signal_period, generated_at, status, returns, reason,
       input_dates, input_sources, data_quality, provider_versions, origin)
       VALUES ('REGIONAL_SEK','regional-sek-v1.0.0','2026-08-31',now(),'WAITING_FOR_DATA','{}','x','{}','{}','{}','{}','research_pipeline')`))
      .rejects.toThrow();
    await expect(q(`INSERT INTO signals (strategy_id, strategy_version, signal_period, generated_at, status, returns, reason,
       input_dates, input_sources, data_quality, provider_versions, origin)
       VALUES ('REGIONAL_SEK','9.9.9','2026-08-31',now(),'VALID','{}','x','{}','{}','{}','{}','research_pipeline')`))
      .rejects.toThrow(/signals_version_fk|foreign key/);
  });
});



