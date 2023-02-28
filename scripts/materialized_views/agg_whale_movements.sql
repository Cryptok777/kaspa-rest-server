CREATE MATERIALIZED VIEW agg_whale_movements AS (
  SELECT 
    transactions_outputs.transaction_id, 
    transactions_outputs.script_public_key_address, 
    transactions_outputs.amount, 
    transactions.block_time 
  FROM 
    transactions_outputs 
    LEFT JOIN transactions ON transactions.transaction_id = transactions_outputs.transaction_id 
  WHERE 
    TRUE 
    AND transactions_outputs.amount > 1 * 1e6 * 1e8 
    AND transactions.block_time > extract(
      epoch 
      from 
        (now() - INTERVAL '1 DAY')
    ) * 1000 
  ORDER BY 
    transactions.block_time DESC 
  LIMIT 
    100
) WITH NO DATA;

REFRESH MATERIALIZED VIEW agg_whale_movements;

SELECT cron.schedule('*/5 * * * *', $$REFRESH MATERIALIZED VIEW agg_whale_movements$$);