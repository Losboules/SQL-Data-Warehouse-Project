# Northstar Retail Project Completeness Checklist

This checklist separates what is **verified inside the downloadable package** from what can only be verified after the project is connected to your own SQL Server, PostgreSQL, Databricks, and Power BI environments.

Status meanings:

- `[x]` Verified in the packaged environment
- `[ ]` Requires execution or evidence in the user’s environment
- `[!]` Use only when a verification fails and needs troubleshooting

## A. Package structure and safety

- [x] Root `README.md`, license, dependency files, `.gitignore`, and `.env.example` exist.
- [x] No real `.env`, password, private key, Databricks token, or GitHub token is packaged.
- [x] Python caches, pytest caches, virtual environments, and local database files are excluded from the release ZIP.
- [x] `FILE_MANIFEST.md` records every packaged artifact except itself with size, SHA-256 hash, and purpose.
- [x] The complete Markdown and PDF manuals are included under `docs/manual/`.
- [x] Repository-relative Markdown links outside the imported manual pass validation.
- [x] JSON, YAML, notebook JSON, Python syntax, SQL dialect headers, and diagram wrappers pass static validation.

## B. Deterministic fictional source data

- [x] The quick fixture contains 23 source files across SQL Server, PostgreSQL, CSV, JSON, and metadata folders.
- [x] The generator uses a fixed random seed and a fixed generated-through timestamp for reproducibility.
- [x] `batch_manifest.json` includes row counts and SHA-256 checksums.
- [x] Intentional data-quality defects are documented in `expected_quality_issues.json`.
- [x] Generated orders do not contain unexpected customer orphans.
- [x] Generated order items do not contain unexpected order orphans.

## C. Local Gold parity model

- [x] All nine dimensions are generated: date, customer, product, store, employee, supplier, promotion, channel, and campaign.
- [x] All six facts are generated: sales, returns, inventory snapshot, shipments, web sessions, and marketing spend.
- [x] Every dimension has exactly one key-0 Unknown member.
- [x] Customer and product include SCD Type 2 fields and deterministic historical versions in the local parity path.
- [x] Fact grains are unique.
- [x] Fact foreign keys resolve to dimension members or the Unknown member.
- [x] Required sales arithmetic, nonnegative-value, accepted-value, and date rules pass.
- [x] Seventy required local quality checks pass with zero required failures.
- [x] Source-to-Gold valid-sales row reconciliation passes.
- [x] Source-to-Gold net-sales reconciliation passes to the configured currency tolerance.
- [x] The packaged sample reconciles to 397 valid sales lines and `$28,325.94` net sales.

## D. SQL Server ERP and PostgreSQL source systems

- [x] SQL Server ERP database/schema/table DDL is included and guarded for safe development reruns.
- [x] PostgreSQL digital/marketing database/schema/table DDL is included.
- [x] Source loaders use environment variables rather than embedded credentials.
- [x] Source validation SQL covers counts, orphans, duplicates, malformed values, and controlled defects.
- [ ] Install or connect to SQL Server in your environment.
- [ ] Execute the SQL Server ERP DDL and record the actual server/database context.
- [ ] Load the generated ERP fixture and save validation-query evidence.
- [ ] Install or connect to PostgreSQL in your environment.
- [ ] Execute the PostgreSQL digital DDL and record the actual host/port/database context.
- [ ] Load the generated digital fixture and save validation-query evidence.

## E. Full and incremental local extraction

- [x] The extraction code supports full and incremental modes.
- [x] Batch IDs, manifests, row counts, timestamps, and checksums are implemented.
- [x] High-water-mark state is updated only after a completed extraction.
- [x] Rerun-safe output folder checks are implemented.
- [ ] Run a full extraction against your populated SQL Server and PostgreSQL sources.
- [ ] Run an incremental extraction after adding changed records.
- [ ] Verify the incremental batch contains only the intended inserts/updates.
- [ ] Archive the actual manifest and high-water-mark evidence.

## F. Databricks medallion pipeline and orchestration

