-- Dialect: SQL Server / T-SQL
USE NorthstarRetail_DW;
GO

-- Duplicate fact grain should be zero.
SELECT order_item_id, COUNT_BIG(*) AS duplicate_count
FROM dw.fact_sales GROUP BY order_item_id HAVING COUNT_BIG(*) > 1;

-- Orphan dimension keys should be zero; key 0 is valid and means Unknown.
SELECT COUNT_BIG(*) AS orphan_customer_keys
FROM dw.fact_sales f LEFT JOIN dw.dim_customer d ON d.customer_key=f.customer_key
WHERE d.customer_key IS NULL;

-- SCD2 dimensions: no more than one current row per business key.
SELECT customer_number, COUNT_BIG(*) AS current_count
FROM dw.dim_customer WHERE is_current=1
GROUP BY customer_number HAVING COUNT_BIG(*) > 1;

SELECT sku, COUNT_BIG(*) AS current_count
FROM dw.dim_product WHERE is_current=1
GROUP BY sku HAVING COUNT_BIG(*) > 1;

-- Revenue identity: net sales equals gross minus discount.
SELECT COUNT_BIG(*) AS invalid_revenue_rows
FROM dw.fact_sales
WHERE ABS(net_sales_amount - (gross_sales_amount - discount_amount)) > 0.01;

-- Inspect the most recent ETL and reconciliation results.
SELECT TOP (20) * FROM audit.etl_batch ORDER BY started_at_utc DESC;
SELECT TOP (50) * FROM audit.reconciliation_result ORDER BY checked_at_utc DESC;
