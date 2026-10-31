import { afterEach, describe, expect, it } from "vitest";
import { GET as cronGET, POST as cronPOST } from "@/app/api/cron/monthly-signal/route";
import { GET as historyGET } from "@/app/api/history/route";
import { GET as signalGET } from "@/app/api/signal/route";
import { GET as statusGET } from "@/app/api/status/route";
import { authorizeCron } from "@/lib/cronAuth";
import { setDepsForTests } from "@/lib/deps";
import { STRATEGY_ID } from "@/lib/engine/regional";
import { runMonthlySignal } from "@/lib/pipeline";
import { deriveStatus, loadSignalState, offlineDisplay } from "@/lib/status";
import { MemoryStore } from "@/lib/store/memory";
import type { SignalRecord } from "@/lib/store/types";
import { FakeNavProvider, FakeYieldProvider, NOW, providerDown } from "./helpers";

const SECRET = "test-secret-0123456789abcdef";

function rec(period: string, status: "VALID" | "NO_SIGNAL" = "VALID", fund: string | null = "AVANZA_USA"): SignalRecord {
  return { strategyId: STRATEGY_ID, strategyVersion: "1.0.0", signalPeriod: period, generatedAt: `${period}T00:00:00Z`, status,
           selectedAsset: fund ? "usa" : null, selectedFund: status === "VALID" ? fund : null,
           returns: { usa: 0.1, europe: 0.05, em: 0.02, cash: 0.02 }, cashHurdle: 0.02, reason: "test", inputDates: {}, inputSources: {},
           dataQuality: {}, providerVersions: {}, inputs: [], origin: "live" };
}

afterEach(() => { setDepsForTests(null); delete process.env.CRON_SECRET; });

describe("display status", () => {
  const at = (iso: string) => new Date(iso);
  it("VALID for the expected period; no 'last valid' shown separately", () => {
    const s = deriveStatus(NOW, rec("2026-09-30"), rec("2026-09-30"), null);
    expect(s.status).toBe("VALID");
    expect(s.current!.signalPeriod).toBe("2026-09-30");
    expect(s.lastValid).toBeNull();
  });
  it("early in the month without signal -> WAITING_FOR_DATA; previous month kept apart as lastValid, never current", () => {
    const s = deriveStatus(NOW, null, rec("2026-08-31"), null);
    expect(s.status).toBe("WAITING_FOR_DATA");
    expect(s.current).toBeNull();
    expect(s.lastValid!.signalPeriod).toBe("2026-08-31");
  });
  it("publication window passed without signal -> STALE_DATA", () => {
    const s = deriveStatus(at("2026-10-12T08:00:00Z"), null, rec("2026-08-31"), null);
    expect(s.status).toBe("STALE_DATA");
    expect(s.current).toBeNull();
    expect(s.lastValid!.signalPeriod).toBe("2026-08-31");
  });
  it("a month later the old signal is still not current", () => {
    const s = deriveStatus(at("2026-11-20T08:00:00Z"), null, rec("2026-09-30"), null);
    expect(s.expectedPeriod).toBe("2026-10-31");
    expect(s.status).toBe("STALE_DATA");
    expect(s.current).toBeNull();
  });
  it("final NO_SIGNAL for the period", () => {
    const s = deriveStatus(NOW, rec("2026-09-30", "NO_SIGNAL", null), rec("2026-08-31"), null);
    expect(s.status).toBe("NO_SIGNAL");
    expect(s.current!.selectedFund).toBeNull();
    expect(s.lastValid!.signalPeriod).toBe("2026-08-31");
  });
  it("latest attempt failed -> DATA_ERROR", () => {
    const s = deriveStatus(NOW, null, rec("2026-08-31"), { strategyId: STRATEGY_ID, signalPeriod: "2026-09-30",
      checkedAt: NOW.toISOString(), status: "DATA_ERROR", detail: "HTTP 503", sources: {} });
    expect(s.status).toBe("DATA_ERROR");
    expect(s.current).toBeNull();
  });
  it("loadSignalState reads the store", async () => {
    const s = await loadSignalState(new MemoryStore([rec("2026-08-31"), rec("2026-09-30")]), NOW);
    expect(s.status).toBe("VALID");
  });
});

describe("offline display", () => {
  it("online VALID is current", () => {
    expect(offlineDisplay(true, null, "VALID")).toMatchObject({ banner: null, treatAsCurrent: true });
  });
  it("offline never treats the cached signal as current", () => {
    const o = offlineDisplay(false, "2026-10-02T08:00:00Z", "VALID");
    expect(o.treatAsCurrent).toBe(false);
    expect(o.label).toBe("OFFLINE_CACHED");
    expect(o.banner).toMatch(/^Offline · Senast synkroniserad 2026-10-02/);
  });
  it("offline with unknown sync time", () => {
    expect(offlineDisplay(false, null, "STALE_DATA").banner).toBe("Offline · Senast synkroniserad okänt");
  });
});

