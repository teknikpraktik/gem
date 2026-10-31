import { neon } from "@neondatabase/serverless";
import type { NavPoint } from "../providers/types";
import { AttemptRecord, SignalRecord, SignalStore } from "./types";

type Row = Record<string, unknown>;

function toDate(v: unknown): string {
  if (v instanceof Date) return v.toISOString().slice(0, 10);
  return String(v).slice(0, 10);
}

function rowToSignal(r: Row, inputs: Row[]): SignalRecord {
  return {
    strategyId: String(r.strategy_id),
    strategyVersion: String(r.strategy_version),
    signalPeriod: toDate(r.signal_period),
    generatedAt: new Date(String(r.generated_at)).toISOString(),
    status: r.status as SignalRecord["status"],
    selectedAsset: (r.selected_asset as string) ?? null,
    selectedFund: (r.selected_fund as string) ?? null,
    returns: r.returns as SignalRecord["returns"],
    cashHurdle: r.cash_hurdle === null ? null : Number(r.cash_hurdle),
    reason: String(r.reason),
    inputDates: r.input_dates as SignalRecord["inputDates"],
    inputSources: r.input_sources as SignalRecord["inputSources"],
    dataQuality: r.data_quality as SignalRecord["dataQuality"],
    providerVersions: r.provider_versions as SignalRecord["providerVersions"],
    origin: (r.origin as SignalRecord["origin"]) ?? "live",
    inputs: inputs.map((i) => ({
      instrumentId: String(i.instrument_id),
      startDate: i.start_date ? toDate(i.start_date) : null,
      startNav: i.start_nav === null ? null : Number(i.start_nav),
      endDate: i.end_date ? toDate(i.end_date) : null,
      endNav: i.end_nav === null ? null : Number(i.end_nav),
      return12m: i.return_12m === null ? null : Number(i.return_12m),
    })),
  };
}

/** Postgres (Neon serverless HTTP driver). Schema: db/schema.sql. */
export type QueryFn = (text: string, params: unknown[]) => Promise<Row[]>;

export class PostgresStore implements SignalStore {
  readonly kind = "postgres";
  readonly writable = true;
  private readonly query: QueryFn;

  /** `target`: a DATABASE_URL (Neon HTTP driver) or a query function (tests: PGlite). */
  constructor(target: string | QueryFn) {
    if (typeof target === "string") {
      const sql = neon(target);
      this.query = async (text, params) => (await sql.query(text, params)) as Row[];
    } else {
      this.query = target;
    }
  }

  private async q(text: string, params: unknown[] = []): Promise<Row[]> {
    return this.query(text, params);
  }

  private async withInputs(rows: Row[]): Promise<SignalRecord[]> {
    if (!rows.length) return [];
    const ids = rows.map((r) => r.signal_id);
    const inputs = await this.q("SELECT * FROM signal_inputs WHERE signal_id = ANY($1)", [ids]);
    return rows.map((r) => rowToSignal(r, inputs.filter((i) => String(i.signal_id) === String(r.signal_id))));
  }

  async getSignal(strategyId: string, period: string, version: string) {
    const rows = await this.q(
      "SELECT * FROM signals WHERE strategy_id = $1 AND signal_period = $2 AND strategy_version = $3",
      [strategyId, period, version]);
    return (await this.withInputs(rows))[0] ?? null;
  }

