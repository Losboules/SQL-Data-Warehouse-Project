# Databricks notebook source
# Northstar Retail End-to-End Data Platform
# Track A reads uploaded Delta tables and never attempts to reach localhost.

# COMMAND ----------
# MAGIC %md
# MAGIC # 04 — Silver customers
# MAGIC Rebuilds every customer affected by a customer or address change, standardizes
# MAGIC descriptive fields, records malformed-email evidence, resolves duplicate business
# MAGIC keys, and writes a rerun-safe Silver batch.

# COMMAND ----------
from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

for name, default in {
    "catalog": "northstar_retail",
    "bronze_schema": "bronze",
    "silver_schema": "silver",
    "quality_schema": "quality",
    "batch_id": "MANUAL-REPLACE-ME",
}.items():
    dbutils.widgets.text(name, default)

catalog = dbutils.widgets.get("catalog")
bronze_schema = dbutils.widgets.get("bronze_schema")
silver_schema = dbutils.widgets.get("silver_schema")
quality_schema = dbutils.widgets.get("quality_schema")
batch_id = dbutils.widgets.get("batch_id")
if batch_id == "MANUAL-REPLACE-ME":
    raise ValueError("Pass batch_id from the workflow.")


def latest_by_key(table_name: str, key_column: str, *order_columns: str) -> DataFrame:
    """Return the latest Bronze record for each operational primary key."""
    frame = spark.table(f"{catalog}.{bronze_schema}.{table_name}")
    order = [F.to_timestamp(F.col(column)).desc_nulls_last() for column in order_columns]
    order.append(F.col("_ingested_at_utc").desc_nulls_last())
    window = Window.partitionBy(key_column).orderBy(*order)
    return (
        frame.withColumn("_latest_rank", F.row_number().over(window))
        .filter(F.col("_latest_rank") == 1)
        .drop("_latest_rank")
    )


def replace_batch(frame: DataFrame, table_name: str) -> None:
    """Replace this Silver batch only, making an exact repair run idempotent."""
    full_name = f"`{catalog}`.`{silver_schema}`.`{table_name}`"
    escaped_batch = batch_id.replace("'", "''")
    if spark.catalog.tableExists(full_name.replace("`", "")):
        spark.sql(f"DELETE FROM {full_name} WHERE batch_id = '{escaped_batch}'")
    (
        frame.write.format("delta")
        .mode("append")
        .option("mergeSchema", "true")
        .saveAsTable(full_name)
    )


def quarantine(frame: DataFrame, rule_name: str, table_name: str) -> None:
    """Replace one batch/rule slice so quarantine evidence does not duplicate on rerun."""
    if not frame.limit(1).count():
        return
    full_name = f"`{catalog}`.`{quality_schema}`.`{table_name}`"
    escaped_batch = batch_id.replace("'", "''")
    escaped_rule = rule_name.replace("'", "''")
    if spark.catalog.tableExists(full_name.replace("`", "")):
        spark.sql(
            f"DELETE FROM {full_name} "
            f"WHERE batch_id = '{escaped_batch}' AND quality_rule = '{escaped_rule}'"
        )
    (
        frame.withColumn("quality_rule", F.lit(rule_name))
        .withColumn("batch_id", F.lit(batch_id))
        .withColumn("quarantined_at_utc", F.current_timestamp())
        .write.format("delta")
        .mode("append")
        .option("mergeSchema", "true")
        .saveAsTable(full_name)
    )


# COMMAND ----------
customer_table = f"{catalog}.{bronze_schema}.erp_customers"
address_table = f"{catalog}.{bronze_schema}.erp_addresses"
customer_history = spark.table(customer_table)
current_customers = customer_history.filter(F.col("_batch_id") == batch_id)
current_addresses = spark.table(address_table).filter(F.col("_batch_id") == batch_id)

changed_customer_ids = (
    current_customers.select(F.col("customer_id").cast("long").alias("customer_id"))
    .unionByName(
        current_addresses.select(F.col("customer_id").cast("long").alias("customer_id"))
    )
    .filter(F.col("customer_id").isNotNull())
    .distinct()
)

latest_customers = latest_by_key("erp_customers", "customer_id", "updated_at")
latest_addresses = latest_by_key("erp_addresses", "address_id", "updated_at")

# Include every historical business key used by a changed customer ID. If a customer
# number itself changes, both the old and new duplicate groups are recalculated.
affected_numbers = (
    customer_history.withColumn("customer_id", F.col("customer_id").cast("long"))
    .join(changed_customer_ids, "customer_id", "inner")
    .select(F.upper(F.trim("customer_number")).alias("customer_number"))
    .filter(F.col("customer_number").isNotNull())
    .distinct()
)

candidate_customers = (
    latest_customers.withColumn("customer_number", F.upper(F.trim("customer_number")))
    .join(affected_numbers, "customer_number", "inner")
)

address_one = (
    latest_addresses.withColumn(
        "_address_rank",
        F.row_number().over(
            Window.partitionBy("customer_id").orderBy(
                F.col("is_default").cast("int").desc(),
                F.to_timestamp("updated_at").desc_nulls_last(),
                F.col("address_id").desc(),
            )
        ),
    )
    .filter(F.col("_address_rank") == 1)
    .select(
        F.col("customer_id").cast("long").alias("customer_id"),
        F.upper(F.trim("state_code")).alias("state_code"),
        F.upper(F.trim("country_code")).alias("country_code"),
    )
)

cleaned = (
    candidate_customers.withColumn("customer_id", F.col("customer_id").cast("long"))
    .withColumn("first_name", F.initcap(F.trim("first_name")))
    .withColumn("last_name", F.initcap(F.trim("last_name")))
    .withColumn("email", F.lower(F.trim("email")))
    .withColumn("loyalty_tier", F.initcap(F.lower(F.trim("loyalty_tier"))))
    .withColumn("signup_date", F.to_date("signup_date"))
    .join(address_one, "customer_id", "left")
    .withColumn(
        "email_valid_flag",
        F.col("email").isNull()
        | (F.col("email") == "")
        | F.col("email").rlike(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"),
    )
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("source_system", F.lit("SQLSERVER_ERP"))
)

email_issues = cleaned.filter(~F.col("email_valid_flag"))
quarantine(email_issues, "MALFORMED_EMAIL", "customer_quarantine")
cleaned = cleaned.withColumn(
    "email",
    F.when(F.col("email_valid_flag"), F.col("email")).otherwise(F.lit(None).cast("string")),
)

ranked = cleaned.withColumn(
    "business_key_rank",
    F.row_number().over(
        Window.partitionBy("customer_number").orderBy(
            F.to_timestamp("updated_at").desc_nulls_last(),
            F.col("customer_id").desc(),
        )
    ),
)
missing_or_duplicate = ranked.filter(
    F.col("customer_number").isNull()
    | (F.col("customer_number") == "")
    | (F.col("business_key_rank") > 1)
)
quarantine(
    missing_or_duplicate,
    "MISSING_OR_DUPLICATE_CUSTOMER_BUSINESS_KEY",
    "customer_quarantine",
)
valid = (
    ranked.filter(
        F.col("customer_number").isNotNull()
        & (F.col("customer_number") != "")
        & (F.col("business_key_rank") == 1)
    )
    .drop("business_key_rank")
)
replace_batch(valid, "customers")

print(
    {
        "changed_customer_ids": changed_customer_ids.count(),
        "silver_rows": valid.count(),
        "business_key_rejects": missing_or_duplicate.count(),
        "email_issues": email_issues.count(),
    }
)
dbutils.jobs.taskValues.set(key="silver_customers_status", value="PASS")
