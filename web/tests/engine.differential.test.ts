/**
 * Randomized differential test: TypeScript port vs. Python reference (gem.live).
 *
 * research/scripts/differential_cases.py generates N deterministic scenarios
 * (fixed seed), runs the Python reference and writes inputs + full outputs
 * (incl. intermediate values). This test feeds the same inputs to
 * computeRegionalSignal and compares: period, status, target, reason, NAV dates,
 * all returns, 12-month endpoints (dates + NAVs) and the monthly cash window.
 *
 * Requires Python with the research package's dependencies (pandas, numpy).
 * Set SKIP_PY_DIFFERENTIAL=1 to skip explicitly (the skip is reported, never silent).
 * Divergences are written to tests/.differential-failures/<id>.json.
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { computeRegionalSignal, EngineResult, Point } from "@/lib/engine/regional";

const N = Number(process.env.DIFFERENTIAL_N ?? 1000);
const SEED = Number(process.env.DIFFERENTIAL_SEED ?? 20261031);
const RET_TOL = 1e-12;

type Pair = [string, number | null];
interface Case {
  id: number;
  tags: string[];
  as_of: string;
  navs: Record<string, Pair[]>;
  yields: Pair[];
  expected: {
    strategy_version: string; signal_period_end: string; status: string; target: string | null; reason: string;
    returns: Record<string, number | null>; nav_dates: Record<string, string | null>;
    diagnostics: { endpoints: EngineResult["endpoints"]; cash_window: [string, number][] };
  };
}

const toPoints = (xs: Pair[]): Point[] => xs.map(([date, value]) => ({ date, value: value === null ? Number.NaN : value }));

/** Returns a list of human-readable differences (empty = identical within tolerance). */
export function compare(c: Case, r: EngineResult, stats: { maxRetDiff: number }): string[] {
  const e = c.expected;
  const d: string[] = [];
  const eq = (name: string, a: unknown, b: unknown) => {
    if (JSON.stringify(a) !== JSON.stringify(b)) d.push(`${name}: python=${JSON.stringify(a)} ts=${JSON.stringify(b)}`);
  };
  eq("strategy_version", e.strategy_version, r.strategy_version);
  eq("signal_period_end", e.signal_period_end, r.signal_period_end);
  eq("status", e.status, r.status);
  eq("target", e.target, r.target);
  eq("reason", e.reason, r.reason);
  eq("nav_dates", e.nav_dates, r.nav_dates);
  const rr = r.returns as Record<string, number | null>;
  eq("returns.keys", Object.keys(e.returns).sort(), Object.keys(rr).sort());
  for (const [k, v] of Object.entries(e.returns)) {
    const got = rr[k] ?? null;
    if (v === null || got === null) eq(`returns.${k}`, v, got);
    else {
      const diff = Math.abs(got - v);
      stats.maxRetDiff = Math.max(stats.maxRetDiff, diff);
      if (!(diff <= RET_TOL)) d.push(`returns.${k}: python=${v} ts=${got} diff=${diff}`);
    }
  }
  const pe = e.diagnostics.endpoints;
  eq("endpoints.keys", Object.keys(pe).sort(), Object.keys(r.endpoints).sort());
  for (const [iid, ep] of Object.entries(pe)) eq(`endpoints.${iid}`, ep, r.endpoints[iid]);
  eq("cash_window", e.diagnostics.cash_window, r.cash_window);
  return d;
}

function generate(): { cases: Case[]; seed: number; n: number } | null {
  if (process.env.SKIP_PY_DIFFERENTIAL === "1") return null;
  const dir = mkdtempSync(join(tmpdir(), "gem-diff-"));
  const out = join(dir, "cases.json");
  const script = resolve(__dirname, "..", "..", "research", "scripts", "differential_cases.py");
  execFileSync(process.env.PYTHON ?? "python3", [script, out, "--n", String(N), "--seed", String(SEED)],
               { stdio: ["ignore", "pipe", "inherit"], timeout: 300_000 });
  return JSON.parse(readFileSync(out, "utf8"));
}

const data = generate();

describe.skipIf(data === null)(`Python ↔ TypeScript randomized differential (seed ${SEED}, N=${N})`, () => {
  it("generated the requested number of scenarios with the requested seed", () => {
    expect(data!.n).toBe(N);
    expect(data!.seed).toBe(SEED);
    expect(data!.cases).toHaveLength(N);
    expect(N).toBeGreaterThanOrEqual(500);
  });

  it("every scenario: identical decision and intermediate values", () => {
    const stats = { maxRetDiff: 0 };
    const failures: { id: number; diffs: string[] }[] = [];
    const failDir = resolve(__dirname, ".differential-failures");
    for (const c of data!.cases) {
      const navs = Object.fromEntries(Object.entries(c.navs).map(([k, v]) => [k, toPoints(v)]));
      const r = computeRegionalSignal(c.as_of, navs, toPoints(c.yields));
      const diffs = compare(c, r, stats);
      if (diffs.length) {
        failures.push({ id: c.id, diffs });
        mkdirSync(failDir, { recursive: true });
        writeFileSync(join(failDir, `${c.id}.json`), JSON.stringify({ seed: SEED, input: { as_of: c.as_of, navs: c.navs, yields: c.yields, tags: c.tags },
          python: c.expected, typescript: r, diffs }, null, 1));
      }
    }
    const coverage = { valid: data!.cases.filter((c) => c.expected.status === "VALID").length,
                       defensive: data!.cases.filter((c) => c.expected.target === "AVANZA_RANTA_KORT").length,
                       boundary: data!.cases.filter((c) => c.tags.some((t) => t.startsWith("hurdle_boundary"))).length };
    console.log(`differential: ${N} scenarios, ${failures.length} divergent, max |Δreturn| = ${stats.maxRetDiff}`, coverage);
    expect(failures.slice(0, 5)).toEqual([]);
  });
});

if (data === null) console.warn("SKIPPED: Python ↔ TS differential test (SKIP_PY_DIFFERENTIAL=1)");
