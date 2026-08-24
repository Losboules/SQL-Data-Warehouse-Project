-- Dialect: SQL Server / T-SQL
-- Purpose: thin semantic access views for analysts and Power BI.
USE NorthstarRetail_DW;
GO

CREATE OR ALTER VIEW semantic.vw_sales_detail AS
SELECT
    fs.order_number,
    dd.full_date AS order_date,
    dc.customer_number,
    CONCAT(dc.first_name, ' ', dc.last_name) AS customer_name,
    dp.sku,
    dp.product_name,
    dp.category_name,
    ds.store_name,
    ds.region,
    dch.channel_name,
    fs.quantity,
    fs.net_sales_amount,
    fs.cost_of_goods_sold,
    fs.gross_profit_amount,
    fs.discount_amount,
    fs.tax_amount
FROM dw.fact_sales AS fs
JOIN dw.dim_date AS dd ON dd.date_key = fs.order_date_key
JOIN dw.dim_customer AS dc ON dc.customer_key = fs.customer_key
JOIN dw.dim_product AS dp ON dp.product_key = fs.product_key
JOIN dw.dim_store AS ds ON ds.store_key = fs.store_key
JOIN dw.dim_channel AS dch ON dch.channel_key = fs.channel_key;
GO

CREATE OR ALTER VIEW semantic.vw_executive_daily_kpi AS
SELECT
    dd.full_date,
    SUM(fs.net_sales_amount) AS total_revenue,
    SUM(fs.gross_profit_amount) AS gross_profit,
    COUNT(DISTINCT fs.order_id) AS orders,
    SUM(fs.quantity) AS units_sold,
    CAST(SUM(fs.net_sales_amount) / NULLIF(COUNT(DISTINCT fs.order_id), 0) AS DECIMAL(18,2)) AS average_order_value
FROM dw.fact_sales AS fs
JOIN dw.dim_date AS dd ON dd.date_key = fs.order_date_key
GROUP BY dd.full_date;
GO

CREATE OR ALTER VIEW semantic.vw_data_quality_monitor AS
SELECT batch_id, check_name, source_value, target_value, difference_value, status, checked_at_utc
FROM audit.reconciliation_result;
GO