- [x] Thirteen Git-friendly Databricks source notebooks are included, numbered `00` through `12`.
- [x] Bronze ingestion covers SQL Server extracts, PostgreSQL extracts, and file feeds.
- [x] Silver transformations include typing, standardization, deduplication, business-rule validation, and quarantine outputs.
- [x] Gold logic implements all nine dimensions and all six facts.
- [x] Gold fact publication uses deterministic-key Delta MERGEs across batches; full and incremental quality modes are explicitly parameterized.
- [x] Initial customer/product SCD2 versions begin on source-relevant dates so historical facts can resolve point-in-time keys.
- [x] Customer/product SCD Type 2 logic, unknown-member handling, and fact dimension-key resolution are implemented.
- [x] The data-quality notebook persists results and blocks publication on required failures.
- [x] The publication notebook exports all validated Gold tables plus audit metadata.
- [x] The final notebook performs KPI and source-to-Gold reconciliation checks.
- [x] The Lakeflow Job definition has 13 tasks with a complete dependency chain.
- [ ] Import or sync the notebooks into your authorized Databricks workspace.
- [ ] Select available compute and configure catalog/schema/volume permissions.
- [ ] Upload one complete extraction batch without changing its filenames or manifest.
- [ ] Run the Job with the exact `batch_id` and save the run ID.
- [ ] Inspect every task output and verify the quality gate before publication.
- [ ] Rerun the same batch and verify idempotent counts.
- [ ] Add a changed batch and verify SCD Type 2 and incremental fact behavior.

## G. SQL Server dimensional serving warehouse

- [x] Warehouse DDL creates nine dimensions, six facts, audit tables, constraints, indexes, and semantic views.
- [x] Staging structures exist for every Gold table.
- [x] Key-0 Unknown members are created before fact publication.
- [x] The Python publisher supports transactional `full-dev` and key-based `incremental` modes.
- [x] Analyst SQL includes 20 business questions and independent KPI validation queries.
- [ ] Execute the warehouse DDL in `NorthstarRetail_DW`.
- [ ] Download a validated Databricks Gold publication folder.
- [ ] Run the `full-dev` publication and inspect audit/row-count results.
- [ ] Run the same publication again and prove it does not duplicate facts.
- [ ] Run the incremental publication with a changed batch and verify merges.
- [ ] Execute warehouse validation and analyst queries against actual tables.

## H. Power BI semantic model and report

- [x] The semantic-model contract defines tables, relationships, cardinality, filter direction, date handling, formatting, and hidden keys.
- [x] The DAX file contains revenue, profit, margin, orders, units, AOV, returns, shipments, marketing, conversion, customer, and inventory measures.
- [x] The report requirements define executive, sales, customer, inventory, marketing, shipping, and return analysis pages.
- [x] Independent SQL validation queries are included.
- [ ] Connect Power BI Desktop to your verified SQL Server warehouse.
- [ ] Create and inspect every relationship in Model view.
- [ ] Add and format every DAX measure.
- [ ] Build each required report page and configure interactions.
- [ ] Compare Power BI values to independent SQL under matching filters.
- [ ] Save the `.pbix` or PBIP locally and add only safe screenshots/evidence to Git.

## I. Documentation, portfolio, and CI

- [x] Architecture, local-flow, cloud-flow, two ERDs, Gold star schema, Job dependencies, lineage, and SCD2 diagrams are included in DOT, Mermaid, and SVG formats.
- [x] Data dictionary, source-to-target mapping, KPI definitions, runbook, risk register, security/cost guidance, and assumption log are included.
- [x] An executed local showcase notebook and HTML rendering are included.
- [x] Resume, LinkedIn, demo-video, and interview materials distinguish source implementation from verified execution.
- [x] GitHub Actions validates files, SQL dialect headers, notebooks, secrets, links, project assets, and tests.
- [ ] Add your own external run IDs, query outputs, screenshots, and lessons learned.
- [ ] Remove or revise any portfolio claim that is not supported by your own evidence.
- [ ] Push a reviewed branch and confirm the GitHub Actions run passes in your repository.

## J. Final user-environment definition of done

Do not mark the end-to-end deployment complete until all items below are true.

- [ ] SQL Server ERP source DDL and load are verified by you.
- [ ] PostgreSQL digital source DDL and load are verified by you.
- [ ] Full and incremental extraction batches are verified by you.
- [ ] Databricks Bronze, Silver, Gold, quality, publication, and reconciliation tasks are verified by you.
- [ ] SQL Server warehouse full and incremental publication are verified by you.
- [ ] Power BI relationships, measures, report pages, and SQL reconciliations are verified by you.
- [ ] No secret or unnecessary personal information appears in Git history or screenshots.
- [ ] Every public achievement statement points to a run, query, test, file, or screenshot you personally inspected.
- [ ] You can explain the architecture, grains, keys, SCD choices, incremental strategy, quality gates, orchestration, and tradeoffs without reading a script.
