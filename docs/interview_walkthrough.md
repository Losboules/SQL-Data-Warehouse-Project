# Interview and Teach-Back Preparation

## 30-second explanation

Northstar Retail is a fictional omnichannel data platform I am building from local SQL Server, PostgreSQL, and file feeds. I generate reproducible synthetic data, extract it in traceable batches, process Bronze, Silver, and Gold Delta layers in Databricks Jobs, publish a dimensional warehouse back to SQL Server, and define Power BI measures. I only present results after reconciliation and data-quality gates pass.

## 2-minute explanation

Leadership's reports disagree because operational sales and inventory, digital behavior, marketing, shipping, and returns are separated. The local-first architecture keeps SQL Server and PostgreSQL on my Windows computer, uses Python for generation, load, manifest-driven extraction, and publication, and uses a manual Unity Catalog volume boundary because cloud Databricks cannot reach localhost. Bronze preserves source evidence, Silver standardizes and quarantines controlled defects, and Gold uses conformed dimensions, SCD Type 2 for customers/products, and facts with explicit grain. A Lakeflow Job enforces dependencies and blocks publication on failed tests. The validated Gold export is loaded transactionally into `NorthstarRetail_DW`, and Power BI uses a single-direction star schema and documented DAX measures. My proof is the batch manifest, job run, quality results, SQL reconciliation, and matching Power BI values—not file existence alone.

## 5-minute architecture walkthrough

1. **Requirements:** define stakeholders, grains, KPI formulas, date roles, quality expectations, and exclusions first.
2. **Sources:** normalized ERP in SQL Server, digital model in PostgreSQL, and file feeds. All records are fictional and reproducible.
3. **Local orchestration boundary:** Python extracts full or incremental batches with batch ID, row count, and checksum; I manually upload one immutable folder.
4. **Lakehouse:** Bronze appends/replaces the batch with audit metadata; Silver casts, cleans, deduplicates, conforms, and quarantines; Gold resolves SCD-aware dimensions and fact grains.
5. **Workflow:** environment, parallel Bronze tasks, dependent Silver domains, dimensions, facts, data-quality gate, publish, and final reconciliation.
6. **Serving:** download validated Gold, stage and load SQL Server warehouse in a transaction, then refresh Power BI.
7. **Trust:** reconcile source-to-Bronze, Bronze-to-Silver, Silver-to-Gold, revenue, duplicate reruns, and semantic measures.
8. **Limitations:** manual handoffs and simplified attribution are intentional Track A constraints; Track B covers managed networking and direct JDBC as an extension.

## 10-minute technical walkthrough outline

- Minute 0–1: business problem and definitions.
- Minute 1–2: source ERDs and generated quality fixtures.
- Minute 2–3: repository, configuration, credentials, and batch manifest.
- Minute 3–5: medallion contracts, example customer cleanup, and quarantine.
- Minute 5–6: SCD2 timeline and event-time dimension lookup.
- Minute 6–7: fact_sales grain, revenue arithmetic, unknown keys.
- Minute 7–8: Jobs dependency and failure/repair behavior.
- Minute 8–9: SQL Server publication and Power BI relationships/measures.
- Minute 9–10: verification evidence, limitations, and next scaling step.

# Interview questions and beginner-friendly answers

## 1. What business problem does the project solve?

**Answer:** It brings operational sales, digital behavior, batch files, inventory, shipping, returns, and marketing into a governed daily platform so different teams use the same definitions. The technical success criterion is not merely moving data; it is producing traceable, reconciled facts and reusable semantic measures.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 2. Why use Bronze, Silver, and Gold?

**Answer:** Each layer has a different contract. Bronze preserves the source and batch evidence, Silver applies explicit quality and conformance rules, and Gold presents stable dimensional grains. Separating them makes reruns, debugging, lineage, and ownership clearer than one giant transformation.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 3. Why use both SQL Server and PostgreSQL?

**Answer:** The fictional company has separate operational domains and the project demonstrates heterogeneous-source integration. It also teaches that SQL dialects, drivers, tools, and operational design differ; it is not an argument that every real company needs both.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 4. Why is the source model normalized but the warehouse dimensional?

