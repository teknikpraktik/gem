import { describe, expect, it } from "vitest";
import { buildEngineInput, canonicalJson, codeVersion, dataAsOf, inputChecksum, runEngine, verifySnapshot } from "@/lib/audit";
import { STRATEGY_ID } from "@/lib/engine/regional";
import { assessSeries } from "@/lib/freshness";
import { INSTRUMENTS, instrumentById } from "@/lib/instruments";
import { runMonthlySignal } from "@/lib/pipeline";
import { AvanzaNavProvider, Fetcher } from "@/lib/providers/avanza";
import { RiksbankYieldProvider } from "@/lib/providers/riksbank";
import type { NavPoint } from "@/lib/providers/types";
import { MemoryStore } from "@/lib/store/memory";
import { FakeNavProvider, FakeYieldProvider, NOW } from "./helpers";

const EM = instrumentById("AVANZA_EM")!;
const ms = (d: string) => new Date(`${d}T00:00:00+02:00`).getTime();
const body = (text: string, status = 200) => new Response(text, { status });
const hanging: Fetcher = (_u, init) => new Promise((_, reject) => {
  init?.signal?.addEventListener("abort", () => reject(init.signal!.reason));
});

describe("Avanza provider fails closed", () => {
  const avz = (f: Fetcher) => new AvanzaNavProvider(f, () => NOW, 50);
  const hist = (f: Fetcher) => avz(f).history(EM, "2026-09-28", "2026-09-30");
  it("HTTP error", async () => { await expect(hist(async () => body("{}", 502))).rejects.toThrow(/HTTP 502/); });
  it("timeout", async () => { await expect(hist(hanging)).rejects.toThrow(/timeout/); });
  it("empty response", async () => { await expect(hist(async () => body(""))).rejects.toThrow(/empty response/); });
  it("malformed JSON", async () => { await expect(hist(async () => body("{\"dataSerie\": ["))).rejects.toThrow(/invalid JSON/); });
  it("changed schema (renamed array)", async () => {
    await expect(hist(async () => body(JSON.stringify({ series: [{ x: ms("2026-09-29"), y: 1 }] })))).rejects.toThrow(/unexpected chart payload/);
  });
  it("missing field in a point", async () => {
    await expect(hist(async () => body(JSON.stringify({ dataSerie: [{ x: ms("2026-09-29"), value: 1 }] })))).rejects.toThrow(/without x\/y/);
  });
  it("unexpected data type", async () => {
    await expect(hist(async () => body(JSON.stringify({ dataSerie: [{ x: ms("2026-09-29"), y: "101,2" }] })))).rejects.toThrow(/non-numeric/);
    await expect(hist(async () => body(JSON.stringify({ dataSerie: "n/a" })))).rejects.toThrow(/unexpected chart payload/);
  });
  it("empty time series is returned as empty (classified EMPTY by the pipeline)", async () => {
    await expect(hist(async () => body(JSON.stringify({ dataSerie: [] })))).resolves.toEqual([]);
  });
  it("explicit null NAV is skipped, not repaired", async () => {
    const pts = await hist(async () => body(JSON.stringify({ dataSerie: [{ x: ms("2026-09-29"), y: null }, { x: ms("2026-09-30"), y: 5 }] })));
    expect(pts.map((p) => p.navDate)).toEqual(["2026-09-30"]);
  });
  it("guide: missing nav field / wrong type", async () => {
    const g = (o: object) => avz(async () => body(JSON.stringify({ isin: EM.isin, currency: "SEK", ...o }))).verifyInstrument(EM);
    await expect(g({ navDate: "2026-09-30" })).rejects.toThrow(/nav\/navDate missing/);
    await expect(g({ nav: "1", navDate: "2026-09-30" })).rejects.toThrow(/nav\/navDate missing/);
  });
});

describe("Riksbank provider fails closed", () => {
  const rb = (f: Fetcher) => new RiksbankYieldProvider(f, undefined, () => NOW, 50).ssvx3m("2026-09-01", "2026-09-30");
  it("HTTP error", async () => { await expect(rb(async () => body("", 500))).rejects.toThrow(/HTTP 500/); });
  it("timeout", async () => { await expect(rb(hanging)).rejects.toThrow(/timeout/); });
  it("empty response", async () => { await expect(rb(async () => body("  "))).rejects.toThrow(/empty response/); });
  it("malformed JSON", async () => { await expect(rb(async () => body("[{"))).rejects.toThrow(/invalid JSON/); });
  it("changed schema", async () => { await expect(rb(async () => body(JSON.stringify({ observations: [] })))).rejects.toThrow(/unexpected payload/); });
  it("missing field", async () => { await expect(rb(async () => body(JSON.stringify([{ date: "2026-09-30" }])))).rejects.toThrow(/schema change/); });
  it("unexpected type", async () => {
    await expect(rb(async () => body(JSON.stringify([{ date: 20260930, value: 1.9 }])))).rejects.toThrow(/bad date/);
    await expect(rb(async () => body(JSON.stringify([{ date: "2026-09-30", value: "1.9" }])))).rejects.toThrow(/bad value/);
  });
  it("empty series is returned as empty (classified EMPTY by the pipeline)", async () => {
    await expect(rb(async () => body("[]"))).resolves.toEqual([]);
  });
});

