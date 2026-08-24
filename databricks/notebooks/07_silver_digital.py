# Databricks notebook source
# Northstar Retail End-to-End Data Platform
# Track A reads uploaded Delta tables and never attempts to reach localhost.

# COMMAND ----------
# MAGIC %md
# MAGIC # 07 — Silver digital and marketing data
# MAGIC Rebuilds sessions affected by new session or event records, normalizes UTC timestamps,
# MAGIC quarantines invalid event order, and cleans campaign, spend, user, and touchpoint data.

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
users = latest_in_batch("digital_web_users", "web_user_id", "updated_at")
clean_users = (
    users.withColumn("web_user_id", F.col("web_user_id").cast("long"))
    .withColumn("customer_id", F.col("customer_id").cast("long"))
    .withColumn("anonymous_cookie_id", F.lower(F.trim("anonymous_cookie_id")))
    .withColumn("email_hash", F.lower(F.trim("email_hash")))
    .withColumn("created_at_utc", F.to_timestamp("created_at"))
    .withColumn("updated_at_utc", F.to_timestamp("updated_at"))
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("source_system", F.lit("POSTGRES_DIGITAL"))
)
user_rejects = clean_users.filter(
    F.col("web_user_id").isNull()
    | F.col("anonymous_cookie_id").isNull()
    | (F.length("anonymous_cookie_id") == 0)
)
quarantine(user_rejects, "INVALID_WEB_USER", "web_user_quarantine")
replace_batch(
    clean_users.join(user_rejects.select("web_user_id"), "web_user_id", "left_anti"),
    "web_users",
)

# COMMAND ----------
current_sessions = spark.table(
    f"{catalog}.{bronze_schema}.digital_web_sessions"
).filter(F.col("_batch_id") == batch_id)
current_events = spark.table(f"{catalog}.{bronze_schema}.digital_web_events").filter(
    F.col("_batch_id") == batch_id
)
latest_sessions = latest_by_key(
    "digital_web_sessions",
    "session_id",
    "created_at",
).withColumn("session_id", F.col("session_id").cast("long"))
changed_web_user_ids = users.select(
    F.col("web_user_id").cast("long").alias("web_user_id")
).distinct()
user_impacted_session_ids = (
    latest_sessions.withColumn("web_user_id", F.col("web_user_id").cast("long"))
    .join(changed_web_user_ids, "web_user_id", "left_semi")
    .select("session_id")
)
affected_session_ids = (
    current_sessions.select(F.col("session_id").cast("long").alias("session_id"))
    .unionByName(
        current_events.select(F.col("session_id").cast("long").alias("session_id"))
    )
    .unionByName(user_impacted_session_ids)
    .filter(F.col("session_id").isNotNull())
    .distinct()
)
latest_events = latest_by_key(
    "digital_web_events",
    "event_id",
    "created_at",
).withColumn("session_id", F.col("session_id").cast("long"))

session_candidates = latest_sessions.join(
    affected_session_ids,
    "session_id",
    "inner",
)
clean_sessions = (
    session_candidates.withColumn(
        "session_start_utc",
        F.to_utc_timestamp(F.to_timestamp("session_start_utc"), "UTC"),
    )
    .withColumn(
        "session_end_utc",
        F.to_utc_timestamp(F.to_timestamp("session_end_utc"), "UTC"),
    )
    .withColumn("source_channel", F.initcap(F.trim("source_channel")))
    .withColumn("device_type", F.lower(F.trim("device_type")))
    .withColumn(
        "duration_seconds",
        F.col("session_end_utc").cast("long")
        - F.col("session_start_utc").cast("long"),
    )
    .withColumn("converted_flag", F.col("converted_order_id").isNotNull())
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("source_system", F.lit("POSTGRES_DIGITAL"))
)
session_rejects = clean_sessions.filter(
    F.col("session_start_utc").isNull()
    | F.col("session_end_utc").isNull()
    | (F.col("duration_seconds") < 0)
)
quarantine(session_rejects, "INVALID_WEB_SESSION", "digital_session_quarantine")
valid_sessions = clean_sessions.join(
    session_rejects.select("session_id"),
    "session_id",
    "left_anti",
)
replace_batch(valid_sessions, "web_sessions")

# Rebuild all events for affected sessions. This makes an event-only incremental batch
# refresh the complete page-view and add-to-cart totals for its existing session.
event_candidates = latest_events.join(
    affected_session_ids,
    "session_id",
    "inner",
)
clean_events = (
    event_candidates.withColumn(
        "event_timestamp_utc",
        F.to_utc_timestamp(F.to_timestamp("event_timestamp"), "UTC"),
    )
    .withColumn("event_type", F.lower(F.trim("event_type")))
    .join(
        valid_sessions.select("session_id", "session_start_utc"),
        "session_id",
        "left",
    )
    .withColumn(
        "out_of_order_flag",
        F.col("event_timestamp_utc") < F.col("session_start_utc"),
    )
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("source_system", F.lit("POSTGRES_DIGITAL"))
)
event_rejects = clean_events.filter(
    F.col("session_start_utc").isNull()
    | F.col("event_timestamp_utc").isNull()
    | F.coalesce(F.col("out_of_order_flag"), F.lit(True))
)
quarantine(
    event_rejects,
    "MISSING_SESSION_OR_OUT_OF_ORDER_EVENT",
    "digital_event_quarantine",
)
valid_events = clean_events.join(
    event_rejects.select("event_id"),
    "event_id",
    "left_anti",
)
replace_batch(valid_events, "web_events")

