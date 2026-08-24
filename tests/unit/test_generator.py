from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


def run_generator(output: Path) -> None:
    subprocess.run([
        sys.executable, "-m", "scripts.data_generation.generate_northstar_data",
        "--scale", "quick", "--seed", "20260815", "--output-dir", str(output),
    ], check=True)


def test_quick_generator_counts_and_integrity(tmp_path: Path) -> None:
    output = tmp_path / "generated"
    run_generator(output)
    customers = pd.read_csv(output / "sqlserver/customers.csv")
    orders = pd.read_csv(output / "sqlserver/orders.csv")
    items = pd.read_csv(output / "sqlserver/order_items.csv")
    assert len(customers) == 60
    assert len(orders) == 200
    assert not (set(orders.customer_id) - set(customers.customer_id))
    assert not (set(items.order_id) - set(orders.order_id))
    results = json.loads((output / "metadata/validation_results.json").read_text())
    assert all(row["status"] == "PASS" for row in results)


def test_same_seed_reproduces_business_content(tmp_path: Path) -> None:
    left, right = tmp_path / "left", tmp_path / "right"
    run_generator(left)
    run_generator(right)
    for relative in ["sqlserver/customers.csv", "sqlserver/orders.csv", "postgres/web_sessions.csv", "files/returns.csv"]:
        assert (left / relative).read_bytes() == (right / relative).read_bytes()
