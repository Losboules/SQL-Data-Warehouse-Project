# Databricks notebook source
# Northstar Retail End-to-End Data Platform
# Track A reads uploaded Delta tables and never attempts to reach localhost.

# COMMAND ----------
# MAGIC %md
# MAGIC # 09 — Gold facts
# MAGIC Builds six facts at declared grain, resolves natural identifiers to effective
# MAGIC dimension keys, and MERGEs deterministic fact keys so reruns and later batches
# MAGIC cannot double-count previously loaded business events.

# COMMAND ----------
from __future__ import annotations

from delta.tables import DeltaTable
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

for name, default in {
    "catalog": "northstar_retail",
    "bronze_schema": "bronze",
    "silver_schema": "silver",
    "gold_schema": "gold",
    "batch_id": "MANUAL-REPLACE-ME",
    "load_mode": "full",
}.items():
    dbutils.widgets.text(name, default)

catalog = dbutils.widgets.get("catalog")
bronze_schema = dbutils.widgets.get("bronze_schema")
silver_schema = dbutils.widgets.get("silver_schema")
gold_schema = dbutils.widgets.get("gold_schema")
batch_id = dbutils.widgets.get("batch_id")
load_mode = dbutils.widgets.get("load_mode").strip().lower()
if batch_id == "MANUAL-REPLACE-ME":
    raise ValueError("Pass batch_id from the Lakeflow Job or set the widget manually.")
if load_mode not in {"full", "incremental"}:
    raise ValueError("load_mode must be 'full' or 'incremental'.")

BIG_KEY_MODULUS = 9_007_199_254_740_991


def big_key(*columns: str):
    expressions = [F.coalesce(F.col(column).cast("string"), F.lit("<NULL>")) for column in columns]
    return (F.pmod(F.xxhash64(*expressions), F.lit(BIG_KEY_MODULUS)) + 1).cast("long")


def latest_bronze(table_name: str, key_column: str, *order_columns: str) -> DataFrame:
    """Return the latest known source row per primary key across all Bronze batches."""
    frame = spark.table(f"{catalog}.{bronze_schema}.{table_name}")
    order = [F.to_timestamp(F.col(column)).desc_nulls_last() for column in order_columns]
    order.append(F.col("_ingested_at_utc").desc_nulls_last())
    window = Window.partitionBy(key_column).orderBy(*order)
    return (
        frame.withColumn("_latest_rank", F.row_number().over(window))
        .filter(F.col("_latest_rank") == 1)
        .drop("_latest_rank")
    )


def merge_fact(frame: DataFrame, table_name: str, key_column: str) -> None:
    """Upsert fact rows by deterministic surrogate key and prove merge idempotency."""
    full_name = f"{catalog}.{gold_schema}.{table_name}"
    duplicate_stage_keys = (
        frame.groupBy(key_column).count().filter(F.col("count") > 1).count()
    )
    if duplicate_stage_keys:
        raise AssertionError(
            f"{table_name} has {duplicate_stage_keys} duplicate staged {key_column} groups"
        )

    staged_rows = frame.count()
    if not spark.catalog.tableExists(full_name):
        frame.write.format("delta").mode("overwrite").option(
            "overwriteSchema", "true"
        ).saveAsTable(full_name)
    elif staged_rows:
        target = DeltaTable.forName(spark, full_name)
        (
            target.alias("t")
            .merge(frame.alias("s"), f"t.`{key_column}` = s.`{key_column}`")
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )

    target = spark.table(full_name)
    matched_rows = (
        target.join(frame.select(key_column).distinct(), key_column, "inner").count()
        if staged_rows
        else 0
    )
    if matched_rows != staged_rows:
        raise AssertionError(
            f"{table_name} merge reconciliation failed: staged={staged_rows}, "
            f"matched_target={matched_rows}"
        )
    duplicate_target_keys = (
        target.groupBy(key_column).count().filter(F.col("count") > 1).count()
    )
    if duplicate_target_keys:
        raise AssertionError(
            f"{table_name} has {duplicate_target_keys} duplicate target {key_column} groups"
        )


