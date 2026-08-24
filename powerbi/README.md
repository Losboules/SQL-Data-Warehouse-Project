# Power BI Assets

This folder contains the complete text-based semantic-model contract, DAX measures, relationship specification, and page-by-page dashboard requirements. A `.pbix` file is intentionally not fabricated because Power BI Desktop must create and validate that binary/model artifact against the user’s actual SQL Server warehouse.

Build order:

1. Execute the SQL Server warehouse DDL and load validated Gold exports.
2. Open Power BI Desktop and use **Get Data > SQL Server** in Import mode.
3. Select the nine `dw.dim_*` and six `dw.fact_*` tables.
4. Create the relationships in `semantic_model.md`.
5. Create a dedicated `_Measures` table and add every measure from `measures.dax`.
6. Build and validate each page in `dashboard_requirements.md`.
7. Compare KPI values with `sql/sqlserver/analytics/kpi_validation_queries.sql` before publishing screenshots.