**Answer:** Operational systems normalize data to support correct transactional updates and reduce repeated facts. Analytics favors dimensions and facts because users repeatedly filter, group, and aggregate; a star schema reduces join ambiguity and makes business grain visible.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 5. What is the grain of fact_sales?

**Answer:** One valid order item, identified by order_item_id. Quantity, revenue, discounts, cost, and profit are additive at that grain, and order-level metrics use distinct order_id rather than counting fact rows.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 6. What is grain and why declare it first?

**Answer:** Grain is exactly what one row represents. Without it, keys and measures can silently double-count. Declaring grain determines uniqueness tests, dimension lookups, additive behavior, and valid joins.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 7. What is a surrogate key?

**Answer:** A warehouse-controlled key such as customer_key. It is separate from the source customer_number and allows multiple historical versions, unknown members, and source-system integration without changing the natural business identifier.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 8. How did you prevent duplicate loads?

**Answer:** Each task receives one batch ID. Bronze replaces the same batch before appending; Silver uses batch replacement or merge; Gold enforces deterministic grain and uniqueness checks; the Job permits only one concurrent run. I verify a repair rerun leaves counts stable.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 9. What makes a pipeline idempotent?

**Answer:** Running the same input and batch again produces the same trusted state rather than an extra copy. Idempotency requires stable identities, controlled overwrite/merge scopes, transactions where appropriate, and tests—not merely a statement in documentation.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 10. How did you handle SCD Type 2?

**Answer:** I compare a hash of tracked attributes on the current dimension row. A change expires the old version with an end date and current flag false, then inserts a new current version. Facts look up the version whose effective dates contain the event date.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 11. Why Type 2 for customer and product?

**Answer:** Historical customer tier/address attributes and product category/cost/descriptions can change, and past reports may need the attributes that were true at the event time. Type 1 would overwrite history. I choose tracked columns deliberately because Type 2 on every field creates noise.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 12. What is the unknown member?

**Answer:** Dimension key 0 represents missing, invalid, or late-arriving dimension context. It keeps fact foreign keys valid and makes the problem measurable. It is not permission to ignore source quality; unknown-key rates are quality checks.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 13. How do you handle late-arriving dimensions?

**Answer:** The fact can temporarily use key 0 while retaining the natural key and batch evidence. A later repair resolves the dimension and updates the fact under a controlled rule. Alternatively, a minimal inferred member can be created, but that policy must be explicit.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 14. How did you validate revenue?

**Answer:** I use the same valid-line population and formula—quantity times unit price minus line discount—from Silver through Gold, SQL Server, and Power BI. I compare row counts and sums, define exclusions, and accept only documented rounding tolerance.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 15. What does a data-quality gate do?

**Answer:** It stores test results and raises a task failure when a required rule fails. Publication depends on that task, so a bad batch cannot be exported just because a user clicks the next notebook.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 16. What kinds of dirty data are included?

**Answer:** Controlled duplicate business keys, null/malformed emails, whitespace/case issues, invalid codes, impossible quantities, unknown references, mixed date formats, late records, out-of-order events, currency differences, and time-zone variations. A fixture records configured injections.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 17. Why intentionally generate dirty data?

**Answer:** Real engineering is mostly about behavior when inputs are imperfect. Controlled defects make quality rules testable and repeatable without using real personal data. Clean-only fixtures would let transformations appear correct without proving rejection and quarantine paths.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 18. What is quarantine?

**Answer:** A governed table or path for records that cannot enter a trusted layer under current rules. It retains the source values, rule, batch, and timestamp so owners can investigate. Quarantine counts must reconcile with layer input.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 19. What is the difference between ETL and ELT here?

**Answer:** Local source loading and extraction include ETL-like movement, while Databricks primarily follows ELT: land raw data first, then transform in the lakehouse. The important point is where transformation occurs and which copy is preserved.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 20. What happens when a Databricks task fails?

**Answer:** Dependent tasks do not run. I inspect the exact task log and quality/quarantine evidence, fix the cause in version control, rerun local checks, then use a repair run from the earliest affected task. Same-batch behavior must not duplicate data.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 21. Why can't Databricks connect to localhost?

**Answer:** The Databricks compute runs in a remote environment; its localhost is not my Windows computer. Track A therefore uses an uploaded file batch. Track B needs a network-accessible managed source, firewall/private networking, supported driver, and secret-managed identity.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 22. Why is Track A partly manual?

