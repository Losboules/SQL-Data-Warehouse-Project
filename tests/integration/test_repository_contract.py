from pathlib import Path
import yaml


def test_job_notebook_paths_exist() -> None:
    payload = yaml.safe_load(Path("databricks/jobs/job_definition.example.yml").read_text())
    tasks = payload["resources"]["jobs"]["northstar_retail_daily"]["tasks"]
    jobs_dir = Path("databricks/jobs")
    for task in tasks:
        path = (jobs_dir / task["notebook_task"]["notebook_path"]).resolve()
        assert path.exists(), f"Missing job notebook: {path}"


def test_all_gold_tables_are_in_dictionary() -> None:
    text = Path("docs/data_dictionary.csv").read_text(encoding="utf-8")
    for table in ["dim_date","dim_customer","dim_product","dim_store","dim_employee","dim_supplier","dim_promotion","dim_channel","dim_campaign","fact_sales","fact_returns","fact_inventory_snapshot","fact_shipments","fact_web_sessions","fact_marketing_spend"]:
        assert table in text
