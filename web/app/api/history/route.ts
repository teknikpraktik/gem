import { NextResponse } from "next/server";
import { getHistory } from "@/lib/api";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  try {
    return NextResponse.json({ strategy: "REGIONAL_SEK", signals: await getHistory() });
  } catch (e) {
    return NextResponse.json({ error: "STORE_UNAVAILABLE", detail: (e as Error).message }, { status: 503 });
  }
}
