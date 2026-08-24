"""CI-friendly structural check for the complete Northstar Retail package."""
from __future__ import annotations

from pathlib import Path

REQUIRED_FILES = [
    # Repository and governance
    "README.md",
    "LICENSE",
    ".env.example",
    ".gitignore",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "FILE_MANIFEST.md",
    "PROJECT_COMPLETENESS_CHECKLIST.md",
    ".github/workflows/validate_project.yml",
    # Core documentation and manuals
    "docs/architecture.md",
    "docs/business_requirements.md",
    "docs/data_dictionary.csv",
    "docs/data_dictionary.md",
    "docs/source_to_target_mapping.csv",
    "docs/source_to_target_mapping.md",
    "docs/kpi_definitions.csv",
    "docs/kpi_definitions.md",
    "docs/EXECUTION_STATUS.md",
    "docs/LOCAL_VALIDATION_REPORT.md",
    "docs/manual/Northstar_Retail_Complete_Manual_Build_Workbook.md",
    "docs/manual/Northstar_Retail_Complete_Manual_Build_Workbook.pdf",
    # Source generator, loaders, extraction, local parity, and validation
    "scripts/data_generation/generate_northstar_data.py",
    "scripts/loading/load_sqlserver_source.py",
    "scripts/loading/load_postgres_source.py",
    "scripts/loading/load_gold_to_sqlserver.py",
    "scripts/extraction/extract_local_sources.py",
    "scripts/local_demo/build_local_gold.py",
    "scripts/documentation/generate_metadata_docs.py",
    "scripts/validation/validate_generated_data.py",
    "scripts/validation/validate_project_assets.py",
    # SQL Server / PostgreSQL / Databricks SQL
    "sql/sqlserver/source/01_create_erp_database.sql",
    "sql/sqlserver/source/02_create_erp_tables.sql",
    "sql/sqlserver/warehouse/01_create_warehouse.sql",
    "sql/sqlserver/warehouse/02_create_staging_tables.sql",
    "sql/sqlserver/warehouse/03_semantic_views.sql",
    "sql/sqlserver/analytics/20_analyst_questions.sql",
    "sql/sqlserver/analytics/kpi_validation_queries.sql",
    "sql/postgres/source/00_create_database.sql",
    "sql/postgres/source/01_create_digital_schema.sql",
    "sql/postgres/validation/01_validate_digital_source.sql",
    "sql/databricks/gold/02_kpi_views.sql",
    # Databricks notebooks and workflow
    *[f"databricks/notebooks/{index:02d}_{name}.py" for index, name in [
        (0, "environment_check"),
        (1, "bronze_sqlserver"),
        (2, "bronze_postgres"),
        (3, "bronze_files"),
        (4, "silver_customers"),
        (5, "silver_products"),
        (6, "silver_sales"),
        (7, "silver_digital"),
        (8, "gold_dimensions"),
        (9, "gold_facts"),
        (10, "data_quality"),
        (11, "publish_gold"),
        (12, "demo_queries"),
    ]],
    "databricks/jobs/job_definition.example.yml",
    # Power BI contracts
    "powerbi/semantic_model.md",
    "powerbi/measures.dax",
    "powerbi/dashboard_requirements.md",
    # Deterministic fixture and validated Gold output
    "datasets/sample/metadata/batch_manifest.json",
    "datasets/sample/metadata/expected_quality_issues.json",
    "datasets/demo_gold/gold_manifest.json",
    "datasets/demo_gold/quality_results.json",
    "datasets/demo_gold/reconciliation_results.json",
    # Executed showcase
    "notebooks/Northstar_Retail_Local_Validation_Demo.ipynb",
    "notebooks/Northstar_Retail_Local_Validation_Demo.executed.ipynb",
    "notebooks/Northstar_Retail_Local_Validation_Demo.html",
]

REQUIRED_GOLD_TABLES = [
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
]

REQUIRED_DIAGRAMS = [
    "overall_architecture",
    "local_first_flow",
    "cloud_connected_flow",
    "sqlserver_erd",
    "postgres_erd",
    "gold_star_schema",
    "jobs_dependency",
    "lineage",
    "scd2_timeline",
]


def main() -> None:
    required = list(REQUIRED_FILES)
    required.extend(f"datasets/demo_gold/{name}.csv" for name in REQUIRED_GOLD_TABLES)
    for diagram in REQUIRED_DIAGRAMS:
        required.extend(
            [
                f"docs/images/{diagram}.dot",
                f"docs/images/{diagram}.mmd",
                f"docs/images/{diagram}.svg",
            ]
        )

    missing = [item for item in required if not Path(item).is_file()]
    empty = [item for item in required if Path(item).is_file() and Path(item).stat().st_size == 0]
    if missing or empty:
        lines = []
        if missing:
            lines.append("Missing required files:\n- " + "\n- ".join(missing))
        if empty:
            lines.append("Required files are empty:\n- " + "\n- ".join(empty))
        raise SystemExit("\n".join(lines))

    print(f"Required-file check passed: {len(required)} non-empty artifacts found.")


if __name__ == "__main__":
    main()
