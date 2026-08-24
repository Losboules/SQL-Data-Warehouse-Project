"""Validate .ipynb JSON and compile Git-friendly Databricks source notebooks."""
from __future__ import annotations

import ast
import json
from pathlib import Path


def main() -> None:
    failures = []
    for path in Path("notebooks").glob("*.ipynb"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("nbformat") != 4 or "cells" not in payload:
                failures.append(f"{path}: missing notebook v4 fields")
        except Exception as exc:
            failures.append(f"{path}: {exc}")
    for path in Path("databricks/notebooks").glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{path}:{exc.lineno}: {exc.msg}")
    if failures:
        raise SystemExit("Notebook validation failed:\n- " + "\n- ".join(failures))
    print("Notebook validation passed.")


if __name__ == "__main__":
    main()