**Answer:** It is a low-cost, honest learning architecture. The manual boundary isolates local systems from cloud networking while still teaching source extraction, manifests, lakehouse layers, orchestration, publication, and consumption. I label the operational limitation rather than disguising it.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 23. What is a high-water mark?

**Answer:** The latest source update value that a successful extraction has fully processed. The next incremental run requests rows greater than that value. It advances only after success, and tie-breaker keys may be needed when timestamps are not unique.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 24. How do you handle a failure halfway through extraction?

**Answer:** The extractor writes to a unique batch folder and records status in a manifest. I do not advance the watermark until the batch is complete. A failed partial batch is not treated as trusted input; I rerun with the same logical bounds or a new controlled batch.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 25. Why use checksums?

**Answer:** A checksum helps prove that the file uploaded or processed is the same bytes the extractor wrote. It detects accidental change or corruption; it does not prove the data is semantically correct.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 26. What is Delta Lake adding?

**Answer:** Delta tables provide transactional table behavior over lake files, schema metadata, versioned changes, and merge/update patterns. In this project they support batch replacement, merge, reproducible table access, and governed medallion layers.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 27. Why use a star schema?

**Answer:** It gives each business event a clear fact grain and shared descriptive dimensions. BI relationships are predictable, SQL is understandable, and measures aggregate correctly when keys and relationships are designed well.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 28. What are additive and non-additive measures?

**Answer:** Revenue and quantity are generally additive across all relevant dimensions. Ratios such as margin percentage are recalculated from aggregated numerator and denominator. Inventory snapshots are not additive across time because summing daily stock double-counts the same inventory.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 29. How do you define return rate?

**Answer:** Returned units divided by sold units for a compatible population. I must state whether date filtering is by purchase date or return date, and I do not divide return rows by orders unless the business explicitly wants an order-return incidence metric.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 30. How do you define on-time delivery?

**Answer:** Delivered shipments with actual delivery date on or before promised date divided by delivered shipments with an actual date. The grain is shipment, not order, because one order may split into multiple shipments.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 31. How is ROAS limited?

**Answer:** The beginner model links converting sessions to order IDs and is essentially simplified last-session attribution. It does not establish causality or allocate multi-touch credit. I check duplicate links and present the attribution assumption beside the metric.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 32. Why use a semantic layer?

**Answer:** It centralizes relationships, date behavior, measure formulas, formatting, descriptions, and reusable business definitions. Otherwise each report author can compute a different version of revenue or return rate.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 33. Why prefer explicit DAX measures?

**Answer:** They are named, documented, format-controlled, reusable, and testable. Implicit sums hide business logic and can encourage users to aggregate technical columns incorrectly.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 34. Import or DirectQuery for Track A?

**Answer:** Import is the default because the local warehouse is modest, interactive performance is predictable, and refresh can be controlled after publication. DirectQuery has freshness advantages but adds source load, latency, feature, and modeling constraints.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 35. How do you avoid ambiguous Power BI relationships?

**Answer:** I use one-to-many, single-direction dimension-to-fact relationships. Secondary shipment date roles are inactive and activated in specific measures if needed. I avoid direct fact-to-fact joins and bidirectional filtering without a tested reason.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 36. What is data lineage?

**Answer:** Evidence connecting a report value back through a measure, serving table, Gold fact/dimension, Silver transformation, Bronze record, source file/table, and batch. This project uses mappings, batch IDs, source/file metadata, task order, and reconciliation results.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 37. How do you protect secrets?

**Answer:** Passwords stay in ignored `.env` files; Databricks uses secret management or identities; logs/screenshots are redacted; CI scans common patterns. If a secret is committed, I revoke or rotate it before cleaning history.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 38. What does least privilege mean here?

**Answer:** Each identity gets only the permissions needed: source extractor read-only, workflow access to its catalog/schema/volume, publisher stage/load rights, and analysts read-only semantic access. An administrator credential is not a normal runtime credential.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 39. How does CI/CD help this project?

**Answer:** The free GitHub Actions workflow checks structure, SQL dialect labels, notebook syntax/JSON, secret patterns, relative links, linting, and local tests. It cannot execute SQL Server or Databricks without paid/secured infrastructure, so those gates remain documented run evidence.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 40. What would change at 100 times the data volume?

