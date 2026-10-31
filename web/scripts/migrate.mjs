// Applies pending db/migrations/*.sql to DATABASE_URL. Usage: DATABASE_URL=... npm run db:migrate
import { neon } from "@neondatabase/serverless";
import { migrate } from "../db/migrations.mjs";

const url = process.env.DATABASE_URL;
if (!url) {
  console.error("DATABASE_URL is not set");
  process.exit(1);
}
const sql = neon(url);
const done = await migrate((text, params) => sql.query(text, params), console.log);
console.log(done.length ? `applied: ${done.join(", ")}` : "schema up to date");
