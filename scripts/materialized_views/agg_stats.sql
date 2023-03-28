SELECT 
  cron.schedule(
    '0 1 * * *', 
    $$
        INSERT INTO agg_stats (key, value, created_at)
        WITH transactions_with_counts AS
        (
            SELECT  *
                ,COUNT(*) OVER (PARTITION BY 'transaction_count' ORDER BY block_time RANGE BETWEEN 999 PRECEDING AND CURRENT ROW) AS transaction_count
            FROM transactions
        )

        SELECT  'max_tps'           AS key
            ,MAX(transaction_count) AS value
            ,NOW()                  AS created_at
        FROM transactions_with_counts;
     $$
);
