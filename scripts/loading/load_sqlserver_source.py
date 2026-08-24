"""Load generated ERP CSVs into the local SQL Server source database.

``replace-dev`` clears child tables before parents inside one transaction, then loads
parents before children. This avoids the foreign-key failure caused by deleting a parent
while rows still exist in dependent tables.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import Connection, text

from scripts.utilities.config import load_environment
from scripts.utilities.database import sqlserver_engine
from scripts.utilities.logging_utils import configure_logging

LOGGER = logging.getLogger("northstar.load_sqlserver")
TABLE_ORDER = [
    "product_categories",
    "suppliers",
    "products",
    "stores",
    "employees",
    "customers",
    "addresses",
    "orders",
    "order_items",
    "payments",
    "shipments",
    "inventory_transactions",
    "inventory_snapshots",
]


def read_inputs(input_dir: Path) -> dict[str, pd.DataFrame]:
    """Read every required source CSV before changing the database."""
    frames: dict[str, pd.DataFrame] = {}
    for table in TABLE_ORDER:
        path = input_dir / f"{table}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Missing expected generated file: {path}")
        frames[table] = pd.read_csv(path)
    return frames


def clear_development_source(connection: Connection) -> None:
    """Delete child tables before parents so source foreign keys remain valid."""
    for table in reversed(TABLE_ORDER):
        connection.execute(text(f"DELETE FROM erp.[{table}];"))


def load_frames(
    connection: Connection,
    frames: dict[str, pd.DataFrame],
    *,
    expect_empty_targets: bool,
) -> None:
    """Load parents before children and reconcile each table immediately."""
    for table in TABLE_ORDER:
        frame = frames[table]
        before = int(
            connection.execute(text(f"SELECT COUNT_BIG(*) FROM erp.[{table}];")).scalar_one()
        )
        frame.to_sql(
            table,
            connection,
            schema="erp",
            if_exists="append",
            index=False,
            chunksize=1000,
        )
        after = int(
            connection.execute(text(f"SELECT COUNT_BIG(*) FROM erp.[{table}];")).scalar_one()
        )
        inserted = after - before
        if inserted != len(frame):
            raise AssertionError(
                f"erp.{table} row-count mismatch: before={before}, "
                f"input={len(frame)}, after={after}"
            )
        if expect_empty_targets and before != 0:
            raise AssertionError(f"erp.{table} was not empty after the development reset")
        LOGGER.info(
            "erp.%s before=%s inserted=%s after=%s",
            table,
            before,
            inserted,
            after,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("datasets/sample/sqlserver"),
    )
    parser.add_argument(
        "--mode",
        choices=["append", "replace-dev"],
        default="append",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging()
    load_environment()
    frames = read_inputs(args.input_dir)
    engine = sqlserver_engine()
    with engine.begin() as connection:
        if args.mode == "replace-dev":
            clear_development_source(connection)
        load_frames(
            connection,
            frames,
            expect_empty_targets=args.mode == "replace-dev",
        )
    LOGGER.info("SQL Server source load committed successfully")


if __name__ == "__main__":
    main()
