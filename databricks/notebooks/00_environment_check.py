# Databricks notebook source
# Northstar Retail End-to-End Data Platform
# This file is a Git-friendly Databricks source notebook.
# Track A reads files that you manually uploaded to a Unity Catalog volume.
# It never attempts to reach SQL Server or PostgreSQL on localhost.


# COMMAND ----------
# MAGIC %md
# MAGIC # 00 — Environment check
# MAGIC **Purpose:** verify Spark, parameters, catalog, schemas, volume access, and Delta read/write.
# MAGIC **Input:** widget values. **Output:** one disposable Delta test table and a task value.

# COMMAND ----------
from datetime import datetime, timezone
from pyspark.sql import functions as F

for name, default in {
    "catalog": "northstar_retail",
    "landing_schema": "landing",
    "bronze_schema": "bronze",
    "silver_schema": "silver",
    "gold_schema": "gold",
    "quality_schema": "quality",
    "volume": "track_a_files",
    "batch_id": "MANUAL-REPLACE-ME",
}.items():
    dbutils.widgets.text(name, default)

catalog = dbutils.widgets.get("catalog")
landing_schema = dbutils.widgets.get("landing_schema")
bronze_schema = dbutils.widgets.get("bronze_schema")
silver_schema = dbutils.widgets.get("silver_schema")
gold_schema = dbutils.widgets.get("gold_schema")
quality_schema = dbutils.widgets.get("quality_schema")
volume = dbutils.widgets.get("volume")
batch_id = dbutils.widgets.get("batch_id")

if batch_id == "MANUAL-REPLACE-ME":
    raise ValueError("Set batch_id to the exact extraction folder name, such as EXT-20260815T180000Z.")

# COMMAND ----------
# Creating a catalog may require workspace permissions. If this fails, use a catalog you can access.
spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`")
for schema_name in [landing_schema, bronze_schema, silver_schema, gold_schema, quality_schema]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema_name}`")
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{landing_schema}`.`{volume}`")

volume_root = f"/Volumes/{catalog}/{landing_schema}/{volume}"
batch_root = f"{volume_root}/{batch_id}"
print({"catalog": catalog, "batch_root": batch_root, "spark_version": spark.version})

# COMMAND ----------
# Write and read a tiny Delta table. This proves Spark and the Gold schema work.
test_table = f"`{catalog}`.`{quality_schema}`.`environment_check`"
test_df = spark.createDataFrame([(batch_id, datetime.now(timezone.utc), "PASS")], ["batch_id", "checked_at_utc", "status"])
(test_df.write.format("delta").mode("append").saveAsTable(test_table))
assert spark.table(test_table).filter(F.col("batch_id") == batch_id).count() >= 1

# Verify the uploaded batch folder. It is normal for this to fail before you upload extracts.
try:
    uploaded = dbutils.fs.ls(batch_root)
    print(f"Found {len(uploaded)} objects in {batch_root}")
except Exception as exc:
    raise FileNotFoundError(
        f"Databricks cannot find {batch_root}. Upload the entire local extraction batch folder "
        "to the volume and keep the batch folder name unchanged."
    ) from exc

# COMMAND ----------
dbutils.jobs.taskValues.set(key="environment_status", value="PASS")
dbutils.jobs.taskValues.set(key="batch_root", value=batch_root)
print("ENVIRONMENT CHECK PASSED")
