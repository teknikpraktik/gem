import { NextResponse } from "next/server";
import { authorizeCron } from "@/lib/cronAuth";
import { getDeps } from "@/lib/deps";
import { runMonthlySignal } from "@/lib/pipeline";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const maxDuration = 60;

/**
 * Monthly signal job. Vercel Cron calls GET; POST is accepted for manual runs.
 * Idempotent: once the month's final signal exists every call is a no-op.
 * Never trades, never writes anything except signal snapshots and run logs.
 */
async function handle(req: Request) {
  const auth = authorizeCron(req);
  if (!auth.ok) return NextResponse.json({ error: auth.error }, { status: auth.status });
  const deps = getDeps();
  if (!deps.store.writable) {
    return NextResponse.json({ error: "DATABASE_URL not configured - store is read-only" }, { status: 503 });
  }
  const result = await runMonthlySignal(deps);
  const { record, ...rest } = result;
  return NextResponse.json({ ...rest, signal: record ? { period: record.signalPeriod, status: record.status,
    selectedFund: record.selectedFund, reason: record.reason, generatedAt: record.generatedAt } : null });
}

export const GET = handle;
export const POST = handle;
