-- Dialect: SQL Server / T-SQL
-- Independent SQL checks used to validate Power BI measures.
USE NorthstarRetail_DW;
GO
SELECT SUM(net_sales_amount) AS Total_Revenue FROM dw.fact_sales;
SELECT SUM(gross_profit_amount) AS Gross_Profit FROM dw.fact_sales;
SELECT SUM(gross_profit_amount)/NULLIF(SUM(net_sales_amount),0) AS Gross_Margin_Ratio FROM dw.fact_sales;
SELECT COUNT(DISTINCT order_id) AS Orders FROM dw.fact_sales;
SELECT SUM(quantity) AS Units_Sold FROM dw.fact_sales;
SELECT SUM(net_sales_amount)/NULLIF(COUNT(DISTINCT order_id),0) AS Average_Order_Value FROM dw.fact_sales;
SELECT 1.0*SUM(return_quantity)/NULLIF((SELECT SUM(quantity) FROM dw.fact_sales),0) AS Return_Rate FROM dw.fact_returns;
SELECT 1.0*SUM(CASE WHEN on_time_flag=1 THEN 1 ELSE 0 END)/NULLIF(COUNT_BIG(*),0) AS On_Time_Delivery_Rate FROM dw.fact_shipments;
SELECT SUM(spend_amount) AS Marketing_Spend FROM dw.fact_marketing_spend;
SELECT 1.0*SUM(CASE WHEN converted_flag=1 THEN 1 ELSE 0 END)/NULLIF(SUM(session_count),0) AS Conversion_Rate FROM dw.fact_web_sessions;
SELECT SUM(quantity_on_hand) AS Inventory_On_Hand, SUM(CASE WHEN stockout_risk_flag=1 THEN 1 ELSE 0 END) AS Stockout_Risk_Count FROM dw.fact_inventory_snapshot;
-- Promotion Gross Profit by promotion. This is contribution, not causal incremental lift.
SELECT
    p.promotion_code,
    p.promotion_name,
    SUM(s.gross_profit_amount) AS Promotion_Gross_Profit
FROM dw.fact_sales AS s
INNER JOIN dw.dim_promotion AS p
    ON p.promotion_key = s.promotion_key
WHERE s.promotion_key <> 0
GROUP BY p.promotion_code, p.promotion_name
ORDER BY Promotion_Gross_Profit DESC;
