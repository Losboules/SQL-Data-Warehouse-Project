# Databricks notebook source
# Northstar Retail End-to-End Data Platform
# Track A reads uploaded Delta tables and never attempts to reach localhost.

# COMMAND ----------
# MAGIC %md
# MAGIC # 05 — Silver products
# MAGIC Rebuilds products affected by product, category, supplier, or supplier-cost changes
# MAGIC using the latest operational records available across all Bronze batches.

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
latest_products = latest_by_key("erp_products", "product_id", "updated_at")
latest_categories = latest_by_key("erp_product_categories", "category_id", "updated_at")
latest_suppliers = latest_by_key("erp_suppliers", "supplier_id", "updated_at")

current_products = spark.table(f"{catalog}.{bronze_schema}.erp_products").filter(
    F.col("_batch_id") == batch_id
)
current_categories = spark.table(
    f"{catalog}.{bronze_schema}.erp_product_categories"
).filter(F.col("_batch_id") == batch_id)
current_suppliers = spark.table(f"{catalog}.{bronze_schema}.erp_suppliers").filter(
    F.col("_batch_id") == batch_id
)
current_costs = spark.table(
    f"{catalog}.{bronze_schema}.file_supplier_cost_updates"
).filter(F.col("_batch_id") == batch_id)

changed_product_ids = current_products.select(
    F.col("product_id").cast("long").alias("product_id")
)
changed_category_ids = current_categories.select(
    F.col("category_id").cast("long").alias("category_id")
).distinct()
changed_supplier_ids = current_suppliers.select(
    F.col("supplier_id").cast("long").alias("supplier_id")
).distinct()
changed_cost_skus = current_costs.select(
    F.upper(F.trim("sku")).alias("sku")
).distinct()

products_typed = (
    latest_products.withColumn("product_id", F.col("product_id").cast("long"))
    .withColumn("category_id", F.col("category_id").cast("long"))
    .withColumn("supplier_id", F.col("supplier_id").cast("long"))
    .withColumn("sku", F.upper(F.trim("sku")))
)
category_impacted = products_typed.join(
    changed_category_ids,
    "category_id",
    "left_semi",
).select("product_id")
supplier_impacted = products_typed.join(
    changed_supplier_ids,
    "supplier_id",
    "left_semi",
).select("product_id")
cost_impacted = products_typed.join(changed_cost_skus, "sku", "left_semi").select(
    "product_id"
)
affected_product_ids = (
    changed_product_ids.unionByName(category_impacted)
    .unionByName(supplier_impacted)
    .unionByName(cost_impacted)
    .filter(F.col("product_id").isNotNull())
    .distinct()
)
candidate_products = products_typed.join(
    affected_product_ids,
    "product_id",
    "inner",
)

# File feeds are uploaded as complete snapshots. Deduplicate repeated batch copies by
# source update ID before choosing the latest effective cost for each SKU.
cost_history = spark.table(f"{catalog}.{bronze_schema}.file_supplier_cost_updates")
cost_updates = (
    cost_history.withColumn(
        "_cost_copy_rank",
        F.row_number().over(
            Window.partitionBy("supplier_cost_update_id").orderBy(
                F.col("_ingested_at_utc").desc_nulls_last()
            )
        ),
    )
    .filter(F.col("_cost_copy_rank") == 1)
    .drop("_cost_copy_rank")
    .withColumn("sku", F.upper(F.trim("sku")))
    .withColumn("effective_date_parsed", F.to_date("effective_date"))
)
latest_cost = (
    cost_updates.withColumn(
        "_cost_rank",
        F.row_number().over(
            Window.partitionBy("sku").orderBy(
                F.col("effective_date_parsed").desc_nulls_last(),
                F.col("supplier_cost_update_id").desc(),
            )
        ),
    )
    .filter(F.col("_cost_rank") == 1)
    .select(
        "sku",
        F.col("new_unit_cost").cast("decimal(12,2)").alias("latest_unit_cost"),
        "effective_date_parsed",
    )
)

cleaned = (
    candidate_products.alias("p")
    .join(
        latest_categories.alias("c"),
        F.col("p.category_id") == F.col("c.category_id").cast("long"),
        "left",
    )
    .join(
        latest_suppliers.alias("s"),
        F.col("p.supplier_id") == F.col("s.supplier_id").cast("long"),
        "left",
    )
    .join(latest_cost.alias("lc"), F.col("p.sku") == F.col("lc.sku"), "left")
    .select(
        F.col("p.product_id").cast("long").alias("product_id"),
        F.col("p.sku").alias("sku"),
        F.trim(F.col("p.product_name")).alias("product_name"),
        F.initcap(F.trim(F.col("c.category_name"))).alias("category_name"),
        F.trim(F.col("p.brand")).alias("brand"),
        F.upper(F.trim(F.col("s.supplier_code"))).alias("supplier_code"),
        F.coalesce(
            F.col("lc.latest_unit_cost"),
            F.col("p.unit_cost").cast("decimal(12,2)"),
        ).alias("unit_cost"),
        F.col("p.list_price").cast("decimal(12,2)").alias("list_price"),
        F.upper(F.trim(F.col("p.currency_code"))).alias("currency_code"),
        F.col("p.active_flag").cast("boolean").alias("active_flag"),
        F.to_timestamp(F.col("p.updated_at")).alias("updated_at"),
        F.lit(batch_id).alias("batch_id"),
        F.current_timestamp().alias("load_timestamp_utc"),
        F.lit("SQLSERVER_ERP").alias("source_system"),
    )
)
invalid = cleaned.filter(
    F.col("sku").isNull()
    | (F.col("sku") == "")
    | F.col("category_name").isNull()
    | F.col("supplier_code").isNull()
    | F.col("unit_cost").isNull()
    | (F.col("unit_cost") < 0)
    | F.col("list_price").isNull()
    | (F.col("list_price") < 0)
)
quarantine(invalid, "INVALID_PRODUCT", "product_quarantine")
valid = cleaned.join(invalid.select("product_id"), "product_id", "left_anti")
replace_batch(valid, "products")

print(
    {
        "affected_product_ids": affected_product_ids.count(),
        "silver_rows": valid.count(),
        "quarantined": invalid.count(),
    }
)
dbutils.jobs.taskValues.set(key="silver_products_status", value="PASS")
