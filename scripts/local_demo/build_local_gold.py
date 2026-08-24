"""Build a deterministic local pandas version of the Northstar Gold model.

This module is a locally executable parity harness for the Databricks design.  It
reads the generated CSV/JSON fixture, applies the same core conformance rules, and
writes all nine dimensions and six facts as CSV exports.  It does not replace the
Databricks implementation; it gives contributors and CI a way to validate grains,
keys, arithmetic, and reconciliation without cloud credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from scripts.utilities.checksums import sha256_file
from scripts.utilities.logging_utils import configure_logging

LOGGER = logging.getLogger("northstar.local_gold")

DIMENSION_TABLES = [
    "dim_date",
    "dim_customer",
    "dim_product",
    "dim_store",
    "dim_employee",
    "dim_supplier",
    "dim_promotion",
    "dim_channel",
    "dim_campaign",
]
FACT_TABLES = [
    "fact_sales",
    "fact_returns",
    "fact_inventory_snapshot",
    "fact_shipments",
    "fact_web_sessions",
    "fact_marketing_spend",
]
ALL_TABLES = DIMENSION_TABLES + FACT_TABLES


@dataclass(frozen=True)
class BuildContext:
    input_dir: Path
    output_dir: Path
    batch_id: str
    load_timestamp_utc: str


def stable_key(*values: Any) -> int:
    """Return a deterministic positive 63-bit integer; key 0 stays reserved for Unknown."""
    payload = "||".join("<NULL>" if pd.isna(value) else str(value) for value in values)
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % 9_007_199_254_740_991 + 1


def stable_int_key(*values: Any) -> int:
    """Return a deterministic positive SQL Server INT-compatible surrogate key."""
    payload = "||".join("<NULL>" if pd.isna(value) else str(value) for value in values)
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % 2_147_483_646 + 1


def record_hash(values: Iterable[Any]) -> str:
    payload = "||".join("<NULL>" if pd.isna(value) else str(value) for value in values)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()



def lookup_key(series: pd.Series, mapping: dict[Any, int]) -> pd.Series:
    """Map to 64-bit surrogate keys without passing through lossy float values."""
    return series.map(mapping).map(lambda value: int(value) if pd.notna(value) else 0).astype("int64")


def date_key(value: Any) -> int:
    if pd.isna(value):
        return 0
    parsed = pd.Timestamp(value)
    return int(parsed.strftime("%Y%m%d"))


def read_csv(path: Path, **kwargs: Any) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, **kwargs)


def normalize_text(series: pd.Series, *, upper: bool = False, title: bool = False) -> pd.Series:
    cleaned = series.astype("string").str.strip()
    if upper:
        cleaned = cleaned.str.upper()
    if title:
        cleaned = cleaned.str.lower().str.title()
    return cleaned


def add_audit(frame: pd.DataFrame, context: BuildContext, source_system: str) -> pd.DataFrame:
    result = frame.copy()
    result["load_timestamp_utc"] = context.load_timestamp_utc
    result["batch_id"] = context.batch_id
    result["source_system"] = source_system
    return result


def build_dimensions(context: BuildContext) -> tuple[dict[str, pd.DataFrame], dict[str, dict[Any, int]]]:
    root = context.input_dir
    sql = root / "sqlserver"
    digital = root / "postgres"
    feeds = root / "files"

    customers = read_csv(sql / "customers.csv")
    addresses = read_csv(sql / "addresses.csv")
    products = read_csv(sql / "products.csv")
    categories = read_csv(sql / "product_categories.csv")
    suppliers = read_csv(sql / "suppliers.csv")
    stores = read_csv(sql / "stores.csv")
    employees = read_csv(sql / "employees.csv")
    promotions = read_csv(feeds / "promotion_calendar.csv")
    campaigns = read_csv(digital / "campaigns.csv")
    costs = read_csv(feeds / "supplier_cost_updates.csv")

    # One current customer row per natural key, choosing the most recently updated source record.
    customers["customer_number"] = normalize_text(customers["customer_number"], upper=True)
    customers["updated_at_parsed"] = pd.to_datetime(customers["updated_at"], utc=True)
    customer_winners = (
        customers.sort_values(["customer_number", "updated_at_parsed", "customer_id"])
        .drop_duplicates("customer_number", keep="last")
        .copy()
    )
    addresses["updated_at_parsed"] = pd.to_datetime(addresses["updated_at"], utc=True)
    addresses["is_default_num"] = pd.to_numeric(addresses["is_default"], errors="coerce").fillna(0)
    address_winners = (
        addresses.sort_values(["customer_id", "is_default_num", "updated_at_parsed", "address_id"])
        .drop_duplicates("customer_id", keep="last")[["customer_id", "state_code"]]
    )
    customer_winners = customer_winners.merge(address_winners, on="customer_id", how="left")
    customer_winners["first_name"] = normalize_text(customer_winners["first_name"], title=True)
    customer_winners["last_name"] = normalize_text(customer_winners["last_name"], title=True)
    customer_winners["email"] = normalize_text(customer_winners["email"]).str.lower()
    customer_winners["state_code"] = normalize_text(customer_winners["state_code"], upper=True)
    customer_winners["loyalty_tier"] = normalize_text(customer_winners["loyalty_tier"], title=True)
    customer_winners["signup_date"] = pd.to_datetime(customer_winners["signup_date"]).dt.date.astype("string")
    customer_winners["customer_key"] = customer_winners["customer_number"].map(stable_key)
    hash_cols = ["first_name", "last_name", "email", "state_code", "loyalty_tier"]
    customer_winners["record_hash"] = customer_winners[hash_cols].apply(
        lambda row: record_hash(row.tolist()), axis=1
    )
    dim_customer = customer_winners[
        [
            "customer_key",
            "customer_number",
            "first_name",
            "last_name",
            "email",
            "state_code",
            "loyalty_tier",
            "signup_date",
            "record_hash",
        ]
    ].copy()
    dim_customer["effective_start_date"] = pd.to_datetime(
        customer_winners["updated_at_parsed"], utc=True
    ).dt.date.astype("string")
    dim_customer["effective_end_date"] = "9999-12-31"
    dim_customer["is_current"] = True
    dim_customer = dim_customer[
        [
            "customer_key",
            "customer_number",
            "first_name",
            "last_name",
            "email",
            "state_code",
            "loyalty_tier",
            "signup_date",
            "effective_start_date",
            "effective_end_date",
            "is_current",
            "record_hash",
        ]
    ]
    dim_customer = add_audit(dim_customer, context, "SQLSERVER_ERP")
    unknown_customer = {
        "customer_key": 0,
        "customer_number": "UNKNOWN",
        "first_name": "Unknown",
        "last_name": "Unknown",
        "email": pd.NA,
        "state_code": pd.NA,
        "loyalty_tier": "Unknown",
        "signup_date": pd.NA,
        "effective_start_date": "1900-01-01",
        "effective_end_date": "9999-12-31",
        "is_current": True,
        "record_hash": pd.NA,
        "load_timestamp_utc": context.load_timestamp_utc,
        "batch_id": "SYSTEM",
        "source_system": "SYSTEM",
    }
    dim_customer = pd.concat([pd.DataFrame([unknown_customer]), dim_customer], ignore_index=True)

    # Product enrichment uses the latest supplier cost update per SKU.
    categories["category_name"] = normalize_text(categories["category_name"], title=True)
    suppliers["supplier_code"] = normalize_text(suppliers["supplier_code"], upper=True)
    costs["sku"] = normalize_text(costs["sku"], upper=True)
    costs["effective_date_parsed"] = pd.to_datetime(costs["effective_date"])
    latest_cost = (
        costs.sort_values(["sku", "effective_date_parsed", "supplier_cost_update_id"])
        .drop_duplicates("sku", keep="last")[["sku", "new_unit_cost"]]
        .rename(columns={"new_unit_cost": "latest_unit_cost"})
    )
    product_enriched = (
        products.merge(categories[["category_id", "category_name"]], on="category_id", how="left")
        .merge(suppliers[["supplier_id", "supplier_code"]], on="supplier_id", how="left")
    )
    product_enriched["sku"] = normalize_text(product_enriched["sku"], upper=True)
    product_enriched = product_enriched.merge(latest_cost, on="sku", how="left")
    product_enriched["unit_cost"] = pd.to_numeric(
        product_enriched["latest_unit_cost"].combine_first(product_enriched["unit_cost"]),
        errors="coerce",
    ).round(2)
    product_enriched["list_price"] = pd.to_numeric(product_enriched["list_price"], errors="coerce").round(2)
    product_enriched["product_name"] = normalize_text(product_enriched["product_name"])
    product_enriched["brand"] = normalize_text(product_enriched["brand"])
    product_enriched["product_key"] = product_enriched["sku"].map(stable_key)
    product_hash_cols = [
        "product_name",
        "category_name",
        "brand",
        "supplier_code",
        "unit_cost",
        "list_price",
    ]
    product_enriched["record_hash"] = product_enriched[product_hash_cols].apply(
        lambda row: record_hash(row.tolist()), axis=1
    )
    dim_product = product_enriched[
        [
            "product_key",
            "sku",
            "product_name",
            "category_name",
            "brand",
            "supplier_code",
            "unit_cost",
            "list_price",
            "record_hash",
            "updated_at",
        ]
    ].copy()
    dim_product["effective_start_date"] = pd.to_datetime(dim_product.pop("updated_at"), utc=True).dt.date.astype("string")
    dim_product["effective_end_date"] = "9999-12-31"
    dim_product["is_current"] = True
    dim_product = dim_product[
        [
            "product_key",
            "sku",
            "product_name",
            "category_name",
            "brand",
            "supplier_code",
            "unit_cost",
            "list_price",
            "effective_start_date",
            "effective_end_date",
            "is_current",
            "record_hash",
        ]
    ]
    dim_product = add_audit(dim_product, context, "SQLSERVER_ERP")
    unknown_product = {
        "product_key": 0,
        "sku": "UNKNOWN",
        "product_name": "Unknown Product",
        "category_name": "Unknown",
        "brand": "Unknown",
        "supplier_code": "UNKNOWN",
        "unit_cost": pd.NA,
        "list_price": pd.NA,
        "effective_start_date": "1900-01-01",
        "effective_end_date": "9999-12-31",
        "is_current": True,
        "record_hash": pd.NA,
        "load_timestamp_utc": context.load_timestamp_utc,
        "batch_id": "SYSTEM",
        "source_system": "SYSTEM",
    }
    dim_product = pd.concat([pd.DataFrame([unknown_product]), dim_product], ignore_index=True)

    stores["store_code"] = normalize_text(stores["store_code"], upper=True)
    stores["store_key"] = stores["store_code"].map(stable_int_key)
    dim_store = stores[
        ["store_key", "store_code", "store_name", "region", "state_code", "city", "open_date", "active_flag"]
    ].copy()
    dim_store = add_audit(dim_store, context, "SQLSERVER_ERP")
    dim_store = pd.concat(
        [
            pd.DataFrame(
                [
                    {
                        "store_key": 0,
                        "store_code": "UNKNOWN",
                        "store_name": "Unknown Store",
                        "region": "Unknown",
                        "state_code": pd.NA,
                        "city": pd.NA,
                        "open_date": pd.NA,
                        "active_flag": False,
                        "load_timestamp_utc": context.load_timestamp_utc,
                        "batch_id": "SYSTEM",
                        "source_system": "SYSTEM",
                    }
                ]
            ),
            dim_store,
        ],
        ignore_index=True,
    )

    employees = employees.merge(stores[["store_id", "store_code"]], on="store_id", how="left")
    employees["employee_number"] = normalize_text(employees["employee_number"], upper=True)
    employees["employee_name"] = (
        normalize_text(employees["first_name"], title=True).fillna("")
        + " "
        + normalize_text(employees["last_name"], title=True).fillna("")
    ).str.strip()
    employees["employee_key"] = employees["employee_number"].map(stable_int_key)
    dim_employee = employees[
        ["employee_key", "employee_number", "employee_name", "job_title", "store_code", "active_flag"]
    ].copy()
    dim_employee = add_audit(dim_employee, context, "SQLSERVER_ERP")
    dim_employee = pd.concat(
        [
            pd.DataFrame(
                [
                    {
                        "employee_key": 0,
                        "employee_number": "UNKNOWN",
                        "employee_name": "Unknown Employee",
                        "job_title": pd.NA,
                        "store_code": pd.NA,
                        "active_flag": False,
                        "load_timestamp_utc": context.load_timestamp_utc,
                        "batch_id": "SYSTEM",
                        "source_system": "SYSTEM",
                    }
                ]
            ),
            dim_employee,
        ],
        ignore_index=True,
    )

    suppliers["supplier_key"] = suppliers["supplier_code"].map(stable_int_key)
    dim_supplier = suppliers[
        ["supplier_key", "supplier_code", "supplier_name", "country_code", "lead_time_days", "active_flag"]
    ].copy()
    dim_supplier = add_audit(dim_supplier, context, "SQLSERVER_ERP")
    dim_supplier = pd.concat(
        [
            pd.DataFrame(
                [
                    {
                        "supplier_key": 0,
                        "supplier_code": "UNKNOWN",
                        "supplier_name": "Unknown Supplier",
                        "country_code": pd.NA,
                        "lead_time_days": pd.NA,
                        "active_flag": False,
                        "load_timestamp_utc": context.load_timestamp_utc,
                        "batch_id": "SYSTEM",
                        "source_system": "SYSTEM",
                    }
                ]
            ),
            dim_supplier,
        ],
        ignore_index=True,
    )

    promotions["promotion_code"] = normalize_text(promotions["promotion_code"], upper=True)
    promotions["promotion_key"] = promotions["promotion_code"].map(stable_int_key)
    dim_promotion = promotions[
        [
            "promotion_key",
            "promotion_code",
            "promotion_name",
            "discount_type",
            "discount_value",
            "start_date",
            "end_date",
            "channel_code",
        ]
    ].copy()
    dim_promotion = add_audit(dim_promotion, context, "FILE_FEED")
    dim_promotion = pd.concat(
        [
            pd.DataFrame(
                [
                    {
                        "promotion_key": 0,
                        "promotion_code": "NONE",
                        "promotion_name": "No Promotion",
                        "discount_type": pd.NA,
                        "discount_value": pd.NA,
                        "start_date": pd.NA,
                        "end_date": pd.NA,
                        "channel_code": pd.NA,
                        "load_timestamp_utc": context.load_timestamp_utc,
                        "batch_id": "SYSTEM",
                        "source_system": "SYSTEM",
                    }
                ]
            ),
            dim_promotion,
        ],
        ignore_index=True,
    )

    channel_rows = [
        ("STORE", "Store", "Sales"),
        ("ONLINE", "Online", "Sales"),
        ("PAID SEARCH", "Paid Search", "Marketing"),
        ("SOCIAL", "Social", "Marketing"),
        ("EMAIL", "Email", "Marketing"),
        ("AFFILIATE", "Affiliate", "Marketing"),
        ("ORGANIC", "Organic", "Marketing"),
        ("DIRECT", "Direct", "Marketing"),
    ]
    dim_channel = pd.DataFrame(channel_rows, columns=["channel_code", "channel_name", "channel_group"])
    dim_channel["channel_key"] = dim_channel["channel_code"].map(stable_int_key)
    dim_channel = dim_channel[["channel_key", "channel_code", "channel_name", "channel_group"]]
    dim_channel = add_audit(dim_channel, context, "CONFORMED")
    dim_channel = pd.concat(
        [
            pd.DataFrame(
                [
                    {
                        "channel_key": 0,
                        "channel_code": "UNKNOWN",
                        "channel_name": "Unknown Channel",
                        "channel_group": "Unknown",
                        "load_timestamp_utc": context.load_timestamp_utc,
                        "batch_id": "SYSTEM",
                        "source_system": "SYSTEM",
                    }
                ]
            ),
            dim_channel,
        ],
        ignore_index=True,
    )

    campaigns["campaign_code"] = normalize_text(campaigns["campaign_code"], upper=True)
    campaigns["campaign_key"] = campaigns["campaign_code"].map(stable_int_key)
    dim_campaign = campaigns[
        [
            "campaign_key",
            "campaign_code",
            "campaign_name",
            "channel",
            "start_date",
            "end_date",
            "budget_amount",
            "currency_code",
        ]
    ].copy()
    dim_campaign = add_audit(dim_campaign, context, "POSTGRES_DIGITAL")
    dim_campaign = pd.concat(
        [
            pd.DataFrame(
                [
                    {
                        "campaign_key": 0,
                        "campaign_code": "NONE",
                        "campaign_name": "No Campaign",
                        "channel": pd.NA,
                        "start_date": pd.NA,
                        "end_date": pd.NA,
                        "budget_amount": pd.NA,
                        "currency_code": pd.NA,
                        "load_timestamp_utc": context.load_timestamp_utc,
                        "batch_id": "SYSTEM",
                        "source_system": "SYSTEM",
                    }
                ]
            ),
            dim_campaign,
        ],
        ignore_index=True,
    )

    # Date dimension covers the complete project window plus a key-0 Unknown date.
    full_dates = pd.date_range("2020-01-01", "2029-12-31", freq="D")
    dim_date = pd.DataFrame({"full_date": full_dates})
    iso = dim_date["full_date"].dt.isocalendar()
    dim_date["date_key"] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["day_number"] = dim_date["full_date"].dt.day
    dim_date["day_name"] = dim_date["full_date"].dt.day_name()
    dim_date["week_number"] = iso.week.astype(int)
    dim_date["month_number"] = dim_date["full_date"].dt.month
    dim_date["month_name"] = dim_date["full_date"].dt.month_name()
    dim_date["quarter_number"] = dim_date["full_date"].dt.quarter
    dim_date["calendar_year"] = dim_date["full_date"].dt.year
    dim_date["is_weekend"] = dim_date["full_date"].dt.weekday >= 5
    dim_date["full_date"] = dim_date["full_date"].dt.date.astype("string")
    dim_date = dim_date[
        [
            "date_key",
            "full_date",
            "day_number",
            "day_name",
            "week_number",
            "month_number",
            "month_name",
            "quarter_number",
            "calendar_year",
            "is_weekend",
        ]
    ]
    dim_date = add_audit(dim_date, context, "GENERATED")
    dim_date = pd.concat(
        [
            pd.DataFrame(
                [
                    {
                        "date_key": 0,
                        "full_date": "1900-01-01",
                        "day_number": 1,
                        "day_name": "Unknown",
                        "week_number": 1,
                        "month_number": 1,
                        "month_name": "Unknown",
                        "quarter_number": 1,
                        "calendar_year": 1900,
                        "is_weekend": False,
                        "load_timestamp_utc": context.load_timestamp_utc,
                        "batch_id": "SYSTEM",
                        "source_system": "SYSTEM",
                    }
                ]
            ),
            dim_date,
        ],
        ignore_index=True,
    )

    dimensions = {
        "dim_date": dim_date,
        "dim_customer": dim_customer,
        "dim_product": dim_product,
        "dim_store": dim_store,
        "dim_employee": dim_employee,
        "dim_supplier": dim_supplier,
        "dim_promotion": dim_promotion,
        "dim_channel": dim_channel,
        "dim_campaign": dim_campaign,
    }
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
    # Concatenating Unknown rows that contain nullable attributes can make pandas infer a
    # floating key column. Recast immediately so 64-bit hash keys never lose precision.
    for table_name, key_column in dimension_keys.items():
        dimensions[table_name][key_column] = (
            dimensions[table_name][key_column].map(int).astype("int64")
        )

    lookups: dict[str, dict[Any, int]] = {
        "customer_number": dict(zip(dim_customer["customer_number"], dim_customer["customer_key"], strict=False)),
        "sku": dict(zip(dim_product["sku"], dim_product["product_key"], strict=False)),
        "store_code": dict(zip(dim_store["store_code"], dim_store["store_key"], strict=False)),
        "employee_number": dict(zip(dim_employee["employee_number"], dim_employee["employee_key"], strict=False)),
        "promotion_code": dict(zip(dim_promotion["promotion_code"], dim_promotion["promotion_key"], strict=False)),
        "channel_code": dict(zip(dim_channel["channel_code"], dim_channel["channel_key"], strict=False)),
        "campaign_code": dict(zip(dim_campaign["campaign_code"], dim_campaign["campaign_key"], strict=False)),
    }
    return dimensions, lookups


def build_facts(
    context: BuildContext,
    dimensions: dict[str, pd.DataFrame],
    lookups: dict[str, dict[Any, int]],
) -> dict[str, pd.DataFrame]:
    root = context.input_dir
    sql = root / "sqlserver"
    digital = root / "postgres"
    feeds = root / "files"

    customers = read_csv(sql / "customers.csv")
    products = read_csv(sql / "products.csv")
    stores = read_csv(sql / "stores.csv")
    employees = read_csv(sql / "employees.csv")
    orders = read_csv(sql / "orders.csv")
    items = read_csv(sql / "order_items.csv")
    shipments = read_csv(sql / "shipments.csv")
    inventory = read_csv(sql / "inventory_snapshots.csv")
    returns = read_csv(feeds / "returns.csv")
    web_users = read_csv(digital / "web_users.csv")
    web_sessions = read_csv(digital / "web_sessions.csv")
    web_events = read_csv(digital / "web_events.csv")
    campaigns = read_csv(digital / "campaigns.csv")
    spend = read_csv(digital / "marketing_spend.csv")

    customer_id_to_number = customers.set_index("customer_id")["customer_number"].astype("string").str.strip().str.upper().to_dict()
    product_id_to_sku = products.set_index("product_id")["sku"].astype("string").str.strip().str.upper().to_dict()
    store_id_to_code = stores.set_index("store_id")["store_code"].astype("string").str.strip().str.upper().to_dict()
    employee_id_to_number = employees.set_index("employee_id")["employee_number"].astype("string").str.strip().str.upper().to_dict()
    campaign_id_to_code = campaigns.set_index("campaign_id")["campaign_code"].astype("string").str.strip().str.upper().to_dict()

    valid_items = items[pd.to_numeric(items["quantity"], errors="coerce") > 0].copy()
    sales = valid_items.merge(orders, on="order_id", how="inner", suffixes=("_item", "_order"))
    sales["customer_number"] = sales["customer_id"].map(customer_id_to_number)
    sales["sku"] = sales["product_id"].map(product_id_to_sku)
    sales["store_code"] = sales["store_id"].map(store_id_to_code)
    sales["employee_number"] = sales["employee_id"].map(employee_id_to_number)
    sales["promotion_code_normalized"] = normalize_text(sales["promotion_code"], upper=True).fillna("NONE")
    sales["channel_code_normalized"] = normalize_text(sales["channel_code"], upper=True)
    quantity = pd.to_numeric(sales["quantity"], errors="raise")
    unit_price = pd.to_numeric(sales["unit_price"], errors="raise")
    unit_cost = pd.to_numeric(sales["unit_cost"], errors="raise")
    discount = pd.to_numeric(sales["discount_amount"], errors="raise")
    tax = pd.to_numeric(sales["tax_amount"], errors="raise")
    order_dates = pd.to_datetime(sales["order_timestamp"])
    fact_sales = pd.DataFrame(
        {
            "sales_key": sales["order_item_id"].map(stable_key),
            "order_item_id": sales["order_item_id"].astype(int),
            "order_id": sales["order_id"].astype(int),
            "order_number": sales["order_number"],
            "order_date_key": order_dates.map(date_key),
            "customer_key": lookup_key(sales["customer_number"], lookups["customer_number"]),
            "product_key": lookup_key(sales["sku"], lookups["sku"]),
            "store_key": lookup_key(sales["store_code"], lookups["store_code"]),
            "employee_key": lookup_key(sales["employee_number"], lookups["employee_number"]),
            "promotion_key": lookup_key(sales["promotion_code_normalized"], lookups["promotion_code"]),
            "channel_key": lookup_key(sales["channel_code_normalized"], lookups["channel_code"]),
            "quantity": quantity.astype(int),
            "gross_sales_amount": (quantity * unit_price).round(2),
            "discount_amount": discount.round(2),
            "net_sales_amount": (quantity * unit_price - discount).round(2),
            "tax_amount": tax.round(2),
            "unit_cost_amount": unit_cost.round(2),
            "cost_of_goods_sold": (quantity * unit_cost).round(2),
            "gross_profit_amount": ((quantity * unit_price - discount) - quantity * unit_cost).round(2),
            "currency_code": normalize_text(sales["currency_code"], upper=True),
        }
    )
    fact_sales = add_audit(fact_sales, context, "CONFORMED")

    return_dates = pd.to_datetime(returns["return_date"], format="mixed", errors="coerce")
    valid_returns = returns[(return_dates.notna()) & (pd.to_numeric(returns["return_quantity"], errors="coerce") > 0)].copy()
    valid_returns["return_date_parsed"] = return_dates.loc[valid_returns.index]
    return_orders = orders[["order_id", "store_id"]]
    valid_returns = valid_returns.merge(return_orders, on="order_id", how="left")
    valid_returns["customer_number"] = valid_returns["customer_id"].map(customer_id_to_number)
    valid_returns["sku"] = valid_returns["product_id"].map(product_id_to_sku)
    valid_returns["store_code"] = valid_returns["store_id"].map(store_id_to_code)
    fact_returns = pd.DataFrame(
        {
            "return_key": valid_returns["return_id"].map(stable_key),
            "return_id": valid_returns["return_id"],
            "order_item_id": pd.to_numeric(valid_returns["order_item_id"], errors="coerce").astype("Int64"),
            "return_date_key": valid_returns["return_date_parsed"].map(date_key),
            "customer_key": lookup_key(valid_returns["customer_number"], lookups["customer_number"]),
            "product_key": lookup_key(valid_returns["sku"], lookups["sku"]),
            "store_key": lookup_key(valid_returns["store_code"], lookups["store_code"]),
            "return_quantity": pd.to_numeric(valid_returns["return_quantity"], errors="raise").astype(int),
            "refund_amount": pd.to_numeric(valid_returns["refund_amount"], errors="raise").round(2),
            "return_reason": valid_returns["return_reason"],
            "currency_code": normalize_text(valid_returns["currency_code"], upper=True),
        }
    )
    fact_returns = add_audit(fact_returns, context, "FILE_FEED")

    inventory["store_code"] = inventory["store_id"].map(store_id_to_code)
    inventory["sku"] = inventory["product_id"].map(product_id_to_sku)
    current_product_cost = dimensions["dim_product"].query("product_key != 0").set_index("sku")["unit_cost"].to_dict()
    inventory["unit_cost"] = inventory["sku"].map(current_product_cost)
    quantity_on_hand = pd.to_numeric(inventory["quantity_on_hand"], errors="raise")
    quantity_reserved = pd.to_numeric(inventory["quantity_reserved"], errors="raise")
    reorder_point = pd.to_numeric(inventory["reorder_point"], errors="raise")
    inventory_store_keys = lookup_key(inventory["store_code"], lookups["store_code"])
    inventory_product_keys = lookup_key(inventory["sku"], lookups["sku"])
    inventory_dates = pd.to_datetime(inventory["snapshot_date"])
    fact_inventory = pd.DataFrame(
        {
            "inventory_snapshot_key": [
                stable_key(d, s, p)
                for d, s, p in zip(inventory_dates.dt.date, inventory_store_keys, inventory_product_keys, strict=False)
            ],
            "snapshot_date_key": inventory_dates.map(date_key),
            "store_key": inventory_store_keys,
            "product_key": inventory_product_keys,
            "quantity_on_hand": quantity_on_hand.astype(int),
            "quantity_reserved": quantity_reserved.astype(int),
            "reorder_point": reorder_point.astype(int),
            "stockout_risk_flag": (quantity_on_hand - quantity_reserved) <= reorder_point,
            "inventory_value_amount": (quantity_on_hand * pd.to_numeric(inventory["unit_cost"], errors="coerce")).round(2),
        }
    )
    fact_inventory = add_audit(fact_inventory, context, "SQLSERVER_ERP")

    shipment_rows = shipments.merge(
        orders[["order_id", "customer_id", "store_id"]], on="order_id", how="left"
    )
    shipment_rows["customer_number"] = shipment_rows["customer_id"].map(customer_id_to_number)
    shipment_rows["store_code"] = shipment_rows["store_id"].map(store_id_to_code)
    ship_dates = pd.to_datetime(shipment_rows["ship_date"], errors="coerce")
    promised_dates = pd.to_datetime(shipment_rows["promised_delivery_date"], errors="coerce")
    delivery_dates = pd.to_datetime(shipment_rows["actual_delivery_date"], errors="coerce")
    fact_shipments = pd.DataFrame(
        {
            "shipment_key": shipment_rows["shipment_id"].map(stable_key),
            "shipment_id": shipment_rows["shipment_id"].astype(int),
            "order_id": shipment_rows["order_id"].astype(int),
            "ship_date_key": ship_dates.map(date_key),
            "promised_date_key": promised_dates.map(date_key),
            "delivery_date_key": delivery_dates.map(date_key),
            "customer_key": lookup_key(shipment_rows["customer_number"], lookups["customer_number"]),
            "store_key": lookup_key(shipment_rows["store_code"], lookups["store_code"]),
            "carrier": shipment_rows["carrier"],
            "delivery_days": (delivery_dates - ship_dates).dt.days.astype("Int64"),
            "on_time_flag": (delivery_dates.notna()) & (delivery_dates <= promised_dates),
            "shipping_cost": pd.to_numeric(shipment_rows["shipping_cost"], errors="coerce").fillna(0).round(2),
        }
    )
    fact_shipments = add_audit(fact_shipments, context, "SQLSERVER_ERP")

    web_sessions["session_start_parsed"] = pd.to_datetime(web_sessions["session_start_utc"], utc=True)
    web_sessions["session_end_parsed"] = pd.to_datetime(web_sessions["session_end_utc"], utc=True)
    web_events["event_timestamp_parsed"] = pd.to_datetime(web_events["event_timestamp"], utc=True)
    event_join = web_events.merge(
        web_sessions[["session_id", "session_start_parsed"]], on="session_id", how="left"
    )
    valid_events = event_join[event_join["event_timestamp_parsed"] >= event_join["session_start_parsed"]].copy()
    event_counts = (
        valid_events.assign(
            page_view=(normalize_text(valid_events["event_type"]).str.lower() == "page_view").astype(int),
            add_to_cart=(normalize_text(valid_events["event_type"]).str.lower() == "add_to_cart").astype(int),
        )
        .groupby("session_id", as_index=False)[["page_view", "add_to_cart"]]
        .sum()
        .rename(columns={"page_view": "page_view_count", "add_to_cart": "add_to_cart_count"})
    )
    sessions = web_sessions.merge(web_users[["web_user_id", "customer_id"]], on="web_user_id", how="left")
    sessions = sessions.merge(event_counts, on="session_id", how="left")
    sessions["customer_number"] = sessions["customer_id"].map(customer_id_to_number)
    sessions["campaign_code"] = sessions["campaign_id"].map(campaign_id_to_code)
    sessions["source_channel_code"] = normalize_text(sessions["source_channel"], upper=True)
    fact_web_sessions = pd.DataFrame(
        {
            "web_session_key": sessions["session_id"].map(stable_key),
            "session_id": sessions["session_id"].astype(int),
            "session_date_key": sessions["session_start_parsed"].map(date_key),
            "customer_key": lookup_key(sessions["customer_number"], lookups["customer_number"]),
            "campaign_key": lookup_key(sessions["campaign_code"], lookups["campaign_code"]),
            "channel_key": lookup_key(sessions["source_channel_code"], lookups["channel_code"]),
            "session_count": 1,
            "duration_seconds": (
                sessions["session_end_parsed"] - sessions["session_start_parsed"]
            ).dt.total_seconds().round().astype("Int64"),
            "page_view_count": sessions["page_view_count"].fillna(0).astype(int),
            "add_to_cart_count": sessions["add_to_cart_count"].fillna(0).astype(int),
            "converted_flag": sessions["converted_order_id"].notna(),
            "converted_order_id": pd.to_numeric(sessions["converted_order_id"], errors="coerce").astype("Int64"),
        }
    )
    fact_web_sessions = add_audit(fact_web_sessions, context, "POSTGRES_DIGITAL")

    spend["campaign_code"] = spend["campaign_id"].map(campaign_id_to_code)
    spend["channel_code"] = normalize_text(spend["channel"], upper=True)
    spend["spend_date_parsed"] = pd.to_datetime(spend["spend_date"])
    spend["campaign_key"] = lookup_key(spend["campaign_code"], lookups["campaign_code"])
    spend["channel_key"] = lookup_key(spend["channel_code"], lookups["channel_code"])
    spend["spend_date_key"] = spend["spend_date_parsed"].map(date_key)
    grouped_spend = (
        spend.groupby(["spend_date_key", "campaign_key", "channel_key", "currency_code"], as_index=False)
        .agg(spend_amount=("spend_amount", "sum"), impressions=("impressions", "sum"), clicks=("clicks", "sum"))
    )
    grouped_spend["marketing_spend_key"] = [
        stable_key(d, c, ch)
        for d, c, ch in zip(
            grouped_spend["spend_date_key"],
            grouped_spend["campaign_key"],
            grouped_spend["channel_key"],
            strict=False,
        )
    ]
    fact_marketing_spend = grouped_spend[
        [
            "marketing_spend_key",
            "spend_date_key",
            "campaign_key",
            "channel_key",
            "spend_amount",
            "impressions",
            "clicks",
            "currency_code",
        ]
    ].copy()
    fact_marketing_spend["spend_amount"] = fact_marketing_spend["spend_amount"].round(2)
    fact_marketing_spend = add_audit(fact_marketing_spend, context, "POSTGRES_DIGITAL")

    return {
        "fact_sales": fact_sales,
        "fact_returns": fact_returns,
        "fact_inventory_snapshot": fact_inventory,
        "fact_shipments": fact_shipments,
        "fact_web_sessions": fact_web_sessions,
        "fact_marketing_spend": fact_marketing_spend,
    }


def validate_model(
    context: BuildContext,
    dimensions: dict[str, pd.DataFrame],
    facts: dict[str, pd.DataFrame],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, details: str, *, required: bool = True) -> None:
        checks.append(
            {
                "batch_id": context.batch_id,
                "check_name": name,
                "status": "PASS" if passed else "FAIL",
                "required": required,
                "details": details,
            }
        )

    for name, frame in dimensions.items():
        key = "date_key" if name == "dim_date" else name.replace("dim_", "") + "_key"
        check(f"{name}_not_empty", not frame.empty, f"rows={len(frame)}")
        check(f"{name}_unique_key", not frame[key].duplicated().any(), f"duplicate_keys={int(frame[key].duplicated().sum())}")
        check(f"{name}_unknown_member", bool((frame[key] == 0).any()), "key_0_present=" + str(bool((frame[key] == 0).any())))

    fact_grains = {
        "fact_sales": ["order_item_id"],
        "fact_returns": ["return_id"],
        "fact_inventory_snapshot": ["snapshot_date_key", "store_key", "product_key"],
        "fact_shipments": ["shipment_id"],
        "fact_web_sessions": ["session_id"],
        "fact_marketing_spend": ["spend_date_key", "campaign_key", "channel_key"],
    }
    for name, frame in facts.items():
        check(f"{name}_not_empty", not frame.empty, f"rows={len(frame)}")
        duplicates = int(frame.duplicated(fact_grains[name]).sum())
        check(f"{name}_unique_grain", duplicates == 0, f"duplicates={duplicates}")

    sales = facts["fact_sales"]
    arithmetic_errors = int(
        ((sales["gross_sales_amount"] - sales["discount_amount"] - sales["net_sales_amount"]).abs() > 0.01).sum()
    )
    check("fact_sales_revenue_identity", arithmetic_errors == 0, f"errors={arithmetic_errors}")
    profit_errors = int(
        ((sales["net_sales_amount"] - sales["cost_of_goods_sold"] - sales["gross_profit_amount"]).abs() > 0.01).sum()
    )
    check("fact_sales_profit_identity", profit_errors == 0, f"errors={profit_errors}")
    check("fact_sales_positive_quantity", bool((sales["quantity"] > 0).all()), f"nonpositive={int((sales['quantity'] <= 0).sum())}")

    # Foreign-key conformance against every referenced dimension.
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
        frame = facts[fact_name]
        for fact_column, (dim_name, dim_column) in mapping.items():
            orphans = set(frame[fact_column].dropna()) - set(dimensions[dim_name][dim_column].dropna())
            check(
                f"{fact_name}_{fact_column}_referential_integrity",
                not orphans,
                f"orphans={sorted(orphans)[:5]}",
            )

    source_items = read_csv(context.input_dir / "sqlserver" / "order_items.csv")
    source_valid = source_items[pd.to_numeric(source_items["quantity"], errors="coerce") > 0].copy()
    source_net = (
        pd.to_numeric(source_valid["quantity"]) * pd.to_numeric(source_valid["unit_price"])
        - pd.to_numeric(source_valid["discount_amount"])
    ).sum()
    target_net = sales["net_sales_amount"].sum()
    reconciliation = [
        {
            "batch_id": context.batch_id,
            "check_name": "source_to_gold_valid_sales_rows",
            "source_value": float(len(source_valid)),
            "target_value": float(len(sales)),
            "difference_value": float(len(sales) - len(source_valid)),
            "status": "PASS" if len(source_valid) == len(sales) else "FAIL",
        },
        {
            "batch_id": context.batch_id,
            "check_name": "source_to_gold_net_sales",
            "source_value": round(float(source_net), 2),
            "target_value": round(float(target_net), 2),
            "difference_value": round(float(target_net - source_net), 2),
            "status": "PASS" if abs(float(target_net - source_net)) <= 0.01 else "FAIL",
        },
    ]
    check(
        "source_to_gold_valid_sales_rows",
        reconciliation[0]["status"] == "PASS",
        f"source={len(source_valid)} target={len(sales)}",
    )
    check(
        "source_to_gold_net_sales",
        reconciliation[1]["status"] == "PASS",
        f"source={source_net:.2f} target={target_net:.2f}",
    )
    return checks, reconciliation


def write_outputs(
    context: BuildContext,
    dimensions: dict[str, pd.DataFrame],
    facts: dict[str, pd.DataFrame],
    checks: list[dict[str, Any]],
    reconciliation: list[dict[str, Any]],
) -> None:
    context.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, Any]] = []
    for table_name, frame in {**dimensions, **facts}.items():
        path = context.output_dir / f"{table_name}.csv"
        frame.to_csv(path, index=False, lineterminator="\n")
        manifest_rows.append(
            {
                "table_name": table_name,
                "file": path.name,
                "rows": len(frame),
                "columns": list(frame.columns),
                "sha256": sha256_file(path),
            }
        )

    quality_path = context.output_dir / "quality_results.json"
    quality_path.write_text(json.dumps(checks, indent=2), encoding="utf-8")
    reconciliation_path = context.output_dir / "reconciliation_results.json"
    reconciliation_path.write_text(json.dumps(reconciliation, indent=2), encoding="utf-8")
    summary = {
        "batch_id": context.batch_id,
        "load_timestamp_utc": context.load_timestamp_utc,
        "input_dir": str(context.input_dir),
        "output_dir": str(context.output_dir),
        "tables": manifest_rows,
        "quality_status": "PASS" if all(row["status"] == "PASS" for row in checks if row["required"]) else "FAIL",
        "required_checks": sum(1 for row in checks if row["required"]),
        "failed_required_checks": sum(1 for row in checks if row["required"] and row["status"] != "PASS"),
    }
    (context.output_dir / "gold_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if summary["quality_status"] != "PASS":
        failures = [row for row in checks if row["required"] and row["status"] != "PASS"]
        raise AssertionError(f"Local Gold quality gate failed: {failures}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("datasets/sample"))
    parser.add_argument("--output-dir", type=Path, default=Path("datasets/demo_gold"))
    args = parser.parse_args()

    configure_logging()
    manifest_path = args.input_dir / "metadata" / "batch_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    context = BuildContext(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        batch_id=str(manifest["batch_id"]),
        load_timestamp_utc=str(manifest["generated_at_utc"]),
    )
    dimensions, lookups = build_dimensions(context)
    facts = build_facts(context, dimensions, lookups)
    checks, reconciliation = validate_model(context, dimensions, facts)
    write_outputs(context, dimensions, facts, checks, reconciliation)
    LOGGER.info(
        "Built %s dimensions and %s facts in %s; quality gate PASS",
        len(dimensions),
        len(facts),
        context.output_dir,
    )


if __name__ == "__main__":
    main()
