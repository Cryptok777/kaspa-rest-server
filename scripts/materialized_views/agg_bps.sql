CREATE MATERIALIZED VIEW agg_bps AS (
  SELECT
    COUNT(hash)::decimal / 5 / 60 as count,
    now() as last_updated
  from
    blocks
  where
    timestamp >= (now() - INTERVAL '5 minute')
) WITH NO DATA;

CREATE UNIQUE INDEX ON agg_bps (last_updated);
REFRESH MATERIALIZED VIEW agg_bps;

SELECT 
  cron.schedule(
    '*/2 * * * *', $$REFRESH MATERIALIZED VIEW CONCURRENTLY agg_bps$$
  );
