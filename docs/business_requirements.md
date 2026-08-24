# Business Requirements

## Company background

Northstar Retail is a fictional omnichannel retailer with physical stores and an e-commerce website. Its operational sales, customer, product, employee, shipment, and inventory data live in SQL Server. Website behavior and marketing activity live in PostgreSQL. Returns, supplier cost changes, promotions, and tracking events arrive as files.

## Business problem

Leadership has inconsistent reports because sales, customers, inventory, website behavior, marketing, shipments, and returns live in separate systems. The company needs a governed data platform that produces trusted daily metrics and supports executive, sales, operations, marketing, and customer analysis.

## Stakeholders

| Stakeholder | Decision | Needed information | Primary concern |
|---|---|---|---|
| Chief Executive Officer | Overall business direction | Revenue, profit, customer, operations health | One trusted summary |
| Finance leader | Profitability and reconciliation | Revenue, COGS, gross profit, discounts, refunds | Definitions and tie-outs |
| Sales leader | Channel/store performance | Orders, AOV, revenue, margin | Comparable stores and channels |
| Merchandising | Product and category choices | Units, margin, discount, return rate | Product-level grain |
| Marketing | Campaign allocation | Spend, sessions, conversion, attributed revenue | Attribution assumptions |
| Operations | Inventory and shipping | On hand, risk, delivery performance | Timeliness and exceptions |
| Customer experience | Returns and delays | Return reasons, late shipments | Traceable order detail |
| Data engineering | Reliability | Freshness, quality, lineage, rerun safety | Recoverable batches |
| Analysts | Self-service reporting | Star schema and semantic measures | Clear definitions |

## User stories

- As an executive, I need a daily overview so I can identify material changes without reconciling multiple reports.
- As a finance analyst, I need line-level revenue and cost logic so I can reproduce gross profit.
- As a store leader, I need store and region comparisons so I can investigate underperformance.
- As a marketer, I need spend, sessions, and converting orders joined under a documented attribution rule.
- As an inventory planner, I need latest store-product stock and reorder thresholds so I can prioritize replenishment.
- As a data engineer, I need batch manifests, tests, quarantine records, and idempotent tasks so failed loads can be repaired safely.

## Business questions

1. How much revenue and gross profit are we generating?
2. Which products, categories, stores, regions, and channels perform best?
3. What is average order value?
4. What is the return rate?
5. What percentage of delivered shipments arrive on time?
6. Which promotions create profitable sales?
7. How does website activity convert into orders?
8. How effective is marketing spend by channel and campaign?
9. Which products are at risk of stocking out?
10. How many new versus returning customers do we have?

Definitions and validation methods are in [`kpi_definitions.md`](kpi_definitions.md).

## Freshness targets

| Data domain | Target for this portfolio | Reason |
|---|---|---|
| Sales/orders/payments | Daily by 8:00 AM local reporting time | Executive and store reporting |
| Shipments/returns | Daily by 9:00 AM | Operations and customer experience |
| Inventory snapshot | Daily after source snapshot closes | Avoid summing partial snapshots |
| Website events/sessions | Daily | Batch learning scope |
| Marketing spend | Daily when feed is available | Campaign pacing |
| Power BI | Refresh only after warehouse publication succeeds | Prevent partial reports |

These are learning objectives, not measured service-level agreements until you schedule and observe several verified runs.

## Data-quality expectations

- Required keys are not null in trusted tables.
- Fact grain is unique.
- Dimension references resolve or intentionally use unknown key `0`.
- Sales arithmetic reconciles within one cent per row.
- Source manifests tie to Bronze accepted plus unreadable records.
- Bronze ties to Silver valid plus quarantined records.
- Silver ties to Gold under documented filtering/deduplication rules.
- Currency is USD in the beginner path; non-USD rows are quarantined until conversion is designed.
- Dates are parseable, event order is plausible, and timestamps are normalized to UTC.
- No required quality check is hidden or filtered out before publication.

## Security assumptions

- All data is synthetic, but customer-like fields are treated as synthetic PII for practice.
- Local credentials belong only in `.env`, which is ignored by Git.
- Databricks credentials belong in secret management or supported identity mechanisms, never notebooks.
- Analysts receive read-only access to serving schemas/views.
- Screenshots must not expose passwords, tokens, connection strings, personal workspace email, or local paths unnecessarily.

## Success criteria

The project is successful only when Kirolos has personally verified the gates in the final definition-of-done section in this workbook, can reproduce KPI values in SQL and Power BI, can explain every major design choice, and has screenshot/run evidence. Files existing in Git are not proof of execution.

## Out of scope for the required path

- Real customer data, production operations, or legal compliance certification.
- Streaming, CDC, Kafka, production IaC, or automated cloud networking.
- Multi-currency conversion and financial accounting close.
- Causal campaign attribution.
- A fabricated `.pbix` file or fabricated Databricks run.
- Production-scale performance claims.

## Assumption log template

| ID | Assumption | Why | How to test or revisit | Status |
|---|---|---|---|---|
| A-001 | USD is the reporting currency in Track A | Keeps beginner calculations interpretable | Add FX source and effective-rate rules in an extension | Accepted for Track A |
| A-002 | One sales fact row equals one valid order item | Supports additive revenue and product analysis | Run grain uniqueness and source reconciliation | Must verify |
| A-003 | A shipment is on time when actual date <= promised date | Common operational definition | Confirm business owner treatment of missing dates | Must verify |
| A-004 | Converting session order ID provides simplified attribution | Source has a direct link for some sessions | Check duplicate order links; document last-session limitation | Must verify |
| A-005 | Manual upload/download is acceptable for learning | Avoids unsupported localhost connectivity claims | Move to Track B only with network-accessible sources | Accepted for Track A |