def key_at_event(
    source: DataFrame,
    dimension: DataFrame,
    source_business_key: str,
    dimension_business_key: str,
    event_date: str,
    surrogate_key: str,
) -> DataFrame:
    """Join an SCD2 dimension using natural key and inclusive effective-date range."""
    source_columns = [F.col(f"s.{column}") for column in source.columns]
    return (
        source.alias("s")
        .join(
            dimension.alias("d"),
            (
                F.col(f"s.{source_business_key}")
                == F.col(f"d.{dimension_business_key}")
            )
            & F.col(f"s.{event_date}").between(
                F.col("d.effective_start_date"), F.col("d.effective_end_date")
            ),
            "left",
        )
        .select(
            *source_columns,
            F.coalesce(F.col(f"d.{surrogate_key}"), F.lit(0)).alias(surrogate_key),
        )
    )


# COMMAND ----------
# Natural-key bridges use the latest source record across every Bronze batch. Incremental
# extracts contain only changes, so limiting these bridges to the current batch would lose
# unchanged parent context and create false Unknown keys.
customer_bridge = latest_bronze(
    "erp_customers", "customer_id", "updated_at"
).select(
    F.col("customer_id").cast("long").alias("customer_id"),
    F.upper(F.trim("customer_number")).alias("customer_number"),
)
product_bridge = latest_bronze("erp_products", "product_id", "updated_at").select(
    F.col("product_id").cast("long").alias("product_id"),
    F.upper(F.trim("sku")).alias("sku"),
)
store_bridge = latest_bronze("erp_stores", "store_id", "updated_at").select(
    F.col("store_id").cast("long").alias("store_id"),
    F.upper(F.trim("store_code")).alias("store_code"),
)
employee_bridge = latest_bronze(
    "erp_employees", "employee_id", "updated_at"
).select(
    F.col("employee_id").cast("long").alias("employee_id"),
    F.upper(F.trim("employee_number")).alias("employee_number"),
)
order_bridge = latest_bronze("erp_orders", "order_id", "updated_at").select(
    F.col("order_id").cast("long").alias("order_id"),
    F.col("customer_id").cast("long").alias("order_customer_id"),
    F.col("store_id").cast("long").alias("order_store_id"),
)
web_user_bridge = latest_bronze(
    "digital_web_users", "web_user_id", "updated_at"
).select(
    F.col("web_user_id").cast("long").alias("web_user_id"),
    F.col("customer_id").cast("long").alias("customer_id"),
)
campaign_bridge = latest_bronze(
    "digital_campaigns", "campaign_id", "updated_at"
).select(
    F.col("campaign_id").cast("long").alias("campaign_id"),
    F.upper(F.trim("campaign_code")).alias("campaign_code"),
)

customers = spark.table(f"{catalog}.{gold_schema}.dim_customer")
products = spark.table(f"{catalog}.{gold_schema}.dim_product")
stores = spark.table(f"{catalog}.{gold_schema}.dim_store")
employees = spark.table(f"{catalog}.{gold_schema}.dim_employee")
promotions = spark.table(f"{catalog}.{gold_schema}.dim_promotion")
channels = spark.table(f"{catalog}.{gold_schema}.dim_channel")
campaigns = spark.table(f"{catalog}.{gold_schema}.dim_campaign")

