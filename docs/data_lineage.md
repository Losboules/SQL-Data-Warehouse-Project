# Data Lineage

Lineage answers, “Where did this number come from?” The project records technical lineage through source names, file paths, batch IDs, load timestamps, record hashes, task order, source-to-target mapping, and reconciliation results.

## Example: Total Revenue

1. `SQLSERVER_ERP.erp.order_items.quantity`, `unit_price`, and `discount_amount` are extracted to a batch Parquet file.
2. Bronze preserves source values and adds `_source_file`, `_batch_id`, `_ingested_at_utc`, and `_record_hash`.
3. Silver casts numeric fields, quarantines quantity `<= 0`, joins valid order context, and derives `net_sales_amount`.
4. Gold stores one row per valid order item in `fact_sales` and resolves dimension keys.
5. The local publisher stages and transactionally loads `dw.fact_sales`.
6. Power BI measure `[Total Revenue]` sums `fact_sales[net_sales_amount]` under the current filter context.
7. The SQL validation query independently sums the same column.

![Lineage diagram](images/lineage.svg)

## Evidence to retain per run

- Local extraction `batch_manifest.json` with row counts and SHA-256 checksums.
- Databricks job run ID and task logs.
- Bronze/Silver/Gold row-count and rejection results.
- `quality.test_results` rows.
- Gold export manifest.
- SQL Server `audit.etl_batch` and `audit.reconciliation_result` rows.
- Power BI refresh timestamp and validation screenshot.
