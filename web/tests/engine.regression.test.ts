import { describe, expect, it } from "vitest";
import { addDays, monthEndMinus, weekday } from "@/lib/engine/dates";
import { cashHurdleDetail } from "@/lib/engine/regional";

/**
 * Regression: found by the randomized differential test (seed 20261031, 770/1000 cases).
 * The TS port computed the monthly cash return as y/1200; the Python reference
 * computes (y/100)/12. The results differ in the last bit for many yields
 * (e.g. 4.909 -> 0.0040908333333333335 vs 0.004090833333333333), which can flip
 * a decision when a region's momentum equals the hurdle exactly.
 */
describe("cash hurdle uses the Python operation order (y / 100 / 12)", () => {
  it("monthly returns are bit-identical to (y/100)/12", () => {
    expect(4.909 / 1200).not.toBe(4.909 / 100 / 12); // the two formulas really differ
    const pe = "2006-12-31";
    const ys: { date: string; value: number }[] = [];
    for (let d = monthEndMinus(pe, 14); d <= pe; d = addDays(d, 1)) if (weekday(d) < 5) ys.push({ date: d, value: 4.909 });
    const r = cashHurdleDetail(ys, pe);
    expect(r.window).toHaveLength(12);
    for (const [, v] of r.window) expect(v).toBe(4.909 / 100 / 12);
    expect(r.value).toBe(r.window.reduce((a, [, v]) => a * (1 + v), 1) - 1);
  });
});
