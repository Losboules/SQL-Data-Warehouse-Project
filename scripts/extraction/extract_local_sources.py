"""Extract local SQL Server, PostgreSQL, and file feeds for Track A.

The extractor produces one immutable, upload-ready batch folder. Database tables use
an explicit table-to-watermark-column contract because not every operational table has
an ``updated_at`` column. State advances only after every source and file feed has been
written and checksummed successfully.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import Connection, text

from scripts.utilities.config import load_environment
from scripts.utilities.database import postgres_engine, sqlserver_engine
from scripts.utilities.logging_utils import configure_logging

LOGGER = logging.getLogger("northstar.extract")
DEFAULT_WATERMARK = "1900-01-01T00:00:00+00:00"

# The source DDL intentionally uses ``created_at`` for append-only entities and
# ``updated_at`` for mutable entities. Keeping this mapping explicit prevents an
# incremental query from referencing a column that does not exist.
SQLSERVER_WATERMARK_COLUMNS = {
    "customers": "updated_at",
    "addresses": "updated_at",
    "products": "updated_at",
    "product_categories": "updated_at",
    "suppliers": "updated_at",
    "stores": "updated_at",
    "employees": "updated_at",
    "orders": "updated_at",
    "order_items": "updated_at",
    "payments": "updated_at",
    "shipments": "updated_at",
    "inventory_transactions": "created_at",
    "inventory_snapshots": "created_at",
}
POSTGRES_WATERMARK_COLUMNS = {
    "web_users": "updated_at",
    "web_sessions": "created_at",
    "web_events": "created_at",
    "campaigns": "updated_at",
    "campaign_touchpoints": "created_at",
    "marketing_spend": "created_at",
}


def checksum(path: Path) -> str:
    """Return a streaming SHA-256 checksum for one file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_state(path: Path) -> dict[str, Any]:
    """Read extraction state or return a safe empty state for the first run."""
    if not path.exists():
        return {"version": 1, "sqlserver": {}, "postgres": {}, "files": {}}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Extraction state must be a JSON object: {path}")
    payload.setdefault("version", 1)
    payload.setdefault("sqlserver", {})
    payload.setdefault("postgres", {})
    payload.setdefault("files", {})
    return payload


def normalize_watermark(value: str) -> str:
    """Normalize an ISO-8601 value to an explicit UTC offset string."""
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("UTC")
    else:
        stamp = stamp.tz_convert("UTC")
    return stamp.isoformat()


def query_parameter(value: str, *, source_system: str) -> datetime:
    """Return the datetime shape expected by the selected database driver."""
    stamp = pd.Timestamp(normalize_watermark(value))
    python_value = stamp.to_pydatetime()
    if source_system == "sqlserver":
        # SQL Server DATETIME2 is timezone-naive in this project. Treat its values as UTC.
        return python_value.astimezone(UTC).replace(tzinfo=None)
    return python_value.astimezone(UTC)


def next_watermark(frame: pd.DataFrame, column: str, previous: str) -> str:
    """Advance to the maximum valid timestamp in a frame, or keep the prior value."""
    if frame.empty or column not in frame.columns:
        return normalize_watermark(previous)
    values = pd.to_datetime(frame[column], errors="coerce", utc=True)
    maximum = values.max()
    if pd.isna(maximum):
        return normalize_watermark(previous)
    return pd.Timestamp(maximum).isoformat()


def relative_file(path: Path, batch_root: Path) -> str:
    """Return an upload-portable path relative to the batch folder."""
    return path.relative_to(batch_root).as_posix()


def write_parquet(frame: pd.DataFrame, path: Path) -> None:
    """Write a Parquet extract while preserving schema for zero-row batches."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


def extract_database_group(
    *,
    connection: Connection,
    source_system: str,
    schema: str,
    table_watermarks: dict[str, str],
    state: dict[str, Any],
    pending_state: dict[str, Any],
    batch_root: Path,
    mode: str,
    watermark_override: str | None,
    manifest_files: list[dict[str, Any]],
) -> None:
    """Extract one database in deterministic table order."""
    for table, watermark_column in table_watermarks.items():
        prior = normalize_watermark(
            watermark_override
            or str(state.get(source_system, {}).get(table, DEFAULT_WATERMARK))
        )
        if mode == "incremental":
            if source_system == "sqlserver":
                query = (
                    f"SELECT * FROM {schema}.[{table}] "
                    f"WHERE [{watermark_column}] > :watermark"
                )
            else:
                query = (
                    f'SELECT * FROM {schema}."{table}" '
                    f'WHERE "{watermark_column}" > :watermark'
                )
            frame = pd.read_sql_query(
                text(query),
                connection,
                params={
                    "watermark": query_parameter(
                        prior,
                        source_system=source_system,
                    )
                },
            )
        else:
            if source_system == "sqlserver":
                query = f"SELECT * FROM {schema}.[{table}]"
            else:
                query = f'SELECT * FROM {schema}."{table}"'
            frame = pd.read_sql_query(text(query), connection)

        output = batch_root / source_system / f"{table}.parquet"
        write_parquet(frame, output)
        advanced = next_watermark(frame, watermark_column, prior)
        pending_state[source_system][table] = advanced
        manifest_files.append(
            {
                "source_system": source_system,
                "table": table,
                "file": relative_file(output, batch_root),
                "rows": int(len(frame)),
                "sha256": checksum(output),
                "watermark_column": watermark_column,
                "watermark_start": prior,
                "watermark_end": advanced,
            }
        )


def count_file_rows(path: Path) -> int:
    """Count logical records in the supported file-feed formats."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return int(len(pd.read_csv(path)))
    if suffix in {".jsonl", ".ndjson"}:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip())
    return 1


