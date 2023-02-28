SELECT 
  cron.schedule(
    '0 * * * *', 
    $$(
      INSERT INTO agg_active_addresses (date, count) 
      SELECT 
        DATE_TRUNC(
          'day', 
          TO_TIMESTAMP(block_time / 1e3)
        ) AS date, 
        COUNT(
          DISTINCT(address)
        ) AS count 
      FROM 
        tx_id_address_mapping 
      WHERE 
        DATE_TRUNC(
          'day', 
          TO_TIMESTAMP(block_time / 1e3)
        ) :: date = now() :: date 
      GROUP BY 
        DATE_TRUNC(
          'day', 
          TO_TIMESTAMP(block_time / 1e3)
        ) ON CONFLICT (date) DO 
      UPDATE 
      SET 
        count = EXCLUDED.count;
) $$
);
