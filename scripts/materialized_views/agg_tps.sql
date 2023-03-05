CREATE MATERIALIZED VIEW agg_tps AS (
  Select
    COUNT(*)::decimal / 5 / 60 as count,
    now() as last_updated
  from
    transactions
  where
    block_time >= extract(
      epoch
      from
        (now() - INTERVAL '5 minute')
    ) * 1000
) WITH NO DATA;

CREATE UNIQUE INDEX ON agg_tps (last_updated);
REFRESH MATERIALIZED VIEW agg_tps;

SELECT 
  cron.schedule(
    '*/2 * * * *', $$REFRESH MATERIALIZED VIEW CONCURRENTLY agg_tps$$
  );
