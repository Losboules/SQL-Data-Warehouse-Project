"""Generate data dictionary, source-to-target mapping, and KPI contracts.

The script derives columns from the included deterministic sample and Gold exports,
then adds stable project metadata such as grain, key role, and business definition.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import pandas as pd

SOURCE_GRAINS = {
    "product_categories": "One product category",
    "suppliers": "One supplier",
    "products": "One product",
    "stores": "One physical store",
    "employees": "One employee",
    "customers": "One customer source record",
    "addresses": "One customer address",
    "orders": "One customer order",
    "order_items": "One line on one order",
    "payments": "One payment attempt/transaction",
    "shipments": "One shipment",
    "inventory_transactions": "One inventory movement",
    "inventory_snapshots": "One date-store-product inventory snapshot",
    "web_users": "One website user identity",
    "web_sessions": "One website session",
    "web_events": "One website event",
    "campaigns": "One marketing campaign",
    "campaign_touchpoints": "One user/session campaign touchpoint",
    "marketing_spend": "One campaign-channel-date spend row",
    "returns": "One return record",
    "supplier_cost_updates": "One supplier/SKU cost change",
    "promotion_calendar": "One promotion",
    "shipment_tracking_events": "One shipment tracking document/event payload",
}

GOLD_GRAINS = {
    "dim_date": "One calendar date",
    "dim_customer": "One historical version of one customer",
    "dim_product": "One historical version of one product",
    "dim_store": "One current store",
    "dim_employee": "One current employee",
    "dim_supplier": "One current supplier",
    "dim_promotion": "One promotion",
    "dim_channel": "One conformed channel",
    "dim_campaign": "One campaign",
    "fact_sales": "One valid order item",
    "fact_returns": "One accepted return record",
    "fact_inventory_snapshot": "One snapshot date-store-product",
    "fact_shipments": "One shipment",
    "fact_web_sessions": "One web session",
    "fact_marketing_spend": "One spend date-campaign-channel",
}

KEY_COLUMNS = {
    "dim_date": {"date_key": "Primary key"},
    "dim_customer": {"customer_key": "Primary key", "customer_number": "Natural key"},
    "dim_product": {"product_key": "Primary key", "sku": "Natural key"},
    "dim_store": {"store_key": "Primary key", "store_code": "Natural key"},
    "dim_employee": {"employee_key": "Primary key", "employee_number": "Natural key"},
    "dim_supplier": {"supplier_key": "Primary key", "supplier_code": "Natural key"},
    "dim_promotion": {"promotion_key": "Primary key", "promotion_code": "Natural key"},
    "dim_channel": {"channel_key": "Primary key", "channel_code": "Natural key"},
    "dim_campaign": {"campaign_key": "Primary key", "campaign_code": "Natural key"},
    "fact_sales": {"sales_key": "Primary key", "order_item_id": "Degenerate source key"},
    "fact_returns": {"return_key": "Primary key", "return_id": "Degenerate source key"},
    "fact_inventory_snapshot": {"inventory_snapshot_key": "Primary key"},
    "fact_shipments": {"shipment_key": "Primary key", "shipment_id": "Degenerate source key"},
    "fact_web_sessions": {"web_session_key": "Primary key", "session_id": "Degenerate source key"},
    "fact_marketing_spend": {"marketing_spend_key": "Primary key"},
}

TABLE_PURPOSES = {
    "dim_date": "Reusable calendar attributes for consistent time analysis.",
    "dim_customer": "Customer descriptive history using SCD Type 2.",
    "dim_product": "Product descriptive and cost history using SCD Type 2.",
    "dim_store": "Current store attributes used by sales and operations facts.",
    "dim_employee": "Current employee attributes for assisted store sales.",
    "dim_supplier": "Current supplier attributes and lead-time context.",
    "dim_promotion": "Promotion definitions used on sales lines.",
    "dim_channel": "Conformed sales and marketing channels.",
    "dim_campaign": "Campaign definitions used by sessions and spend.",
    "fact_sales": "Sales quantity, revenue, cost, discount, tax, and profit at order-item grain.",
    "fact_returns": "Returned units and refunds at return-record grain.",
    "fact_inventory_snapshot": "Point-in-time stock, risk, and value at store-product-date grain.",
    "fact_shipments": "Delivery timing, service, and shipping cost at shipment grain.",
    "fact_web_sessions": "Session engagement and conversion outcomes at session grain.",
    "fact_marketing_spend": "Spend, impressions, and clicks at date-campaign-channel grain.",
}

KPI_ROWS = [
    ("Total Revenue", "SUM(fact_sales[net_sales_amount])", "Net sales after line discount; excludes tax.", "Currency", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("Gross Profit", "SUM(fact_sales[gross_profit_amount])", "Net sales minus cost of goods sold.", "Currency", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("Gross Margin Percentage", "DIVIDE([Gross Profit], [Total Revenue])", "Gross profit divided by net sales.", "Percentage", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("Orders", "DISTINCTCOUNT(fact_sales[order_id])", "Distinct orders represented by valid sales lines.", "Whole number", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("Units Sold", "SUM(fact_sales[quantity])", "Valid sold item quantity.", "Whole number", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("Average Order Value", "DIVIDE([Total Revenue], [Orders])", "Average net revenue per distinct order.", "Currency", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("Returned Units", "SUM(fact_returns[return_quantity])", "Accepted returned quantity.", "Whole number", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("Return Rate", "DIVIDE([Returned Units], [Units Sold])", "Returned units divided by sold units in filter context.", "Percentage", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("On-Time Delivery Percentage", "DIVIDE(on-time shipments, shipments)", "Delivered on/before promised date divided by shipments.", "Percentage", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("Marketing Spend", "SUM(fact_marketing_spend[spend_amount])", "Recorded campaign spend.", "Currency", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("Web Sessions", "SUM(fact_web_sessions[session_count])", "Website sessions.", "Whole number", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("Conversion Rate", "DIVIDE(converted sessions, web sessions)", "Sessions linked to an order divided by sessions.", "Percentage", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("Attributed Revenue", "Revenue for distinct converted session order IDs", "Simplified converting-session attribution; not causal lift.", "Currency", "powerbi/measures.dax"),
    ("Return on Ad Spend", "DIVIDE([Attributed Revenue], [Marketing Spend])", "Attributed revenue divided by spend under the documented rule.", "Decimal", "powerbi/measures.dax"),
    ("Inventory On Hand", "SUM(fact_inventory_snapshot[quantity_on_hand])", "On-hand units; use one snapshot date.", "Whole number", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
    ("Stockout Risk Count", "Count rows where stockout_risk_flag is true", "Store-product snapshot rows at or below reorder threshold.", "Whole number", "sql/sqlserver/analytics/kpi_validation_queries.sql"),
]


def humanize(column: str) -> str:
    special = {
        "id": "identifier",
        "utc": "UTC",
        "sku": "stock keeping unit",
        "cogs": "cost of goods sold",
    }
    words = column.split("_")
    return " ".join(special.get(word, word) for word in words).capitalize() + "."


def pandas_type(dtype: Any) -> str:
    name = str(dtype)
    if name.startswith("int") or name.startswith("Int"):
        return "integer"
    if name.startswith("float"):
        return "decimal/number"
    if "bool" in name:
        return "boolean"
    if "datetime" in name:
        return "date/time"
    return "text or source-specific scalar"


def parse_warehouse_types(path: Path) -> dict[tuple[str, str], str]:
    text = path.read_text(encoding="utf-8")
    result: dict[tuple[str, str], str] = {}
    table_pattern = re.compile(r"CREATE TABLE dw\.(\w+)\s*\((.*?)\n\);", re.S | re.I)
    column_pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z]+(?:\([^\)]*\))?)", re.I)
    for table, body in table_pattern.findall(text):
        for line in body.splitlines():
            line = line.rstrip().rstrip(",")
            if not line or line.lstrip().upper().startswith(("CONSTRAINT", "PRIMARY", "UNIQUE", "FOREIGN")):
                continue
            match = column_pattern.match(line)
            if match:
                result[(table, match.group(1))] = match.group(2).upper()
    # Computed warehouse column.
    result[("fact_inventory_snapshot", "quantity_available")] = "COMPUTED INT"
    return result


def frame_dictionary(table: str, frame: pd.DataFrame, layer: str, type_map: dict[tuple[str, str], str]) -> list[dict[str, Any]]:
    rows = []
    grain = GOLD_GRAINS.get(table, SOURCE_GRAINS.get(table, "One source record"))
    purpose = TABLE_PURPOSES.get(table, f"Operational {table.replace('_', ' ')} data.")
    for ordinal, column in enumerate(frame.columns, start=1):
        key_role = KEY_COLUMNS.get(table, {}).get(column, "")
        if not key_role and layer == "Gold" and column.endswith("_key"):
            key_role = "Foreign key"
        if not key_role and layer != "Gold" and column.endswith("_id"):
            key_role = "Source identifier/foreign key"
        rows.append(
            {
                "layer": layer,
                "table_name": table,
                "table_purpose": purpose,
                "grain": grain,
                "ordinal_position": ordinal,
                "column_name": column,
                "data_type": type_map.get((table, column), pandas_type(frame[column].dtype)),
                "nullable_in_sample": bool(frame[column].isna().any()),
                "key_role": key_role,
                "business_definition": humanize(column),
            }
        )
    return rows


def write_markdown_table(frame: pd.DataFrame, path: Path, title: str, intro: str) -> None:
    path.write_text(
        f"# {title}\n\n{intro}\n\n" + frame.to_markdown(index=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-dir", type=Path, default=Path("datasets/sample"))
    parser.add_argument("--gold-dir", type=Path, default=Path("datasets/demo_gold"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    args = parser.parse_args()
    args.docs_dir.mkdir(parents=True, exist_ok=True)

    type_map = parse_warehouse_types(Path("sql/sqlserver/warehouse/01_create_warehouse.sql"))
    rows: list[dict[str, Any]] = []
    for folder, layer in [("sqlserver", "SQL Server source"), ("postgres", "PostgreSQL source"), ("files", "File feed")]:
        for path in sorted((args.sample_dir / folder).glob("*.csv")):
            frame = pd.read_csv(path)
            rows.extend(frame_dictionary(path.stem, frame, layer, type_map))
    for path in sorted(args.gold_dir.glob("*.csv")):
        frame = pd.read_csv(path)
        rows.extend(frame_dictionary(path.stem, frame, "Gold", type_map))

    dictionary = pd.DataFrame(rows)
    dictionary.to_csv(args.docs_dir / "data_dictionary.csv", index=False, lineterminator="\n")
    write_markdown_table(
        dictionary,
        args.docs_dir / "data_dictionary.md",
        "Northstar Retail Data Dictionary",
        "Generated from the deterministic sample, local Gold exports, and SQL Server warehouse DDL. Nullability describes the included sample; authoritative warehouse constraints remain in the DDL.",
    )

    mappings = pd.DataFrame(
        [
            ("SQLSERVER_ERP", "customers + addresses", "silver.customers", "gold.dim_customer", "customer_number", "Trim/case standardize, choose latest duplicate, attach default state, SCD2 hash"),
            ("SQLSERVER_ERP", "products + categories + suppliers", "silver.products", "gold.dim_product", "sku", "Conform category/supplier, apply latest supplier cost, SCD2 hash"),
            ("SQLSERVER_ERP", "stores", "bronze.erp_stores", "gold.dim_store", "store_code", "Trim/uppercase and Type 1 upsert"),
            ("SQLSERVER_ERP", "employees + stores", "bronze.erp_employees", "gold.dim_employee", "employee_number", "Conform employee name and store code; Type 1 upsert"),
            ("SQLSERVER_ERP", "suppliers", "bronze.erp_suppliers", "gold.dim_supplier", "supplier_code", "Trim/uppercase and Type 1 upsert"),
            ("FILE_FEED", "promotion_calendar.csv", "silver.promotions", "gold.dim_promotion", "promotion_code", "Parse dates/decimal discount and Type 1 upsert"),
            ("CONFORMED", "static channel contract", "n/a", "gold.dim_channel", "channel_code", "Create consistent sales/marketing channel members"),
            ("POSTGRES_DIGITAL", "campaigns", "silver.campaigns", "gold.dim_campaign", "campaign_code", "Parse dates/budget and Type 1 upsert"),
            ("SQLSERVER_ERP", "orders + order_items", "silver.sales", "gold.fact_sales", "order_item_id", "Reject nonpositive quantity; calculate revenue, COGS, profit; resolve effective keys"),
            ("FILE_FEED", "returns.csv + orders", "silver.returns", "gold.fact_returns", "return_id", "Parse mixed dates, reject invalid quantity/date, resolve order/store/customer/product keys"),
            ("SQLSERVER_ERP", "inventory_snapshots", "silver.inventory_snapshots", "gold.fact_inventory_snapshot", "date+store+product", "Cast quantities, calculate risk and inventory value"),
            ("SQLSERVER_ERP", "shipments + orders", "silver.shipments", "gold.fact_shipments", "shipment_id", "Parse dates, calculate delivery days/on-time flag, resolve order dimensions"),
            ("POSTGRES_DIGITAL", "web_sessions + web_users + web_events", "silver.web_sessions + web_events", "gold.fact_web_sessions", "session_id", "Normalize UTC timestamps, quarantine out-of-order events, aggregate engagement"),
            ("POSTGRES_DIGITAL", "marketing_spend + campaigns", "silver.marketing_spend", "gold.fact_marketing_spend", "date+campaign+channel", "Reject negative/non-USD rows, aggregate spend/impressions/clicks"),
        ],
        columns=["source_system", "source_objects", "silver_object", "gold_object", "target_grain_key", "transformation_summary"],
    )
    mappings.to_csv(args.docs_dir / "source_to_target_mapping.csv", index=False, lineterminator="\n")
    write_markdown_table(
        mappings,
        args.docs_dir / "source_to_target_mapping.md",
        "Source-to-Target Mapping",
        "Table-level lineage contract for the implemented Northstar Retail pipeline.",
    )

    kpis = pd.DataFrame(KPI_ROWS, columns=["kpi_name", "formula", "business_definition", "format", "validation_asset"])
    kpis.to_csv(args.docs_dir / "kpi_definitions.csv", index=False, lineterminator="\n")
    write_markdown_table(
        kpis,
        args.docs_dir / "kpi_definitions.md",
        "KPI Definitions",
        "The Power BI measure names, business definitions, and independent SQL validation assets used by the project.",
    )


if __name__ == "__main__":
    main()
