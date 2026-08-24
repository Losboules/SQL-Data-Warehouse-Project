"""Validate generated files without requiring SQL Server, PostgreSQL, or Databricks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("datasets/sample"))
    args = parser.parse_args()
    customer = pd.read_csv(args.input_dir / "sqlserver/customers.csv")
    orders = pd.read_csv(args.input_dir / "sqlserver/orders.csv")
    items = pd.read_csv(args.input_dir / "sqlserver/order_items.csv")
    manifest = json.loads((args.input_dir / "metadata/batch_manifest.json").read_text(encoding="utf-8"))
    failures = []
    if customer.empty:
        failures.append("customers.csv is empty")
    if orders.empty:
        failures.append("orders.csv is empty")
    if set(orders.customer_id) - set(customer.customer_id):
        failures.append("orders contain unexpected customer orphans")
    if set(items.order_id) - set(orders.order_id):
        failures.append("order_items contain unexpected order orphans")
    if len(manifest["files"]) < 20:
        failures.append("manifest contains fewer files than expected")
    if failures:
        raise SystemExit("VALIDATION FAILED\n- " + "\n- ".join(failures))
    print(f"VALIDATION PASSED: {len(manifest['files'])} files, {len(customer)} customers, {len(orders)} orders")


if __name__ == "__main__":
    main()
