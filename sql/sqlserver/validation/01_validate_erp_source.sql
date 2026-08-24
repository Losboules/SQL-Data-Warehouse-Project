-- Dialect: SQL Server / T-SQL
-- Run in: SSMS, NorthstarRetail_ERP.
USE NorthstarRetail_ERP;
GO

-- Row counts. Replace expected values with the generation summary for your chosen scale.
SELECT 'customers' AS table_name, COUNT_BIG(*) AS row_count FROM erp.customers
UNION ALL SELECT 'orders', COUNT_BIG(*) FROM erp.orders
UNION ALL SELECT 'order_items', COUNT_BIG(*) FROM erp.order_items
UNION ALL SELECT 'products', COUNT_BIG(*) FROM erp.products
UNION ALL SELECT 'shipments', COUNT_BIG(*) FROM erp.shipments;

-- Referential integrity checks should return zero because source foreign keys are enabled.
SELECT COUNT_BIG(*) AS orphan_order_customers
FROM erp.orders AS o
LEFT JOIN erp.customers AS c ON c.customer_id = o.customer_id
WHERE c.customer_id IS NULL;

SELECT COUNT_BIG(*) AS orphan_order_items
FROM erp.order_items AS oi
LEFT JOIN erp.orders AS o ON o.order_id = oi.order_id
WHERE o.order_id IS NULL;

-- Controlled dirty-data observations; nonzero values are expected in the learning dataset.
SELECT COUNT_BIG(*) AS null_or_malformed_emails
FROM erp.customers
WHERE email IS NULL OR email NOT LIKE '%_@_%._%';

SELECT COUNT_BIG(*) AS impossible_quantities
FROM erp.order_items
WHERE quantity <= 0;

SELECT customer_number, COUNT_BIG(*) AS duplicate_count
FROM erp.customers
GROUP BY customer_number
HAVING COUNT_BIG(*) > 1;
