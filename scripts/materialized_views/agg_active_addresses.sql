SELECT 
  cron.schedule(
    '0 * * * *', 
    $$
      WITH range AS
      (
        SELECT  (EXTRACT(EPOCH
        FROM CURRENT_DATE::timestamp) * 1e3) :: bigint AS START_DATE, (EXTRACT(EPOCH
        FROM (CURRENT_DATE + 1)::timestamp) * 1e3) :: bigint AS END_DATE
      )
      INSERT INTO agg_active_addresses (date, count)
      SELECT  DATE_TRUNC('day',TO_TIMESTAMP(block_time / 1e3)) AS date
            ,COUNT(DISTINCT(address))                         AS count
      FROM tx_id_address_mapping
      WHERE block_time >= (
      SELECT  START_DATE
      FROM range) AND block_time < (
      SELECT  END_DATE
      FROM range)
      GROUP BY  date
      ON CONFLICT (date) DO UPDATE

      SET count = EXCLUDED.count;
    $$
);
