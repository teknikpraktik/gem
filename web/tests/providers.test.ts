import { describe, expect, it } from "vitest";
import { AvanzaNavProvider, Fetcher, parseChart } from "@/lib/providers/avanza";
import { RiksbankYieldProvider } from "@/lib/providers/riksbank";
import { ProviderError } from "@/lib/providers/types";
import { instrumentById } from "@/lib/instruments";

const EM = instrumentById("AVANZA_EM")!;
const ms = (d: string) => new Date(`${d}T00:00:00+02:00`).getTime(); // 00:00 Stockholm (CEST)
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
const fetcherOf = (f: (url: string) => Response | Promise<Response>): Fetcher => async (url) => f(url);

describe("Avanza provider", () => {
  it("parses chart points as Stockholm dates and skips nulls", () => {
    const pts = parseChart({ dataSerie: [{ x: ms("2026-09-29"), y: 150.1 }, { x: ms("2026-09-30"), y: null }] }, EM, "t");
    expect(pts).toHaveLength(1);
    expect(pts[0]).toMatchObject({ instrumentId: "AVANZA_EM", isin: EM.isin, navDate: "2026-09-29", nav: 150.1,
                                   currency: "SEK", source: "avanza_fund_guide", quality: "UNDOCUMENTED_ENDPOINT" });
  });

  it("unexpected payload -> ProviderError", () => {
    expect(() => parseChart({ foo: 1 }, EM, "t")).toThrow(ProviderError);
    expect(() => parseChart({ dataSerie: [{ x: "a", y: 1 }] }, EM, "t")).toThrow(ProviderError);
  });

  it("history: daily windows, dedup, filter; HTTP error and bad JSON -> ProviderError", async () => {
    const days = ["2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01"];
    const ok = new AvanzaNavProvider(fetcherOf(() => json({ dataSerie: days.map((d, i) => ({ x: ms(d), y: 100 + i })) })));
    const pts = await ok.history(EM, "2026-09-29", "2026-09-30");
    expect(pts.map((p) => p.navDate)).toEqual(["2026-09-29", "2026-09-30"]);
    await expect(new AvanzaNavProvider(fetcherOf(() => json({}, 500))).history(EM, "2026-09-01", "2026-09-30")).rejects.toThrow(/HTTP 500/);
    await expect(new AvanzaNavProvider(fetcherOf(() => new Response("<html>", { status: 200 }))).history(EM, "2026-09-01", "2026-09-30"))
      .rejects.toThrow(/invalid JSON/);
    await expect(new AvanzaNavProvider(async () => { throw new Error("ECONNRESET"); }).history(EM, "2026-09-01", "2026-09-30"))
      .rejects.toThrow(/network error/);
  });

  it("monthly-downsampled response (format change) is rejected", async () => {
    const months = ["2026-06-30", "2026-07-31", "2026-08-31", "2026-09-30"];
    const p = new AvanzaNavProvider(fetcherOf(() => json({ dataSerie: months.map((d) => ({ x: ms(d), y: 100 })) })));
    await expect(p.history(EM, "2026-06-01", "2026-09-30")).rejects.toThrow(/not daily/);
  });

  it("implausible jump (>25 %) is refused, never repaired", async () => {
    const p = new AvanzaNavProvider(fetcherOf(() => json({ dataSerie: [
      { x: ms("2026-09-28"), y: 100 }, { x: ms("2026-09-29"), y: 140 }, { x: ms("2026-09-30"), y: 141 }] })));
    await expect(p.history(EM, "2026-09-28", "2026-09-30")).rejects.toThrow(/NAV move/);
  });

  it("verifyInstrument detects ISIN / currency changes", async () => {
    const guide = (o: object) => new AvanzaNavProvider(fetcherOf(() => json({ isin: EM.isin, currency: "SEK", nav: 1, navDate: "2026-09-30", ...o })));
    await expect(guide({}).verifyInstrument(EM)).resolves.toEqual({ navDate: "2026-09-30", nav: 1 });
    await expect(guide({ isin: "SE0000000000" }).verifyInstrument(EM)).rejects.toThrow(/ISIN/);
    await expect(guide({ currency: "USD" }).verifyInstrument(EM)).rejects.toThrow(/currency/);
  });
});

describe("Riksbank provider", () => {
  it("parses, sorts, skips nulls, sends key only when configured", async () => {
    let seen: RequestInit | undefined;
    const p = new RiksbankYieldProvider(async (_u, init) => { seen = init; return json([{ date: "2026-09-30", value: 1.9 },
      { date: "2026-09-29", value: null }, { date: "2026-09-28", value: 1.95 }]); }, "k".repeat(20));
    const ys = await p.ssvx3m("2026-09-28", "2026-09-30");
    expect(ys.map((y) => y.date)).toEqual(["2026-09-28", "2026-09-30"]);
    expect((seen!.headers as Record<string, string>)["Ocp-Apim-Subscription-Key"]).toBe("k".repeat(20));
    const p2 = new RiksbankYieldProvider(async (_u, init) => { seen = init; return json([]); }, undefined);
    await p2.ssvx3m("2026-09-28", "2026-09-30");
    expect((seen!.headers as Record<string, string>)["Ocp-Apim-Subscription-Key"]).toBeUndefined();
  });
  it("errors -> ProviderError", async () => {
    await expect(new RiksbankYieldProvider(async () => json({}, 429), undefined).ssvx3m("a", "b")).rejects.toThrow(/HTTP 429/);
    await expect(new RiksbankYieldProvider(async () => json({ x: 1 }), undefined).ssvx3m("a", "b")).rejects.toThrow(/unexpected payload/);
    await expect(new RiksbankYieldProvider(async () => json([{ date: "2026-09-30", value: "1,9" }]), undefined).ssvx3m("a", "b"))
      .rejects.toThrow(/bad value/);
  });
});
