# Optional Extensions — Not Required for the Beginner Definition of Done

| Extension | New concept | Prerequisite | Main new risk | Evidence before claiming completion |
|---|---|---|---|---|
| Streaming ingestion | Event-time, checkpoints, watermarks | Stable batch model | Duplicates/late data/state cost | Restart and late-event tests |
| Change Data Capture | Operation logs and source positions | Source privileges | Missed deletes/order | Replay and delete reconciliation |
| Auto Loader | Incremental file discovery | Cloud storage/UC setup | Schema drift/quota | Backfill and rescued-data tests |
| Lakeflow Declarative Pipelines/current equivalent | Managed declarative dependencies | Workspace feature | Tier/support changes | Current official docs and run evidence |
| dbt | SQL model DAGs/tests/docs | Reachable target/adapter | Duplicate orchestration | CI and lineage evidence |
| Data contracts | Producer-consumer schema/quality agreement | Stable domains | Governance overhead | Version/change simulation |
| Great Expectations or similar | External quality framework | Existing test strategy | Tool complexity | Same risk coverage and stored results |
| Infrastructure as Code | Repeatable cloud resources | Cloud account and budget | Accidental spend/destruction | Plan/review/destroy evidence |
| Databricks Declarative Automation Bundles | Versioned workspace deployment | CLI/auth/workspace | Environment mismatch | Dev deployment and rollback |
| Azure Data Factory | Managed movement/orchestration | Azure account/network | Cost/duplicate orchestration | Monitored pipeline and rerun proof |
| Kafka | Distributed event streaming | Streaming design | Operational complexity | Partition/replay/exactness tests |
| Machine learning | Forecast/segmentation use | Trusted features and evaluation | Leakage/unfair interpretation | Baseline, holdout, monitoring |
| Forecasting | Time-series demand prediction | Consistent date/product grain | Leakage/seasonality | Backtest and business baseline |
| Customer segmentation | Feature engineering/clustering | Identity/conformed customer | Unstable/unexplainable groups | Stability and interpretation review |
| Slowly changing facts | Correct fact updates over time | Stable fact grain | Double-count/history confusion | Versioning and as-of queries |
| Role/row-level security | User-specific visibility | Identity/governance | Unauthorized access | Positive and negative access tests |
| Cloud deployment | Managed sources/storage/BI | Budget/network/secrets | Security/cost | Architecture review and teardown plan |

Treat every extension as a new project decision, not a badge to add automatically.
