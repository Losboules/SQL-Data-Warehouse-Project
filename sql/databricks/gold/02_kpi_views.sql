-- Dialect: Databricks SQL / Spark SQL
CREATE OR REPLACE VIEW IDENTIFIER(:catalog || '.gold_semantic.executive_daily_kpi') AS
SELECT
  d.full_date,
  SUM(f.net_sales_amount) AS total_revenue,
  SUM(f.gross_profit_amount) AS gross_profit,
  COUNT(DISTINCT f.order_id) AS orders,
  SUM(f.quantity) AS units_sold,
  SUM(f.net_sales_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS average_order_value
FROM IDENTIFIER(:catalog || '.gold.fact_sales') AS f
JOIN IDENTIFIER(:catalog || '.gold.dim_date') AS d ON d.date_key = f.order_date_key
GROUP BY d.full_date;
