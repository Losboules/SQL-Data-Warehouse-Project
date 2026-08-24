-- Dialect: Databricks SQL / Spark SQL
-- Tiny teaching example: clean and rank duplicate business keys.
WITH cleaned AS (
  SELECT
    upper(trim(customer_number)) AS customer_number,
    initcap(trim(first_name)) AS first_name,
    lower(trim(email)) AS email,
    updated_at,
    row_number() OVER (
      PARTITION BY upper(trim(customer_number))
      ORDER BY updated_at DESC, customer_id DESC
    ) AS business_key_rank
  FROM IDENTIFIER(:bronze_customer_table)
)
SELECT * FROM cleaned WHERE business_key_rank = 1;
