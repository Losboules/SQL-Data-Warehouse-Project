# LinkedIn Post Draft

I have been building **Northstar Retail**, a fictional end-to-end data engineering portfolio project designed to teach me the decisions behind the tools—not just give me code to copy.

The project connects synthetic SQL Server ERP data, PostgreSQL website/marketing data, and CSV/JSON feeds. I use Python for reproducible data generation and batch manifests, Databricks and Delta Lake for Bronze/Silver/Gold processing, Lakeflow Jobs for dependencies and quality gates, SQL Server as a serving warehouse, and Power BI for the semantic and reporting layer.

The most important lessons so far:

- A fact table must have one explicit grain before measures are written.
- A cloud workspace cannot reach my computer's `localhost`, so the beginner track uses an honest manual file handoff.
- Dirty data is useful when it is controlled: it lets me prove deduplication, quarantine, date parsing, SCD Type 2, and rerun behavior.
- A dashboard number is not trustworthy until it reconciles to source rules and independent SQL.

Verified evidence from my run:

- Batch: `[ADD VERIFIED BATCH ID]`
- Required quality checks passed: `[ADD VERIFIED COUNT]`
- Revenue reconciliation difference: `[ADD VERIFIED DIFFERENCE]`
- Same-batch rerun duplicate difference: `[ADD VERIFIED RESULT]`

Next I am improving `[ADD REAL NEXT STEP]`.

#DataEngineering #SQL #Python #Databricks #DeltaLake #PowerBI #DataWarehouse #PortfolioProject
