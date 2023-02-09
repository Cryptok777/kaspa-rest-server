CREATE MATERIALIZED VIEW agg_transactions_count AS (
  SELECT 
    DATE_TRUNC(
      'day', 
      TO_TIMESTAMP(transactions.block_time / 1e3)
    ) AS date, 
    COUNT(*) 
  FROM 
    transactions 
  GROUP BY 
    DATE_TRUNC(
      'day', 
      TO_TIMESTAMP(transactions.block_time / 1e3)
    ) 
  ORDER BY 
    date
) WITH NO DATA;

REFRESH MATERIALIZED VIEW agg_transactions_count;

SELECT 
  cron.schedule(
    '*/30 * * * *', $$REFRESH MATERIALIZED VIEW agg_transactions_count$$
  );
