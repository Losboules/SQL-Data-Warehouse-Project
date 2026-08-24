"""Track A local loader: publish downloaded Gold exports to NorthstarRetail_DW safely.

The required beginner mode is ``full-dev`` for a disposable learning warehouse. It stages and
validates every table before changing targets, deletes child facts before parent dimensions,
inserts parents before children with explicit noncomputed columns, and commits once.
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import Connection, text

from scripts.utilities.config import load_environment
from scripts.utilities.database import sqlserver_warehouse_engine
from scripts.utilities.logging_utils import configure_logging

LOGGER = logging.getLogger("northstar.publish_gold")
DIMENSION_TABLES = [
    "dim_date", "dim_customer", "dim_product", "dim_store", "dim_employee",
    "dim_supplier", "dim_promotion", "dim_channel", "dim_campaign",
]
FACT_TABLES = [
    "fact_sales", "fact_returns", "fact_inventory_snapshot", "fact_shipments",
    "fact_web_sessions", "fact_marketing_spend",
]
TABLE_ORDER = DIMENSION_TABLES + FACT_TABLES
PRIMARY_KEYS = {
    "dim_date": "date_key",
    "dim_customer": "customer_key",
    "dim_product": "product_key",
    "dim_store": "store_key",
    "dim_employee": "employee_key",
    "dim_supplier": "supplier_key",
    "dim_promotion": "promotion_key",
    "dim_channel": "channel_key",
    "dim_campaign": "campaign_key",
    "fact_sales": "sales_key",
    "fact_returns": "return_key",
    "fact_inventory_snapshot": "inventory_snapshot_key",
    "fact_shipments": "shipment_key",
    "fact_web_sessions": "web_session_key",
    "fact_marketing_spend": "marketing_spend_key",
}


def read_export(path: Path) -> pd.DataFrame:
    """Read one downloaded Spark Parquet directory/file or CSV file."""
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported Gold export path: {path}")


def find_export(input_dir: Path, table: str) -> Path:
    """Find exactly one ``table.parquet`` or ``table.csv`` export."""
    candidates = [input_dir / f"{table}.parquet", input_dir / f"{table}.csv"]
    existing = [path for path in candidates if path.exists()]
    if len(existing) != 1:
        raise FileNotFoundError(
            f"Expected exactly one Gold export for {table}; found {existing} in {input_dir}"
        )
    return existing[0]


def quote_identifier(name: str) -> str:
    """Quote a trusted SQL Server identifier after a strict local allow-list check."""
    if not name.replace("_", "").isalnum():
        raise ValueError(f"Unsafe identifier: {name!r}")
    return f"[{name}]"


def insertable_columns(connection: Connection, table: str) -> list[str]:
    """Return target columns excluding identity and computed columns, in physical order."""
    rows = connection.execute(
        text(
            """
            SELECT c.name
            FROM sys.columns AS c
            WHERE c.object_id = OBJECT_ID(:object_name)
              AND c.is_identity = 0
              AND c.is_computed = 0
            ORDER BY c.column_id;
            """
        ),
        {"object_name": f"dw.{table}"},
    ).fetchall()
    columns = [str(row[0]) for row in rows]
    if not columns:
        raise RuntimeError(f"No insertable columns found for dw.{table}")
    return columns


def stage_all(connection: Connection, input_dir: Path) -> tuple[dict[str, pd.DataFrame], list[dict[str, Any]]]:
    """Read and stage every table before any target row is deleted."""
    frames: dict[str, pd.DataFrame] = {}
    results: list[dict[str, Any]] = []
    for table in TABLE_ORDER:
        export_path = find_export(input_dir, table)
        frame = read_export(export_path)
        if frame.empty and table in {"dim_date", "dim_channel"}:
            raise ValueError(f"Required reference table {table} is empty")
        expected_columns = insertable_columns(connection, table)
        missing_columns = [column for column in expected_columns if column not in frame.columns]
        extra_columns = [column for column in frame.columns if column not in expected_columns]
        if missing_columns or extra_columns:
            raise ValueError(
                f"Gold export column mismatch for {table}: "
                f"missing={missing_columns}, extra={extra_columns}"
            )
        frame = frame.loc[:, expected_columns]
        stage = f"stg_{table}"
        connection.execute(text(f"TRUNCATE TABLE stg.{quote_identifier(stage)};"))
        frame.to_sql(
            stage,
            connection,
            schema="stg",
            if_exists="append",
            index=False,
            chunksize=500,
        )
        staged_count = int(
            connection.execute(text(f"SELECT COUNT_BIG(*) FROM stg.{quote_identifier(stage)};")).scalar_one()
        )
        if staged_count != len(frame):
            raise AssertionError(
                f"Staging mismatch for {table}: file={len(frame)} stage={staged_count}"
            )
        frames[table] = frame
        results.append(
            {
                "table": table,
                "export_path": str(export_path),
                "file_rows": len(frame),
                "staged_rows": staged_count,
            }
        )
    return frames, results


def full_dev_publish(connection: Connection, results: list[dict[str, Any]]) -> None:
    """Replace a disposable development warehouse in foreign-key-safe order."""
    for table in FACT_TABLES:
        connection.execute(text(f"DELETE FROM dw.{quote_identifier(table)};"))
    for table in reversed(DIMENSION_TABLES):
        connection.execute(text(f"DELETE FROM dw.{quote_identifier(table)};"))

    for table in TABLE_ORDER:
        columns = insertable_columns(connection, table)
        quoted_columns = ", ".join(quote_identifier(column) for column in columns)
        stage = f"stg_{table}"
        connection.execute(
            text(
                f"INSERT INTO dw.{quote_identifier(table)} ({quoted_columns}) "
                f"SELECT {quoted_columns} FROM stg.{quote_identifier(stage)};"
            )
        )
        target_count = int(
            connection.execute(text(f"SELECT COUNT_BIG(*) FROM dw.{quote_identifier(table)};")).scalar_one()
        )
        result = next(item for item in results if item["table"] == table)
        result["target_rows"] = target_count
        if target_count != result["staged_rows"]:
            raise AssertionError(
                f"Target mismatch for {table}: stage={result['staged_rows']} target={target_count}"
            )


def incremental_publish(connection: Connection, results: list[dict[str, Any]]) -> None:
    """Upsert every staged row by surrogate primary key without deleting unrelated history.

    Dimensions exported from Databricks include all SCD2 versions, so matched rows refresh
    their current/end-date attributes and new versions insert with new surrogate keys. Facts
    use deterministic keys, making exact reruns idempotent. Source-side hard deletes are not
    inferred; use ``full-dev`` for a complete disposable rebuild or implement an approved
    production delete contract before enabling one.
    """
    for table in TABLE_ORDER:
        key_column = PRIMARY_KEYS[table]
        columns = insertable_columns(connection, table)
        if key_column not in columns:
            raise RuntimeError(f"Primary key {key_column} is not insertable for dw.{table}")
        update_columns = [column for column in columns if column != key_column]
        quoted_table = quote_identifier(table)
        quoted_stage = quote_identifier(f"stg_{table}")
        on_clause = f"t.{quote_identifier(key_column)} = s.{quote_identifier(key_column)}"
        update_clause = ", ".join(
            f"t.{quote_identifier(column)} = s.{quote_identifier(column)}"
            for column in update_columns
        )
        insert_columns = ", ".join(quote_identifier(column) for column in columns)
        insert_values = ", ".join(f"s.{quote_identifier(column)}" for column in columns)
        merge_sql = f"""
            MERGE dw.{quoted_table} WITH (HOLDLOCK) AS t
            USING stg.{quoted_stage} AS s
               ON {on_clause}
            WHEN MATCHED THEN
                UPDATE SET {update_clause}
            WHEN NOT MATCHED BY TARGET THEN
                INSERT ({insert_columns}) VALUES ({insert_values});
        """
        connection.execute(text(merge_sql))
        missing = int(
            connection.execute(
                text(
                    f"SELECT COUNT_BIG(*) FROM stg.{quoted_stage} AS s "
                    f"LEFT JOIN dw.{quoted_table} AS t ON {on_clause} "
                    f"WHERE t.{quote_identifier(key_column)} IS NULL;"
                )
            ).scalar_one()
        )
        if missing:
            raise AssertionError(f"Incremental merge left {missing} staged rows missing in dw.{table}")
        target_count = int(
            connection.execute(text(f"SELECT COUNT_BIG(*) FROM dw.{quoted_table};")).scalar_one()
        )
        result = next(item for item in results if item["table"] == table)
        result["target_rows"] = target_count
        result["merge_key"] = key_column
        result["missing_after_merge"] = missing


def write_artifact(batch_id: str, status: str, results: list[dict[str, Any]], error: str | None = None) -> Path:
    """Write a local nonsecret publication summary."""
    output_dir = Path("run_artifacts")
    output_dir.mkdir(exist_ok=True)
    path = output_dir / f"{batch_id}.json"
    path.write_text(
        json.dumps({"batch_id": batch_id, "status": status, "error": error, "tables": results}, indent=2),
        encoding="utf-8",
    )
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=["full-dev", "incremental"], default="full-dev")
    args = parser.parse_args()
    if not args.input_dir.exists():
        raise FileNotFoundError(args.input_dir)

    configure_logging()
    load_environment()
    batch_id = f"PUB-{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}"
    engine = sqlserver_warehouse_engine()
    results: list[dict[str, Any]] = []
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO audit.etl_batch"
                    "(batch_id, process_name, status, started_at_utc) "
                    "VALUES (:batch_id, 'publish_gold', 'RUNNING', SYSUTCDATETIME())"
                ),
                {"batch_id": batch_id},
            )
            _, results = stage_all(connection, args.input_dir)
            if args.mode == "full-dev":
                full_dev_publish(connection, results)
            else:
                incremental_publish(connection, results)
            connection.execute(
                text(
                    "UPDATE audit.etl_batch SET status='SUCCESS', "
                    "finished_at_utc=SYSUTCDATETIME() WHERE batch_id=:batch_id"
                ),
                {"batch_id": batch_id},
            )
        artifact = write_artifact(batch_id, "SUCCESS", results)
        LOGGER.info("Published batch %s; artifact=%s", batch_id, artifact)
    except Exception as exc:
        # The data transaction above rolls back. Record failure in a separate transaction.
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO audit.etl_batch"
                        "(batch_id, process_name, status, started_at_utc, finished_at_utc, error_message) "
                        "VALUES (:batch_id, 'publish_gold', 'FAILED', SYSUTCDATETIME(), "
                        "SYSUTCDATETIME(), :error_message)"
                    ),
                    {"batch_id": batch_id, "error_message": str(exc)[:2000]},
                )
        except Exception:
            LOGGER.exception("Could not record failed publication audit row")
        write_artifact(batch_id, "FAILED", results, str(exc))
        raise


if __name__ == "__main__":
    main()
