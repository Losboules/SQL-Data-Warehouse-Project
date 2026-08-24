# Northstar Retail End-to-End Data Platform

**Data Engineering Portfolio Project | Python • SQL • PySpark • Databricks • Delta Lake • SQL Server • PostgreSQL • Power BI**

Northstar Retail is an end-to-end batch data engineering project built for a fictional omnichannel retailer. The platform integrates ERP, e-commerce, marketing, inventory, shipment, promotion, and return data from multiple source systems into a governed lakehouse and dimensional data warehouse.

The project demonstrates practical data engineering skills including:

* Multi-source data ingestion
* ETL/ELT pipeline development
* Medallion architecture
* PySpark and Spark SQL transformations
* Dimensional modeling
* SCD Type 2 history
* Incremental and idempotent processing
* Data-quality testing
* Source-to-target reconciliation
* Workflow orchestration
* CI/CD validation
* Analytics and semantic-model design

### Data flow

```text
SQL Server ERP ────────────┐
                           │
PostgreSQL Digital Data ───┼──> Python Extraction
                           │        │
CSV and JSON Files ────────┘        ▼
                              Batch Manifest
                              Row Counts
                              SHA-256 Checksums
                                    │
                                    ▼
                          Databricks / Delta Lake
                        Bronze → Silver → Gold
                                    │
                             Data-Quality Gate
                                    │
                                    ▼
                         SQL Server Data Warehouse
                                    │
                                    ▼
                         Power BI Semantic Model
```

The primary implementation follows a **local-first batch architecture**:

1. Python generates deterministic fictional retail data.
2. ERP data is modeled for SQL Server.
3. Website and marketing data are modeled for PostgreSQL.
4. Additional business feeds arrive as CSV and JSON files.
5. Python extracts the sources into versioned batch folders.
6. Databricks processes the data through Bronze, Silver, and Gold layers.
7. A required quality gate validates the data before publication.
8. Gold tables are published to a SQL Server dimensional warehouse.
9. Power BI uses the warehouse for reporting and KPI analysis.

Because a cloud Databricks workspace cannot directly access a laptop’s `localhost`, the local-first path uses explicit upload and download boundaries. A cloud-connected extension is documented separately for managed databases, cloud storage, secure JDBC connectivity, and managed serving tools.

## Project Results

The included deterministic sample was executed and locally validated.

| Result                        |      Verified Value |
| ----------------------------- | ------------------: |
| Source data files             |                  23 |
| Gold dimensions               |                   9 |
| Gold fact tables              |                   6 |
| Required quality checks       | 70 passed, 0 failed |
| Automated tests               |           21 passed |
| Valid sales rows              |                 397 |
| Distinct orders represented   |                 198 |
| Reconciled net sales          |          $28,325.94 |
| Source-to-Gold reconciliation |              Passed |

These values come from fictional sample data and do not represent a real company.

Detailed evidence is available in:

* [`datasets/demo_gold/quality_results.json`](datasets/demo_gold/quality_results.json)
* [`datasets/demo_gold/reconciliation_results.json`](datasets/demo_gold/reconciliation_results.json)
* [`datasets/demo_gold/gold_manifest.json`](datasets/demo_gold/gold_manifest.json)
* [`docs/LOCAL_VALIDATION_REPORT.md`](docs/LOCAL_VALIDATION_REPORT.md)
* [`run_artifacts/validation_report.txt`](run_artifacts/validation_report.txt)

## Business Problem

Northstar Retail’s information is distributed across separate operational systems:

* Sales, customers, products, employees, stores, inventory, payments, and shipments are stored in SQL Server.
* Website sessions, web events, marketing campaigns, and marketing spend are stored in PostgreSQL.
* Returns, supplier-cost changes, promotions, and shipment-tracking events arrive as CSV or JSON files.

This separation creates inconsistent reporting and makes it difficult for business teams to agree on trusted numbers.

The platform creates one governed path for answering questions such as:

* How much revenue and gross profit is the company generating?
* Which products, categories, stores, regions, and channels perform best?
* What is the average order value?
* What is the product return rate?
* What percentage of shipments arrive on time?
* Which products are at risk of stocking out?
* How well does website activity convert into orders?
* How effective is marketing spend by campaign and channel?
* How do new and returning customers compare?

## Technology Stack

