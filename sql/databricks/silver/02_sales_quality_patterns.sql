-- Dialect: Databricks SQL / Spark SQL
SELECT
  order_item_id,
  CAST(quantity AS INT) AS quantity,
  CAST(unit_price AS DECIMAL(12,2)) AS unit_price,
  CAST(discount_amount AS DECIMAL(12,2)) AS discount_amount,
  CAST(quantity AS INT) * CAST(unit_price AS DECIMAL(12,2)) AS gross_sales_amount,
  CAST(quantity AS INT) * CAST(unit_price AS DECIMAL(12,2)) - CAST(discount_amount AS DECIMAL(12,2)) AS net_sales_amount
FROM IDENTIFIER(:bronze_order_item_table)
WHERE CAST(quantity AS INT) > 0;
