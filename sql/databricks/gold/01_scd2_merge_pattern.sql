-- Dialect: Databricks SQL / Spark SQL
-- Near-complete SCD2 pattern. Test on a copy before adapting it.
MERGE INTO IDENTIFIER(:target_dimension) AS target
USING IDENTIFIER(:changed_source_rows) AS source
ON target.business_key = source.business_key AND target.is_current = true
WHEN MATCHED AND target.record_hash <> source.record_hash THEN UPDATE SET
  target.is_current = false,
  target.effective_end_date = date_sub(current_date(), 1);

-- A second INSERT step adds new and changed current versions. The two-step reason is explained in Phase 11.
