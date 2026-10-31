-- 002: audit trail and provenance for signal snapshots.
-- Never edit an applied migration; add a new one (scripts/migrate.mjs enforces this by checksum).

-- Explicit, machine-readable rule version. Same rule as '1.0.0'; the hurdle formula text is
-- corrected to the exact operation order of the Python reference.
INSERT INTO strategy_versions (strategy_id, strategy_version, rule) VALUES
  ('REGIONAL_SEK', 'regional-sek-v1.0.0', '{"lookback_months": 12, "top_n": 1, "regions": ["usa","europe","em"],
    "hurdle": "SE_CASH_SSVX_SYNTH_V1 (Riksbank SETB3MBENCH month-end, r_m = (y_{m-1}/100)/12)", "defensive": "AVANZA_RANTA_KORT",
    "nav_staleness_bdays": 3, "yield_staleness_bdays": 5, "ties": "strict >, earlier region wins (usa, europe, em)",
    "reference": "research/src/gem/live.py::regional_live_signal", "engine": "web/lib/engine/regional.ts"}')
ON CONFLICT DO NOTHING;

ALTER TABLE signals ADD COLUMN IF NOT EXISTS data_as_of date;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS input_data_checksum text;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS code_version text;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS engine_version text;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS reference_implementation text;

-- Every live snapshot written from now on must carry its provenance. NOT VALID: rows that
-- existed before this migration are not rewritten (they cannot be - signals are immutable).
ALTER TABLE signals ADD CONSTRAINT signals_audit_required CHECK (
  origin <> 'live' OR (
    data_as_of IS NOT NULL
    AND input_data_checksum ~ '^sha256:[0-9a-f]{64}$'
    AND code_version IS NOT NULL AND code_version <> ''
    AND engine_version IS NOT NULL
    AND reference_implementation IS NOT NULL)) NOT VALID;

-- The exact engine input of every snapshot (re-run + checksum verification: lib/audit.ts).
CREATE TABLE IF NOT EXISTS signal_input_snapshots (
  signal_id            bigint PRIMARY KEY REFERENCES signals (signal_id),
  input_data_checksum  text NOT NULL CHECK (input_data_checksum ~ '^sha256:[0-9a-f]{64}$'),
  payload              jsonb NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS signal_input_snapshots_immutable ON signal_input_snapshots;
CREATE TRIGGER signal_input_snapshots_immutable BEFORE UPDATE OR DELETE ON signal_input_snapshots
  FOR EACH ROW EXECUTE FUNCTION forbid_signal_mutation();

-- Run log: freshness/provenance per series; append-only like the snapshots.
ALTER TABLE data_source_status ADD COLUMN IF NOT EXISTS freshness jsonb NOT NULL DEFAULT '[]'::jsonb;
DROP TRIGGER IF EXISTS data_source_status_append_only ON data_source_status;
CREATE TRIGGER data_source_status_append_only BEFORE UPDATE OR DELETE ON data_source_status
  FOR EACH ROW EXECUTE FUNCTION forbid_signal_mutation();
