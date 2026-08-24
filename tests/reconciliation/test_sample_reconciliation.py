from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("datasets/sample")


def test_valid_line_revenue_formula_is_reproducible() -> None:
    items = pd.read_csv(ROOT / "sqlserver/order_items.csv")
    valid = items[items.quantity > 0].copy()
    valid["net"] = valid.quantity * valid.unit_price - valid.discount_amount
    valid["profit"] = valid["net"] - valid.quantity * valid.unit_cost
    assert valid["net"].notna().all()
    assert abs(valid["profit"].sum() - (valid["net"].sum() - (valid.quantity * valid.unit_cost).sum())) < 0.01


def test_inventory_snapshot_grain_is_unique() -> None:
    snapshot = pd.read_csv(ROOT / "sqlserver/inventory_snapshots.csv")
    assert not snapshot.duplicated(["snapshot_date", "store_id", "product_id"]).any()