# COMMAND ----------
# fact_sales grain: one valid source order item.
sales_source = (
    spark.table(f"{catalog}.{silver_schema}.sales")
    .filter(F.col("batch_id") == batch_id)
    .join(customer_bridge, "customer_id", "left")
    .join(product_bridge, "product_id", "left")
    .join(store_bridge, "store_id", "left")
    .join(employee_bridge, "employee_id", "left")
    .withColumn(
        "promotion_code_nk",
        F.coalesce(F.upper(F.trim("promotion_code")), F.lit("NONE")),
    )
    .withColumn("channel_code_nk", F.upper(F.trim("channel_code")))
)
sales_keys = key_at_event(
    sales_source,
    customers,
    "customer_number",
    "customer_number",
    "order_date",
    "customer_key",
)
sales_keys = key_at_event(
    sales_keys, products, "sku", "sku", "order_date", "product_key"
)
fact_sales = (
    sales_keys.alias("s")
    .join(
        stores.alias("st"), F.col("s.store_code") == F.col("st.store_code"), "left"
    )
    .join(
        employees.alias("e"),
        F.col("s.employee_number") == F.col("e.employee_number"),
        "left",
    )
    .join(
        promotions.alias("pr"),
        F.col("s.promotion_code_nk") == F.col("pr.promotion_code"),
        "left",
    )
    .join(
        channels.alias("ch"),
        F.col("s.channel_code_nk") == F.col("ch.channel_code"),
        "left",
    )
    .select(
        big_key("s.order_item_id").alias("sales_key"),
        F.col("s.order_item_id").cast("long").alias("order_item_id"),
        F.col("s.order_id").cast("long").alias("order_id"),
        "s.order_number",
        F.date_format("s.order_date", "yyyyMMdd").cast("int").alias("order_date_key"),
        F.col("s.customer_key").cast("long").alias("customer_key"),
        F.col("s.product_key").cast("long").alias("product_key"),
        F.coalesce(F.col("st.store_key"), F.lit(0)).cast("int").alias("store_key"),
        F.coalesce(F.col("e.employee_key"), F.lit(0))
        .cast("int")
        .alias("employee_key"),
        F.coalesce(F.col("pr.promotion_key"), F.lit(0))
        .cast("int")
        .alias("promotion_key"),
        F.coalesce(F.col("ch.channel_key"), F.lit(0))
        .cast("int")
        .alias("channel_key"),
        F.col("s.quantity_int").cast("int").alias("quantity"),
        F.col("s.gross_sales_amount").cast("decimal(16,2)"),
        F.col("s.discount_dec").cast("decimal(16,2)").alias("discount_amount"),
        F.col("s.net_sales_amount").cast("decimal(16,2)"),
        F.col("s.tax_dec").cast("decimal(16,2)").alias("tax_amount"),
        F.col("s.unit_cost_dec").cast("decimal(16,2)").alias("unit_cost_amount"),
        F.col("s.cost_of_goods_sold").cast("decimal(16,2)"),
        F.col("s.gross_profit_amount").cast("decimal(16,2)"),
        F.upper(F.trim(F.col("s.currency_code"))).alias("currency_code"),
        F.current_timestamp().alias("load_timestamp_utc"),
        F.lit(batch_id).alias("batch_id"),
        F.lit("CONFORMED").alias("source_system"),
    )
)
merge_fact(fact_sales, "fact_sales", "sales_key")

# COMMAND ----------
# fact_returns grain: one accepted return record.
returns_source = (
    spark.table(f"{catalog}.{silver_schema}.returns")
    .filter(F.col("batch_id") == batch_id)
    .withColumn("customer_id", F.col("customer_id").cast("long"))
    .withColumn("product_id", F.col("product_id").cast("long"))
    .withColumn("order_id", F.col("order_id").cast("long"))
    .join(customer_bridge, "customer_id", "left")
    .join(product_bridge, "product_id", "left")
    .join(order_bridge, "order_id", "left")
    .join(store_bridge, F.col("order_store_id") == F.col("store_id"), "left")
    .drop("store_id")
)
return_keys = key_at_event(
    returns_source,
    customers,
    "customer_number",
    "customer_number",
    "return_date_parsed",
    "customer_key",
)
return_keys = key_at_event(
    return_keys,
    products,
    "sku",
    "sku",
    "return_date_parsed",
    "product_key",
)
fact_returns = (
    return_keys.alias("r")
    .join(
        stores.alias("st"), F.col("r.store_code") == F.col("st.store_code"), "left"
    )
    .select(
        big_key("r.return_id").alias("return_key"),
        "r.return_id",
        F.col("r.order_item_id").cast("long").alias("order_item_id"),
        F.date_format("r.return_date_parsed", "yyyyMMdd")
        .cast("int")
        .alias("return_date_key"),
        F.col("r.customer_key").cast("long").alias("customer_key"),
        F.col("r.product_key").cast("long").alias("product_key"),
        F.coalesce(F.col("st.store_key"), F.lit(0)).cast("int").alias("store_key"),
        F.col("r.return_quantity_int").cast("int").alias("return_quantity"),
        F.col("r.refund_amount_dec").cast("decimal(16,2)").alias("refund_amount"),
        "r.return_reason",
        F.upper(F.trim(F.col("r.currency_code"))).alias("currency_code"),
        F.current_timestamp().alias("load_timestamp_utc"),
        F.lit(batch_id).alias("batch_id"),
        F.lit("FILE_FEED").alias("source_system"),
    )
)
merge_fact(fact_returns, "fact_returns", "return_key")