describe("cron auth", () => {
  const req = (h?: string) => new Request("http://x/api/cron/monthly-signal", { headers: h ? { authorization: h } : {} });
  it("fails closed without a secret", () => {
    expect(authorizeCron(req(`Bearer ${SECRET}`), undefined)).toMatchObject({ ok: false, status: 503 });
    expect(authorizeCron(req("Bearer short"), "short")).toMatchObject({ ok: false, status: 503 });
  });
  it("rejects wrong / missing bearer", () => {
    expect(authorizeCron(req(), SECRET)).toMatchObject({ ok: false, status: 401 });
    expect(authorizeCron(req(`Bearer ${SECRET}x`), SECRET)).toMatchObject({ ok: false, status: 401 });
    expect(authorizeCron(req(SECRET), SECRET)).toMatchObject({ ok: false, status: 401 });
  });
  it("accepts the Vercel cron header", () => {
    expect(authorizeCron(req(`Bearer ${SECRET}`), SECRET)).toEqual({ ok: true });
  });
});

describe("API routes", () => {
  it("GET /api/signal: WAITING before the cron ran, VALID after; read endpoints never write", async () => {
    const store = new MemoryStore([rec("2026-08-31")]);
    setDepsForTests({ store, navProvider: new FakeNavProvider(), yieldProvider: new FakeYieldProvider(), now: () => NOW });
    let body = await (await signalGET()).json();
    expect(body.state.status).toBe("WAITING_FOR_DATA");
    expect(body.state.current).toBeNull();
    expect(body.state.lastValid.signalPeriod).toBe("2026-08-31");
    expect(await store.listSignals(STRATEGY_ID)).toHaveLength(1);

    process.env.CRON_SECRET = SECRET;
    const auth = { headers: { authorization: `Bearer ${SECRET}` } };
    const run = await cronGET(new Request("http://x/api/cron/monthly-signal", auth));
    expect(run.status).toBe(200);
    expect((await run.json()).outcome).toBe("VALID");
    const again = await cronPOST(new Request("http://x/api/cron/monthly-signal", { method: "POST", ...auth }));
    expect((await again.json()).outcome).toBe("ALREADY_FINAL");

    body = await (await signalGET()).json();
    expect(body.state.status).toBe("VALID");
    expect(body.state.current.selectedFund).toBe("AVANZA_EM");
    expect(body.state.lastValid).toBeNull();
    expect(body.disclaimer).toBeTruthy();
  });

  it("cron endpoint: 401 without secret header, 503 without configured secret", async () => {
    setDepsForTests({ store: new MemoryStore(), now: () => NOW });
    expect((await cronGET(new Request("http://x/api/cron/monthly-signal"))).status).toBe(503);
    process.env.CRON_SECRET = SECRET;
    expect((await cronGET(new Request("http://x/api/cron/monthly-signal"))).status).toBe(401);
  });

  it("cron endpoint with failing provider reports DATA_ERROR and /api/signal shows it", async () => {
    process.env.CRON_SECRET = SECRET;
    const store = new MemoryStore([rec("2026-08-31")]);
    setDepsForTests({ store, navProvider: new FakeNavProvider({ fail: providerDown() }), yieldProvider: new FakeYieldProvider(), now: () => NOW });
    const r = await cronGET(new Request("http://x", { headers: { authorization: `Bearer ${SECRET}` } }));
    expect((await r.json()).outcome).toBe("DATA_ERROR");
    const body = await (await signalGET()).json();
    expect(body.state.status).toBe("DATA_ERROR");
    expect(body.state.current).toBeNull();
  });

  it("GET /api/history marks live rows and switches; GET /api/status reports store", async () => {
    const store = new MemoryStore();
    setDepsForTests({ store, navProvider: new FakeNavProvider(), yieldProvider: new FakeYieldProvider(), now: () => NOW });
    await runMonthlySignal({ store, navProvider: new FakeNavProvider(), yieldProvider: new FakeYieldProvider(), now: () => NOW });
    const h = await (await historyGET()).json();
    const rows = Array.isArray(h) ? h : h.signals ?? h.rows;
    const live = rows.find((x: { signalPeriod: string }) => x.signalPeriod === "2026-09-30");
    expect(live.origin).toBe("live");
    expect(live.selectedFund).toBe("AVANZA_EM");
    const st = await (await statusGET()).json();
    expect(JSON.stringify(st)).toContain("memory");
  });

  it("store failure -> 503, not an old signal", async () => {
    const store = new MemoryStore();
    store.getSignal = async () => { throw new Error("connection refused"); };
    setDepsForTests({ store, now: () => NOW });
    const r = await signalGET();
    expect(r.status).toBe(503);
  });
});

describe("cron + store from scratch (provider repeatedly late)", () => {
  it("WAITING on day 1, VALID once NAVs appear, then stable", async () => {
    const store = new MemoryStore();
    const mk = (through: string, iso: string) => ({ store, navProvider: new FakeNavProvider({ publishedThrough: through }),
      yieldProvider: new FakeYieldProvider(), now: () => new Date(iso) });
    expect((await runMonthlySignal(mk("2026-09-29", "2026-10-01T05:15:00Z"))).outcome).toBe("WAITING_FOR_DATA");
    expect((await runMonthlySignal(mk("2026-09-30", "2026-10-01T16:15:00Z"))).outcome).toBe("VALID");
    expect((await runMonthlySignal(mk("2026-10-02", "2026-10-02T05:15:00Z"))).outcome).toBe("ALREADY_FINAL");
    expect(await store.listSignals(STRATEGY_ID)).toHaveLength(1);
  });
});
