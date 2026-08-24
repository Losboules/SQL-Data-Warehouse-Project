# Databricks learning assets

- `notebooks/00...12`: Git-friendly Databricks source notebooks in execution order.
- `jobs/job_definition.example.yml`: version-controlled dependency map.
- `jobs/job_task_map.md`: human-readable dependency diagram.

## Track A boundary

Your local SQL Server and PostgreSQL instances are not reachable from a cloud workspace simply because they use the name `localhost`. Track A therefore extracts locally, uploads a batch folder to a Unity Catalog volume, processes it in Databricks, and exports Gold files for local download. This manual boundary is intentional, honest, and inexpensive for learning.

## Workspace-specific placeholders

Replace catalog, schema, volume, user email, and batch ID values with resources that your workspace permits. Do not commit tokens or passwords. Read Phase 8 and Phase 14 before creating a Job.