# COMMAND ----------
# fact_inventory_snapshot grain: one snapshot date, store, and product.
inventory_source = (
    spark.table(f"{catalog}.{silver_schema}.inventory_snapshots")
    .filter(F.col("batch_id") == batch_id)
    .withColumn("store_id", F.col("store_id").cast("long"))
    .withColumn("product_id", F.col("product_id").cast("long"))
    .join(store_bridge, "store_id", "left")
    .join(product_bridge, "product_id", "left")
)
inventory_keys = key_at_event(
    inventory_source, products, "sku", "sku", "snapshot_date", "product_key"
)
fact_inventory = (
    inventory_keys.alias("i")
    .join(
        stores.alias("st"), F.col("i.store_code") == F.col("st.store_code"), "left"
    )
    .join(
        products.select("product_key", "unit_cost").alias("pd"),
        F.col("i.product_key") == F.col("pd.product_key"),
        "left",
    )
    .select(
        big_key("i.snapshot_date", "i.store_id", "i.product_id").alias(
            "inventory_snapshot_key"
        ),
        F.date_format("i.snapshot_date", "yyyyMMdd")
        .cast("int")
        .alias("snapshot_date_key"),
        F.coalesce(F.col("st.store_key"), F.lit(0)).cast("int").alias("store_key"),
        F.col("i.product_key").cast("long").alias("product_key"),
        F.col("i.quantity_on_hand").cast("int"),
        F.col("i.quantity_reserved").cast("int"),
        F.col("i.reorder_point").cast("int"),
        F.col("i.stockout_risk_flag").cast("boolean"),
        (
            F.col("i.quantity_on_hand")
            * F.coalesce(F.col("pd.unit_cost"), F.lit(0))
        )
        .cast("decimal(18,2)")
        .alias("inventory_value_amount"),
        F.current_timestamp().alias("load_timestamp_utc"),
        F.lit(batch_id).alias("batch_id"),
        F.lit("SQLSERVER_ERP").alias("source_system"),
    )
)
merge_fact(
    fact_inventory,
    "fact_inventory_snapshot",
    "inventory_snapshot_key",
)

# COMMAND ----------
# fact_shipments grain: one source shipment.
shipment_source = (
    spark.table(f"{catalog}.{silver_schema}.shipments")
    .filter(F.col("batch_id") == batch_id)
    .withColumn("order_id", F.col("order_id").cast("long"))
    .join(order_bridge, "order_id", "left")
    .join(customer_bridge, F.col("order_customer_id") == F.col("customer_id"), "left")
    .drop("customer_id")
    .join(store_bridge, F.col("order_store_id") == F.col("store_id"), "left")
    .drop("store_id")
)
shipment_keys = key_at_event(
    shipment_source,
    customers,
    "customer_number",
    "customer_number",
    "ship_date",
    "customer_key",
)
fact_shipments = (
    shipment_keys.alias("s")
    .join(
        stores.alias("st"), F.col("s.store_code") == F.col("st.store_code"), "left"
    )
    .select(
        big_key("s.shipment_id").alias("shipment_key"),
        F.col("s.shipment_id").cast("long").alias("shipment_id"),
        F.col("s.order_id").cast("long").alias("order_id"),
        F.date_format("s.ship_date", "yyyyMMdd").cast("int").alias("ship_date_key"),
        F.date_format("s.promised_delivery_date", "yyyyMMdd")
        .cast("int")
        .alias("promised_date_key"),
        F.coalesce(
            F.date_format("s.actual_delivery_date", "yyyyMMdd").cast("int"),
            F.lit(0),
        ).alias("delivery_date_key"),
        F.col("s.customer_key").cast("long").alias("customer_key"),
        F.coalesce(F.col("st.store_key"), F.lit(0)).cast("int").alias("store_key"),
        "s.carrier",
        F.datediff("s.actual_delivery_date", "s.ship_date")
        .cast("int")
        .alias("delivery_days"),
        F.coalesce(
            F.col("s.actual_delivery_date") <= F.col("s.promised_delivery_date"),
            F.lit(False),
        ).alias("on_time_flag"),
        F.col("s.shipping_cost").cast("decimal(16,2)").alias("shipping_cost"),
        F.current_timestamp().alias("load_timestamp_utc"),
        F.lit(batch_id).alias("batch_id"),
        F.lit("SQLSERVER_ERP").alias("source_system"),
    )
)
merge_fact(fact_shipments, "fact_shipments", "shipment_key")

