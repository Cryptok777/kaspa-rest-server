SELECT 
  cron.schedule(
    '0 */1 * * *', 
    $$
    INSERT INTO agg_address_statistics (
        select
            COUNT(address) filter (where balance > 0              and balance < 1 * 1e2 *  1e8)  as addresses_in_1e2,
            COUNT(address) filter (where balance >= 1 * 1e2 * 1e8 and balance < 1 * 1e3 *  1e8)  as addresses_in_1e3,
            COUNT(address) filter (where balance >= 1 * 1e3 * 1e8 and balance < 1 * 1e4 *  1e8)  as addresses_in_1e4,
            COUNT(address) filter (where balance >= 1 * 1e4 * 1e8 and balance < 1 * 1e5 *  1e8)  as addresses_in_1e5,
            COUNT(address) filter (where balance >= 1 * 1e5 * 1e8 and balance < 1 * 1e6 *  1e8)  as addresses_in_1e6,
            COUNT(address) filter (where balance >= 1 * 1e6 * 1e8 and balance < 1 * 1e7 *  1e8)  as addresses_in_1e7,
            COUNT(address) filter (where balance >= 1 * 1e7 * 1e8 and balance < 1 * 1e8 *  1e8)  as addresses_in_1e8,
            COUNT(address) filter (where balance >= 1 * 1e8 * 1e8 and balance < 1 * 1e9 *  1e8)  as addresses_in_1e9,
            COUNT(address) filter (where balance >= 1 * 1e9 * 1e8 and balance < 1 * 1e10 * 1e8)  as addresses_in_1e10,
            now() as created_at
        from
            address_balances
    );
    $$
);