| Category        | Technologies                                                     |
| --------------- | ---------------------------------------------------------------- |
| Programming     | Python, SQL, PowerShell                                          |
| Data Processing | Pandas, PySpark, Spark SQL                                       |
| Source Systems  | SQL Server, PostgreSQL, CSV, JSON, JSONL                         |
| Lakehouse       | Databricks, Delta Lake, Unity Catalog design                     |
| Data Warehouse  | SQL Server dimensional warehouse                                 |
| Modeling        | Star schema, surrogate keys, SCD Type 1 and Type 2               |
| Orchestration   | Databricks Workflows / Lakeflow Jobs                             |
| Analytics       | Power BI, DAX, SQL semantic views                                |
| Testing         | pytest, data-quality checks, reconciliation tests                |
| CI/CD           | Git, GitHub, GitHub Actions                                      |
| Integration     | SQLAlchemy, pyodbc, psycopg                                      |
| Security        | Environment variables, secret scanning, least-privilege guidance |

## Medallion Architecture

### Bronze Layer

The Bronze layer preserves the original batch with technical metadata.

Responsibilities include:

* Reading SQL Server, PostgreSQL, CSV, and JSON extracts
* Preserving source values
* Recording batch identifiers
* Recording ingestion timestamps
* Capturing source filenames
* Supporting repeatable batch processing
* Preventing accidental duplicate ingestion

### Silver Layer

The Silver layer cleans, standardizes, and validates the source data.

Responsibilities include:

* Schema enforcement
* Type conversion
* Timestamp normalization
* Deduplication
* Required-field validation
* Business-rule validation
* Referential-integrity checks
* Invalid-record quarantine
* Accepted-value validation
* Sales arithmetic validation

### Gold Layer

The Gold layer creates business-ready dimensions, facts, and KPI outputs.

Responsibilities include:

* Conformed dimensions
* Surrogate-key generation
* SCD Type 2 customer and product history
* Unknown-member handling
* Point-in-time dimension resolution
* Fact-table grain enforcement
* Incremental MERGE behavior
* Source-to-Gold reconciliation
* Business-facing KPI views

## Dimensional Data Model

### Dimensions

The Gold model contains nine dimensions:

* `dim_date`
* `dim_customer`
* `dim_product`
* `dim_store`
* `dim_employee`
* `dim_supplier`
* `dim_promotion`
* `dim_channel`
* `dim_campaign`

Customer and product dimensions include **SCD Type 2 history** so historical facts remain connected to the correct version of each record.

Every dimension includes a key-`0` Unknown member so incomplete business events remain visible instead of being silently dropped.

### Fact Tables

| Fact Table                | Declared Grain                        |
| ------------------------- | ------------------------------------- |
| `fact_sales`              | One valid order item                  |
| `fact_returns`            | One accepted return record            |
| `fact_inventory_snapshot` | One snapshot date, store, and product |
| `fact_shipments`          | One shipment                          |
| `fact_web_sessions`       | One web session                       |
| `fact_marketing_spend`    | One spend date, campaign, and channel |

Column definitions are available in the [`data dictionary`](docs/data_dictionary.md), and source mappings are documented in the [`source-to-target mapping`](docs/source_to_target_mapping.md).

## Data Quality and Reliability

The project includes automated checks for:

* Required files and columns
* Data types
* Missing identifiers
* Duplicate business keys
* Duplicate fact grains
* Referential integrity
* Accepted status values
* Positive quantities
* Nonnegative prices and costs
* Valid date ranges
* Sales arithmetic
* SCD Type 2 overlap
* Current-record uniqueness
* Unknown-member coverage
* Source-to-Bronze reconciliation
* Bronze-to-Silver reconciliation
* Silver-to-Gold reconciliation
* Exact source-to-Gold net-sales reconciliation

A required quality failure blocks the publication stage.

### Idempotency

The project is designed so repeated processing does not create duplicate business records:

* Bronze replaces data for the same batch before appending.
* Silver replaces data for the same batch.
* Gold facts use deterministic keys and MERGE logic.
* Type 1 dimensions merge by natural key.
* Customer and product SCD Type 2 records expire and insert versions when tracked values change.
* SQL Server publication uses transactional loading.
* Incremental warehouse publication merges by deterministic surrogate key.

## Workflow Orchestration

The repository includes a 13-task Databricks/Lakeflow workflow:

