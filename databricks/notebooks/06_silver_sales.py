# Databricks notebook source
# Northstar Retail End-to-End Data Platform
# Track A reads uploaded Delta tables and never attempts to reach localhost.

# COMMAND ----------
# MAGIC %md
# MAGIC # 06 — Silver sales, shipments, inventory, returns, and promotions
# MAGIC Reconstructs complete order lines for every affected order, cleans the remaining
# MAGIC operational subjects at their declared grains, and writes rerun-safe quarantine evidence.

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
    frame = spark.table(f"{catalog}.{bronze_schema}.{table_name}")
    order = [F.to_timestamp(F.col(column)).desc_nulls_last() for column in order_columns]
    order.append(F.col("_ingested_at_utc").desc_nulls_last())
    window = Window.partitionBy(key_column).orderBy(*order)
    return (
        frame.withColumn("_latest_rank", F.row_number().over(window))
        .filter(F.col("_latest_rank") == 1)
        .drop("_latest_rank")
    )


def latest_in_batch(
    table_name: str,
    key_column: str,
    *order_columns: str,
) -> DataFrame:
    frame = spark.table(f"{catalog}.{bronze_schema}.{table_name}").filter(
        F.col("_batch_id") == batch_id
    )
    order = [F.to_timestamp(F.col(column)).desc_nulls_last() for column in order_columns]
    order.append(F.col("_ingested_at_utc").desc_nulls_last())
    window = Window.partitionBy(key_column).orderBy(*order)
    return (
        frame.withColumn("_batch_rank", F.row_number().over(window))
        .filter(F.col("_batch_rank") == 1)
        .drop("_batch_rank")
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
# A change to an order affects every line on that order. A change to one order item needs
# the latest order header. Reconstructing from all Bronze history prevents an incremental
# batch from losing unchanged parent/child context.
current_orders = spark.table(f"{catalog}.{bronze_schema}.erp_orders").filter(
    F.col("_batch_id") == batch_id
)
current_items = spark.table(f"{catalog}.{bronze_schema}.erp_order_items").filter(
    F.col("_batch_id") == batch_id
)
changed_order_ids = (
    current_orders.select(F.col("order_id").cast("long").alias("order_id"))
    .unionByName(
        current_items.select(F.col("order_id").cast("long").alias("order_id"))
    )
    .filter(F.col("order_id").isNotNull())
    .distinct()
)
latest_orders = latest_by_key("erp_orders", "order_id", "updated_at").withColumn(
    "order_id",
    F.col("order_id").cast("long"),
)
latest_items = latest_by_key("erp_order_items", "order_item_id", "updated_at").withColumn(
    "order_id",
    F.col("order_id").cast("long"),
)
orders = latest_orders.join(changed_order_ids, "order_id", "inner")
items = latest_items.join(changed_order_ids, "order_id", "inner")

sales_typed = (
    items.alias("i")
    .join(orders.alias("o"), "order_id", "inner")
    .select(
        F.col("i.order_item_id").cast("long").alias("order_item_id"),
        F.col("order_id").cast("long").alias("order_id"),
        F.col("i.line_number").cast("int").alias("line_number"),
        F.col("i.product_id").cast("long").alias("product_id"),
        F.col("o.customer_id").cast("long").alias("customer_id"),
        F.col("o.store_id").cast("long").alias("store_id"),
        F.col("o.employee_id").cast("long").alias("employee_id"),
        F.col("o.order_number").alias("order_number"),
        F.upper(F.trim(F.col("o.channel_code"))).alias("channel_code"),
        F.upper(F.trim(F.col("o.promotion_code"))).alias("promotion_code"),
        F.to_timestamp(F.col("o.order_timestamp")).alias("order_timestamp_utc"),
        F.to_date(F.col("o.order_timestamp")).alias("order_date"),
        F.col("i.quantity").cast("int").alias("quantity_int"),
        F.col("i.unit_price").cast("decimal(12,2)").alias("unit_price_dec"),
        F.col("i.unit_cost").cast("decimal(12,2)").alias("unit_cost_dec"),
        F.col("i.discount_amount").cast("decimal(12,2)").alias("discount_dec"),
        F.col("i.tax_amount").cast("decimal(12,2)").alias("tax_dec"),
        F.upper(F.trim(F.col("o.currency_code"))).alias("currency_code"),
    )
)
invalid_sales = sales_typed.filter(
    (F.col("quantity_int") <= 0)
    | F.col("product_id").isNull()
    | F.col("unit_price_dec").isNull()
    | F.col("unit_cost_dec").isNull()
    | (F.col("discount_dec") < 0)
    | (F.col("tax_dec") < 0)
)
quarantine(
    invalid_sales,
    "IMPOSSIBLE_QUANTITY_OR_INVALID_AMOUNT",
    "sales_quarantine",
)
sales = (
    sales_typed.join(
        invalid_sales.select("order_item_id").distinct(),
        "order_item_id",
        "left_anti",
    )
    .withColumn(
        "gross_sales_amount",
        (F.col("quantity_int") * F.col("unit_price_dec")).cast("decimal(16,2)"),
    )
    .withColumn(
        "net_sales_amount",
        (
            F.col("quantity_int") * F.col("unit_price_dec")
            - F.col("discount_dec")
        ).cast("decimal(16,2)"),
    )
    .withColumn(
        "cost_of_goods_sold",
        (F.col("quantity_int") * F.col("unit_cost_dec")).cast("decimal(16,2)"),
    )
    .withColumn(
        "gross_profit_amount",
        (
            F.col("quantity_int") * F.col("unit_price_dec")
            - F.col("discount_dec")
            - F.col("quantity_int") * F.col("unit_cost_dec")
        ).cast("decimal(16,2)"),
    )
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("source_system", F.lit("SQLSERVER_ERP"))
)
replace_batch(sales, "sales")

# COMMAND ----------
current_shipments = spark.table(
    f"{catalog}.{bronze_schema}.erp_shipments"
).filter(F.col("_batch_id") == batch_id)
changed_shipment_ids = current_shipments.select(
    F.col("shipment_id").cast("long").alias("shipment_id")
).distinct()
latest_shipments = latest_by_key(
    "erp_shipments", "shipment_id", "updated_at"
).withColumn("shipment_id", F.col("shipment_id").cast("long"))
order_impacted_shipment_ids = (
    latest_shipments.withColumn("order_id", F.col("order_id").cast("long"))
    .join(changed_order_ids, "order_id", "left_semi")
    .select("shipment_id")
)
affected_shipment_ids = (
    changed_shipment_ids.unionByName(order_impacted_shipment_ids).distinct()
)
shipments = latest_shipments.join(
    affected_shipment_ids, "shipment_id", "inner"
)
shipments_clean = (
    shipments.withColumn("ship_date", F.to_date("ship_date"))
    .withColumn("promised_delivery_date", F.to_date("promised_delivery_date"))
    .withColumn("actual_delivery_date", F.to_date("actual_delivery_date"))
    .withColumn(
        "on_time_flag",
        F.coalesce(
            F.col("actual_delivery_date") <= F.col("promised_delivery_date"),
            F.lit(False),
        ),
    )
    .withColumn("shipping_cost", F.col("shipping_cost").cast("decimal(12,2)"))
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("source_system", F.lit("SQLSERVER_ERP"))
)
shipment_rejects = shipments_clean.filter(
    F.col("ship_date").isNull()
    | F.col("promised_delivery_date").isNull()
    | (F.col("shipping_cost") < 0)
)
quarantine(shipment_rejects, "INVALID_SHIPMENT", "shipment_quarantine")
replace_batch(
    shipments_clean.join(
        shipment_rejects.select("shipment_id"),
        "shipment_id",
        "left_anti",
    ),
    "shipments",
)

inventory = latest_in_batch(
    "erp_inventory_snapshots",
    "inventory_snapshot_id",
    "created_at",
)
inventory_clean = (
    inventory.withColumn("snapshot_date", F.to_date("snapshot_date"))
    .withColumn("quantity_on_hand", F.col("quantity_on_hand").cast("int"))
    .withColumn("quantity_reserved", F.col("quantity_reserved").cast("int"))
    .withColumn("reorder_point", F.col("reorder_point").cast("int"))
    .withColumn(
        "stockout_risk_flag",
        (F.col("quantity_on_hand") - F.col("quantity_reserved"))
        <= F.col("reorder_point"),
    )
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("source_system", F.lit("SQLSERVER_ERP"))
)
inventory_rejects = inventory_clean.filter(
    F.col("snapshot_date").isNull()
    | F.col("store_id").isNull()
    | F.col("product_id").isNull()
    | (F.col("quantity_reserved") < 0)
    | (F.col("reorder_point") < 0)
)
quarantine(
    inventory_rejects,
    "INVALID_INVENTORY_SNAPSHOT",
    "inventory_quarantine",
)
replace_batch(
    inventory_clean.join(
        inventory_rejects.select("inventory_snapshot_id"),
        "inventory_snapshot_id",
        "left_anti",
    ),
    "inventory_snapshots",
)

# COMMAND ----------
returns_raw = spark.table(f"{catalog}.{bronze_schema}.file_returns").filter(
    F.col("_batch_id") == batch_id
)
returns_one = (
    returns_raw.withColumn(
        "_return_rank",
        F.row_number().over(
            Window.partitionBy("return_id").orderBy(
                F.col("_ingested_at_utc").desc_nulls_last()
            )
        ),
    )
    .filter(F.col("_return_rank") == 1)
    .drop("_return_rank")
)
parsed_return_date = F.coalesce(
    F.to_date("return_date", "yyyy-MM-dd"),
    F.to_date("return_date", "MM/dd/yyyy"),
    F.to_date("return_date", "dd-MMM-yyyy"),
    F.to_date("return_date", "yyyy/MM/dd"),
)
returns_clean = (
    returns_one.withColumn("return_date_parsed", parsed_return_date)
    .withColumn("return_quantity_int", F.col("return_quantity").cast("int"))
    .withColumn("refund_amount_dec", F.col("refund_amount").cast("decimal(12,2)"))
    .withColumn("customer_id", F.col("customer_id").cast("long"))
    .withColumn("product_id", F.col("product_id").cast("long"))
    .withColumn("order_id", F.col("order_id").cast("long"))
    .withColumn("order_item_id", F.col("order_item_id").cast("long"))
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("source_system", F.lit("FILE_FEED"))
)
return_rejects = returns_clean.filter(
    F.col("return_id").isNull()
    | F.col("return_date_parsed").isNull()
    | (F.col("return_quantity_int") <= 0)
    | (F.col("refund_amount_dec") < 0)
)
quarantine(return_rejects, "INVALID_RETURN", "return_quarantine")
replace_batch(
    returns_clean.join(return_rejects.select("return_id"), "return_id", "left_anti"),
    "returns",
)

promotions_raw = spark.table(
    f"{catalog}.{bronze_schema}.file_promotion_calendar"
).filter(F.col("_batch_id") == batch_id)
promotions = (
    promotions_raw.withColumn("promotion_code", F.upper(F.trim("promotion_code")))
    .withColumn("start_date", F.to_date("start_date"))
    .withColumn("end_date", F.to_date("end_date"))
    .withColumn("discount_value", F.col("discount_value").cast("decimal(12,4)"))
    .withColumn("discount_type", F.upper(F.trim("discount_type")))
    .withColumn("channel_code", F.upper(F.trim("channel_code")))
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("source_system", F.lit("FILE_FEED"))
    .dropDuplicates(["promotion_code"])
)
promotion_rejects = promotions.filter(
    F.col("promotion_code").isNull()
    | F.col("start_date").isNull()
    | F.col("end_date").isNull()
    | (F.col("end_date") < F.col("start_date"))
    | (F.col("discount_value") < 0)
)
quarantine(promotion_rejects, "INVALID_PROMOTION", "promotion_quarantine")
replace_batch(
    promotions.join(
        promotion_rejects.select("promotion_code"),
        "promotion_code",
        "left_anti",
    ),
    "promotions",
)

print(
    {
        "affected_orders": changed_order_ids.count(),
        "sales_rows": sales.count(),
        "sales_quarantine": invalid_sales.count(),
        "shipments": shipments_clean.count(),
        "inventory_snapshots": inventory_clean.count(),
        "returns": returns_clean.count(),
    }
)
dbutils.jobs.taskValues.set(key="silver_sales_status", value="PASS")
