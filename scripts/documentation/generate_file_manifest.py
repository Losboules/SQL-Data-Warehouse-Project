"""Generate FILE_MANIFEST.md with sizes, hashes, and concise purposes."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(".")
OUTPUT = ROOT / "FILE_MANIFEST.md"
SKIP_PARTS = {".git", ".venv", ".pytest_cache", "__pycache__", ".ruff_cache"}
SKIP_FILES = {OUTPUT.as_posix()}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def purpose(path: Path) -> str:
    value = path.as_posix()
    name = path.name
    if value == "README.md":
        return "Project overview, run order, evidence boundary, and navigation"
    if value == "PROJECT_COMPLETENESS_CHECKLIST.md":
        return "Package and external-environment completion gates"
    if value.startswith(".github/workflows/"):
        return "GitHub Actions validation workflow"
    if value.startswith("config/"):
        return "Non-secret generation or runtime configuration example"
    if value.startswith("databricks/notebooks/"):
        return "Databricks source notebook for the numbered pipeline task"
    if value.startswith("databricks/jobs/"):
        return "Version-controlled Lakeflow Job dependency definition"
    if value.startswith("datasets/sample/"):
        return "Deterministic fictional source fixture or its audit metadata"
    if value.startswith("datasets/demo_gold/"):
        return "Locally validated Gold dimension, fact, quality, or reconciliation evidence"
    if value.startswith("docs/manual/"):
        return "Complete beginner build manual reference"
    if value.startswith("docs/images/"):
        return "Architecture, lineage, ERD, job, or dimensional-model diagram asset"
    if value.startswith("docs/"):
        return "Technical, governance, portfolio, validation, or operating documentation"
    if value.startswith("notebooks/"):
        return "Local showcase notebook source, executed output, or HTML rendering"
    if value.startswith("powerbi/"):
        return "Power BI semantic-model, DAX, dashboard, or evidence contract"
    if value.startswith("scripts/data_generation/"):
        return "Deterministic fictional source-data generation code"
    if value.startswith("scripts/extraction/"):
        return "Full and incremental local source extraction code"
    if value.startswith("scripts/loading/"):
        return "Source or serving-warehouse loading code"
    if value.startswith("scripts/local_demo/"):
        return "Locally executable pandas parity implementation of the Gold model"
    if value.startswith("scripts/documentation/"):
        return "Reproducible documentation and manifest generator"
    if value.startswith("scripts/validation/"):
        return "Static, data, notebook, link, secret, or project-contract validator"
    if value.startswith("scripts/utilities/"):
        return "Shared configuration, database, checksum, or logging utility"
    if value.startswith("scripts/setup/"):
        return "Local tool verification helper"
    if value.startswith("sql/sqlserver/source/"):
        return "SQL Server ERP source database/schema/table DDL"
    if value.startswith("sql/sqlserver/warehouse/"):
        return "SQL Server dimensional serving-warehouse DDL or semantic views"
    if value.startswith("sql/sqlserver/analytics/"):
        return "Analyst and KPI validation queries"
    if value.startswith("sql/sqlserver/validation/"):
        return "SQL Server source or warehouse verification queries"
    if value.startswith("sql/postgres/source/"):
        return "PostgreSQL digital/marketing source DDL"
    if value.startswith("sql/postgres/validation/"):
        return "PostgreSQL source verification queries"
    if value.startswith("sql/databricks/"):
        return "Databricks SQL reference pattern for medallion, quality, or KPI logic"
    if value.startswith("tests/"):
        return "Automated unit, integration, quality, or reconciliation test"
    if name.startswith("requirements"):
        return "Pinned-range Python dependency declaration"
    if name == "pyproject.toml":
        return "Python package, pytest, and lint configuration"
    if name == ".env.example":
        return "Safe non-secret environment-variable template"
    if name == ".gitignore":
        return "Git exclusions for secrets, local data, caches, and generated artifacts"
    if name == "LICENSE":
        return "MIT license"
    if name == ".gitkeep":
        return "Keeps an intentionally empty directory in Git"
    return "Project support artifact"


def main() -> None:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.as_posix() in SKIP_FILES:
            continue
        files.append(path)
    files.sort(key=lambda item: item.as_posix().lower())

    total_bytes = sum(path.stat().st_size for path in files)
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# Northstar Retail File Manifest",
        "",
        f"Generated: `{generated}`",
        "",
        "`FILE_MANIFEST.md` is intentionally excluded from its own hash listing.",
        "",
        f"Files listed: **{len(files)}**  ",
        f"Total listed size: **{total_bytes:,} bytes**",
        "",
        "| Path | Bytes | SHA-256 | Purpose |",
        "|---|---:|---|---|",
    ]
    for path in files:
        lines.append(
            f"| `{path.as_posix()}` | {path.stat().st_size:,} | `{sha256(path)}` | {purpose(path)} |"
        )
    lines.extend(
        [
            "",
            "## Recreate this manifest",
            "",
            "From the repository root, run:",
            "",
            "```bash",
            "python -m scripts.documentation.generate_file_manifest",
            "```",
            "",
            "Regenerating the manifest changes its generated timestamp and may change hashes when project files change.",
        ]
    )
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(files)} files.")


if __name__ == "__main__":
    main()
