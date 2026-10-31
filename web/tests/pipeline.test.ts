import { describe, expect, it } from "vitest";
import { STRATEGY_ID, STRATEGY_VERSION } from "@/lib/engine/regional";
import { runMonthlySignal } from "@/lib/pipeline";
import { MemoryStore } from "@/lib/store/memory";
import { ImmutableSignalError } from "@/lib/store/types";
import { FakeNavProvider, FakeYieldProvider, NOW, providerDown } from "./helpers";

const deps = (o: Partial<Parameters<typeof runMonthlySignal>[0]> = {}) => ({
  store: new MemoryStore(), navProvider: new FakeNavProvider(), yieldProvider: new FakeYieldProvider(), now: () => NOW, ...o,
});

describe("monthly pipeline", () => {
  it("produces a VALID, final, fully documented snapshot", async () => {
    const d = deps();
    const r = await runMonthlySignal(d);
    expect(r.outcome).toBe("VALID");
    expect(r.signalPeriod).toBe("2026-09-30");
    const rec = r.record!;
    expect(rec.selectedFund).toBe("AVANZA_EM");
    expect(rec.selectedAsset).toBe("em");
    expect(rec.strategyId).toBe(STRATEGY_ID);
    expect(rec.strategyVersion).toBe(STRATEGY_VERSION);
    expect(rec.returns.em!).toBeGreaterThan(rec.returns.usa!);
    expect(rec.cashHurdle).not.toBeNull();
    expect(rec.inputDates.AVANZA_EM).toEqual({ start: "2025-09-30", end: "2026-09-30" });
    expect(rec.inputSources.AVANZA_EM).toBe("fake_nav");
    expect(rec.providerVersions).toEqual({ nav: "fake/1", yield: "fake/1" });
    expect(rec.inputs).toHaveLength(3);
    expect(rec.origin).toBe("live");
  });

  it("chooses the defensive fund when no region beats the cash hurdle", async () => {
    const r = await runMonthlySignal(deps({ navProvider: new FakeNavProvider({ growth: { AVANZA_USA: -0.1, AVANZA_EUROPA: -0.05, AVANZA_EM: 0.0 } }) }));
    expect(r.outcome).toBe("VALID");
    expect(r.record!.selectedFund).toBe("AVANZA_RANTA_KORT");
    expect(r.record!.selectedAsset).toBe("cash");
  });

  it("missing month-end NAV before publication -> WAITING_FOR_DATA, nothing stored, no fallback", async () => {
    const store = new MemoryStore();
    const r = await runMonthlySignal(deps({ store, navProvider: new FakeNavProvider({ publishedThrough: "2026-09-24" }) }));
    expect(r.outcome).toBe("WAITING_FOR_DATA");
    expect(r.record).toBeUndefined();
    expect(await store.listSignals(STRATEGY_ID)).toHaveLength(0);
    expect((await store.latestAttempt(STRATEGY_ID, "2026-09-30"))!.status).toBe("WAITING_FOR_DATA");
  });

  it("EM closed over month end (holiday gap) with later NAV published -> final NO_SIGNAL", async () => {
    const gaps = { AVANZA_EM: (d: string) => d >= "2026-09-23" && d <= "2026-09-30" };
    const r = await runMonthlySignal(deps({ navProvider: new FakeNavProvider({ gaps }) }));
    expect(r.outcome).toBe("NO_SIGNAL");
    expect(r.record!.status).toBe("NO_SIGNAL");
    expect(r.record!.selectedFund).toBeNull();
  });

  it("short EM holiday gap within tolerance still gives VALID", async () => {
    const gaps = { AVANZA_EM: (d: string) => d === "2026-09-29" || d === "2026-09-30" };
    const r = await runMonthlySignal(deps({ navProvider: new FakeNavProvider({ gaps }) }));
    expect(r.outcome).toBe("VALID");
    expect(r.record!.inputDates.AVANZA_EM.end).toBe("2026-09-28");
  });

  it("hurdle yields not yet available -> WAITING_FOR_DATA", async () => {
    const r = await runMonthlySignal(deps({ yieldProvider: new FakeYieldProvider(2, "2026-09-10") }));
    expect(r.outcome).toBe("WAITING_FOR_DATA");
  });

  it("provider failure -> DATA_ERROR, logged, nothing stored", async () => {
    for (const d of [deps({ navProvider: new FakeNavProvider({ fail: providerDown() }) }),
                     deps({ yieldProvider: new FakeYieldProvider(2, undefined, new Error("socket hang up")) })]) {
      const r = await runMonthlySignal(d);
      expect(r.outcome).toBe("DATA_ERROR");
      expect(await d.store.listSignals(STRATEGY_ID)).toHaveLength(0);
      expect((await d.store.latestAttempt(STRATEGY_ID, "2026-09-30"))!.status).toBe("DATA_ERROR");
    }
  });

  it("future-dated NAV is rejected as DATA_ERROR", async () => {
    const nav = new FakeNavProvider();
    const orig = nav.history.bind(nav);
    nav.history = async (i, f, t) => orig(i, f, t > "2026-10-02" ? t : "2026-10-09");
    const r = await runMonthlySignal(deps({ navProvider: nav }));
    expect(r.outcome).toBe("DATA_ERROR");
    expect(r.detail).toMatch(/after as-of/);
  });

  it("read-only store refuses to run", async () => {
    const store = new MemoryStore();
    Object.defineProperty(store, "writable", { value: false });
    const r = await runMonthlySignal(deps({ store }));
    expect(r.outcome).toBe("DATA_ERROR");
  });
});