# COMMAND ----------
campaigns = latest_in_batch("digital_campaigns", "campaign_id", "updated_at")
clean_campaigns = (
    campaigns.withColumn("campaign_id", F.col("campaign_id").cast("long"))
    .withColumn("campaign_code", F.upper(F.trim("campaign_code")))
    .withColumn("campaign_name", F.trim("campaign_name"))
    .withColumn("channel", F.initcap(F.trim("channel")))
    .withColumn("start_date", F.to_date("start_date"))
    .withColumn("end_date", F.to_date("end_date"))
    .withColumn("budget_amount", F.col("budget_amount").cast("decimal(14,2)"))
    .withColumn("currency_code", F.upper(F.trim("currency_code")))
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("source_system", F.lit("POSTGRES_DIGITAL"))
)
campaign_rejects = clean_campaigns.filter(
    F.col("campaign_code").isNull()
    | F.col("start_date").isNull()
    | F.col("end_date").isNull()
    | (F.col("end_date") < F.col("start_date"))
    | (F.col("budget_amount") < 0)
)
quarantine(campaign_rejects, "INVALID_CAMPAIGN", "campaign_quarantine")
replace_batch(
    clean_campaigns.join(
        campaign_rejects.select("campaign_id"),
        "campaign_id",
        "left_anti",
    ),
    "campaigns",
)

spend = latest_in_batch("digital_marketing_spend", "spend_id", "created_at")
clean_spend = (
    spend.withColumn("spend_id", F.col("spend_id").cast("long"))
    .withColumn("campaign_id", F.col("campaign_id").cast("long"))
    .withColumn("spend_date", F.to_date("spend_date"))
    .withColumn("channel", F.initcap(F.trim("channel")))
    .withColumn("spend_amount", F.col("spend_amount").cast("decimal(14,2)"))
    .withColumn("impressions", F.col("impressions").cast("long"))
    .withColumn("clicks", F.col("clicks").cast("long"))
    .withColumn("currency_code", F.upper(F.trim("currency_code")))
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("source_system", F.lit("POSTGRES_DIGITAL"))
)
spend_rejects = clean_spend.filter(
    F.col("spend_date").isNull()
    | (F.col("spend_amount") < 0)
    | (F.col("impressions") < 0)
    | (F.col("clicks") < 0)
    | (F.col("currency_code") != "USD")
)
quarantine(
    spend_rejects,
    "NEGATIVE_OR_NON_USD_SPEND",
    "marketing_spend_quarantine",
)
replace_batch(
    clean_spend.join(spend_rejects.select("spend_id"), "spend_id", "left_anti"),
    "marketing_spend",
)

touchpoints = latest_in_batch(
    "digital_campaign_touchpoints",
    "touchpoint_id",
    "created_at",
)
clean_touchpoints = (
    touchpoints.withColumn("touchpoint_id", F.col("touchpoint_id").cast("long"))
    .withColumn("web_user_id", F.col("web_user_id").cast("long"))
    .withColumn("session_id", F.col("session_id").cast("long"))
    .withColumn("campaign_id", F.col("campaign_id").cast("long"))
    .withColumn("touchpoint_timestamp_utc", F.to_timestamp("touchpoint_timestamp"))
    .withColumn("touchpoint_type", F.upper(F.trim("touchpoint_type")))
    .withColumn("attribution_weight", F.col("attribution_weight").cast("decimal(8,6)"))
    .withColumn("batch_id", F.lit(batch_id))
    .withColumn("load_timestamp_utc", F.current_timestamp())
    .withColumn("source_system", F.lit("POSTGRES_DIGITAL"))
)
touchpoint_rejects = clean_touchpoints.filter(
    F.col("campaign_id").isNull()
    | F.col("touchpoint_timestamp_utc").isNull()
    | (F.col("attribution_weight") < 0)
    | (F.col("attribution_weight") > 1)
)
quarantine(
    touchpoint_rejects,
    "INVALID_CAMPAIGN_TOUCHPOINT",
    "campaign_touchpoint_quarantine",
)
replace_batch(
    clean_touchpoints.join(
        touchpoint_rejects.select("touchpoint_id"),
        "touchpoint_id",
        "left_anti",
    ),
    "campaign_touchpoints",
)

print(
    {
        "affected_sessions": affected_session_ids.count(),
        "valid_sessions": valid_sessions.count(),
        "valid_events": valid_events.count(),
        "event_quarantine": event_rejects.count(),
        "campaigns": clean_campaigns.count(),
        "marketing_spend": clean_spend.count(),
    }
)
dbutils.jobs.taskValues.set(key="silver_digital_status", value="PASS")
