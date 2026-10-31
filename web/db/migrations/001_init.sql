-- GEM signal monitor - Postgres schema (Neon / Vercel Postgres compatible).
-- Idempotent: safe to run repeatedly (npm run db:migrate).

CREATE TABLE IF NOT EXISTS instruments (
  instrument_id  text PRIMARY KEY,
  name           text NOT NULL,
  isin           text NOT NULL UNIQUE,
  currency       text NOT NULL,
  orderbook_id   text NOT NULL,
  role           text NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS strategy_versions (
  strategy_id       text NOT NULL,
  strategy_version  text NOT NULL,
  rule              jsonb NOT NULL,
  created_at        timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (strategy_id, strategy_version)
);

-- Final monthly signals. One row per (strategy, period, version); never updated.
CREATE TABLE IF NOT EXISTS signals (
  signal_id          bigserial PRIMARY KEY,
  strategy_id        text NOT NULL,
  strategy_version   text NOT NULL,
  signal_period      date NOT NULL,
  generated_at       timestamptz NOT NULL,
  status             text NOT NULL CHECK (status IN ('VALID', 'NO_SIGNAL')),
  selected_asset     text,
  selected_fund      text,
  returns            jsonb NOT NULL,
  cash_hurdle        double precision,
  reason             text NOT NULL,
  input_dates        jsonb NOT NULL,
  input_sources      jsonb NOT NULL,
  data_quality       jsonb NOT NULL,
  provider_versions  jsonb NOT NULL,
  origin             text NOT NULL DEFAULT 'live',
  CONSTRAINT signals_unique_period UNIQUE (strategy_id, signal_period, strategy_version),
  CONSTRAINT signals_version_fk FOREIGN KEY (strategy_id, strategy_version)
    REFERENCES strategy_versions (strategy_id, strategy_version)
);

CREATE TABLE IF NOT EXISTS signal_inputs (
  signal_id      bigint NOT NULL REFERENCES signals (signal_id),
  instrument_id  text NOT NULL,
  start_date     date,
  start_nav      double precision,
  end_date       date,
  end_nav        double precision,
  return_12m     double precision,
  PRIMARY KEY (signal_id, instrument_id)
);

CREATE TABLE IF NOT EXISTS nav_observations (
  instrument_id  text NOT NULL,
  nav_date       date NOT NULL,
  nav            double precision NOT NULL CHECK (nav > 0),
  currency       text NOT NULL,
  source         text NOT NULL,
  quality        text NOT NULL,
  retrieved_at   timestamptz NOT NULL,
  PRIMARY KEY (instrument_id, nav_date, source)
);

-- Every pipeline run (final or not): WAITING_FOR_DATA, DATA_ERROR, VALID, NO_SIGNAL, ALREADY_FINAL.
CREATE TABLE IF NOT EXISTS data_source_status (
  id             bigserial PRIMARY KEY,
  strategy_id    text NOT NULL,
  signal_period  date NOT NULL,
  checked_at     timestamptz NOT NULL,
  status         text NOT NULL,
  detail         text NOT NULL,
  sources        jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS data_source_status_period ON data_source_status (strategy_id, signal_period, checked_at DESC);

-- Immutability: final signals and their inputs can never be changed or removed.
CREATE OR REPLACE FUNCTION forbid_signal_mutation() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'signals are immutable (% on %)', TG_OP, TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS signals_immutable ON signals;
CREATE TRIGGER signals_immutable BEFORE UPDATE OR DELETE ON signals
  FOR EACH ROW EXECUTE FUNCTION forbid_signal_mutation();
DROP TRIGGER IF EXISTS signal_inputs_immutable ON signal_inputs;
CREATE TRIGGER signal_inputs_immutable BEFORE UPDATE OR DELETE ON signal_inputs
  FOR EACH ROW EXECUTE FUNCTION forbid_signal_mutation();

-- Reference rows
INSERT INTO strategy_versions (strategy_id, strategy_version, rule) VALUES
  ('REGIONAL_SEK', '1.0.0', '{"lookback_months": 12, "top_n": 1, "regions": ["usa","europe","em"],
    "hurdle": "SE_CASH_SSVX_SYNTH_V1 (Riksbank SETB3MBENCH, r_m = y_{m-1}/1200)", "defensive": "AVANZA_RANTA_KORT",
    "nav_staleness_bdays": 3, "yield_staleness_bdays": 5, "reference": "research/src/gem/live.py"}')
ON CONFLICT DO NOTHING;
INSERT INTO instruments (instrument_id, name, isin, currency, orderbook_id, role) VALUES
  ('AVANZA_USA', 'Avanza USA', 'SE0012741163', 'SEK', '1025150', 'REGION_USA'),
  ('AVANZA_EUROPA', 'Avanza Europa', 'SE0013718699', 'SEK', '1041067', 'REGION_EUROPE'),
  ('AVANZA_EM', 'Avanza Emerging Markets', 'SE0012454338', 'SEK', '944976', 'REGION_EM'),
  ('AVANZA_RANTA_KORT', 'Avanza Ränta Kort', 'SE0021021425', 'SEK', '1684019', 'DEFENSIVE'),
  ('AVANZA_GLOBAL', 'Avanza Global', 'SE0011527613', 'SEK', '878733', 'BENCHMARK')
ON CONFLICT DO NOTHING;
