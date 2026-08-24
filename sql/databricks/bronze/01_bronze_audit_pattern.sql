-- Dialect: Databricks SQL / Spark SQL
-- Teaching pattern. The runnable Bronze implementation is in databricks/notebooks/01-03.
SELECT
  source.*,
  input_file_name() AS _source_file,
  current_timestamp() AS _ingested_at_utc,
  '${batch_id}' AS _batch_id,
  sha2(to_json(struct(source.*)), 256) AS _record_hash
FROM read_files('${input_path}', format => 'parquet') AS source;
