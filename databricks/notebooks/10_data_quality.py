# Databricks notebook source
# Northstar Retail End-to-End Data Platform
# Track A reads uploaded Delta tables and never attempts to reach localhost.

# COMMAND ----------
# MAGIC %md
# MAGIC # 10 — Blocking data-quality gate
# MAGIC Validates global table integrity plus the current batch. Full loads require rows in
# MAGIC every fact; incremental loads may legitimately have zero affected rows in a subject.
# MAGIC Required failures raise an exception and prevent Gold publication.

# COMMAND ----------
from __future__ import annotations

from pyspark.sql import functions as F

for name, default in {
    "catalog": "northstar_retail",
    "silver_schema": "silver",
    "gold_schema": "gold",
    "quality_schema": "quality",
    "batch_id": "MANUAL-REPLACE-ME",
    "load_mode": "full",
}.items():
    dbutils.widgets.text(name, default)

catalog = dbutils.widgets.get("catalog")
silver_schema = dbutils.widgets.get("silver_schema")
gold_schema = dbutils.widgets.get("gold_schema")
quality_schema = dbutils.widgets.get("quality_schema")
batch_id = dbutils.widgets.get("batch_id")
load_mode = dbutils.widgets.get("load_mode").strip().lower()
if batch_id == "MANUAL-REPLACE-ME":
    raise ValueError("Pass batch_id from the Lakeflow Job or set the widget manually.")
