"""Load generated digital CSVs into the local PostgreSQL source database."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import Connection, text

from scripts.utilities.config import load_environment
from scripts.utilities.database import postgres_engine
from scripts.utilities.logging_utils import configure_logging

LOGGER = logging.getLogger("northstar.load_postgres")
TABLE_ORDER = [
    "web_users",
    "campaigns",
    "web_sessions",
    "web_events",
    "campaign_touchpoints",
    "marketing_spend",
]


def read_inputs(input_dir: Path) -> dict[str, pd.DataFrame]:
    """Read every CSV before opening the database transaction."""
    frames: dict[str, pd.DataFrame] = {}
    for table in TABLE_ORDER:
        path = input_dir / f"{table}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Missing expected generated file: {path}")
        frames[table] = pd.read_csv(path)
    return frames


def clear_development_source(connection: Connection) -> None:
    """Truncate the complete related set once instead of cascading repeatedly."""
    targets = ", ".join(f'digital."{table}"' for table in TABLE_ORDER)
    connection.execute(text(f"TRUNCATE TABLE {targets} RESTART IDENTITY CASCADE;"))


def load_frames(
    connection: Connection,
    frames: dict[str, pd.DataFrame],
    *,
    expect_empty_targets: bool,
) -> None:
    """Load parents before children and reconcile every table."""
    for table in TABLE_ORDER:
        frame = frames[table]
        before = int(
            connection.execute(text(f'SELECT COUNT(*) FROM digital."{table}";')).scalar_one()
        )
        frame.to_sql(
            table,
            connection,
            schema="digital",
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi",
        )
        after = int(
            connection.execute(text(f'SELECT COUNT(*) FROM digital."{table}";')).scalar_one()
        )
        inserted = after - before
        if inserted != len(frame):
            raise AssertionError(
                f"digital.{table} row-count mismatch: before={before}, "
                f"input={len(frame)}, after={after}"
            )
        if expect_empty_targets and before != 0:
            raise AssertionError(f"digital.{table} was not empty after the development reset")
        LOGGER.info(
            "digital.%s before=%s inserted=%s after=%s",
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
        default=Path("datasets/sample/postgres"),
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
    engine = postgres_engine()
    with engine.begin() as connection:
        if args.mode == "replace-dev":
            clear_development_source(connection)
        load_frames(
            connection,
            frames,
            expect_empty_targets=args.mode == "replace-dev",
        )
    LOGGER.info("PostgreSQL source load committed successfully")


if __name__ == "__main__":
    main()
