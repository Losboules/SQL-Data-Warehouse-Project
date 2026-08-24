# Databricks notebook source
# Northstar Retail End-to-End Data Platform

# COMMAND ----------
# MAGIC %md
# MAGIC # 11 — Publish validated Gold exports
# MAGIC Writes all nine dimensions and six facts to a batch-named volume folder only after the required quality gate passes.

# COMMAND ----------
from __future__ import annotations

from datetime import datetime, timezone

from pyspark.sql import functions as F

for name, default in {
    "catalog": "northstar_retail",
    "landing_schema": "landing",
    "gold_schema": "gold",
    "quality_schema": "quality",
    "volume": "track_a_files",
    "batch_id": "MANUAL-REPLACE-ME",
}.items():
    dbutils.widgets.text(name, default)

catalog = dbutils.widgets.get("catalog")
landing_schema = dbutils.widgets.get("landing_schema")
gold_schema = dbutils.widgets.get("gold_schema")
quality_schema = dbutils.widgets.get("quality_schema")
volume = dbutils.widgets.get("volume")
batch_id = dbutils.widgets.get("batch_id")
if batch_id == "MANUAL-REPLACE-ME":
    raise ValueError("Pass batch_id from the Lakeflow Job or set the widget manually.")

results_name = f"{catalog}.{quality_schema}.test_results"
if not spark.catalog.tableExists(results_name):
    raise RuntimeError(f"Quality result table does not exist: {results_name}")
failed = (
    spark.table(results_name)
    .filter((F.col("batch_id") == batch_id) & F.col("required_flag") & (F.col("status") == "FAIL"))
    .count()
)
if failed:
    raise AssertionError(f"Publication blocked: {failed} required quality checks failed for {batch_id}")

# COMMAND ----------
tables = [
    "dim_date",
    "dim_customer",
    "dim_product",
    "dim_store",
    "dim_employee",
    "dim_supplier",
    "dim_promotion",
    "dim_channel",
    "dim_campaign",
    "fact_sales",
    "fact_returns",
    "fact_inventory_snapshot",
    "fact_shipments",
    "fact_web_sessions",
    "fact_marketing_spend",
]
export_root = f"/Volumes/{catalog}/{landing_schema}/{volume}/gold_exports/{batch_id}"
manifest_rows = []
for table_name in tables:
    full_name = f"{catalog}.{gold_schema}.{table_name}"
    if not spark.catalog.tableExists(full_name):
        raise RuntimeError(f"Required Gold table does not exist: {full_name}")
    frame = spark.table(full_name)
    row_count = frame.count()
    if row_count == 0:
        raise AssertionError(f"Required Gold table is empty: {full_name}")
    target_path = f"{export_root}/{table_name}.parquet"
    frame.write.mode("overwrite").parquet(target_path)
    manifest_rows.append((batch_id, table_name, target_path, row_count, datetime.now(timezone.utc)))

manifest = spark.createDataFrame(
    manifest_rows,
    ["batch_id", "table_name", "export_path", "row_count", "exported_at_utc"],
)
manifest.coalesce(1).write.mode("overwrite").json(f"{export_root}/_manifest")
manifest.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(
    f"{catalog}.{quality_schema}.gold_export_manifest"
)
display(manifest.orderBy("table_name"))
dbutils.jobs.taskValues.set(key="gold_export_root", value=export_root)
dbutils.jobs.taskValues.set(key="publish_status", value="PASS")
print(f"PUBLISHED {len(tables)} GOLD TABLES TO {export_root}")
