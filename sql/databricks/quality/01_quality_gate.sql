-- Dialect: Databricks SQL / Spark SQL
-- These assertion queries should each return zero failed rows.
SELECT COUNT(*) AS duplicate_order_item_rows
FROM (
  SELECT order_item_id FROM IDENTIFIER(:fact_sales_table)
  GROUP BY order_item_id HAVING COUNT(*) > 1
);

SELECT COUNT(*) AS invalid_revenue_identity_rows
FROM IDENTIFIER(:fact_sales_table)
WHERE abs(net_sales_amount - (gross_sales_amount - discount_amount)) > 0.01;
