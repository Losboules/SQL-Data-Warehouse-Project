# Northstar Retail End-to-End Data Platform

A complete, evidence-oriented data engineering portfolio implementation for a fictional omnichannel retailer. The repository integrates SQL Server ERP data, PostgreSQL digital/marketing data, and CSV/JSON feeds through Python extraction, a Databricks medallion lakehouse, a dimensional SQL Server serving warehouse, and a Power BI semantic model.

![Northstar Retail architecture](docs/images/overall_architecture.svg)

## Implementation status

**Source implementation:** complete.  
**Packaged local validation:** complete.  
**External deployment:** requires the user’s own SQL Server, PostgreSQL, Databricks, and Power BI environments; no external success is fabricated.

The included deterministic quick fixture was executed during packaging and produced:

| Result | Locally verified value |
|---|---:|
| Source data files | 23 |
| Gold dimensions | 9 |
| Gold facts | 6 |
| Required local quality checks | 70 passed, 0 failed |
| Valid sales lines | 397 |
| Distinct orders represented | 198 |
| Reconciled sample net sales | $28,325.94 |
| Source-to-Gold sales reconciliation | Passed |

See [`docs/EXECUTION_STATUS.md`](docs/EXECUTION_STATUS.md) for the exact boundary between locally verified work and environment-dependent deployment.

## Business problem

Northstar Retail’s sales, inventory, customers, website behavior, marketing, shipments, returns, supplier costs, and promotions live in separate operational systems. The platform creates one governed daily path from source records to conformed dimensions, fact tables, quality evidence, KPI definitions, analyst SQL, and report requirements.

## Architecture

### Track A — local-first portfolio path

1. Generate deterministic fictional data.
2. Load ERP entities into local SQL Server and digital entities into local PostgreSQL.
3. Extract timestamped Parquet/file batches with a manifest and SHA-256 checksums.
4. Manually upload one complete batch to a Databricks Unity Catalog volume.
5. Run the 13-task Lakeflow Job: environment, Bronze, Silver, Gold, quality, publication, and final reconciliation.
6. Download the validated Gold export.
7. Publish all nine dimensions and six facts transactionally into `NorthstarRetail_DW`.
8. Import the star schema into Power BI and validate every measure against independent SQL.

Databricks does **not** connect to a laptop’s `localhost` in Track A. The manual cloud handoffs are explicit architecture boundaries.

### Track B — optional cloud-connected path

The optional extension replaces local/manual boundaries with network-accessible managed databases, cloud storage, secured JDBC connectivity, secret-managed identities, and managed serving/BI services. It is not required for the core portfolio project.

## Data model

![Northstar Retail Gold star schema](docs/images/gold_star_schema.svg)

### Dimensions

`dim_date`, `dim_customer`, `dim_product`, `dim_store`, `dim_employee`, `dim_supplier`, `dim_promotion`, `dim_channel`, and `dim_campaign`.

Customer and product use SCD Type 2 history. Every dimension includes a key-0 Unknown member. Store, employee, supplier, promotion, channel, and campaign use SQL Server `INT`-compatible keys; customer/product and fact row keys use deterministic `BIGINT`-compatible keys.

### Facts

| Fact | Declared grain |
|---|---|
| `fact_sales` | One valid order item |
| `fact_returns` | One accepted return record |
| `fact_inventory_snapshot` | One snapshot date, store, and product |
| `fact_shipments` | One shipment |
| `fact_web_sessions` | One web session |
| `fact_marketing_spend` | One spend date, campaign, and channel |

The full column-level dictionary is in [`docs/data_dictionary.md`](docs/data_dictionary.md), and table-level lineage is in [`docs/source_to_target_mapping.md`](docs/source_to_target_mapping.md).

## Repository contents

```text
SQL-Data-Warehouse-Project/
├── .github/workflows/             # CI validation workflow
├── config/                        # Non-secret generation/runtime examples
├── databricks/
│   ├── notebooks/                 # 00–12 complete source notebooks
│   └── jobs/                      # 13-task Lakeflow Job definition
├── datasets/
│   ├── sample/                    # Deterministic source fixture
│   └── demo_gold/                 # Locally validated 9-dimension/6-fact exports
├── docs/
│   ├── images/                    # DOT, Mermaid, and rendered SVG diagrams
│   ├── manual/                    # Complete Markdown/PDF build manuals
│   ├── data_dictionary.*
│   ├── source_to_target_mapping.*
│   ├── kpi_definitions.*
│   └── execution, architecture, runbook, security, and portfolio docs
├── notebooks/                     # Executed local validation showcase + HTML
├── powerbi/                       # Semantic model, DAX, and report requirements
├── scripts/
│   ├── data_generation/           # Deterministic synthetic data
│   ├── loading/                   # SQL Server/PostgreSQL/Gold loaders
│   ├── extraction/                # Full/incremental local extraction
│   ├── local_demo/                # pandas parity build for all Gold objects
│   ├── documentation/             # Reproducible metadata docs
│   └── validation/                # Static, secret, notebook, and link checks
├── sql/
│   ├── sqlserver/                 # ERP, warehouse, semantic, validation, analytics
│   ├── postgres/                  # Digital source and validation
│   └── databricks/                # Delta/Spark SQL patterns and KPI views
├── tests/                         # Unit, integration, DQ, and reconciliation tests
├── FILE_MANIFEST.md
└── PROJECT_COMPLETENESS_CHECKLIST.md
```

## Fastest locally executable demonstration

