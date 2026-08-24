from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(".")
GOLD = ROOT / "datasets" / "demo_gold"


def test_local_gold_manifest_is_complete_and_passing() -> None:
    manifest = json.loads((GOLD / "gold_manifest.json").read_text(encoding="utf-8"))
    assert manifest["quality_status"] == "PASS"
    assert manifest["failed_required_checks"] == 0
    assert manifest["required_checks"] >= 70
    assert len(manifest["tables"]) == 15
    assert {row["table_name"] for row in manifest["tables"]} == {
        "dim_date",
        "dim_customer",
        "dim_product",
        "dim_store",
        "dim_employee",
        "dim_supplier",
        "dim_promotion",
        "dim_channel",
        "dim_campaign",
        "fact_sales",
        "fact_returns",
        "fact_inventory_snapshot",
        "fact_shipments",
        "fact_web_sessions",
        "fact_marketing_spend",
    }


def test_every_dimension_has_exactly_one_unknown_member() -> None:
    key_columns = {
        "dim_date": "date_key",
        "dim_customer": "customer_key",
        "dim_product": "product_key",
        "dim_store": "store_key",
        "dim_employee": "employee_key",
        "dim_supplier": "supplier_key",
        "dim_promotion": "promotion_key",
        "dim_channel": "channel_key",
        "dim_campaign": "campaign_key",
    }
    for table, key in key_columns.items():
        frame = pd.read_csv(GOLD / f"{table}.csv")
        assert (frame[key] == 0).sum() == 1, table
        assert not frame[key].duplicated().any(), table


def test_fact_grains_are_unique() -> None:
    grains = {
        "fact_sales": ["order_item_id"],
        "fact_returns": ["return_id"],
        "fact_inventory_snapshot": ["snapshot_date_key", "store_key", "product_key"],
        "fact_shipments": ["shipment_id"],
        "fact_web_sessions": ["session_id"],
        "fact_marketing_spend": ["spend_date_key", "campaign_key", "channel_key"],
    }
    for table, grain in grains.items():
        frame = pd.read_csv(GOLD / f"{table}.csv")
        assert not frame.duplicated(grain).any(), table


def test_int_dimension_keys_fit_sql_server_int() -> None:
    for table, key in {
        "dim_store": "store_key",
        "dim_employee": "employee_key",
        "dim_supplier": "supplier_key",
        "dim_promotion": "promotion_key",
        "dim_channel": "channel_key",
        "dim_campaign": "campaign_key",
    }.items():
        values = pd.read_csv(GOLD / f"{table}.csv")[key]
        assert values.min() >= 0
        assert values.max() <= 2_147_483_647


def test_reconciliation_results_pass() -> None:
    rows = json.loads((GOLD / "reconciliation_results.json").read_text(encoding="utf-8"))
    assert rows
    assert all(row["status"] == "PASS" for row in rows)
    assert all(abs(row["difference_value"]) <= 0.01 for row in rows)


def test_job_has_complete_dependency_chain() -> None:
    payload = yaml.safe_load(Path("databricks/jobs/job_definition.example.yml").read_text())
    tasks = payload["resources"]["jobs"]["northstar_retail_daily"]["tasks"]
    assert len(tasks) == 13
    assert [task["task_key"] for task in tasks][-4:] == [
        "gold_facts",
        "data_quality_gate",
        "publish_gold",
        "final_reconciliation",
    ]


def test_executable_assets_have_no_deliberate_incomplete_stops() -> None:
    roots = [Path("scripts"), Path("databricks"), Path("sql"), Path(".github")]
    extensions = {".py", ".sql", ".yml", ".yaml"}
    offenders: list[str] = []
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in extensions:
                text = path.read_text(encoding="utf-8", errors="ignore")
                if "NotImplementedError" in text or "TODO(USER)" in text:
                    offenders.append(str(path))
    assert not offenders, offenders


def test_required_documentation_and_rendered_diagrams_exist() -> None:
    required = [
        "docs/data_dictionary.csv",
        "docs/data_dictionary.md",
        "docs/source_to_target_mapping.csv",
        "docs/source_to_target_mapping.md",
        "docs/kpi_definitions.csv",
        "docs/kpi_definitions.md",
        "docs/EXECUTION_STATUS.md",
        "docs/images/overall_architecture.svg",
        "docs/images/gold_star_schema.svg",
        "docs/images/jobs_dependency.svg",
        "notebooks/Northstar_Retail_Local_Validation_Demo.executed.ipynb",
        "notebooks/Northstar_Retail_Local_Validation_Demo.html",
    ]
    missing = [path for path in required if not Path(path).exists()]
    assert not missing, missing
