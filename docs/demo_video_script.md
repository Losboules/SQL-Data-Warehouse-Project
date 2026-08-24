# Demo Video Script

## 0:00–0:30 — Business problem

“Northstar Retail is a fictional omnichannel retailer whose ERP, website, marketing, shipment, return, and inventory data disagree across systems. My goal was to produce trusted daily metrics with evidence from source through dashboard.”

Show: README business problem and overall architecture. Do not show credentials.

## 0:30–1:30 — Sources and synthetic data

Show SQL Server and PostgreSQL ERDs, then the generator command and sample manifest. Explain fixed seed, scale settings, realistic dependencies, and controlled defects. Show one expected issue fixture and one relevant source row.

## 1:30–2:30 — Lakehouse and workflow

Show Bronze/Silver/Gold contracts and the Lakeflow Job graph. Explain the manual Track A boundary and why localhost is not reachable. Open one Silver notebook and one quarantine rule.

## 2:30–3:30 — Dimensional model and SCD2

Show the star schema and SCD2 timeline. State fact_sales grain in one sentence. Show the current/expired customer versions from your verified run.

## 3:30–4:30 — Quality and publication

Show the test-results table and one failed-then-fixed story. Show Gold export manifest, SQL Server audit row, and revenue reconciliation. Use real batch values only.

## 4:30–5:30 — Power BI and conclusion

Show Model view, date table, measure folder, Executive Overview, and Data Quality page. Put SQL validation next to one KPI. Conclude with limitations and the next extension.

## Recording checklist

- Crop or blur account email, paths, server identifiers, tokens, and passwords.
- Zoom so text is readable.
- Keep batch ID visible where it proves lineage.
- Do not claim portfolio-scale timing unless measured.
- Keep the GitHub README open at the final project link.
