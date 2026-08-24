# Daily Batch Runbook — Track A

## Before the run

1. **PowerShell, repository root:** activate `.venv` and run `git status`. Do not run from an unknown folder.
2. Confirm SQL Server and PostgreSQL services are running.
3. Confirm `.env` exists locally and is not tracked: `git check-ignore .env` should print `.env`.
4. Record the last successful high-water marks and any unresolved quality exceptions.

## Extract

```powershell
python -m scripts.extraction.extract_local_sources --mode incremental --watermark "[LAST_VERIFIED_UTC_TIMESTAMP]"
```

Expected: a new `datasets/raw/EXT-.../` batch folder with `batch_manifest.json`. Do not rename individual files.

## Handoff to Databricks

Upload the entire `EXT-...` folder beneath `/Volumes/<catalog>/landing/track_a_files/`. Verify the remote folder name exactly matches the local batch ID.

## Process

Run the Lakeflow Job with `batch_id=EXT-...`. Monitor tasks in dependency order. A red quality task is a stop condition, not permission to run publication manually.

## Repair

1. Open the failed task output and the relevant quarantine/test table.
2. Decide whether the failure is input quality, code, configuration, permission, or transient infrastructure.
3. Correct the cause in a branch and rerun automated tests.
4. Use **Repair run** from the earliest affected task. Same-batch logic must replace/merge safely.
5. Confirm row counts did not double.

## Publish

After the quality gate passes, download `/gold_exports/<batch_id>/` and run:

```powershell
python -m scripts.loading.load_gold_to_sqlserver --input-dir "C:\path\to\downloaded\gold_exports\<batch_id>" --mode full-dev
```

Then run `sql/sqlserver/validation/02_validate_warehouse.sql` in SSMS.

## Consume

Refresh Power BI only after SQL Server audit and reconciliation checks pass. Validate the KPI cards against `kpi_validation_queries.sql`, then capture the batch ID and refresh timestamp.

## Incident evidence

Preserve the local manifest, Databricks run URL/ID, failed message, quarantine counts, repair commit, final quality results, SQL audit rows, and Power BI validation. Redact secrets.
