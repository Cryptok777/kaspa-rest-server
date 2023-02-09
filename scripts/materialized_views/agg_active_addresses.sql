CREATE MATERIALIZED VIEW agg_active_addresses AS (
  SELECT 
    DATE_TRUNC(
      'day', 
      TO_TIMESTAMP(transactions.block_time / 1e3)
    ) as date, 
    COUNT(
      DISTINCT(script_public_key_address)
    ) 
  FROM 
    transactions_outputs 
    LEFT JOIN transactions ON transactions.transaction_id = transactions_outputs.transaction_id 
  GROUP BY 
    DATE_TRUNC(
      'day', 
      TO_TIMESTAMP(transactions.block_time / 1e3)
    ) 
  ORDER BY 
    date
) WITH NO DATA;

REFRESH MATERIALIZED VIEW agg_active_addresses;

SELECT 
  cron.schedule(
    '*/30 * * * *', $$REFRESH MATERIALIZED VIEW agg_active_addresses$$
  );
