# Assumption Log

| ID | Date | Assumption or decision | Owner | Evidence | Risk if wrong | Review date | Status |
|---|---|---|---|---|---|---|---|
| A-001 | 2026-08-16 | Track A reports in USD only. | Project owner | Business requirements and quality rules | Non-USD records are quarantined rather than converted. | Before production use | Accepted for Track A |
| A-002 | 2026-08-16 | Daily batch latency is acceptable for the portfolio scenario. | Project owner | Architecture decision | Near-real-time use cases would be delayed. | Before streaming extension | Accepted for core scope |
| A-003 | 2026-08-16 | Manual upload/download boundaries are acceptable in Track A. | Project owner | Local-first architecture | Operational effort and human error are higher than automated cloud transfer. | Before cloud deployment | Accepted for core scope |
| A-004 | 2026-08-16 | Converting-session order IDs provide a simplified attribution rule. | Project owner | KPI definition | ROAS is descriptive and not causal or multi-touch. | Before marketing decisions | Accepted with limitation |
| A-005 | 2026-08-16 | Inventory reporting normally uses one selected snapshot date. | Project owner | Fact grain contract | Summing snapshots across dates overstates inventory. | During every report review | Required model rule |
| A-006 | 2026-08-16 | Local pandas Gold output is a parity/CI harness, not a substitute for a Databricks run. | Project owner | Execution status | Users could overstate cloud execution. | Before portfolio publication | Required disclosure |
