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

REFRESH MATERIALIZED VIEW agg_tps;

SELECT 
  cron.schedule(
    '*/5 * * * *', $$REFRESH MATERIALIZED VIEW agg_tps$$
  );
