# Databricks notebook source
# Northstar Retail End-to-End Data Platform
# This file is a Git-friendly Databricks source notebook.
# Track A reads files that you manually uploaded to a Unity Catalog volume.
# It never attempts to reach SQL Server or PostgreSQL on localhost.


# COMMAND ----------
# MAGIC %md
# MAGIC # 01 — Bronze SQL Server extracts
# MAGIC Reads Track A Parquet extracts from the uploaded volume; SQL Server itself remains local.

# COMMAND ----------

from __future__ import annotations
from datetime import datetime, timezone
from functools import reduce
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

for name, default in {
    "catalog": "northstar_retail", "landing_schema": "landing", "bronze_schema": "bronze",
    "volume": "track_a_files", "batch_id": "MANUAL-REPLACE-ME"
}.items():
    dbutils.widgets.text(name, default)

catalog = dbutils.widgets.get("catalog")
landing_schema = dbutils.widgets.get("landing_schema")
bronze_schema = dbutils.widgets.get("bronze_schema")
volume = dbutils.widgets.get("volume")
batch_id = dbutils.widgets.get("batch_id")
if batch_id == "MANUAL-REPLACE-ME":
    raise ValueError("Pass the extraction batch_id from the workflow.")
batch_root = f"/Volumes/{catalog}/{landing_schema}/{volume}/{batch_id}"


def with_audit_columns(df: DataFrame, source_system: str) -> DataFrame:
    """Preserve raw columns and add repeatable ingestion metadata."""
    payload = F.to_json(F.struct(*[F.col(c).cast("string").alias(c) for c in df.columns]))
    return (
        df.withColumn("_source_system", F.lit(source_system))
          .withColumn("_source_file", F.input_file_name())
          .withColumn("_ingested_at_utc", F.current_timestamp())
          .withColumn("_batch_id", F.lit(batch_id))
          .withColumn("_record_hash", F.sha2(payload, 256))
    )


def append_once(df: DataFrame, table_name: str) -> None:
    """Append this batch once; an exact rerun replaces the same batch safely."""
    full_name = f"`{catalog}`.`{bronze_schema}`.`{table_name}`"
    if spark.catalog.tableExists(full_name.replace("`", "")):
        spark.sql(f"DELETE FROM {full_name} WHERE _batch_id = '{batch_id}'")
    (df.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(full_name))
    loaded = spark.table(full_name).filter(F.col("_batch_id") == batch_id).count()
    if loaded != df.count():
        raise AssertionError(f"Bronze reconciliation failed for {table_name}: input={df.count()} target={loaded}")


# COMMAND ----------
tables = [
    "customers", "addresses", "products", "product_categories", "suppliers", "stores",
    "employees", "orders", "order_items", "payments", "shipments",
    "inventory_transactions", "inventory_snapshots",
]
results = []
for table in tables:
    path = f"{batch_root}/sqlserver/{table}.parquet"
    raw = spark.read.format("parquet").load(path)
    audited = with_audit_columns(raw, "SQLSERVER_ERP")
    append_once(audited, f"erp_{table}")
    results.append((table, raw.count()))
display(spark.createDataFrame(results, ["table_name", "rows_loaded"]))
dbutils.jobs.taskValues.set(key="bronze_sqlserver_status", value="PASS")
