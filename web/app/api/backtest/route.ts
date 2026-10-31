import { NextResponse } from "next/server";
import { getBacktest } from "@/lib/api";

export const dynamic = "force-static";

export function GET() {
  return NextResponse.json(getBacktest());
}
