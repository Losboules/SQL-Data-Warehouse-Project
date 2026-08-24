from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from scripts.extraction.extract_local_sources import (
    POSTGRES_WATERMARK_COLUMNS,
    SQLSERVER_WATERMARK_COLUMNS,
    next_watermark,
    persist_state,
    read_state,
)

SAMPLE = Path("datasets/sample")


def test_every_watermark_column_exists_in_its_source_fixture() -> None:
    assert len(SQLSERVER_WATERMARK_COLUMNS) == 13
    assert len(POSTGRES_WATERMARK_COLUMNS) == 6
    for table, watermark in SQLSERVER_WATERMARK_COLUMNS.items():
        columns = pd.read_csv(SAMPLE / "sqlserver" / f"{table}.csv", nrows=0).columns
        assert watermark in columns, (table, watermark)
    for table, watermark in POSTGRES_WATERMARK_COLUMNS.items():
        columns = pd.read_csv(SAMPLE / "postgres" / f"{table}.csv", nrows=0).columns
        assert watermark in columns, (table, watermark)


def test_next_watermark_advances_and_preserves_prior_value() -> None:
    prior = "2026-01-01T00:00:00+00:00"
    frame = pd.DataFrame(
        {"updated_at": ["2026-01-02T10:00:00Z", "2026-01-03T12:30:00Z"]}
    )
    assert next_watermark(frame, "updated_at", prior) == "2026-01-03T12:30:00+00:00"
    assert next_watermark(frame.iloc[0:0], "updated_at", prior) == prior
    assert next_watermark(pd.DataFrame({"other": [1]}), "updated_at", prior) == prior


def test_extraction_state_is_written_and_read_as_complete_json(tmp_path: Path) -> None:
    target = tmp_path / "state" / "watermarks.json"
    state = {
        "version": 1,
        "sqlserver": {"orders": "2026-01-03T00:00:00+00:00"},
        "postgres": {},
        "files": {"returns.csv": "abc123"},
    }
    persist_state(target, state)
    assert json.loads(target.read_text(encoding="utf-8")) == state
    assert read_state(target) == state
    assert not target.with_suffix(".json.tmp").exists()


def test_job_wires_full_or_incremental_mode_into_gold_and_quality() -> None:
    payload = yaml.safe_load(
        Path("databricks/jobs/job_definition.example.yml").read_text(encoding="utf-8")
    )
    job = payload["resources"]["jobs"]["northstar_retail_daily"]
    parameters = {item["name"]: item["default"] for item in job["parameters"]}
    assert parameters["load_mode"] == "full"
    tasks = {task["task_key"]: task for task in job["tasks"]}
    for task_key in ("gold_facts", "data_quality_gate"):
        assert (
            tasks[task_key]["notebook_task"]["base_parameters"]["load_mode"]
            == "{{job.parameters.load_mode}}"
        )


def test_gold_notebooks_use_history_aware_bridges_and_fact_merge() -> None:
    dimensions = Path("databricks/notebooks/08_gold_dimensions.py").read_text(
        encoding="utf-8"
    )
    facts = Path("databricks/notebooks/09_gold_facts.py").read_text(encoding="utf-8")
    quality = Path("databricks/notebooks/10_data_quality.py").read_text(encoding="utf-8")
    assert "source_effective_start_date" in dimensions
    assert 'latest_bronze("erp_stores"' in dimensions
    assert "DeltaTable.forName" in facts
    assert ".whenMatchedUpdateAll()" in facts
    assert "overwrite_batch" not in facts
    assert '"load_mode": "full"' in facts
    assert '"load_mode": "full"' in quality
    assert "global_unique_grain" in quality