def copy_file_feeds(
    *,
    source_dir: Path,
    batch_root: Path,
    pending_state: dict[str, Any],
    manifest_files: list[dict[str, Any]],
) -> None:
    """Copy a complete file-feed snapshot into every batch.

    Track A's Bronze file notebook expects the four named feed files in every batch.
    Checksums still reveal whether a file changed, but the full snapshot keeps each batch
    independently replayable.
    """
    if not source_dir.is_dir():
        raise FileNotFoundError(f"File-feed directory does not exist: {source_dir}")
    files = sorted(path for path in source_dir.iterdir() if path.is_file())
    if not files:
        raise FileNotFoundError(f"File-feed directory is empty: {source_dir}")

    for source in files:
        target = batch_root / "files" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        digest = checksum(target)
        previous_digest = pending_state["files"].get(source.name)
        pending_state["files"][source.name] = digest
        manifest_files.append(
            {
                "source_system": "files",
                "file": relative_file(target, batch_root),
                "rows": count_file_rows(target),
                "sha256": digest,
                "changed_since_prior_batch": digest != previous_digest,
            }
        )


def persist_state(path: Path, state: dict[str, Any]) -> None:
    """Atomically persist state only after a successful complete batch."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["full", "incremental"], default="full")
    parser.add_argument(
        "--watermark",
        default=None,
        help="Optional ISO-8601 override applied to every database table.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=Path("datasets/state/extraction_watermarks.json"),
    )
    parser.add_argument(
        "--file-feed-dir",
        type=Path,
        default=Path("datasets/sample/files"),
    )
    parser.add_argument("--output-root", type=Path, default=Path("datasets/raw"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging()
    load_environment()

    started = datetime.now(UTC)
    batch_id = f"EXT-{started:%Y%m%dT%H%M%S%fZ}"
    batch_root = args.output_root / batch_id
    if batch_root.exists():
        raise FileExistsError(f"Refusing to overwrite an existing extraction batch: {batch_root}")

    state = read_state(args.state_file)
    pending_state = deepcopy(state)
    manifest: dict[str, Any] = {
        "batch_id": batch_id,
        "started_at_utc": started.isoformat(),
        "mode": args.mode,
        "watermark_override": args.watermark,
        "state_file": args.state_file.as_posix(),
        "files": [],
    }

    try:
        with sqlserver_engine().connect() as connection:
            extract_database_group(
                connection=connection,
                source_system="sqlserver",
                schema="erp",
                table_watermarks=SQLSERVER_WATERMARK_COLUMNS,
                state=state,
                pending_state=pending_state,
                batch_root=batch_root,
                mode=args.mode,
                watermark_override=args.watermark,
                manifest_files=manifest["files"],
            )
        with postgres_engine().connect() as connection:
            extract_database_group(
                connection=connection,
                source_system="postgres",
                schema="digital",
                table_watermarks=POSTGRES_WATERMARK_COLUMNS,
                state=state,
                pending_state=pending_state,
                batch_root=batch_root,
                mode=args.mode,
                watermark_override=args.watermark,
                manifest_files=manifest["files"],
            )
        copy_file_feeds(
            source_dir=args.file_feed_dir,
            batch_root=batch_root,
            pending_state=pending_state,
            manifest_files=manifest["files"],
        )
        finished = datetime.now(UTC)
        pending_state["last_successful_batch_id"] = batch_id
        pending_state["last_successful_at_utc"] = finished.isoformat()
        persist_state(args.state_file, pending_state)
        manifest["status"] = "SUCCESS"
        manifest["finished_at_utc"] = finished.isoformat()
    except Exception as exc:
        manifest["status"] = "FAILED"
        manifest["finished_at_utc"] = datetime.now(UTC).isoformat()
        manifest["error"] = str(exc)
        raise
    finally:
        batch_root.mkdir(parents=True, exist_ok=True)
        manifest_path = batch_root / "batch_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        LOGGER.info("Wrote extraction manifest %s", manifest_path.resolve())

    LOGGER.info(
        "Extraction %s completed: %s files, state=%s",
        batch_id,
        len(manifest["files"]),
        args.state_file.resolve(),
    )


if __name__ == "__main__":
    main()