describe("pipeline: questionable data never produces a new signal", () => {
  const base = (o: Partial<Parameters<typeof runMonthlySignal>[0]> = {}) => ({
    store: new MemoryStore(), navProvider: new FakeNavProvider(), yieldProvider: new FakeYieldProvider(), now: () => NOW, ...o });

  it("empty NAV series -> DATA_ERROR (EMPTY)", async () => {
    const nav = new FakeNavProvider();
    const orig = nav.history.bind(nav);
    nav.history = async (i, f, t) => (i.instrumentId === "AVANZA_EUROPA" ? [] : orig(i, f, t));
    const r = await runMonthlySignal(base({ navProvider: nav }));
    expect(r.outcome).toBe("DATA_ERROR");
    expect(r.detail).toMatch(/AVANZA_EUROPA: EMPTY/);
  });

  it("empty yield series -> DATA_ERROR (EMPTY)", async () => {
    const y = new FakeYieldProvider();
    y.ssvx3m = async () => [];
    const r = await runMonthlySignal(base({ yieldProvider: y }));
    expect(r.outcome).toBe("DATA_ERROR");
    expect(r.detail).toMatch(/SETB3MBENCH: EMPTY/);
  });

  it("truncated history (provider dropped the start window) -> DATA_ERROR, not a final NO_SIGNAL", async () => {
    const nav = new FakeNavProvider();
    const orig = nav.history.bind(nav);
    nav.history = async (i, f, t) => (i.instrumentId === "AVANZA_USA" && f < "2026-01-01" ? [] : orig(i, f, t));
    const store = new MemoryStore();
    const r = await runMonthlySignal(base({ store, navProvider: nav }));
    expect(r.outcome).toBe("DATA_ERROR");
    expect(r.detail).toMatch(/AVANZA_USA: TRUNCATED/);
    expect(await store.listSignals(STRATEGY_ID)).toHaveLength(0);
  });

  it("old series (provider frozen weeks ago) -> DATA_ERROR (STALE)", async () => {
    const r = await runMonthlySignal(base({ navProvider: new FakeNavProvider({ publishedThrough: "2026-09-02" }) }));
    expect(r.outcome).toBe("DATA_ERROR");
    expect(r.detail).toMatch(/STALE/);
  });

  it("yield dated after as-of -> DATA_ERROR", async () => {
    const y = new FakeYieldProvider();
    const orig = y.ssvx3m.bind(y);
    y.ssvx3m = async (f, t) => [...(await orig(f, t)), { date: "2026-10-09", value: 2, retrievedAt: "", source: "x" }];
    expect((await runMonthlySignal(base({ yieldProvider: y }))).outcome).toBe("DATA_ERROR");
  });

  it("different last NAV dates per fund (closure proven by later NAV) -> VALID with per-fund dates and freshness", async () => {
    const gaps = { AVANZA_EM: (d: string) => d === "2026-09-30", AVANZA_EUROPA: (d: string) => d === "2026-09-29" || d === "2026-09-30" };
    const r = await runMonthlySignal(base({ navProvider: new FakeNavProvider({ gaps }) }));
    expect(r.outcome).toBe("VALID");
    expect(r.record!.inputDates.AVANZA_USA.end).toBe("2026-09-30");
    expect(r.record!.inputDates.AVANZA_EM.end).toBe("2026-09-29");
    expect(r.record!.inputDates.AVANZA_EUROPA.end).toBe("2026-09-28");
    const fr = r.record!.dataQuality.freshness as { instrumentId: string; state: string }[];
    expect(Object.fromEntries(fr.map((f) => [f.instrumentId, f.state]))).toEqual({
      AVANZA_USA: "FRESH", AVANZA_EUROPA: "CLOSED_PROVEN", AVANZA_EM: "CLOSED_PROVEN", SETB3MBENCH: "FRESH" });
  });

  it("different last NAV dates, one fund simply not published yet -> WAITING (no partial signal)", async () => {
    const nav = new FakeNavProvider();
    const orig = nav.history.bind(nav);
    nav.history = async (i, f, t) => (await orig(i, f, t)).filter((p: NavPoint) => i.instrumentId !== "AVANZA_EM" || p.navDate <= "2026-09-29");
    const r = await runMonthlySignal(base({ navProvider: nav }));
    expect(r.outcome).toBe("WAITING_FOR_DATA");
    expect(r.detail).toMatch(/AVANZA_EM/);
  });

  it("every attempt records freshness/provenance per series", async () => {
    const store = new MemoryStore();
    await runMonthlySignal(base({ store, navProvider: new FakeNavProvider({ publishedThrough: "2026-09-29" }) }));
    const a = (await store.latestAttempt(STRATEGY_ID, "2026-09-30"))!;
    expect(a.freshness!.map((f) => [f.instrumentId, f.provider, f.state, f.fresh])).toEqual([
      ["AVANZA_USA", "fake_nav", "NOT_YET_PUBLISHED", false], ["AVANZA_EUROPA", "fake_nav", "NOT_YET_PUBLISHED", false],
      ["AVANZA_EM", "fake_nav", "NOT_YET_PUBLISHED", false], ["SETB3MBENCH", "fake_yield", "FRESH", true]]);
    expect(a.freshness![0]).toMatchObject({ lastObservation: "2026-09-29", requiredDate: "2026-09-30", retrievedAt: expect.any(String) });
  });
});