  async insertSignalIfAbsent(rec: SignalRecord) {
    // Single statement: insert the signal (or nothing on conflict) and its inputs atomically.
    const rows = await this.q(
      `WITH ins AS (
         INSERT INTO signals (strategy_id, strategy_version, signal_period, generated_at, status, selected_asset,
           selected_fund, returns, cash_hurdle, reason, input_dates, input_sources, data_quality, provider_versions, origin)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
         ON CONFLICT ON CONSTRAINT signals_unique_period DO NOTHING
         RETURNING signal_id
       ), inp AS (
         INSERT INTO signal_inputs (signal_id, instrument_id, start_date, start_nav, end_date, end_nav, return_12m)
         SELECT ins.signal_id, x.instrument_id, x.start_date, x.start_nav, x.end_date, x.end_nav, x.return_12m
         FROM ins, jsonb_to_recordset($16::jsonb) AS x(instrument_id text, start_date date, start_nav float8,
           end_date date, end_nav float8, return_12m float8)
         RETURNING 1
       )
       SELECT (SELECT count(*) FROM ins) AS inserted`,
      [rec.strategyId, rec.strategyVersion, rec.signalPeriod, rec.generatedAt, rec.status, rec.selectedAsset,
       rec.selectedFund, JSON.stringify(rec.returns), rec.cashHurdle, rec.reason, JSON.stringify(rec.inputDates),
       JSON.stringify(rec.inputSources), JSON.stringify(rec.dataQuality), JSON.stringify(rec.providerVersions),
       rec.origin,
       JSON.stringify(rec.inputs.map((i) => ({ instrument_id: i.instrumentId, start_date: i.startDate, start_nav: i.startNav,
                                                end_date: i.endDate, end_nav: i.endNav, return_12m: i.return12m })))]);
    const inserted = Number(rows[0]?.inserted ?? 0) > 0;
    const record = (await this.getSignal(rec.strategyId, rec.signalPeriod, rec.strategyVersion)) ?? rec;
    return { inserted, record };
  }

  async listSignals(strategyId: string, limit = 240) {
    const rows = await this.q("SELECT * FROM signals WHERE strategy_id = $1 ORDER BY signal_period DESC LIMIT $2",
      [strategyId, limit]);
    return this.withInputs(rows);
  }

  async latestValid(strategyId: string) {
    const rows = await this.q(
      "SELECT * FROM signals WHERE strategy_id = $1 AND status = 'VALID' ORDER BY signal_period DESC LIMIT 1", [strategyId]);
    return (await this.withInputs(rows))[0] ?? null;
  }

  async recordAttempt(a: AttemptRecord) {
    await this.q(
      "INSERT INTO data_source_status (strategy_id, signal_period, checked_at, status, detail, sources) VALUES ($1,$2,$3,$4,$5,$6)",
      [a.strategyId, a.signalPeriod, a.checkedAt, a.status, a.detail.slice(0, 2000), JSON.stringify(a.sources)]);
  }

  async latestAttempt(strategyId: string, period: string) {
    const rows = await this.q(
      "SELECT * FROM data_source_status WHERE strategy_id = $1 AND signal_period = $2 ORDER BY checked_at DESC, id DESC LIMIT 1",
      [strategyId, period]);
    const r = rows[0];
    if (!r) return null;
    return { strategyId: String(r.strategy_id), signalPeriod: toDate(r.signal_period), checkedAt: new Date(String(r.checked_at)).toISOString(),
             status: r.status as AttemptRecord["status"], detail: String(r.detail), sources: r.sources as Record<string, string> };
  }

  async saveNavObservations(points: NavPoint[]) {
    if (!points.length) return;
    await this.q(
      `INSERT INTO nav_observations (instrument_id, nav_date, nav, currency, source, quality, retrieved_at)
       SELECT x.instrument_id, x.nav_date, x.nav, x.currency, x.source, x.quality, x.retrieved_at
       FROM jsonb_to_recordset($1::jsonb) AS x(instrument_id text, nav_date date, nav float8, currency text, source text,
         quality text, retrieved_at timestamptz)
       ON CONFLICT DO NOTHING`,
      [JSON.stringify(points.map((p) => ({ instrument_id: p.instrumentId, nav_date: p.navDate, nav: p.nav, currency: p.currency,
                                            source: p.source, quality: p.quality, retrieved_at: p.retrievedAt })))]);
  }

  async latestNavs() {
    const rows = await this.q(
      `SELECT DISTINCT ON (instrument_id) n.*, i.isin FROM nav_observations n JOIN instruments i USING (instrument_id)
       ORDER BY instrument_id, nav_date DESC, retrieved_at DESC`);
    const out: Record<string, NavPoint> = {};
    for (const r of rows) {
      out[String(r.instrument_id)] = { instrumentId: String(r.instrument_id), isin: String(r.isin), navDate: toDate(r.nav_date),
        nav: Number(r.nav), currency: String(r.currency), retrievedAt: new Date(String(r.retrieved_at)).toISOString(),
        source: String(r.source), quality: r.quality as NavPoint["quality"] };
    }
    return out;
  }
}