# COMMAND ----------
# fact_web_sessions grain: one web session; event counts exclude quarantined events.
event_counts = (
    spark.table(f"{catalog}.{silver_schema}.web_events")
    .filter(F.col("batch_id") == batch_id)
    .groupBy("session_id")
    .agg(
        F.sum(F.when(F.col("event_type") == "page_view", 1).otherwise(0))
        .cast("int")
        .alias("page_view_count"),
        F.sum(F.when(F.col("event_type") == "add_to_cart", 1).otherwise(0))
        .cast("int")
        .alias("add_to_cart_count"),
    )
)
web_source = (
    spark.table(f"{catalog}.{silver_schema}.web_sessions")
    .filter(F.col("batch_id") == batch_id)
    .withColumn("web_user_id", F.col("web_user_id").cast("long"))
    .withColumn("campaign_id", F.col("campaign_id").cast("long"))
    .join(web_user_bridge, "web_user_id", "left")
    .join(customer_bridge, "customer_id", "left")
    .join(campaign_bridge, "campaign_id", "left")
    .join(event_counts, "session_id", "left")
    .withColumn("session_date", F.to_date("session_start_utc"))
    .withColumn("channel_code_nk", F.upper(F.trim("source_channel")))
)
web_keys = key_at_event(
    web_source,
    customers,
    "customer_number",
    "customer_number",
    "session_date",
    "customer_key",
)
fact_web_sessions = (
    web_keys.alias("s")
    .join(
        campaigns.alias("c"),
        F.col("s.campaign_code") == F.col("c.campaign_code"),
        "left",
    )
    .join(
        channels.alias("ch"),
        F.col("s.channel_code_nk") == F.col("ch.channel_code"),
        "left",
    )
    .select(
        big_key("s.session_id").alias("web_session_key"),
        F.col("s.session_id").cast("long").alias("session_id"),
        F.date_format("s.session_date", "yyyyMMdd")
        .cast("int")
        .alias("session_date_key"),
        F.col("s.customer_key").cast("long").alias("customer_key"),
        F.coalesce(F.col("c.campaign_key"), F.lit(0))
        .cast("int")
        .alias("campaign_key"),
        F.coalesce(F.col("ch.channel_key"), F.lit(0))
        .cast("int")
        .alias("channel_key"),
        F.lit(1).cast("int").alias("session_count"),
        F.col("s.duration_seconds").cast("int"),
        F.coalesce(F.col("s.page_view_count"), F.lit(0))
        .cast("int")
        .alias("page_view_count"),
        F.coalesce(F.col("s.add_to_cart_count"), F.lit(0))
        .cast("int")
        .alias("add_to_cart_count"),
        F.col("s.converted_flag").cast("boolean"),
        F.col("s.converted_order_id").cast("long"),
        F.current_timestamp().alias("load_timestamp_utc"),
        F.lit(batch_id).alias("batch_id"),
        F.lit("POSTGRES_DIGITAL").alias("source_system"),
    )
)
merge_fact(fact_web_sessions, "fact_web_sessions", "web_session_key")

