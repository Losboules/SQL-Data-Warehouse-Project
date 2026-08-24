from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path("datasets/sample")


def test_controlled_dirty_data_is_present() -> None:
    customers = pd.read_csv(ROOT / "sqlserver/customers.csv")
    items = pd.read_csv(ROOT / "sqlserver/order_items.csv")
    expected = json.loads((ROOT / "metadata/expected_quality_issues.json").read_text())["configured_issue_counts"]
    assert customers.email.isna().sum() >= expected["null_emails"]
    assert (items.quantity <= 0).sum() >= expected["impossible_quantities"]
    assert customers.customer_number.duplicated(keep=False).sum() >= expected["duplicate_business_keys"]


def test_no_unexpected_order_orphans() -> None:
    customers = pd.read_csv(ROOT / "sqlserver/customers.csv")
    orders = pd.read_csv(ROOT / "sqlserver/orders.csv")
    assert not (set(orders.customer_id) - set(customers.customer_id))
