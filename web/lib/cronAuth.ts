import { timingSafeEqual } from "node:crypto";

/**
 * Vercel Cron sends `Authorization: Bearer ${CRON_SECRET}`. Without a configured
 * secret the endpoint refuses to run (fail closed).
 */
export function authorizeCron(req: Request, secret = process.env.CRON_SECRET): { ok: true } | { ok: false; status: number; error: string } {
  if (!secret || secret.length < 16) return { ok: false, status: 503, error: "CRON_SECRET not configured (min 16 chars)" };
  const got = req.headers.get("authorization") ?? "";
  const want = `Bearer ${secret}`;
  const a = Buffer.from(got);
  const b = Buffer.from(want);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return { ok: false, status: 401, error: "unauthorized" };
  return { ok: true };
}
