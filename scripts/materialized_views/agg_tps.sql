CREATE MATERIALIZED VIEW agg_tps AS (
  Select 
    COUNT(*), 
    now() as last_updated 
  from 
    transactions 
  where 
    block_time >= extract(
      epoch 
      from 
        (now() - INTERVAL '1 minute')
    ) * 1000
) WITH NO DATA;

CREATE UNIQUE INDEX ON agg_tps (last_updated);
REFRESH MATERIALIZED VIEW CONCURRENTLY agg_tps;

SELECT 
  cron.schedule(
    '*/2 * * * *', $$REFRESH MATERIALIZED VIEW CONCURRENTLY agg_tps$$
  );
