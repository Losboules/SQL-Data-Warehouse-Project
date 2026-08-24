# Lakeflow Jobs task map

```mermaid
flowchart TD
  E[environment_check] --> B1[bronze_sqlserver]
  E --> B2[bronze_postgres]
  E --> B3[bronze_files]
  B1 --> S1[silver_customers]
  B3 --> S1
  B1 --> S2[silver_products]
  B3 --> S2
  B1 --> S3[silver_sales]
  B3 --> S3
  S2 --> S3
  B2 --> S4[silver_digital]
  S1 --> D[gold_dimensions]
  S2 --> D
  S3 --> D
  S4 --> D
  D --> F[gold_facts]
  F --> Q[data_quality_gate]
  Q --> P[publish_gold]
  P --> R[final_reconciliation]
```

The quality gate is intentionally between Gold construction and publication. A failed required check must prevent publication. In Databricks Free Edition, compute and concurrency are quota-limited; this graph uses at most three parallel Bronze tasks and four parallel prerequisites for Gold dimensions, below the documented five-task concurrent Jobs limit as accessed on 2026-08-16.