# COMMAND ----------
# fact_marketing_spend grain: one date, campaign, and channel.
spend_source = (
    spark.table(f"{catalog}.{silver_schema}.marketing_spend")
    .filter(F.col("batch_id") == batch_id)
    .withColumn("campaign_id", F.col("campaign_id").cast("long"))
    .join(campaign_bridge, "campaign_id", "left")
    .withColumn("channel_code_nk", F.upper(F.trim("channel")))
)
fact_marketing_spend = (
    spend_source.alias("s")
    .join(
        campaigns.alias("c"),
        F.col("s.campaign_code") == F.col("c.campaign_code"),
        "left",
    )
    .join(
        channels.alias("ch"),
        F.col("s.channel_code_nk") == F.col("ch.channel_code"),
        "left",
    )
    .groupBy(
        F.date_format("s.spend_date", "yyyyMMdd")
        .cast("int")
        .alias("spend_date_key"),
        F.coalesce(F.col("c.campaign_key"), F.lit(0))
        .cast("int")
        .alias("campaign_key"),
        F.coalesce(F.col("ch.channel_key"), F.lit(0))
        .cast("int")
        .alias("channel_key"),
        F.upper(F.trim(F.col("s.currency_code"))).alias("currency_code"),
    )
    .agg(
        F.sum("s.spend_amount").cast("decimal(16,2)").alias("spend_amount"),
        F.sum("s.impressions").cast("long").alias("impressions"),
        F.sum("s.clicks").cast("long").alias("clicks"),
    )
    .withColumn(
        "marketing_spend_key",
        big_key("spend_date_key", "campaign_key", "channel_key"),
    )
    .select(
        "marketing_spend_key",
        "spend_date_key",
        "campaign_key",
        "channel_key",
        "spend_amount",
        "impressions",
        "clicks",
        "currency_code",
        F.current_timestamp().alias("load_timestamp_utc"),
        F.lit(batch_id).alias("batch_id"),
        F.lit("POSTGRES_DIGITAL").alias("source_system"),
    )
)
merge_fact(
    fact_marketing_spend,
    "fact_marketing_spend",
    "marketing_spend_key",
)

# COMMAND ----------
fact_contracts = {
    "fact_sales": ("sales_key", ["order_item_id"]),
    "fact_returns": ("return_key", ["return_id"]),
    "fact_inventory_snapshot": (
        "inventory_snapshot_key",
        ["snapshot_date_key", "store_key", "product_key"],
    ),
    "fact_shipments": ("shipment_key", ["shipment_id"]),
    "fact_web_sessions": ("web_session_key", ["session_id"]),
    "fact_marketing_spend": (
        "marketing_spend_key",
        ["spend_date_key", "campaign_key", "channel_key"],
    ),
}
validation_rows = []
for table_name, (key_column, grain) in fact_contracts.items():
    all_rows = spark.table(f"{catalog}.{gold_schema}.{table_name}")
    current_batch = all_rows.filter(F.col("batch_id") == batch_id)
    row_count = all_rows.count()
    current_batch_count = current_batch.count()
    duplicate_keys = (
        all_rows.groupBy(key_column).count().filter(F.col("count") > 1).count()
    )
    duplicate_grain_groups = (
        all_rows.groupBy(*grain).count().filter(F.col("count") > 1).count()
    )
    if row_count == 0 or duplicate_keys or duplicate_grain_groups:
        raise AssertionError(
            f"{table_name} validation failed: rows={row_count}, "
            f"duplicate_keys={duplicate_keys}, "
            f"duplicate_grain_groups={duplicate_grain_groups}"
        )
    if load_mode == "full" and current_batch_count == 0:
        raise AssertionError(
            f"{table_name} has no rows for full-load batch {batch_id}"
        )
    validation_rows.append(
        (
            table_name,
            row_count,
            current_batch_count,
            duplicate_keys,
            duplicate_grain_groups,
            "PASS",
        )
    )

sales_batch = spark.table(f"{catalog}.{gold_schema}.fact_sales").filter(
    F.col("batch_id") == batch_id
)
arithmetic_errors = sales_batch.filter(
    F.abs(
        F.col("net_sales_amount")
        - (F.col("gross_sales_amount") - F.col("discount_amount"))
    )
    > F.lit(0.01)
).count()
if arithmetic_errors:
    raise AssertionError(f"fact_sales has {arithmetic_errors} revenue arithmetic errors")

display(
    spark.createDataFrame(
        validation_rows,
        [
            "table_name",
            "global_row_count",
            "current_batch_row_count",
            "duplicate_keys",
            "duplicate_grain_groups",
            "status",
        ],
    )
)
dbutils.jobs.taskValues.set(key="gold_facts_status", value="PASS")
print("GOLD FACTS PASSED")
