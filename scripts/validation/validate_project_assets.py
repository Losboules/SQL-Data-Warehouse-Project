"""Validate cross-file contracts for the packaged Northstar Retail project.

This validator intentionally avoids external database and cloud connections. It checks
that the local package is internally coherent and that its deterministic evidence is
complete. SQL Server, PostgreSQL, Databricks, and Power BI execution remain separate
user-environment verification steps.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from pathlib import Path

import yaml

ROOT = Path(".")
GOLD = ROOT / "datasets" / "demo_gold"

DIMENSIONS = [
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
FACTS = [
    "fact_sales",
    "fact_returns",
    "fact_inventory_snapshot",
    "fact_shipments",
    "fact_web_sessions",
    "fact_marketing_spend",
]
EXPECTED_TASKS = [
    "environment_check",
    "bronze_sqlserver",
    "bronze_postgres",
    "bronze_files",
    "silver_customers",
    "silver_products",
    "silver_sales",
    "silver_digital",
    "gold_dimensions",
    "gold_facts",
    "data_quality_gate",
    "publish_gold",
    "final_reconciliation",
]
EXPECTED_MEASURES = {
    "Total Revenue",
    "Gross Profit",
    "Gross Margin %",
    "Promotion Gross Profit",
    "Orders",
    "Units Sold",
    "Average Order Value",
    "Returned Units",
    "Return Rate",
    "Delivered Shipments",
    "On-Time Shipments",
    "On-Time Delivery %",
    "Marketing Spend",
    "Web Sessions",
    "Converted Sessions",
    "Conversion Rate",
    "Attributed Revenue",
    "Return on Ad Spend",
    "Purchasing Customers",
    "New Customers",
    "Returning Customers",
    "Inventory On Hand",
    "Stockout Risk Count",
}
EXECUTABLE_SUFFIXES = {".py", ".sql", ".yml", ".yaml", ".ps1"}
SKIP_PARTS = {".git", ".venv", ".pytest_cache", "__pycache__", "docs", "datasets", "tests"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add_failure(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def warehouse_insertable_columns(sql_text: str, table: str) -> list[str]:
    """Return SQL Server warehouse columns excluding computed/identity expressions."""
    match = re.search(
        rf"CREATE\s+TABLE\s+dw\.{re.escape(table)}\s*\((.*?)\n\);",
        sql_text,
        re.S | re.I,
    )
    if not match:
        return []
    columns: list[str] = []
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip().rstrip(",")
        if not line or line.upper().startswith(
            ("CONSTRAINT", "PRIMARY", "FOREIGN", "UNIQUE", "CHECK")
        ):
            continue
        column_match = re.match(r"\[?([A-Za-z_][A-Za-z0-9_]*)\]?\s+", line)
        if not column_match:
            continue
        # SQL Server computed columns use `column AS (...)` and are not loadable.
        after_name = line[column_match.end() :].lstrip().upper()
        if after_name.startswith("AS ") or after_name.startswith("AS("):
            continue
        if " IDENTITY(" in f" {line.upper()}":
            continue
        columns.append(column_match.group(1))
    return columns


def validate_structured_files(failures: list[str]) -> None:
    for path in ROOT.rglob("*.json"):
        if any(part in {".pytest_cache", "__pycache__", ".venv"} for part in path.parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - diagnostic path
            failures.append(f"Invalid JSON {path}: {exc}")

    for pattern in ("*.yml", "*.yaml"):
        for path in ROOT.rglob(pattern):
            if any(part in {".venv", ".pytest_cache"} for part in path.parts):
                continue
            try:
                yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception as exc:  # pragma: no cover - diagnostic path
                failures.append(f"Invalid YAML {path}: {exc}")


def validate_python(failures: list[str]) -> None:
    for root_name in ("scripts", "tests", "databricks/notebooks"):
        for path in (ROOT / root_name).rglob("*.py"):
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as exc:
                failures.append(f"Python syntax error {path}:{exc.lineno}: {exc.msg}")


def validate_no_incomplete_stops(failures: list[str]) -> None:
    forbidden = ("Not" + "ImplementedError", "TODO" + "(USER)", "IMPLEMENT" + " ME")
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in EXECUTABLE_SUFFIXES:
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in forbidden:
            if marker in text:
                failures.append(f"Incomplete execution marker {marker!r} in {path}")


def validate_gold_evidence(failures: list[str]) -> None:
    manifest_path = GOLD / "gold_manifest.json"
    add_failure(failures, manifest_path.is_file(), "Missing local Gold manifest")
    if not manifest_path.is_file():
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    add_failure(failures, manifest.get("quality_status") == "PASS", "Gold quality status is not PASS")
    add_failure(
        failures,
        manifest.get("failed_required_checks") == 0,
        "Gold manifest reports failed required checks",
    )
    add_failure(
        failures,
        int(manifest.get("required_checks", 0)) >= 70,
        "Gold manifest contains fewer than 70 required checks",
    )

    table_rows = manifest.get("tables", [])
    names = {row.get("table_name") for row in table_rows}
    expected = set(DIMENSIONS + FACTS)
    add_failure(failures, names == expected, f"Gold table set differs: {sorted(names ^ expected)}")

    by_name = {row["table_name"]: row for row in table_rows if "table_name" in row}
    for table in DIMENSIONS + FACTS:
        path = GOLD / f"{table}.csv"
        add_failure(failures, path.is_file(), f"Missing Gold CSV {path}")
        if not path.is_file():
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration:
                failures.append(f"Empty Gold CSV {path}")
                continue
            row_count = sum(1 for _ in reader)
        manifest_row = by_name.get(table, {})
        add_failure(
            failures,
            row_count == int(manifest_row.get("rows", -1)),
            f"Gold row count mismatch for {table}: CSV={row_count}, manifest={manifest_row.get('rows')}",
        )
        add_failure(
            failures,
            header == manifest_row.get("columns"),
            f"Gold column contract mismatch for {table}",
        )
        add_failure(
            failures,
            file_sha256(path) == manifest_row.get("sha256"),
            f"Gold checksum mismatch for {table}",
        )

    reconciliations = json.loads((GOLD / "reconciliation_results.json").read_text(encoding="utf-8"))
    add_failure(failures, bool(reconciliations), "No reconciliation results were recorded")
    for row in reconciliations:
        add_failure(
            failures,
            row.get("status") == "PASS",
            f"Reconciliation did not pass: {row.get('reconciliation_name', row)}",
        )


def validate_job(failures: list[str]) -> None:
    path = ROOT / "databricks" / "jobs" / "job_definition.example.yml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    job = payload["resources"]["jobs"]["northstar_retail_daily"]
    tasks = job["tasks"]
    keys = [task["task_key"] for task in tasks]
    add_failure(failures, keys == EXPECTED_TASKS, f"Unexpected Databricks task order: {keys}")

    parameters = {item["name"]: item.get("default") for item in job.get("parameters", [])}
    add_failure(
        failures,
        parameters.get("load_mode") == "full",
        "Databricks Job does not define load_mode with a safe full-load default",
    )
    task_by_key = {task["task_key"]: task for task in tasks}
    for task_key in ("gold_facts", "data_quality_gate"):
        actual = (
            task_by_key.get(task_key, {})
            .get("notebook_task", {})
            .get("base_parameters", {})
            .get("load_mode")
        )
        add_failure(
            failures,
            actual == "{{job.parameters.load_mode}}",
            f"Task {task_key} does not receive the Job load_mode parameter",
        )

    task_keys = set(keys)
    for task in tasks:
        for dependency in task.get("depends_on", []):
            dependency_key = dependency["task_key"]
            add_failure(
                failures,
                dependency_key in task_keys,
                f"Task {task['task_key']} depends on missing task {dependency_key}",
            )
        notebook_path = task["notebook_task"]["notebook_path"]
        resolved = (path.parent / notebook_path).resolve()
        add_failure(
            failures,
            resolved.is_file(),
            f"Task {task['task_key']} notebook does not resolve: {notebook_path}",
        )


def validate_warehouse_and_gold_code(failures: list[str]) -> None:
    warehouse = (ROOT / "sql/sqlserver/warehouse/01_create_warehouse.sql").read_text(encoding="utf-8")
    staging = (ROOT / "sql/sqlserver/warehouse/02_create_staging_tables.sql").read_text(encoding="utf-8")
    dimensions_code = (ROOT / "databricks/notebooks/08_gold_dimensions.py").read_text(encoding="utf-8")
    facts_code = (ROOT / "databricks/notebooks/09_gold_facts.py").read_text(encoding="utf-8")

    for table in DIMENSIONS + FACTS:
        csv_path = GOLD / f"{table}.csv"
        if not csv_path.is_file():
            continue
        with csv_path.open(encoding="utf-8", newline="") as handle:
            gold_columns = next(csv.reader(handle))
        warehouse_columns = warehouse_insertable_columns(warehouse, table)
        add_failure(
            failures,
            gold_columns == warehouse_columns,
            f"Gold/warehouse column mismatch for {table}: "
            f"gold={gold_columns}, warehouse={warehouse_columns}",
        )

    dynamic_staging_contract = (
        "SELECT name FROM sys.tables WHERE schema_id = SCHEMA_ID('dw')" in staging
        and "N'stg_' + @table" in staging
        and "SELECT TOP (0) * INTO stg." in staging
    )
    add_failure(
        failures,
        dynamic_staging_contract,
        "Staging DDL does not dynamically mirror every dw table into stg.stg_<table>",
    )

    for table in DIMENSIONS:
        add_failure(
            failures,
            re.search(rf"CREATE\s+TABLE\s+dw\.{re.escape(table)}\b", warehouse, re.I) is not None,
            f"Warehouse DDL does not create dw.{table}",
        )
        add_failure(
            failures,
            table in dimensions_code,
            f"Gold dimensions notebook does not reference {table}",
        )

    for table in FACTS:
        add_failure(
            failures,
            re.search(rf"CREATE\s+TABLE\s+dw\.{re.escape(table)}\b", warehouse, re.I) is not None,
            f"Warehouse DDL does not create dw.{table}",
        )
        add_failure(failures, table in facts_code, f"Gold facts notebook does not reference {table}")


def validate_power_bi_contract(failures: list[str]) -> None:
    dax = (ROOT / "powerbi/measures.dax").read_text(encoding="utf-8")
    declarations = {
        match.group(1).strip()
        for match in re.finditer(r"(?m)^([^/\r\n][^=\r\n]*?)\s*=\s*$", dax)
    }
    missing = EXPECTED_MEASURES - declarations
    add_failure(failures, not missing, f"Missing Power BI measures: {sorted(missing)}")
    add_failure(
        failures,
        "fact_shipments[delivery_date_key] <> 0" in dax,
        "Delivered Shipments does not use the unknown-date key contract",
    )


def validate_diagrams(failures: list[str]) -> None:
    names = {
        "overall_architecture",
        "local_first_flow",
        "cloud_connected_flow",
        "sqlserver_erd",
        "postgres_erd",
        "gold_star_schema",
        "jobs_dependency",
        "lineage",
        "scd2_timeline",
    }
    for name in names:
        for extension in ("dot", "mmd", "svg"):
            path = ROOT / "docs" / "images" / f"{name}.{extension}"
            add_failure(failures, path.is_file() and path.stat().st_size > 0, f"Missing diagram {path}")
        svg = ROOT / "docs" / "images" / f"{name}.svg"
        if svg.is_file():
            text = svg.read_text(encoding="utf-8", errors="ignore")
            add_failure(failures, "<svg" in text and "</svg>" in text, f"Invalid SVG wrapper {svg}")


def main() -> None:
    failures: list[str] = []
    validate_structured_files(failures)
    validate_python(failures)
    validate_no_incomplete_stops(failures)
    validate_gold_evidence(failures)
    validate_job(failures)
    validate_warehouse_and_gold_code(failures)
    validate_power_bi_contract(failures)
    validate_diagrams(failures)

    if failures:
        raise SystemExit("Project-asset validation failed:\n- " + "\n- ".join(failures))
    print(
        "Project-asset validation passed: structured files, Python syntax, "
        "15 Gold tables, 13 Databricks tasks, warehouse contracts, DAX, and diagrams."
    )


if __name__ == "__main__":
    main()
