import { NextResponse } from "next/server";
import { getAudit } from "@/lib/api";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/** GET /api/audit?period=YYYY-MM-DD - provenance + exact input + re-verification of one snapshot (read-only). */
export async function GET(req: Request) {
  const period = new URL(req.url).searchParams.get("period") ?? "";
  if (!/^\d{4}-\d{2}-\d{2}$/.test(period)) return NextResponse.json({ error: "period=YYYY-MM-DD required" }, { status: 400 });
  try {
    const a = await getAudit(period);
    return a.found ? NextResponse.json(a) : NextResponse.json({ error: "no snapshot for period" }, { status: 404 });
  } catch (e) {
    return NextResponse.json({ error: "STORE_UNAVAILABLE", detail: (e as Error).message }, { status: 503 });
  }
}