1. Environment validation
2. SQL Server Bronze ingestion
3. PostgreSQL Bronze ingestion
4. File-feed Bronze ingestion
5. Customer Silver processing
6. Product Silver processing
7. Sales Silver processing
8. Digital-data Silver processing
9. Gold dimension creation
10. Gold fact creation
11. Data-quality gate
12. Gold publication
13. Final reconciliation and demonstration queries

The workflow definition includes:

* Task dependencies
* Runtime parameters
* Batch identifiers
* Full and incremental load modes
* Retry behavior
* Logging
* Required validation gates
* Publication controls

## Power BI and Analytics

The project includes:

* A Power BI semantic-model specification
* Star-schema relationship definitions
* DAX measures
* Dashboard-page requirements
* SQL validation queries
* KPI definitions
* Twenty analyst-ready SQL questions

Example measures include:

* Total Revenue
* Gross Profit
* Gross Margin Percentage
* Orders
* Units Sold
* Average Order Value
* Returned Units
* Return Rate
* On-Time Delivery Percentage
* Marketing Spend
* Web Sessions
* Conversion Rate
* Attributed Revenue
* Return on Ad Spend
* Inventory On Hand
* Stockout Risk Count

Power BI measures are stored in [`powerbi/measures.dax`](powerbi/measures.dax).

Independent SQL validation is stored in [`sql/sqlserver/analytics/kpi_validation_queries.sql`](sql/sqlserver/analytics/kpi_validation_queries.sql).

## Repository Structure

```text
SQL-Data-Warehouse-Project/
├── .github/
│   └── workflows/                  # GitHub Actions validation
├── config/                         # Runtime and generation configuration
├── databricks/
│   ├── notebooks/                  # Bronze, Silver, Gold, quality, and demo tasks
│   └── jobs/                       # 13-task workflow definition
├── datasets/
│   ├── sample/                     # Deterministic fictional source data
│   └── demo_gold/                  # Locally validated Gold outputs
├── docs/
│   ├── images/                     # Architecture, lineage, ERD, and schema diagrams
│   ├── manual/                     # Complete project build manuals
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── source_to_target_mapping.md
│   ├── kpi_definitions.md
│   └── runbook.md
├── notebooks/                      # Executed local validation notebook
├── powerbi/                        # Semantic model, DAX, and dashboard requirements
├── scripts/
│   ├── data_generation/            # Synthetic-data generation
│   ├── extraction/                 # Full and incremental batch extraction
│   ├── loading/                    # SQL Server and PostgreSQL loaders
│   ├── local_demo/                 # Locally executable Gold parity pipeline
│   ├── documentation/              # Metadata-document generation
│   └── validation/                 # Quality and repository validation
├── sql/
│   ├── databricks/                 # Spark SQL and Delta patterns
│   ├── postgres/                   # PostgreSQL DDL and validation
│   └── sqlserver/                  # ERP, warehouse, validation, and analytics SQL
├── tests/                          # Unit, integration, quality, and reconciliation tests
├── .env.example
├── FILE_MANIFEST.md
├── PROJECT_COMPLETENESS_CHECKLIST.md
├── requirements.txt
└── README.md
```

## Quick Start

The fastest demonstration requires **Python 3.13** and does not require database or cloud credentials.

### Windows PowerShell

```powershell
git clone https://github.com/Losboules/SQL-Data-Warehouse-Project.git
cd SQL-Data-Warehouse-Project

py -3.13 -m venv .venv

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

python -m scripts.data_generation.generate_northstar_data `
    --scale quick `
    --seed 20260815 `
    --output-dir datasets\sample

python -m scripts.local_demo.build_local_gold `
    --input-dir datasets\sample `
    --output-dir datasets\demo_gold

python -m pytest -q
```

### macOS or Linux

```bash
git clone https://github.com/Losboules/SQL-Data-Warehouse-Project.git
cd SQL-Data-Warehouse-Project

python3.13 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

python -m scripts.data_generation.generate_northstar_data \
    --scale quick \
    --seed 20260815 \
    --output-dir datasets/sample

python -m scripts.local_demo.build_local_gold \
    --input-dir datasets/sample \
    --output-dir datasets/demo_gold

