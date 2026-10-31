// Applies db/schema.sql to DATABASE_URL (idempotent). Usage: DATABASE_URL=... npm run db:migrate
import { readFileSync } from "node:fs";
import { neon } from "@neondatabase/serverless";

const url = process.env.DATABASE_URL;
if (!url) {
  console.error("DATABASE_URL is not set");
  process.exit(1);
}
const sql = neon(url);
const text = readFileSync(new URL("../db/schema.sql", import.meta.url), "utf8");
// Split on statement boundaries, keeping the plpgsql function body ($$ ... $$) intact.
const statements = [];
let buf = "";
let inDollar = false;
for (const line of text.split("\n")) {
  if (line.trim().startsWith("--") && !inDollar) continue;
  buf += line + "\n";
  if ((line.match(/\$\$/g) || []).length % 2 === 1) inDollar = !inDollar;
  if (!inDollar && line.trim().endsWith(";")) {
    statements.push(buf.trim());
    buf = "";
  }
}
for (const s of statements) {
  await sql.query(s);
  console.log("ok:", s.split("\n")[0].slice(0, 80));
}
console.log(`applied ${statements.length} statements`);
