# Databricks notebook source
# Northstar Retail End-to-End Data Platform
# This file is a Git-friendly Databricks source notebook.
# Track A reads files that you manually uploaded to a Unity Catalog volume.
# It never attempts to reach SQL Server or PostgreSQL on localhost.


# COMMAND ----------
# MAGIC %md
# MAGIC # 03 — Bronze file feeds
# MAGIC CSV values remain strings in Bronze. Nested tracking JSON is preserved and parsed as a struct/array.

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
file_specs = {
    "file_returns": (f"{batch_root}/files/returns.csv", "csv"),
    "file_supplier_cost_updates": (f"{batch_root}/files/supplier_cost_updates.csv", "csv"),
    "file_promotion_calendar": (f"{batch_root}/files/promotion_calendar.csv", "csv"),
    "file_shipment_tracking_events": (f"{batch_root}/files/shipment_tracking_events.jsonl", "json"),
}
results = []
for table_name, (path, kind) in file_specs.items():
    try:
        if kind == "csv":
            raw = spark.read.option("header", "true").option("mode", "PERMISSIVE").csv(path)
        else:
            raw = spark.read.option("mode", "PERMISSIVE").json(path)
        audited = with_audit_columns(raw, "FILE_FEED")
        append_once(audited, table_name)
        results.append((table_name, raw.count(), "PASS"))
    except Exception as exc:
        # Create a visible quarantine record and fail the task so the quality gate cannot be bypassed.
        quarantine = spark.createDataFrame([(batch_id, path, str(exc), datetime.now(timezone.utc))], ["batch_id", "source_path", "error_message", "quarantined_at_utc"])
        quarantine.write.format("delta").mode("append").saveAsTable(f"`{catalog}`.`{bronze_schema}`.`file_read_quarantine`")
        raise

display(spark.createDataFrame(results, ["table_name", "rows_loaded", "status"]))
dbutils.jobs.taskValues.set(key="bronze_files_status", value="PASS")
