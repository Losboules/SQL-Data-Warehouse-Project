-- Dialect: SQL Server / T-SQL
-- Purpose: twenty completed, portfolio-ready analyst queries over NorthstarRetail_DW.
USE NorthstarRetail_DW;
GO

-- 01. Revenue by month.
SELECT d.calendar_year, d.month_number, d.month_name,
       SUM(f.net_sales_amount) AS revenue
FROM dw.fact_sales AS f
JOIN dw.dim_date AS d ON d.date_key = f.order_date_key
GROUP BY d.calendar_year, d.month_number, d.month_name
ORDER BY d.calendar_year, d.month_number;

-- 02. Gross profit by category.
SELECT p.category_name, SUM(f.gross_profit_amount) AS gross_profit
FROM dw.fact_sales AS f
JOIN dw.dim_product AS p ON p.product_key = f.product_key
GROUP BY p.category_name
ORDER BY gross_profit DESC;

-- 03. Store revenue, order count, profit, and gross margin.
SELECT s.store_code, s.store_name, s.region,
       SUM(f.net_sales_amount) AS revenue,
       COUNT(DISTINCT f.order_id) AS order_count,
       SUM(f.gross_profit_amount) AS gross_profit,
       SUM(f.gross_profit_amount) / NULLIF(SUM(f.net_sales_amount), 0) AS gross_margin_ratio
FROM dw.fact_sales AS f
JOIN dw.dim_store AS s ON s.store_key = f.store_key
GROUP BY s.store_code, s.store_name, s.region
ORDER BY revenue DESC;

