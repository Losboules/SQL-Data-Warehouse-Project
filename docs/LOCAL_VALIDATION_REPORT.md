# Northstar Retail Local Validation Report

**Validation timestamp (UTC):** `2026-08-17T00:12:51Z`  
**Repository:** `SQL-Data-Warehouse-Project`  
**Validation boundary:** local execution, deterministic fixture validation, static contract validation, and clean-package testing. No external SQL Server, PostgreSQL, Databricks, or Power BI run is claimed.

## Release result

The source-complete repository passed its local release checks. The package contains executable Python, SQL, Databricks, workflow, test, documentation, diagram, and Power BI contract artifacts. Components that require credentials, licensed desktop software, a database service, or a cloud workspace remain ready for execution in the user's own environment rather than being falsely marked as run.

## Automated validation summary

| Validation | Command or evidence | Result |
|---|---|---|
| Python syntax | `python -m compileall -q scripts tests databricks/notebooks` | Passed |
| Required repository artifacts | `python -m scripts.validation.check_required_files` | 109 required non-empty artifacts found |
| Deterministic source fixture | `python -m scripts.validation.validate_generated_data --input-dir datasets/sample` | 23 business files; 60 customers; 200 orders; passed |
| SQL dialect separation | `python -m scripts.validation.validate_sql_dialects` | Passed |
| Notebook integrity | `python -m scripts.validation.validate_notebooks` | Passed |
| Cross-layer project contracts | `python -m scripts.validation.validate_project_assets` | Passed: structured files, Python syntax, 15 Gold tables, 13 Databricks tasks, warehouse column contracts, DAX, and diagrams |
| Secret-pattern scan | `python -m scripts.validation.scan_secrets` | Passed |
| Relative Markdown links | `python -m scripts.validation.validate_markdown_links` | Passed |
| Automated tests | `python -m pytest -q` | 21 passed |
| Diagram rendering | Graphviz render test | 9 DOT diagrams rendered to non-empty SVG files |
| Reproducible fixture generation | Fresh generator run plus SHA-256 comparison | 27 generated fixture and metadata files matched byte-for-byte |
| Local Gold quality gate | `datasets/demo_gold/quality_results.json` | 70 required checks passed; 0 failed |
| Source-to-Gold reconciliation | `datasets/demo_gold/reconciliation_results.json` | Sales rows and net sales reconciled exactly |

## Locally generated Gold model

The local parity pipeline produced the following business-ready model from the included fictional source fixture:

- **Nine dimensions:** date, customer, product, store, employee, supplier, promotion, channel, and campaign.
- **Six facts:** sales, returns, inventory snapshot, shipments, web sessions, and marketing spend.
- **Unknown-member handling:** required dimension key `0` records are present and validated.
- **Fact integrity:** deterministic fact keys, unique grains, arithmetic identities, and dimension-key referential integrity were validated.

## Reconciled demonstration metrics

These values come from the packaged deterministic sample and are not presented as real company performance:

| Metric | Validated sample result |
|---|---:|
| Valid sales lines | 397 |
| Orders represented in sales | 198 |
| Net sales | $28,325.94 |
| Gross profit | $13,788.97 |
| Returned units | 33 |
| Shipment on-time rate | 47.71% |
| Web sessions | 300 |
| Web conversion rate | 3.67% |
| Marketing spend | $123,951.44 |

The source-to-Gold reconciliation confirmed `397 = 397` valid sales rows and `$28,325.94 = $28,325.94` net sales, with no material difference.

## Implemented but not externally executed here

| Platform component | Included implementation | Required user-side verification |
|---|---|---|
| SQL Server ERP source | Database/schema/table DDL, constraints, indexes, loader, reset controls, and validation SQL | Connect to the user's SQL Server instance, execute the source scripts, load the fixture, and inspect query results |
| PostgreSQL digital source | Database/schema/table DDL, loader, reset behavior, and validation SQL | Connect to the user's PostgreSQL service, load the fixture, and inspect query results |
| Databricks lakehouse | 13 ordered notebooks/tasks covering environment checks, Bronze, Silver, Gold, quality, publication, and demo queries | Import into an authorized workspace, select available compute/storage, upload a batch, and inspect the Job run and Delta objects |
| SQL Server serving warehouse | Warehouse/staging DDL, dimensions, facts, indexes, audit structures, semantic views, and full/incremental loader | Create `NorthstarRetail_DW`, load published Gold files, and run the warehouse reconciliation queries |
| Power BI | Model contract, relationship design, date-table guidance, DAX measures, dashboard requirements, and validation instructions | Build and save the model/report in Power BI Desktop and compare measures against SQL results |
| GitHub Actions lint run | Workflow installs `requirements-dev.txt` and runs Ruff plus the validation/test suite | Push to GitHub and inspect the actual workflow run; Ruff was not installed in the offline packaging runtime |

## Evidence files

- Full command transcript: `run_artifacts/validation_report.txt`
- Gold model inventory and hashes: `datasets/demo_gold/gold_manifest.json`
- Required quality checks: `datasets/demo_gold/quality_results.json`
- Source-to-Gold reconciliation: `datasets/demo_gold/reconciliation_results.json`
- Source generation manifest: `datasets/sample/metadata/batch_manifest.json`
- Repository file hashes: `FILE_MANIFEST.md`

## Truthfulness statement

No database connection result, Databricks run ID, Power BI refresh, cloud deployment, screenshot, or production performance number has been fabricated. Local results are marked as local evidence; external-platform steps remain explicit verification work for the user's environment.
