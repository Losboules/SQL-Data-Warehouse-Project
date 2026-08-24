# Databricks notebook source
# Northstar Retail End-to-End Data Platform

# COMMAND ----------
# MAGIC %md
# MAGIC # 12 — Final KPI and reconciliation queries
# MAGIC Produces a compact batch summary that can be compared with the SQL Server warehouse and Power BI.

# COMMAND ----------
from __future__ import annotations

from pyspark.sql import functions as F

for name, default in {
    "catalog": "northstar_retail",
    "gold_schema": "gold",
    "quality_schema": "quality",
    "batch_id": "MANUAL-REPLACE-ME",
}.items():
    dbutils.widgets.text(name, default)

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
quality_schema = dbutils.widgets.get("quality_schema")
batch_id = dbutils.widgets.get("batch_id")
if batch_id == "MANUAL-REPLACE-ME":
    raise ValueError("Pass batch_id from the Lakeflow Job or set the widget manually.")

sales = spark.table(f"{catalog}.{gold_schema}.fact_sales").filter(F.col("batch_id") == batch_id)
returns = spark.table(f"{catalog}.{gold_schema}.fact_returns").filter(F.col("batch_id") == batch_id)
shipments = spark.table(f"{catalog}.{gold_schema}.fact_shipments").filter(F.col("batch_id") == batch_id)
sessions = spark.table(f"{catalog}.{gold_schema}.fact_web_sessions").filter(F.col("batch_id") == batch_id)
spend = spark.table(f"{catalog}.{gold_schema}.fact_marketing_spend").filter(F.col("batch_id") == batch_id)

summary = spark.createDataFrame(
    [
        (
            batch_id,
            sales.select("order_id").distinct().count(),
            sales.count(),
            float(sales.agg(F.sum("net_sales_amount")).first()[0] or 0),
            float(sales.agg(F.sum("gross_profit_amount")).first()[0] or 0),
            returns.count(),
            float(returns.agg(F.sum("refund_amount")).first()[0] or 0),
            shipments.count(),
            shipments.filter(F.col("on_time_flag")).count(),
            sessions.count(),
            sessions.filter(F.col("converted_flag")).count(),
            float(spend.agg(F.sum("spend_amount")).first()[0] or 0),
        )
    ],
    [
        "batch_id",
        "orders",
        "sales_lines",
        "net_sales_amount",
        "gross_profit_amount",
        "returns",
        "refund_amount",
        "shipments",
        "on_time_shipments",
        "web_sessions",
        "converted_sessions",
        "marketing_spend",
    ],
).withColumn("checked_at_utc", F.current_timestamp())

summary = (
    summary
    .withColumn("gross_margin_percentage", F.when(F.col("net_sales_amount") != 0, F.col("gross_profit_amount") / F.col("net_sales_amount")))
    .withColumn("on_time_delivery_percentage", F.when(F.col("shipments") != 0, F.col("on_time_shipments") / F.col("shipments")))
    .withColumn("conversion_rate", F.when(F.col("web_sessions") != 0, F.col("converted_sessions") / F.col("web_sessions")))
)

full_name = f"{catalog}.{quality_schema}.final_reconciliation"
if spark.catalog.tableExists(full_name):
    escaped_batch = batch_id.replace("'", "''")
    spark.sql(f"DELETE FROM `{catalog}`.`{quality_schema}`.`final_reconciliation` WHERE batch_id = '{escaped_batch}'")
summary.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(full_name)
display(summary)

monthly = (
    sales.join(spark.table(f"{catalog}.{gold_schema}.dim_date"), sales.order_date_key == F.col("date_key"), "left")
    .groupBy("calendar_year", "month_number", "month_name")
    .agg(
        F.sum("net_sales_amount").alias("net_sales_amount"),
        F.sum("gross_profit_amount").alias("gross_profit_amount"),
        F.countDistinct("order_id").alias("orders"),
    )
    .orderBy("calendar_year", "month_number")
)
display(monthly)
dbutils.jobs.taskValues.set(key="final_reconciliation_status", value="PASS")
print("FINAL RECONCILIATION PASSED")
