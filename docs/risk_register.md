# Risk Register

| ID | Risk | Probability | Impact | Early warning | Mitigation | Owner | Status |
|---|---|---:|---:|---|---|---|---|
| R-001 | Credentials are committed | Medium | High | `.env` appears in `git status` | `.gitignore`, secret scan, rotate immediately if exposed | Kirolos | Open |
| R-002 | Databricks cannot see local source | High if misunderstood | Medium | JDBC timeout to localhost | Use Track A volume handoff; do not tunnel casually | Kirolos | Mitigated by design |
| R-003 | Duplicate rerun inflates facts | Medium | High | Same batch doubles row count | Batch deletion/merge, unique grain tests, max concurrent runs 1 | Data engineering | Open until verified |
| R-004 | SCD2 facts join to current instead of event-time row | Medium | High | Historical reports change after customer/product update | Effective-date join tests and worked example | Data engineering | Open |
| R-005 | Return rate mixes incompatible date roles | Medium | Medium | SQL and dashboard disagree by period | Label purchase-date vs return-date view; validation samples | Analytics | Open |
| R-006 | Free-tier quotas interrupt learning runs | Medium | Low | Compute unavailable or quota warning | Use quick/small scale, stop retries, preserve outputs | Kirolos | Monitor |
| R-007 | Power BI ambiguous relationships change totals | Medium | High | Warning icon or totals vary unexpectedly | Single-direction star schema, inactive role dates, SQL validation | Kirolos | Open |
| R-008 | Larger generated files enter Git | Medium | Medium | Git status shows datasets/raw or generated | `.gitignore`, publish quick sample only | Kirolos | Mitigated by config |
| R-009 | Reference TODO is mistaken for completed work | Medium | High | README claims verified results without evidence | Status labels, checklist, screenshot proof, replace placeholders only after verification | Kirolos | Open |
| R-010 | Schema changes break ingestion | Medium | Medium | read/merge error or missing column | Schema drift tests, quarantine, explicit column lists | Data engineering | Open |
