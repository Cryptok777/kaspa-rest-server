CREATE MATERIALIZED VIEW agg_top_holders AS (
  SELECT 
    address, 
    balance, 
    now() AS last_updated FROM address_balances 
  ORDER BY 
    balance DESC 
  LIMIT 
    100
) WITH NO DATA;

REFRESH MATERIALIZED VIEW agg_top_holders;

SELECT 
  cron.schedule(
    '0 */1 * * *', $$REFRESH MATERIALIZED CONCURRENTLY VIEW agg_top_holders$$
  );
