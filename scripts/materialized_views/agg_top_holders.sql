CREATE MATERIALIZED VIEW agg_top_holders AS (
  SELECT 
    address, 
    balance, 
    now() AS last_updated FROM address_balances 
  ORDER BY 
    balance DESC 
  LIMIT 
    1000
) WITH NO DATA;

CREATE UNIQUE INDEX ON agg_top_holders (address);
REFRESH MATERIALIZED VIEW CONCURRENTLY agg_top_holders;

SELECT 
  cron.schedule(
    '0 */1 * * *', $$REFRESH MATERIALIZED VIEW CONCURRENTLY agg_top_holders$$
  );
