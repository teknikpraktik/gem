// Migration plan shared by scripts/migrate.mjs and the tests.
// Files: db/migrations/NNN_name.sql, applied in order, recorded in schema_migrations with
// their sha256. An applied migration whose file content changed is a hard error.
import { createHash } from "node:crypto";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

export const MIGRATIONS_DIR = fileURLToPath(new URL("./migrations/", import.meta.url));

export function loadMigrations(dir = MIGRATIONS_DIR) {
  return readdirSync(dir).filter((f) => /^\d{3}_[a-z0-9_]+\.sql$/.test(f)).sort().map((f) => {
    const text = readFileSync(join(dir, f), "utf8");
    return { version: f.replace(/\.sql$/, ""), text, sha256: createHash("sha256").update(text).digest("hex") };
  });
}

/** Split into statements, keeping $$ ... $$ bodies intact; drops comment-only lines. */
export function splitStatements(text) {
  const out = [];
  let buf = "";
  let inDollar = false;
  for (const line of text.split("\n")) {
    if (line.trim().startsWith("--") && !inDollar) continue;
    buf += line + "\n";
    if ((line.match(/\$\$/g) || []).length % 2 === 1) inDollar = !inDollar;
    if (!inDollar && line.trim().endsWith(";")) {
      out.push(buf.trim());
      buf = "";
    }
  }
  if (buf.trim()) out.push(buf.trim());
  return out;
}

/** query(text, params) -> rows. Returns the list of newly applied versions. */
export async function migrate(query, log = () => {}) {
  await query(`CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())`, []);
  const applied = new Map((await query("SELECT version, sha256 FROM schema_migrations", [])).map((r) => [r.version, r.sha256]));
  const done = [];
  for (const m of loadMigrations()) {
    if (applied.has(m.version)) {
      if (applied.get(m.version) !== m.sha256) {
        throw new Error(`migration ${m.version} was changed after it was applied (sha256 mismatch) - add a new migration instead`);
      }
      continue;
    }
    for (const s of splitStatements(m.text)) await query(s, []);
    await query("INSERT INTO schema_migrations (version, sha256) VALUES ($1, $2)", [m.version, m.sha256]);
    log(`applied ${m.version}`);
    done.push(m.version);
  }
  return done;
}
