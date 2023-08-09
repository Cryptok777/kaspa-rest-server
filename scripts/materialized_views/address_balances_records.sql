SELECT 
  cron.schedule(
    '0 */1 * * *', 
    $$
    INSERT INTO address_balances_records (address, balance, created_at)
    SELECT address, balance, NOW() as created_at
    FROM address_balances
    WHERE tracked = TRUE
    $$
);