describe("freshness classification boundaries (NAV tolerance 3 bdays)", () => {
  const f = (dates: string[]) => assessSeries({ provider: "p", providerVersion: "1", instrumentId: "X", kind: "NAV", dates,
    retrievedAt: null, periodEnd: "2026-09-30", requiredHistoryFrom: "2025-09-30" }).state;
  const hist = ["2025-09-30"];
  it.each([
    [[...hist, "2026-09-30"], "FRESH"],
    [[...hist, "2026-09-25"], "NOT_YET_PUBLISHED"], // exactly 3 bdays before
    [[...hist, "2026-09-24"], "STALE"],             // 4 bdays, nothing later
    [[...hist, "2026-09-25", "2026-10-01"], "CLOSED_PROVEN"],
    [[...hist, "2026-09-24", "2026-10-01"], "GAP_TOO_LONG"],
    [[], "EMPTY"],
    [["2025-10-06", "2026-09-30"], "TRUNCATED"],
  ])("%j -> %s", (dates, state) => { expect(f(dates as string[])).toBe(state); });
});

describe("audit trail", () => {
  const payload = buildEngineInput("2026-10-02", { B: [{ date: "2026-09-30", value: 2 }, { date: "2026-09-29", value: 1.5 }], A: [] },
                                   [{ date: "2026-09-30", value: 1.9 }]);
  it("canonical encoding is order-independent and checksums are stable", () => {
    expect(canonicalJson({ b: 1, a: [2, { d: 1, c: 0.1 }] })).toBe('{"a":[2,{"c":0.1,"d":1}],"b":1}');
    expect(Object.keys(payload.navs)).toEqual(["A", "B"]);
    expect(payload.navs.B[0][0]).toBe("2026-09-29");
    expect(inputChecksum(payload)).toBe(inputChecksum(JSON.parse(JSON.stringify(payload))));
    expect(inputChecksum(payload)).toMatch(/^sha256:[0-9a-f]{64}$/);
    expect(() => canonicalJson({ x: Number.NaN })).toThrow();
    expect(dataAsOf(payload)).toBe("2026-09-30");
  });
  it("any change to the input changes the checksum and is detected by verifySnapshot", async () => {
    const r = await runMonthlySignal({ store: new MemoryStore(), navProvider: new FakeNavProvider(), yieldProvider: new FakeYieldProvider(), now: () => NOW });
    const rec = r.record!;
    expect(verifySnapshot(rec, rec.inputPayload!)).toMatchObject({ checksumMatches: true, decisionMatches: true });
    const tampered = structuredClone(rec.inputPayload!);
    tampered.navs.AVANZA_USA.at(-1)![1] *= 1.0000001;
    const v = verifySnapshot(rec, tampered);
    expect(v.checksumMatches).toBe(false);
    expect(runEngine(rec.inputPayload!).target).toBe(rec.selectedFund);
  });
  it("code version comes from the deployment's git SHA", () => {
    expect(codeVersion({ VERCEL_GIT_COMMIT_SHA: "abc123" })).toBe("abc123");
    expect(codeVersion({ GIT_SHA: "def" })).toBe("def");
    expect(codeVersion({})).toBe("unknown");
  });
});

describe("trading rules are metadata; unverified cut-offs are never guessed", () => {
  it("Ränta Kort 15:00 verified, Europa UNVERIFIED without a value", () => {
    const rk = instrumentById("AVANZA_RANTA_KORT")!.rules;
    expect(rk).toMatchObject({ cutoffTime: "15:00", cutoffStatus: "VERIFIED" });
    const eu = instrumentById("AVANZA_EUROPA")!.rules;
    expect(eu.cutoffTime).toBeNull();
    expect(eu.cutoffStatus).toBe("UNVERIFIED");
    for (const i of INSTRUMENTS) if (i.rules.cutoffStatus === "UNVERIFIED") expect(i.rules.cutoffTime).toBeNull();
    for (const i of INSTRUMENTS) if (i.rules.cutoffTime) expect(i.rules.cutoffTime).toMatch(/^\d{2}:\d{2}$/);
  });
});
