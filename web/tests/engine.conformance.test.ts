import { describe, expect, it } from "vitest";
import fixtures from "./fixtures/live_conformance.json";
import { computeRegionalSignal, Point } from "@/lib/engine/regional";

type Case = {
  name: string;
  as_of: string;
  navs: Record<string, [string, number][]>;
  yields: [string, number][];
  expected: {
    signal_period_end: string;
    status: string;
    target: string | null;
    returns: Record<string, number | null>;
    nav_dates: Record<string, string | null>;
    reason: string;
  };
};

const toPoints = (xs: [string, number][]): Point[] => xs.map(([date, value]) => ({ date, value }));

describe("TypeScript live engine reproduces the Python reference (gem.live)", () => {
  for (const c of (fixtures as unknown as { cases: Case[] }).cases) {
    it(c.name, () => {
      const navs = Object.fromEntries(Object.entries(c.navs).map(([k, v]) => [k, toPoints(v)]));
      const r = computeRegionalSignal(c.as_of, navs, toPoints(c.yields));
      expect(r.signal_period_end).toBe(c.expected.signal_period_end);
      expect(r.status).toBe(c.expected.status);
      expect(r.target).toBe(c.expected.target);
      expect(r.reason).toBe(c.expected.reason);
      expect(r.nav_dates).toEqual(c.expected.nav_dates);
      for (const [k, v] of Object.entries(c.expected.returns)) {
        const got = (r.returns as Record<string, number | null>)[k];
        if (v === null) expect(got).toBeNull();
        else expect(Math.abs((got as number) - v)).toBeLessThan(1e-12);
      }
      expect(Object.keys(r.returns).sort()).toEqual(Object.keys(c.expected.returns).sort());
    });
  }
});