The local parity path requires Python only. It validates the model and business arithmetic without pretending to run Databricks.

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m scripts.data_generation.generate_northstar_data --scale quick --seed 20260815 --output-dir datasets\sample
python -m scripts.local_demo.build_local_gold --input-dir datasets\sample --output-dir datasets\demo_gold
python -m pytest -q
```

### Platform-neutral shell

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m scripts.data_generation.generate_northstar_data --scale quick --seed 20260815 --output-dir datasets/sample
python -m scripts.local_demo.build_local_gold --input-dir datasets/sample --output-dir datasets/demo_gold
python -m pytest -q
```

Inspect:

- `datasets/sample/metadata/batch_manifest.json`
- `datasets/demo_gold/gold_manifest.json`
- `datasets/demo_gold/quality_results.json`
- `datasets/demo_gold/reconciliation_results.json`
- `notebooks/Northstar_Retail_Local_Validation_Demo.html`

## Full Track A execution order

### 1. Configure local secrets

Copy `.env.example` to `.env`, replace only local connection values, and never commit `.env`.

### 2. Create source databases

Run in SSMS:

1. `sql/sqlserver/source/01_create_erp_database.sql`
2. `sql/sqlserver/source/02_create_erp_tables.sql`

Run in pgAdmin/psql:

1. `sql/postgres/source/00_create_database.sql`
2. `sql/postgres/source/01_create_digital_schema.sql`

### 3. Load and validate sources

```powershell
python -m scripts.loading.load_sqlserver_source --input-dir datasets\sample\sqlserver --mode replace-dev
python -m scripts.loading.load_postgres_source --input-dir datasets\sample\postgres --mode replace-dev
```

Then execute the two source validation SQL files under `sql/*/validation/`.

### 4. Create an extraction batch

```powershell
python -m scripts.extraction.extract_local_sources --output-root datasets\raw --mode full
```

Upload the entire generated batch folder, unchanged, to the configured Unity Catalog volume.

### 5. Run the Databricks workflow

Import `databricks/notebooks/00_environment_check.py` through `12_demo_queries.py`, configure the job represented by `databricks/jobs/job_definition.example.yml`, pass the exact extraction `batch_id`, set `load_mode` to `full` for the initial build or `incremental` for later change batches, and run it. Publication is blocked when a required quality check fails.

![Lakeflow dependency graph](docs/images/jobs_dependency.svg)

### 6. Create and load the serving warehouse

Run in SSMS:

1. `sql/sqlserver/warehouse/01_create_warehouse.sql`
2. `sql/sqlserver/warehouse/02_create_staging_tables.sql`
3. `sql/sqlserver/warehouse/03_semantic_views.sql`

After downloading the Databricks Gold export:

```powershell
python -m scripts.loading.load_gold_to_sqlserver --input-dir <DOWNLOADED_GOLD_FOLDER> --mode full-dev
```

For repeat loads after the first verified build:

```powershell
python -m scripts.loading.load_gold_to_sqlserver --input-dir <DOWNLOADED_GOLD_FOLDER> --mode incremental
```

### 7. Build the Power BI model

Follow `powerbi/semantic_model.md`, add the measures from `powerbi/measures.dax`, build the pages in `powerbi/dashboard_requirements.md`, and validate values with `sql/sqlserver/analytics/kpi_validation_queries.sql`.

A `.pbix` is not fabricated in this repository because Power BI Desktop must create and validate it against the user’s actual warehouse connection.

## Quality and idempotency

The project validates required columns, types, business-key uniqueness, null identifiers, accepted values, positive quantities, nonnegative prices, date ranges, referential integrity, duplicate grains, layer reconciliation, sales arithmetic, unknown-member coverage, and exact-batch reruns.

- Bronze replaces the same batch before append.
- Silver replaces the same batch.
- Gold facts MERGE deterministic surrogate keys globally, so repair runs and later batches update matching events instead of duplicating them.
- Type 1 dimensions merge by natural key.
- Customer/product SCD2 expires changed current rows and inserts new versions.
- SQL Server full-development publication is transactional and FK-safe.
- SQL Server incremental publication merges by deterministic surrogate primary key.

## Security and privacy

- All people, companies, identifiers, and performance values are fictional.
- `.env` and secrets are ignored by Git.
- The repository contains only `.env.example` placeholders.
- CI includes a secret scan.
- Public screenshots must hide tokens, passwords, connection strings, account email addresses, and unnecessary personal details.

See [`docs/security_and_cost.md`](docs/security_and_cost.md).

## Portfolio evidence

The completed source package includes an executed local notebook and deterministic evidence. Before claiming external execution, add your own SQL Server query results, Databricks run ID/task outputs, warehouse audit rows, Power BI refresh evidence, and screenshots. The claim-to-evidence contract is documented in [`docs/claim_to_evidence_map.md`](docs/claim_to_evidence_map.md).

## Documentation

- [Complete Markdown build manual](docs/manual/Northstar_Retail_Complete_Manual_Build_Workbook.md)
- [Complete PDF build manual](docs/manual/Northstar_Retail_Complete_Manual_Build_Workbook.pdf)
- [Architecture](docs/architecture.md)
- [Business requirements](docs/business_requirements.md)
- [Data dictionary](docs/data_dictionary.md)
- [Source-to-target mapping](docs/source_to_target_mapping.md)
- [KPI definitions](docs/kpi_definitions.md)
- [Runbook](docs/runbook.md)
- [Execution status](docs/EXECUTION_STATUS.md)
- [Official sources](docs/official_sources.md)
- [Interview walkthrough](docs/interview_walkthrough.md)

## License

MIT. See [`LICENSE`](LICENSE).
