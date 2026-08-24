# Power BI Report Requirements

No actual performance values are included. Replace every placeholder only after running and validating your pipeline.

| Page | Audience | Business question | Fields/KPIs | Slicers | Visuals | Drill-through | Validation | Misleading choice to avoid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Executive Overview | Executives | Are revenue, profit, orders, delivery, and returns on track? | Revenue, gross profit, margin, orders, AOV, return rate, on-time delivery; monthly trend; channel mix | Date, region, channel | KPI cards, line chart, decomposition or bar chart | Sales Performance | Validate every KPI card to SQL; verify date slicer affects all visuals | Do not use a pie chart with many categories or a truncated trend axis. |
| Sales Performance | Sales leadership | Where are sales and profit growing or declining? | Revenue/profit by month, channel, store, region; order and AOV trends | Date, channel, region, store | Lines, clustered bars, matrix, waterfall for change | Order detail or Store and Region | Check totals and drill rows against semantic.vw_sales_detail | Do not mix revenue and margin percentages on one unlabeled axis. |
| Product and Category | Merchandising | Which products and categories drive profitable demand? | Revenue, units, gross profit, margin, discount by SKU/category | Date, category, brand, supplier | Treemap only for high-level mix, bars, scatter price vs margin, matrix | Product detail | Validate top N against analyst query 07 | Top revenue is not automatically top profit. |
| Store and Region | Retail operations | Which stores and regions outperform after accounting for volume? | Revenue, profit, orders, AOV, return rate by store/region | Date, region, store | Map only if location quality is verified; bars and matrix preferred | Store detail | Compare a selected store to SQL query 03 | Avoid maps that imply area size equals performance. |
| Customer | CRM and leadership | How many new and returning customers buy, and how do segments behave? | New/returning, purchasing customers, revenue by tier/state | Date, loyalty tier, state | Cards, cohort-style matrix, bars | Customer history | Inspect first purchase dates for sample customers | Do not label signup as acquisition unless business definition says so. |
| Marketing Funnel | Marketing | Which channels and campaigns create efficient, attributable conversion? | Spend, sessions, conversion, attributed revenue, ROAS | Date, channel, campaign, device | Funnel, scatter spend vs revenue, campaign table | Campaign detail | Verify converted order IDs are unique before ROAS | Correlation and last-touch attribution are not causation. |
| Inventory | Inventory operations | Which store-product combinations are at stockout risk? | On hand, available, inventory value, risk count | Snapshot date, region, store, category | Cards, heatmap/matrix, ranked bars | Product-store detail | Use one snapshot date; recompute risk formula | Never sum snapshot stock across dates. |
| Shipping and Returns | Operations and CX | Where are delivery delays and returns concentrated? | On-time %, delivery days, returned units, return rate, refund amount | Ship/return date, carrier, region, reason | Cards, bars, distribution, matrix | Shipment/order detail | Sample promised vs actual dates and returned lines | Do not compare shipment count directly with order count without split-shipment context. |
| Data Quality | Data engineering and owners | Can decision-makers trust the latest batch? | Pass/fail, quarantines, unknown keys, freshness, reconciliation differences | Batch, date, source, rule | Status cards, rule table, trend | Batch detail | Compare to quality.test_results and audit.reconciliation_result | A green dashboard is meaningless if failed tests were filtered out. |

## Suggested executive wireframe

```text
+--------------------------------------------------------------------------------+
| Northstar Retail — Executive Overview       [Date] [Region] [Channel]           |
+-----------+-----------+-----------+-----------+-----------+--------------------+
| Revenue   | Gross     | Margin %  | Orders    | AOV       | On-time / Returns  |
| [VERIFY]  | [VERIFY]  | [VERIFY]  | [VERIFY]  | [VERIFY]  | [VERIFY]           |
+---------------------------------------------+----------------------------------+
| Monthly Revenue and Gross Profit Trend      | Revenue / Profit by Channel      |
| [YOUR VERIFIED VISUAL]                      | [YOUR VERIFIED VISUAL]           |
+---------------------------------------------+----------------------------------+
| Top/Bottom Category or Store                | Alerts: Stockout / DQ / Shipping |
| [YOUR VERIFIED VISUAL]                      | [YOUR VERIFIED VISUAL]           |
+--------------------------------------------------------------------------------+
```
