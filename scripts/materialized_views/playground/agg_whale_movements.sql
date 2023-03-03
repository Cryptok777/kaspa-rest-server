SELECT
  transaction_id, script_public_key_address, amount, block_time
FROM
  (
    SELECT
      inputs.transaction_id,
      outputs.script_public_key_address,
      outputs.amount - SUM(prev_output.amount) as amount,
      outputs.block_time
    FROM
      (
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
          500
      ) as outputs
      LEFT JOIN transactions_inputs as inputs ON inputs.transaction_id = outputs.transaction_id
      LEFT JOIN transactions_outputs as prev_output ON inputs.previous_outpoint_hash = prev_output.transaction_id
    WHERE
      prev_output.script_public_key_address = outputs.script_public_key_address
    GROUP BY
      inputs.transaction_id,
      outputs.script_public_key_address,
      outputs.amount,
      outputs.block_time
  ) as final_table
WHERE
  TRUE
  AND final_table.amount > 1 * 1e6 * 1e8