describe("idempotency and immutability", () => {
  it("cron runs repeatedly: one snapshot, later runs ALREADY_FINAL without fetching", async () => {
    const d = deps();
    const first = await runMonthlySignal(d);
    expect(first.inserted).toBe(true);
    const calls = (d.navProvider as FakeNavProvider).calls;
    for (let i = 0; i < 5; i++) {
      const again = await runMonthlySignal({ ...d, now: () => new Date(NOW.getTime() + (i + 1) * 3_600_000) });
      expect(again.outcome).toBe("ALREADY_FINAL");
      expect(again.record).toEqual(first.record);
    }
    expect((d.navProvider as FakeNavProvider).calls).toBe(calls);
    expect(await d.store.listSignals(STRATEGY_ID)).toHaveLength(1);
  });

  it("a later run with different data cannot replace a VALID snapshot", async () => {
    const store = new MemoryStore();
    const a = await runMonthlySignal(deps({ store }));
    const b = await runMonthlySignal(deps({ store, navProvider: new FakeNavProvider({ growth: { AVANZA_USA: 0.5, AVANZA_EUROPA: 0, AVANZA_EM: 0 } }) }));
    expect(b.outcome).toBe("ALREADY_FINAL");
    expect((await store.getSignal(STRATEGY_ID, "2026-09-30", STRATEGY_VERSION))!.selectedFund).toBe(a.record!.selectedFund);
  });

  it("concurrent duplicate generation stores exactly one record", async () => {
    const store = new MemoryStore();
    const rs = await Promise.all(Array.from({ length: 4 }, () => runMonthlySignal(deps({ store }))));
    expect(rs.every((r) => r.outcome === "VALID" || r.outcome === "ALREADY_FINAL")).toBe(true);
    expect(rs.filter((r) => r.inserted).length).toBe(1);
    expect(await store.listSignals(STRATEGY_ID)).toHaveLength(1);
  });

  it("stored snapshots are frozen", async () => {
    const r = await runMonthlySignal(deps());
    expect(Object.isFrozen(r.record)).toBe(true);
    expect(() => { (r.record as { selectedFund: string | null }).selectedFund = "AVANZA_USA"; }).toThrow(TypeError);
    expect(() => { (r.record!.returns as { em: number | null }).em = 1; }).toThrow(TypeError);
    expect(ImmutableSignalError).toBeDefined();
  });
});