**Answer:** I would profile bottlenecks before redesigning. Likely changes include source-side partitioned/incremental extraction, bulk copy, optimized file sizes, partition/clustering choices, incremental Gold, stronger orchestration observability, scalable serving mode, and cost/performance testing. I would not simply use the portfolio scale setting.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 41. Which parts are batch and what could stream?

**Answer:** All required phases are daily batch. Web events, inventory movements, and shipment tracking could become streaming, but dimensions, late data, deduplication, watermarks, cost, and exactly-once expectations would need a separate design.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 42. What are the limitations of the local-first track?

**Answer:** Manual handoffs, no real-time operation, local service availability, no production identity/network design, simplified attribution, USD-only reporting, and incomplete production observability. Those are explicitly documented rather than presented as enterprise production readiness.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 43. How would you add CDC?

**Answer:** Choose source-supported change data capture, retain operation type and source ordering metadata in Bronze, deduplicate by source position, apply deletes deliberately, and test replay/idempotency. It requires database configuration and privileges beyond the beginner path.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 44. How would you handle schema drift?

**Answer:** Bronze may permit intentional additive columns while recording schema; Silver uses explicit selections/casts and fails or quarantines unsupported changes. A schema-drift test alerts before Gold and semantic contracts silently change.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.
## 45. What did you personally implement versus use as reference material?

**Answer:** The workbook provides curriculum, boilerplate, patterns, TODO skeletons, tests, and reference answers. I only claim tasks after I type/adapt them, run them in my environment, capture evidence, and explain them. The final definition-of-done distinguishes reference material from personal verification.

**Likely follow-up:** Give one concrete file, query, test, or screenshot from your verified run that proves the answer.


# Defend every design choice worksheet

For each decision, complete all columns before an interview.

| Decision | Requirement it serves | Alternative | Why not chosen now | Failure mode | Test/evidence | What would change at scale |
|---|---|---|---|---|---|---|
| Manual volume handoff | Low-cost local sources | Direct JDBC | No safe route to localhost | Wrong/missing batch | Manifest + environment check | Cloud-managed sources/network |
| SCD2 customer | Historical attributes | Type 1 | Would rewrite history | Overlap/multiple current rows | SCD tests | Identity resolution/MDM |
| [ADD DECISION] | | | | | | |

# STAR troubleshooting story template

- **Situation:** What business/pipeline context existed? Include phase and batch, not confidential details.
- **Task:** What trustworthy outcome were you responsible for?
- **Action:** What evidence did you inspect, how did you isolate the cause, what code/config/test changed, and how did you protect data?
- **Result:** What verified test/reconciliation passed? Use real numbers only after your run.
- **Reflection:** What prevention or monitoring did you add?

# Final self-assessment rubric

Score each 0–3: 0 not started, 1 can follow, 2 can explain and reproduce, 3 can adapt and defend.

| Area | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Requirements/KPIs | Cannot define | Reads definitions | Reproduces and validates | Resolves ambiguity with stakeholders |
| SQL/source design | Cannot navigate | Runs provided DDL | Explains keys/indexes/dialects | Adapts model safely |
| Python/generation | Cannot run | Runs quick mode | Explains functions/seed/FKs | Adds a domain and tests |
| Ingestion/manifest | Cannot trace batch | Follows steps | Explains checksums/watermarks | Repairs/replays safely |
| Spark/Delta | Cannot identify layers | Runs notebooks | Explains transformations/merge | Tunes and handles drift |
| Dimensional model | Cannot state grain | Names facts/dims | Defends grain/SCD/unknowns | Evolves model without breaking history |
| Quality/reconciliation | Relies on screenshots | Runs tests | Explains gates and tie-outs | Designs new risk-based checks |
| Jobs/operations | Clicks run | Follows graph | Repairs failed run safely | Designs alerts and operational SLOs |
| Power BI | Builds visuals only | Adds measures | Validates context/relationships | Diagnoses complex totals/roles |
| Security/cost/Git | Uses defaults | Follows checklist | Explains least privilege/CI | Designs production controls |
| Communication | Recites tools | Gives overview | Tells evidence-based story | Handles follow-up tradeoffs calmly |
