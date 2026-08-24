"""Require a dialect declaration near the start of every SQL file."""
from pathlib import Path

ALLOWED = {
    "-- Dialect: SQL Server / T-SQL",
    "-- Dialect: PostgreSQL SQL",
    "-- Dialect: Databricks SQL / Spark SQL",
    "-- Dialect: Portable ANSI-style SQL",
}


def main() -> None:
    failures = []
    for path in Path("sql").rglob("*.sql"):
        first_lines = path.read_text(encoding="utf-8").splitlines()[:5]
        if not any(line.strip() in ALLOWED for line in first_lines):
            failures.append(str(path))
    if failures:
        raise SystemExit("SQL files missing an approved dialect header:\n- " + "\n- ".join(failures))
    print("SQL dialect check passed.")


if __name__ == "__main__":
    main()