-- 04. Online versus store average order value.
SELECT c.channel_name,
       SUM(f.net_sales_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS average_order_value
FROM dw.fact_sales AS f
JOIN dw.dim_channel AS c ON c.channel_key = f.channel_key
GROUP BY c.channel_name
ORDER BY average_order_value DESC;

-- 05. Returned units divided by sold units at compatible category grain.
WITH sold AS
(
    SELECT p.category_name, SUM(s.quantity) AS sold_quantity
    FROM dw.fact_sales AS s
    JOIN dw.dim_product AS p ON p.product_key = s.product_key
    GROUP BY p.category_name
),
returned AS
(
    SELECT p.category_name, SUM(r.return_quantity) AS returned_quantity
    FROM dw.fact_returns AS r
    JOIN dw.dim_product AS p ON p.product_key = r.product_key
    GROUP BY p.category_name
)
SELECT s.category_name,
       s.sold_quantity,
       COALESCE(r.returned_quantity, 0) AS returned_quantity,
       1.0 * COALESCE(r.returned_quantity, 0) / NULLIF(s.sold_quantity, 0) AS return_rate
FROM sold AS s
LEFT JOIN returned AS r ON r.category_name = s.category_name
ORDER BY return_rate DESC, s.category_name;

-- 06. On-time delivery percentage by carrier.
SELECT carrier,
       100.0 * SUM(CASE WHEN on_time_flag = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT_BIG(*), 0) AS on_time_pct
FROM dw.fact_shipments
GROUP BY carrier
ORDER BY on_time_pct DESC;

-- 07. Top ten products by units sold.
SELECT TOP (10) p.sku, p.product_name, SUM(f.quantity) AS units
FROM dw.fact_sales AS f
JOIN dw.dim_product AS p ON p.product_key = f.product_key
GROUP BY p.sku, p.product_name
ORDER BY units DESC, p.sku;

-- 08. Products with negative gross profit in the latest twelve calendar months present.
DECLARE @max_sales_date date = (SELECT MAX(d.full_date) FROM dw.fact_sales f JOIN dw.dim_date d ON d.date_key = f.order_date_key);
SELECT p.sku, p.product_name, SUM(f.gross_profit_amount) AS gross_profit
FROM dw.fact_sales AS f
JOIN dw.dim_product AS p ON p.product_key = f.product_key
JOIN dw.dim_date AS d ON d.date_key = f.order_date_key
WHERE d.full_date >= DATEADD(month, -12, @max_sales_date)
GROUP BY p.sku, p.product_name
HAVING SUM(f.gross_profit_amount) < 0
ORDER BY gross_profit;

-- 09. Discount amount and revenue by promotion.
SELECT pr.promotion_code, pr.promotion_name,
       SUM(f.discount_amount) AS discount_amount,
       SUM(f.net_sales_amount) AS revenue
FROM dw.fact_sales AS f
JOIN dw.dim_promotion AS pr ON pr.promotion_key = f.promotion_key
GROUP BY pr.promotion_code, pr.promotion_name
ORDER BY discount_amount DESC;

-- 10. New customers by signup month, deduplicating SCD2 versions by natural key.
WITH natural_customers AS
(
    SELECT customer_number, MIN(signup_date) AS signup_date
    FROM dw.dim_customer
    WHERE customer_key <> 0
    GROUP BY customer_number
)
SELECT YEAR(signup_date) AS signup_year, MONTH(signup_date) AS signup_month,
       COUNT_BIG(*) AS new_customers
FROM natural_customers
WHERE signup_date IS NOT NULL
GROUP BY YEAR(signup_date), MONTH(signup_date)
ORDER BY signup_year, signup_month;

-- 11. Returning purchasing customers by month: a sale after the customer's first order date.
WITH customer_orders AS
(
    SELECT customer_key, order_id, MIN(order_date_key) AS order_date_key
    FROM dw.fact_sales
    WHERE customer_key <> 0
    GROUP BY customer_key, order_id
),
first_order AS
(
    SELECT customer_key, MIN(order_date_key) AS first_order_date_key
    FROM customer_orders
    GROUP BY customer_key
)
SELECT d.calendar_year, d.month_number,
       COUNT(DISTINCT o.customer_key) AS returning_customers
FROM customer_orders AS o
JOIN first_order AS first_purchase ON first_purchase.customer_key = o.customer_key
JOIN dw.dim_date AS d ON d.date_key = o.order_date_key
WHERE o.order_date_key > first_purchase.first_order_date_key
GROUP BY d.calendar_year, d.month_number
ORDER BY d.calendar_year, d.month_number;

-- 12. Conversion rate by source channel.
SELECT c.channel_name,
       100.0 * SUM(CASE WHEN f.converted_flag = 1 THEN 1 ELSE 0 END) / NULLIF(SUM(f.session_count), 0) AS conversion_pct
FROM dw.fact_web_sessions AS f
JOIN dw.dim_channel AS c ON c.channel_key = f.channel_key
GROUP BY c.channel_name
ORDER BY conversion_pct DESC;

-- 13. Marketing spend and clicks by campaign.
SELECT c.campaign_code, c.campaign_name,
       SUM(f.spend_amount) AS spend,
       SUM(f.clicks) AS clicks
FROM dw.fact_marketing_spend AS f
JOIN dw.dim_campaign AS c ON c.campaign_key = f.campaign_key
GROUP BY c.campaign_code, c.campaign_name
ORDER BY spend DESC;

-- 14. Simplified converting-session attribution and return on ad spend (ROAS).
-- This is a deterministic reporting rule, not proof that the campaign caused the sale.
WITH attributed_orders AS
(
    SELECT DISTINCT campaign_key, converted_order_id
    FROM dw.fact_web_sessions
    WHERE campaign_key <> 0 AND converted_order_id IS NOT NULL
),
attributed_revenue AS
(
    SELECT a.campaign_key, SUM(s.net_sales_amount) AS attributed_revenue
    FROM attributed_orders AS a
    JOIN dw.fact_sales AS s ON s.order_id = a.converted_order_id
    GROUP BY a.campaign_key
),
campaign_spend AS
(
    SELECT campaign_key, SUM(spend_amount) AS spend_amount
    FROM dw.fact_marketing_spend
    GROUP BY campaign_key
)
SELECT c.campaign_code, c.campaign_name,
       COALESCE(r.attributed_revenue, 0) AS attributed_revenue,
       COALESCE(s.spend_amount, 0) AS spend_amount,
       COALESCE(r.attributed_revenue, 0) / NULLIF(s.spend_amount, 0) AS return_on_ad_spend
FROM dw.dim_campaign AS c
LEFT JOIN attributed_revenue AS r ON r.campaign_key = c.campaign_key
LEFT JOIN campaign_spend AS s ON s.campaign_key = c.campaign_key
WHERE c.campaign_key <> 0
ORDER BY return_on_ad_spend DESC;

-- 15. Stockout-risk products by store.
SELECT s.store_name, p.product_name, COUNT_BIG(*) AS risk_snapshot_count
FROM dw.fact_inventory_snapshot AS f
JOIN dw.dim_store AS s ON s.store_key = f.store_key
JOIN dw.dim_product AS p ON p.product_key = f.product_key
WHERE f.stockout_risk_flag = 1
GROUP BY s.store_name, p.product_name
ORDER BY risk_snapshot_count DESC;

-- 16. Inventory value by category for the most recent snapshot date only.
DECLARE @latest_snapshot_key int = (SELECT MAX(snapshot_date_key) FROM dw.fact_inventory_snapshot);
SELECT p.category_name, SUM(f.inventory_value_amount) AS inventory_value
FROM dw.fact_inventory_snapshot AS f
JOIN dw.dim_product AS p ON p.product_key = f.product_key
WHERE f.snapshot_date_key = @latest_snapshot_key
GROUP BY p.category_name
ORDER BY inventory_value DESC;

-- 17. Average delivery days by region.
SELECT s.region, AVG(1.0 * f.delivery_days) AS average_delivery_days
FROM dw.fact_shipments AS f
JOIN dw.dim_store AS s ON s.store_key = f.store_key
WHERE f.delivery_days IS NOT NULL
GROUP BY s.region
ORDER BY average_delivery_days;

-- 18. Customers whose descriptive attributes changed under SCD Type 2.
SELECT customer_number, COUNT_BIG(*) AS version_count,
       MIN(effective_start_date) AS first_version_start,
       MAX(effective_start_date) AS latest_version_start
FROM dw.dim_customer
WHERE customer_key <> 0
GROUP BY customer_number
HAVING COUNT_BIG(*) > 1
ORDER BY version_count DESC, customer_number;

-- 19. Sales using unknown dimension members.
SELECT
    SUM(CASE WHEN customer_key = 0 THEN 1 ELSE 0 END) AS unknown_customer_rows,
    SUM(CASE WHEN product_key = 0 THEN 1 ELSE 0 END) AS unknown_product_rows,
    SUM(CASE WHEN store_key = 0 THEN 1 ELSE 0 END) AS unknown_store_rows,
    SUM(CASE WHEN employee_key = 0 THEN 1 ELSE 0 END) AS unknown_employee_rows,
    SUM(CASE WHEN promotion_key = 0 THEN 1 ELSE 0 END) AS no_or_unknown_promotion_rows,
    SUM(CASE WHEN channel_key = 0 THEN 1 ELSE 0 END) AS unknown_channel_rows
FROM dw.fact_sales;

-- 20. Daily failed reconciliation checks.
SELECT CAST(checked_at_utc AS date) AS check_date, COUNT_BIG(*) AS failed_checks
FROM audit.reconciliation_result
WHERE status = 'FAIL'
GROUP BY CAST(checked_at_utc AS date)
ORDER BY check_date;
