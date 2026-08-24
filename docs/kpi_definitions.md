# KPI Definitions

The Power BI measure names, business definitions, and independent SQL validation assets used by the project.

| kpi_name                    | formula                                          | business_definition                                            | format       | validation_asset                                   |
|:----------------------------|:-------------------------------------------------|:---------------------------------------------------------------|:-------------|:---------------------------------------------------|
| Total Revenue               | SUM(fact_sales[net_sales_amount])                | Net sales after line discount; excludes tax.                   | Currency     | sql/sqlserver/analytics/kpi_validation_queries.sql |
| Gross Profit                | SUM(fact_sales[gross_profit_amount])             | Net sales minus cost of goods sold.                            | Currency     | sql/sqlserver/analytics/kpi_validation_queries.sql |
| Gross Margin Percentage     | DIVIDE([Gross Profit], [Total Revenue])          | Gross profit divided by net sales.                             | Percentage   | sql/sqlserver/analytics/kpi_validation_queries.sql |
| Orders                      | DISTINCTCOUNT(fact_sales[order_id])              | Distinct orders represented by valid sales lines.              | Whole number | sql/sqlserver/analytics/kpi_validation_queries.sql |
| Units Sold                  | SUM(fact_sales[quantity])                        | Valid sold item quantity.                                      | Whole number | sql/sqlserver/analytics/kpi_validation_queries.sql |
| Average Order Value         | DIVIDE([Total Revenue], [Orders])                | Average net revenue per distinct order.                        | Currency     | sql/sqlserver/analytics/kpi_validation_queries.sql |
| Returned Units              | SUM(fact_returns[return_quantity])               | Accepted returned quantity.                                    | Whole number | sql/sqlserver/analytics/kpi_validation_queries.sql |
| Return Rate                 | DIVIDE([Returned Units], [Units Sold])           | Returned units divided by sold units in filter context.        | Percentage   | sql/sqlserver/analytics/kpi_validation_queries.sql |
| On-Time Delivery Percentage | DIVIDE(on-time shipments, shipments)             | Delivered on/before promised date divided by shipments.        | Percentage   | sql/sqlserver/analytics/kpi_validation_queries.sql |
| Marketing Spend             | SUM(fact_marketing_spend[spend_amount])          | Recorded campaign spend.                                       | Currency     | sql/sqlserver/analytics/kpi_validation_queries.sql |
| Web Sessions                | SUM(fact_web_sessions[session_count])            | Website sessions.                                              | Whole number | sql/sqlserver/analytics/kpi_validation_queries.sql |
| Conversion Rate             | DIVIDE(converted sessions, web sessions)         | Sessions linked to an order divided by sessions.               | Percentage   | sql/sqlserver/analytics/kpi_validation_queries.sql |
| Attributed Revenue          | Revenue for distinct converted session order IDs | Simplified converting-session attribution; not causal lift.    | Currency     | powerbi/measures.dax                               |
| Return on Ad Spend          | DIVIDE([Attributed Revenue], [Marketing Spend])  | Attributed revenue divided by spend under the documented rule. | Decimal      | powerbi/measures.dax                               |
| Inventory On Hand           | SUM(fact_inventory_snapshot[quantity_on_hand])   | On-hand units; use one snapshot date.                          | Whole number | sql/sqlserver/analytics/kpi_validation_queries.sql |
| Stockout Risk Count         | Count rows where stockout_risk_flag is true      | Store-product snapshot rows at or below reorder threshold.     | Whole number | sql/sqlserver/analytics/kpi_validation_queries.sql |
