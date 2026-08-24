# Databricks notebook source
# Northstar Retail End-to-End Data Platform
# Track A reads uploaded files/Delta tables and never attempts to reach localhost.

# COMMAND ----------
# MAGIC %md
# MAGIC # 08 — Gold dimensions
# MAGIC Builds the date dimension, Type 1 dimensions, SCD Type 2 customer/product dimensions,
# MAGIC deterministic surrogate keys, and a required key-0 Unknown member in every dimension.

# COMMAND ----------
from __future__ import annotations

from datetime import date, datetime, timezone

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
}.items():
    dbutils.widgets.text(name, default)

catalog = dbutils.widgets.get("catalog")
bronze_schema = dbutils.widgets.get("bronze_schema")
silver_schema = dbutils.widgets.get("silver_schema")
gold_schema = dbutils.widgets.get("gold_schema")
batch_id = dbutils.widgets.get("batch_id")
if batch_id == "MANUAL-REPLACE-ME":
    raise ValueError("Pass batch_id from the Lakeflow Job or set the widget manually.")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{gold_schema}`")

BIG_KEY_MODULUS = 9_007_199_254_740_991  # exact in IEEE-754 and valid in SQL Server BIGINT
INT_KEY_MODULUS = 2_147_483_646  # +1 remains valid in SQL Server INT


def big_key(*columns: str):
    """Return a deterministic positive BIGINT-compatible key; 0 stays reserved."""
    expressions = [F.coalesce(F.col(column).cast("string"), F.lit("<NULL>")) for column in columns]
    return (F.pmod(F.xxhash64(*expressions), F.lit(BIG_KEY_MODULUS)) + 1).cast("long")


def int_key(*columns: str):
    """Return a deterministic positive SQL Server INT-compatible key; 0 stays reserved."""
    expressions = [F.coalesce(F.col(column).cast("string"), F.lit("<NULL>")) for column in columns]
    return (F.pmod(F.xxhash64(*expressions), F.lit(INT_KEY_MODULUS)) + 1).cast("int")


def latest_bronze(table_name: str, key_column: str, *order_columns: str) -> DataFrame:
    """Return the latest known Bronze row per source key across every loaded batch."""
    frame = spark.table(f"{catalog}.{bronze_schema}.{table_name}")
    order = [F.to_timestamp(F.col(column)).desc_nulls_last() for column in order_columns]
    order.append(F.col("_ingested_at_utc").desc_nulls_last())
    window = Window.partitionBy(key_column).orderBy(*order)
    return (
        frame.withColumn("_latest_rank", F.row_number().over(window))
        .filter(F.col("_latest_rank") == 1)
        .drop("_latest_rank")
    )


def latest_in_batch(table_name: str, key_column: str, *order_columns: str) -> DataFrame:
    """Return one latest row per key from the current extraction batch."""
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


def type1_upsert(source: DataFrame, table_name: str, business_key: str) -> None:
    """Insert new rows and overwrite changed attributes for a Type 1 dimension."""
    target_name = f"{catalog}.{gold_schema}.{table_name}"
    source = source.dropDuplicates([business_key])
    has_rows = bool(source.limit(1).count())
    if not spark.catalog.tableExists(target_name):
        source.write.format("delta").mode("overwrite").option(
            "overwriteSchema", "true"
        ).saveAsTable(target_name)
        return
    if not has_rows:
        return
    target = DeltaTable.forName(spark, target_name)
    (
        target.alias("t")
        .merge(source.alias("s"), f"t.`{business_key}` = s.`{business_key}`")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )


def scd2_merge(
    source: DataFrame,
    table_name: str,
    business_key: str,
    hash_columns: list[str],
    surrogate_key: str,
    initial_start_column: str,
) -> None:
    """Expire changed current rows and insert new SCD2 versions idempotently.

    The first version begins on a source-relevant date so historical facts can resolve it.
    A later changed version begins on the processing date. The model intentionally uses
    DATE-effective history; multiple distinct changes to one business key on the same day
    require an agreed timestamp-grain extension before production use.
    """
    target_name = f"{catalog}.{gold_schema}.{table_name}"
    hash_expression = F.sha2(
        F.concat_ws(
            "||",
            *[
                F.coalesce(F.col(column).cast("string"), F.lit("<NULL>"))
                for column in hash_columns
            ],
        ),
        256,
    )
    base = source.dropDuplicates([business_key]).withColumn("record_hash", hash_expression)
    if not spark.catalog.tableExists(target_name):
        initial = (
            base.withColumn(
                "effective_start_date",
                F.coalesce(
                    F.to_date(F.col(initial_start_column)),
                    F.lit("1900-01-01").cast("date"),
                ),
            )
            .withColumn("effective_end_date", F.lit("9999-12-31").cast("date"))
            .withColumn("is_current", F.lit(True))
            .withColumn(
                surrogate_key,
                big_key(business_key, "record_hash", "effective_start_date"),
            )
            .drop(initial_start_column)
        )
        initial.write.format("delta").mode("overwrite").option(
            "overwriteSchema", "true"
        ).saveAsTable(target_name)
        return

    if not base.limit(1).count():
        return

    current = (
        spark.table(target_name)
        .filter(F.col("is_current"))
        .filter(F.col(surrogate_key) != 0)
        .select(
            F.col(business_key),
            F.col("record_hash").alias("_current_hash"),
            F.lit(True).alias("_had_current"),
        )
    )
    changed = (
        base.alias("s")
        .join(current.alias("t"), business_key, "left")
        .filter(
            F.col("_had_current").isNull()
            | (F.col("record_hash") != F.col("_current_hash"))
        )
        .withColumn(
            "effective_start_date",
            F.when(
                F.col("_had_current").isNull(),
                F.coalesce(
                    F.to_date(F.col(initial_start_column)),
                    F.lit("1900-01-01").cast("date"),
                ),
            ).otherwise(F.current_date()),
        )
        .withColumn("effective_end_date", F.lit("9999-12-31").cast("date"))
        .withColumn("is_current", F.lit(True))
        .withColumn(
            surrogate_key,
            big_key(business_key, "record_hash", "effective_start_date"),
        )
    )
    if not changed.limit(1).count():
        return

    changed_existing = changed.filter(F.col("_had_current")).select(
        business_key
    ).distinct()
    if changed_existing.limit(1).count():
        target = DeltaTable.forName(spark, target_name)
        (
            target.alias("t")
            .merge(
                changed_existing.alias("s"),
                f"t.`{business_key}` = s.`{business_key}` AND t.is_current = true",
            )
            .whenMatchedUpdate(
                set={
                    "is_current": "false",
                    "effective_end_date": "date_sub(current_date(), 1)",
                }
            )
            .execute()
        )

    (
        changed.drop("_current_hash", "_had_current", initial_start_column)
        .write.format("delta")
        .mode("append")
        .saveAsTable(target_name)
    )


def merge_unknown(table_name: str, key_column: str, values: dict[str, object]) -> None:
    """Insert or refresh one key-0 Unknown row using the target table's exact schema."""
    target_name = f"{catalog}.{gold_schema}.{table_name}"
    target_frame = spark.table(target_name)
    defaults = {
        "load_timestamp_utc": datetime.now(timezone.utc).replace(tzinfo=None),
        "batch_id": "SYSTEM",
        "source_system": "SYSTEM",
    }
    payload = {**defaults, **values, key_column: 0}
    row = tuple(payload.get(field.name) for field in target_frame.schema.fields)
    source = spark.createDataFrame([row], schema=target_frame.schema)
    target = DeltaTable.forName(spark, target_name)
    (
        target.alias("t")
        .merge(source.alias("s"), f"t.`{key_column}` = s.`{key_column}`")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )


# COMMAND ----------
# One row per date from 2020-01-01 through 2029-12-31 plus key 0 for unknown/not-yet-known dates.
dates = (
    spark.range(0, 3653)
    .select(
        F.date_add(F.lit("2020-01-01").cast("date"), F.col("id").cast("int")).alias(
            "full_date"
        )
    )
    .withColumn("date_key", F.date_format("full_date", "yyyyMMdd").cast("int"))
    .withColumn("day_number", F.dayofmonth("full_date").cast("int"))
    .withColumn("day_name", F.date_format("full_date", "EEEE"))
    .withColumn("week_number", F.weekofyear("full_date").cast("int"))
    .withColumn("month_number", F.month("full_date").cast("int"))
    .withColumn("month_name", F.date_format("full_date", "MMMM"))
    .withColumn("quarter_number", F.quarter("full_date").cast("int"))
    .withColumn("calendar_year", F.year("full_date").cast("int"))
    .withColumn("is_weekend", F.dayofweek("full_date").isin(1, 7))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("source_system", F.lit("GENERATED"))
)
unknown_date = spark.createDataFrame(
    [
        (
            0,
            date(1900, 1, 1),
            1,
            "Unknown",
            1,
            1,
            "Unknown",
            1,
            1900,
            False,
            datetime.now(timezone.utc).replace(tzinfo=None),
            "SYSTEM",
            "SYSTEM",
        )
    ],
    schema=dates.schema,
)
(
    unknown_date.unionByName(dates)
    .write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"{catalog}.{gold_schema}.dim_date")
)

# COMMAND ----------
customers = (
    spark.table(f"{catalog}.{silver_schema}.customers")
    .filter(F.col("batch_id") == batch_id)
    .select(
        "customer_number",
        "first_name",
        "last_name",
        "email",
        "state_code",
        "loyalty_tier",
        "signup_date",
        F.col("signup_date").alias("source_effective_start_date"),
        "load_timestamp_utc",
        "batch_id",
        "source_system",
    )
)
scd2_merge(
    customers,
    "dim_customer",
    "customer_number",
    ["first_name", "last_name", "email", "state_code", "loyalty_tier"],
    "customer_key",
    "source_effective_start_date",
)

products = (
    spark.table(f"{catalog}.{silver_schema}.products")
    .filter(F.col("batch_id") == batch_id)
    .select(
        "sku",
        "product_name",
        "category_name",
        "brand",
        "supplier_code",
        "unit_cost",
        "list_price",
        F.lit("1900-01-01").cast("date").alias("source_effective_start_date"),
        "load_timestamp_utc",
        "batch_id",
        "source_system",
    )
)
scd2_merge(
    products,
    "dim_product",
    "sku",
    [
        "product_name",
        "category_name",
        "brand",
        "supplier_code",
        "unit_cost",
        "list_price",
    ],
    "product_key",
    "source_effective_start_date",
)

# COMMAND ----------
current_stores = latest_in_batch("erp_stores", "store_id", "updated_at")
stores = (
    current_stores.withColumn("store_code", F.upper(F.trim("store_code")))
    .select(
        int_key("store_code").alias("store_key"),
        "store_code",
        F.trim("store_name").alias("store_name"),
        F.trim("region").alias("region"),
        F.upper(F.trim("state_code")).alias("state_code"),
        F.trim("city").alias("city"),
        F.to_date("open_date").alias("open_date"),
        F.col("active_flag").cast("boolean").alias("active_flag"),
        F.current_timestamp().alias("load_timestamp_utc"),
        F.lit(batch_id).alias("batch_id"),
        F.lit("SQLSERVER_ERP").alias("source_system"),
    )
)
type1_upsert(stores, "dim_store", "store_code")

# A changed store attribute (including store_code) changes the denormalized store_code on
# every employee assigned to that store. Rebuild those employees even when no employee row
# was extracted in the current batch.
latest_stores = latest_bronze("erp_stores", "store_id", "updated_at").select(
    F.col("store_id").cast("long").alias("store_id"),
    F.upper(F.trim("store_code")).alias("store_code"),
)
latest_employees = latest_bronze(
    "erp_employees", "employee_id", "updated_at"
).withColumn("employee_id", F.col("employee_id").cast("long"))
changed_employee_ids = latest_in_batch(
    "erp_employees", "employee_id", "updated_at"
).select(F.col("employee_id").cast("long").alias("employee_id"))
changed_store_ids = current_stores.select(
    F.col("store_id").cast("long").alias("store_id")
).distinct()
store_impacted_employee_ids = (
    latest_employees.select("employee_id", F.col("store_id").cast("long").alias("store_id"))
    .join(changed_store_ids, "store_id", "left_semi")
    .select("employee_id")
)
affected_employee_ids = (
    changed_employee_ids.unionByName(store_impacted_employee_ids).distinct()
)
employees = (
    latest_employees.join(affected_employee_ids, "employee_id", "inner")
    .alias("e")
    .join(
        latest_stores.alias("s"),
        F.col("e.store_id").cast("long") == F.col("s.store_id"),
        "left",
    )
    .withColumn("employee_number", F.upper(F.trim(F.col("e.employee_number"))))
    .select(
        int_key("employee_number").alias("employee_key"),
        "employee_number",
        F.concat_ws(
            " ",
            F.initcap(F.trim(F.col("e.first_name"))),
            F.initcap(F.trim(F.col("e.last_name"))),
        ).alias("employee_name"),
        F.trim(F.col("e.job_title")).alias("job_title"),
        F.col("s.store_code").alias("store_code"),
        F.col("e.active_flag").cast("boolean").alias("active_flag"),
        F.current_timestamp().alias("load_timestamp_utc"),
        F.lit(batch_id).alias("batch_id"),
        F.lit("SQLSERVER_ERP").alias("source_system"),
    )
)
type1_upsert(employees, "dim_employee", "employee_number")

suppliers = (
    latest_in_batch("erp_suppliers", "supplier_id", "updated_at")
    .withColumn("supplier_code", F.upper(F.trim("supplier_code")))
    .select(
        int_key("supplier_code").alias("supplier_key"),
        "supplier_code",
        F.trim("supplier_name").alias("supplier_name"),
        F.upper(F.trim("country_code")).alias("country_code"),
        F.col("lead_time_days").cast("int").alias("lead_time_days"),
        F.col("active_flag").cast("boolean").alias("active_flag"),
        F.current_timestamp().alias("load_timestamp_utc"),
        F.lit(batch_id).alias("batch_id"),
        F.lit("SQLSERVER_ERP").alias("source_system"),
    )
)
type1_upsert(suppliers, "dim_supplier", "supplier_code")

promotions = (
    spark.table(f"{catalog}.{silver_schema}.promotions")
    .filter(F.col("batch_id") == batch_id)
    .withColumn("promotion_code", F.upper(F.trim("promotion_code")))
    .select(
        int_key("promotion_code").alias("promotion_key"),
        "promotion_code",
        "promotion_name",
        "discount_type",
        "discount_value",
        "start_date",
        "end_date",
        "channel_code",
        "load_timestamp_utc",
        "batch_id",
        "source_system",
    )
)
type1_upsert(promotions, "dim_promotion", "promotion_code")

channels = (
    spark.createDataFrame(
        [
            (1, "STORE", "Store", "Sales"),
            (2, "ONLINE", "Online", "Sales"),
            (3, "PAID SEARCH", "Paid Search", "Marketing"),
            (4, "SOCIAL", "Social", "Marketing"),
            (5, "EMAIL", "Email", "Marketing"),
            (6, "AFFILIATE", "Affiliate", "Marketing"),
            (7, "ORGANIC", "Organic", "Marketing"),
            (8, "DIRECT", "Direct", "Marketing"),
        ],
        ["channel_key", "channel_code", "channel_name", "channel_group"],
    )
    .withColumn("channel_key", F.col("channel_key").cast("int"))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("source_system", F.lit("CONFORMED"))
)
type1_upsert(channels, "dim_channel", "channel_code")

campaigns = (
    spark.table(f"{catalog}.{silver_schema}.campaigns")
    .filter(F.col("batch_id") == batch_id)
    .withColumn("campaign_code", F.upper(F.trim("campaign_code")))
    .select(
        int_key("campaign_code").alias("campaign_key"),
        "campaign_code",
        "campaign_name",
        "channel",
        "start_date",
        "end_date",
        "budget_amount",
        "currency_code",
        "load_timestamp_utc",
        "batch_id",
        "source_system",
    )
)
type1_upsert(campaigns, "dim_campaign", "campaign_code")

# COMMAND ----------
merge_unknown(
    "dim_customer",
    "customer_key",
    {
        "customer_number": "UNKNOWN",
        "first_name": "Unknown",
        "last_name": "Unknown",
        "loyalty_tier": "Unknown",
        "effective_start_date": date(1900, 1, 1),
        "effective_end_date": date(9999, 12, 31),
        "is_current": True,
    },
)
merge_unknown(
    "dim_product",
    "product_key",
    {
        "sku": "UNKNOWN",
        "product_name": "Unknown Product",
        "category_name": "Unknown",
        "brand": "Unknown",
        "supplier_code": "UNKNOWN",
        "effective_start_date": date(1900, 1, 1),
        "effective_end_date": date(9999, 12, 31),
        "is_current": True,
    },
)
merge_unknown(
    "dim_store",
    "store_key",
    {
        "store_code": "UNKNOWN",
        "store_name": "Unknown Store",
        "region": "Unknown",
        "active_flag": False,
    },
)
merge_unknown(
    "dim_employee",
    "employee_key",
    {
        "employee_number": "UNKNOWN",
        "employee_name": "Unknown Employee",
        "active_flag": False,
    },
)
merge_unknown(
    "dim_supplier",
    "supplier_key",
    {
        "supplier_code": "UNKNOWN",
        "supplier_name": "Unknown Supplier",
        "active_flag": False,
    },
)
merge_unknown(
    "dim_promotion",
    "promotion_key",
    {"promotion_code": "NONE", "promotion_name": "No Promotion"},
)
merge_unknown(
    "dim_channel",
    "channel_key",
    {
        "channel_code": "UNKNOWN",
        "channel_name": "Unknown Channel",
        "channel_group": "Unknown",
    },
)
merge_unknown(
    "dim_campaign",
    "campaign_key",
    {"campaign_code": "NONE", "campaign_name": "No Campaign"},
)

# COMMAND ----------
dimension_keys = {
    "dim_date": "date_key",
    "dim_customer": "customer_key",
    "dim_product": "product_key",
    "dim_store": "store_key",
    "dim_employee": "employee_key",
    "dim_supplier": "supplier_key",
    "dim_promotion": "promotion_key",
    "dim_channel": "channel_key",
    "dim_campaign": "campaign_key",
}
validation_rows = []
for table_name, key_column in dimension_keys.items():
    frame = spark.table(f"{catalog}.{gold_schema}.{table_name}")
    rows = frame.count()
    duplicate_keys = rows - frame.select(key_column).distinct().count()
    unknown_rows = frame.filter(F.col(key_column) == 0).count()
    if rows == 0 or duplicate_keys != 0 or unknown_rows != 1:
        raise AssertionError(
            f"{table_name} validation failed: rows={rows}, "
            f"duplicate_keys={duplicate_keys}, unknown_rows={unknown_rows}"
        )
    validation_rows.append((table_name, rows, duplicate_keys, unknown_rows, "PASS"))

for table_name, business_key in {
    "dim_customer": "customer_number",
    "dim_product": "sku",
}.items():
    current_duplicates = (
        spark.table(f"{catalog}.{gold_schema}.{table_name}")
        .filter(F.col("is_current"))
        .filter(F.col(business_key) != "UNKNOWN")
        .groupBy(business_key)
        .count()
        .filter(F.col("count") > 1)
        .count()
    )
    if current_duplicates:
        raise AssertionError(
            f"{table_name} has {current_duplicates} business keys with multiple current rows"
        )

# Every non-unknown SCD2 row must have a valid inclusive effective-date interval.
for table_name, key_column in {
    "dim_customer": "customer_key",
    "dim_product": "product_key",
}.items():
    invalid_ranges = (
        spark.table(f"{catalog}.{gold_schema}.{table_name}")
        .filter(F.col(key_column) != 0)
        .filter(F.col("effective_end_date") < F.col("effective_start_date"))
        .count()
    )
    if invalid_ranges:
        raise AssertionError(f"{table_name} has {invalid_ranges} invalid SCD2 date ranges")

display(
    spark.createDataFrame(
        validation_rows,
        ["table_name", "row_count", "duplicate_keys", "unknown_rows", "status"],
    )
)
dbutils.jobs.taskValues.set(key="gold_dimensions_status", value="PASS")
print("GOLD DIMENSIONS PASSED")
