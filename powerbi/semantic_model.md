# Power BI Semantic Model

## Model rule

Use a star schema. Every relationship normally filters from one dimension to one fact in a single direction. Avoid fact-to-fact relationships and bidirectional filtering unless you can explain and test the ambiguity it introduces.

## Relationships

| From dimension column | To fact column | Cardinality | Cross-filter | Active? |
|---|---|---|---|---|
| dim_date[date_key] | fact_sales[order_date_key] | One-to-many | Single | Yes |
| dim_date[date_key] | fact_returns[return_date_key] | One-to-many | Single | Yes |
| dim_date[date_key] | fact_inventory_snapshot[snapshot_date_key] | One-to-many | Single | Yes |
| dim_date[date_key] | fact_shipments[ship_date_key] | One-to-many | Single | Yes |
| dim_date[date_key] | fact_shipments[promised_date_key] | One-to-many | Single | No |
| dim_date[date_key] | fact_shipments[delivery_date_key] | One-to-many | Single | No |
| dim_date[date_key] | fact_web_sessions[session_date_key] | One-to-many | Single | Yes |
| dim_date[date_key] | fact_marketing_spend[spend_date_key] | One-to-many | Single | Yes |
| dim_customer[customer_key] | fact_sales[customer_key] | One-to-many | Single | Yes |
| dim_customer[customer_key] | fact_shipments[customer_key] | One-to-many | Single | Yes |
| dim_customer[customer_key] | fact_web_sessions[customer_key] | One-to-many | Single | Yes |
| dim_customer[customer_key] | fact_returns[customer_key] | One-to-many | Single | Yes |
| dim_product[product_key] | fact_sales[product_key] | One-to-many | Single | Yes |
| dim_product[product_key] | fact_returns[product_key] | One-to-many | Single | Yes |
| dim_product[product_key] | fact_inventory_snapshot[product_key] | One-to-many | Single | Yes |
| dim_employee[employee_key] | fact_sales[employee_key] | One-to-many | Single | Yes |
| dim_promotion[promotion_key] | fact_sales[promotion_key] | One-to-many | Single | Yes |
| dim_store[store_key] | sales/returns/inventory/shipments store_key | One-to-many | Single | Yes |
| dim_channel[channel_key] | sales/web_sessions/marketing_spend channel_key | One-to-many | Single | Yes |
| dim_campaign[campaign_key] | web_sessions/marketing_spend campaign_key | One-to-many | Single | Yes |
| dim_supplier[supplier_code] | dim_product[supplier_code] | One-to-many | Single | Yes — documented snowflake exception |

### Supplier relationship note

`dim_supplier` is the one documented snowflake exception in the beginner model because the required facts do not carry a supplier key. Supplier filters travel through `dim_product`. Verify `dim_supplier[supplier_code]` is unique, keep the relationship single-direction, and do not add a second supplier-to-fact path. A larger production model may denormalize supplier attributes into `dim_product` or add supplier keys to appropriate procurement/inventory facts.

## Date table

In Model view, select `dim_date`, then **Table tools > Mark as date table > Mark as date table**, choose `full_date`, and confirm. Sort `month_name` by `month_number`. Create a hierarchy: `calendar_year > quarter_number > month_name > full_date`.

## Hidden technical columns

Hide surrogate keys from report view after relationships are correct: all `*_key` columns, batch ID, record hash, load timestamp, source system, SCD effective dates unless an audit page needs them. Do not delete them from the model.

## Display folders and formats

- `_Measures\Sales`: Total Revenue, Gross Profit, Gross Margin %, Promotion Gross Profit, Orders, Units Sold, Average Order Value.
- `_Measures\Returns and Shipping`: Return Rate, On-Time Delivery %.
- `_Measures\Marketing`: Marketing Spend, Attributed Revenue, Return on Ad Spend, Conversion Rate.
- `_Measures\Customer`: Purchasing Customers, New Customers, Returning Customers.
- `_Measures\Inventory`: Inventory On Hand, Stockout Risk Count.

Format money as currency with two decimals, counts as whole numbers with thousands separators, and rates as percentages with one or two decimals. Add the business definition from `docs/kpi_definitions.md` to each measure's Description property.

## Import versus DirectQuery decision

Use **Import** for Track A: the local warehouse is modest, development is faster, and you can control refresh manually. DirectQuery is an advanced choice when near-real-time access, data volume, governance, and capacity justify the latency and modeling tradeoffs. Record the choice in `docs/assumption_log.md`.

## Attribution warning

The included `Attributed Revenue` measure uses converting session order IDs, equivalent to a simplified last-converting-session link. It is not a multi-touch causal model. Test that an order ID appears once before presenting ROAS.