python -m pytest -q
```

After the commands finish, inspect:

* [`datasets/sample/metadata/batch_manifest.json`](datasets/sample/metadata/batch_manifest.json)
* [`datasets/demo_gold/gold_manifest.json`](datasets/demo_gold/gold_manifest.json)
* [`datasets/demo_gold/quality_results.json`](datasets/demo_gold/quality_results.json)
* [`datasets/demo_gold/reconciliation_results.json`](datasets/demo_gold/reconciliation_results.json)
* [`notebooks/Northstar_Retail_Local_Validation_Demo.html`](notebooks/Northstar_Retail_Local_Validation_Demo.html)

## Full Platform Execution

The complete environment-based implementation follows this order:

1. Copy `.env.example` to `.env` and enter local connection values.
2. Create the SQL Server ERP database and tables.
3. Create the PostgreSQL digital and marketing database.
4. Load and validate the deterministic source data.
5. Extract a full or incremental batch.
6. Upload the complete batch to a Databricks Unity Catalog volume.
7. Run the 13-task Databricks/Lakeflow workflow.
8. Download the validated Gold publication.
9. Create and load the SQL Server dimensional warehouse.
10. Connect Power BI to the warehouse.
11. Add the provided DAX measures and report pages.
12. Compare Power BI results with independent SQL queries.

Detailed instructions are available in:

* [`docs/runbook.md`](docs/runbook.md)
* [`docs/manual/Northstar_Retail_Complete_Manual_Build_Workbook.md`](docs/manual/Northstar_Retail_Complete_Manual_Build_Workbook.md)

## GitHub Actions

The GitHub Actions workflow validates:

* Python syntax
* Required project files
* SQL dialect separation
* Notebook structure
* JSON and YAML assets
* Markdown links
* Secret patterns
* Data-quality contracts
* Source-to-target reconciliation
* Unit and integration tests

Workflow definition:

[` .github/workflows/validate_project.yml`](.github/workflows/validate_project.yml)

## Implementation Status

| Component                       | Status                                                              |
| ------------------------------- | ------------------------------------------------------------------- |
| Source-code implementation      | Complete                                                            |
| Deterministic sample generation | Locally validated                                                   |
| Local Gold parity model         | Locally validated                                                   |
| Automated quality checks        | Locally validated                                                   |
| Source-to-Gold reconciliation   | Locally validated                                                   |
| SQL Server source assets        | Implemented; requires a SQL Server environment                      |
| PostgreSQL source assets        | Implemented; requires a PostgreSQL environment                      |
| Databricks lakehouse assets     | Implemented; requires an authorized workspace                       |
| SQL Server warehouse assets     | Implemented; requires a SQL Server environment                      |
| Power BI model specification    | Implemented; Power BI Desktop is required to create the report file |

The repository intentionally distinguishes implemented source code and locally verified results from external platform execution evidence.

## Documentation

* [Architecture](docs/architecture.md)
* [Business Requirements](docs/business_requirements.md)
* [Data Dictionary](docs/data_dictionary.md)
* [Data Lineage](docs/data_lineage.md)
* [Source-to-Target Mapping](docs/source_to_target_mapping.md)
* [KPI Definitions](docs/kpi_definitions.md)
* [Runbook](docs/runbook.md)
* [Execution Status](docs/EXECUTION_STATUS.md)
* [Local Validation Report](docs/LOCAL_VALIDATION_REPORT.md)
* [Security and Cost Guidance](docs/security_and_cost.md)
* [Interview Walkthrough](docs/interview_walkthrough.md)
* [Project Completeness Checklist](PROJECT_COMPLETENESS_CHECKLIST.md)

## Key Engineering Decisions

* **Batch instead of streaming:** The project focuses on reliable daily retail reporting and recoverable batch processing.
* **Medallion architecture:** Bronze preserves source data, Silver applies quality rules, and Gold publishes business-ready models.
* **Star schema:** The model supports understandable and efficient business analysis.
* **SCD Type 2:** Customer and product history is preserved across changes.
* **Unknown members:** Incomplete records remain measurable without breaking fact loads.
* **Deterministic keys:** Repeat processing updates existing events rather than duplicating them.
* **Blocking quality gate:** Required failures stop publication.
* **Independent reconciliation:** Trusted metrics are verified using separate calculations and SQL queries.
* **Local-first architecture:** Manual cloud boundaries are documented instead of implying unsupported access to local services.
* **Synthetic data:** The project demonstrates engineering patterns without exposing real customer information.

## Author

**Kirolos Boules**

Data Engineer | Python | SQL | ETL/ELT | Databricks

* GitHub: [github.com/Losboules](https://github.com/Losboules)
* LinkedIn: [linkedin.com/in/KirolosBoules](https://www.linkedin.com/in/KirolosBoules)

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