if load_mode not in {"full", "incremental"}:
    raise ValueError("load_mode must be 'full' or 'incremental'.")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{quality_schema}`")
checks = []


def record(
    name: str,
    actual: float,
    expected: float,
    operator: str,
    *,
    required: bool = True,
    details: str = "",
) -> None:
    passed = {
        "==": actual == expected,
        ">=": actual >= expected,
        "<=": actual <= expected,
    }[operator]
    checks.append(
        (
            batch_id,
            name,
            float(actual),
            float(expected),
            operator,
            "PASS" if passed else "FAIL",
            required,
            details,
        )
    )


def duplicate_groups(frame, columns: list[str]) -> int:
    return frame.groupBy(*columns).count().filter(F.col("count") > 1).count()


def orphan_count(fact, fact_column: str, dimension, dimension_column: str) -> int:
    return (
        fact.select(F.col(fact_column).alias("fact_key"))
        .distinct()
        .join(
            dimension.select(
                F.col(dimension_column).alias("dimension_key")
            ).distinct(),
            F.col("fact_key") == F.col("dimension_key"),
            "left_anti",
        )
        .count()
    )


def persist_results():
    results = (
        spark.createDataFrame(
            checks,
            [
                "batch_id",
                "check_name",
                "actual_value",
                "expected_value",
                "operator",
                "status",
                "required_flag",
                "details",
            ],
        )
        .withColumn("checked_at_utc", F.current_timestamp())
    )
    full_results = f"{catalog}.{quality_schema}.test_results"
    if spark.catalog.tableExists(full_results):
        escaped_batch = batch_id.replace("'", "''")
        spark.sql(
            f"DELETE FROM `{catalog}`.`{quality_schema}`.`test_results` "
            f"WHERE batch_id = '{escaped_batch}'"
        )
    (
        results.write.format("delta")
        .mode("append")
        .option("mergeSchema", "true")
        .saveAsTable(full_results)
    )
    return results, full_results


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
dimensions = {}
missing_objects = []
for table_name, key_column in dimension_keys.items():
    full_name = f"{catalog}.{gold_schema}.{table_name}"
    exists = spark.catalog.tableExists(full_name)
    record(f"{table_name}_exists", int(exists), 1, "==", details=full_name)
    if not exists:
        missing_objects.append(full_name)
        continue
    frame = spark.table(full_name)
    dimensions[table_name] = frame
    record(f"{table_name}_not_empty", frame.count(), 1, ">=")
    record(
        f"{table_name}_unique_key",
        duplicate_groups(frame, [key_column]),
        0,
        "==",
    )
    record(
        f"{table_name}_one_unknown_member",
        frame.filter(F.col(key_column) == 0).count(),
        1,
        "==",
    )

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
facts_all = {}
facts_batch = {}
for table_name, (key_column, grain) in fact_contracts.items():
    full_name = f"{catalog}.{gold_schema}.{table_name}"
    exists = spark.catalog.tableExists(full_name)
    record(f"{table_name}_exists", int(exists), 1, "==", details=full_name)
    if not exists:
        missing_objects.append(full_name)
        continue
    all_rows = spark.table(full_name)
    batch_rows = all_rows.filter(F.col("batch_id") == batch_id)
    facts_all[table_name] = all_rows
    facts_batch[table_name] = batch_rows
    record(f"{table_name}_global_not_empty", all_rows.count(), 1, ">=")
    record(
        f"{table_name}_global_unique_key",
        duplicate_groups(all_rows, [key_column]),
        0,
        "==",
    )
    record(
        f"{table_name}_global_unique_grain",
        duplicate_groups(all_rows, grain),
        0,
        "==",
    )
    record(
        f"{table_name}_batch_not_empty",
        batch_rows.count(),
        1,
        ">=",
        required=load_mode == "full",
        details=f"load_mode={load_mode}; zero rows are allowed only for incremental subjects",
    )
    record(
        f"{table_name}_batch_unique_grain",
        duplicate_groups(batch_rows, grain),
        0,
        "==",
    )

if missing_objects:
    results, full_results = persist_results()
    display(results.orderBy(F.col("status").asc(), F.col("check_name")))
    try:
        dbutils.jobs.taskValues.set(key="quality_status", value="FAIL")
    except Exception:
        pass
    raise AssertionError(
        "QUALITY GATE FAILED: required Gold objects are missing: "
        + ", ".join(sorted(missing_objects))
        + f". Inspect {full_results}."
    )

# COMMAND ----------
sales = facts_batch["fact_sales"]
record(
    "fact_sales_positive_quantity",
    sales.filter(F.col("quantity") <= 0).count(),
    0,
    "==",
)
record(
    "fact_sales_revenue_identity",
    sales.filter(
        F.abs(
            F.col("net_sales_amount")
            - (F.col("gross_sales_amount") - F.col("discount_amount"))
        )
        > F.lit(0.01)
    ).count(),
    0,
    "==",
)
record(
    "fact_sales_profit_identity",
    sales.filter(
        F.abs(
            F.col("gross_profit_amount")
            - (F.col("net_sales_amount") - F.col("cost_of_goods_sold"))
        )
        > F.lit(0.01)
    ).count(),
    0,
    "==",
)

# Unknown-key shares are visible. Anonymous web users and campaign-less sessions are
# expected and are warnings rather than hidden failures.
for table_name, column, threshold, required in [
    ("fact_sales", "customer_key", 0.05, True),
    ("fact_sales", "product_key", 0.05, True),
    ("fact_returns", "product_key", 0.15, True),
    ("fact_web_sessions", "customer_key", 1.00, False),
    ("fact_web_sessions", "campaign_key", 1.00, False),
]:
    frame = facts_batch[table_name]
    total = frame.count()
    share = frame.filter(F.col(column) == 0).count() / max(1, total)
    record(
        f"{table_name}_{column}_unknown_share",
        share,
        threshold,
        "<=",
        required=required,
        details=f"current_batch_rows={total}",
    )

references = {
    "fact_sales": {
        "order_date_key": ("dim_date", "date_key"),
        "customer_key": ("dim_customer", "customer_key"),
        "product_key": ("dim_product", "product_key"),
        "store_key": ("dim_store", "store_key"),
        "employee_key": ("dim_employee", "employee_key"),
        "promotion_key": ("dim_promotion", "promotion_key"),
        "channel_key": ("dim_channel", "channel_key"),
    },
    "fact_returns": {
        "return_date_key": ("dim_date", "date_key"),
        "customer_key": ("dim_customer", "customer_key"),
        "product_key": ("dim_product", "product_key"),
        "store_key": ("dim_store", "store_key"),
    },
    "fact_inventory_snapshot": {
        "snapshot_date_key": ("dim_date", "date_key"),
        "store_key": ("dim_store", "store_key"),
        "product_key": ("dim_product", "product_key"),
    },
    "fact_shipments": {
        "ship_date_key": ("dim_date", "date_key"),
        "promised_date_key": ("dim_date", "date_key"),
        "delivery_date_key": ("dim_date", "date_key"),
        "customer_key": ("dim_customer", "customer_key"),
        "store_key": ("dim_store", "store_key"),
    },
    "fact_web_sessions": {
        "session_date_key": ("dim_date", "date_key"),
        "customer_key": ("dim_customer", "customer_key"),
        "campaign_key": ("dim_campaign", "campaign_key"),
        "channel_key": ("dim_channel", "channel_key"),
    },
    "fact_marketing_spend": {
        "spend_date_key": ("dim_date", "date_key"),
        "campaign_key": ("dim_campaign", "campaign_key"),
        "channel_key": ("dim_channel", "channel_key"),
    },
}
for fact_name, mapping in references.items():
    for fact_column, (dimension_name, dimension_column) in mapping.items():
        count = orphan_count(
            facts_all[fact_name],
            fact_column,
            dimensions[dimension_name],
            dimension_column,
        )
        record(
            f"{fact_name}_{fact_column}_referential_integrity",
            count,
            0,
            "==",
        )

# COMMAND ----------
# Silver-to-Gold reconciliation for the same affected batch.
silver_sales = spark.table(f"{catalog}.{silver_schema}.sales").filter(
    F.col("batch_id") == batch_id
)
record("silver_to_gold_sales_rows", sales.count(), silver_sales.count(), "==")
silver_net = silver_sales.agg(F.sum("net_sales_amount")).first()[0] or 0
gold_net = sales.agg(F.sum("net_sales_amount")).first()[0] or 0
record(
    "silver_to_gold_net_sales_difference",
    abs(float(gold_net) - float(silver_net)),
    0.01,
    "<=",
    details=f"silver={silver_net}; gold={gold_net}",
)

results, full_results = persist_results()
display(results.orderBy(F.col("status").asc(), F.col("check_name")))
failed = results.filter(
    F.col("required_flag") & (F.col("status") == "FAIL")
).count()
try:
    dbutils.jobs.taskValues.set(
        key="quality_status", value="PASS" if failed == 0 else "FAIL"
    )
except Exception:
    pass
if failed:
    raise AssertionError(
        f"QUALITY GATE FAILED: {failed} required checks failed. "
        f"Inspect {full_results} before repairing the run."
    )
print(f"QUALITY GATE PASSED: {results.count()} checks, 0 required failures")
