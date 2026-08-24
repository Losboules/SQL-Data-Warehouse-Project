-- Dialect: SQL Server / T-SQL
-- Purpose: Create the local operational ERP database and schema safely.
-- Run in: SSMS query window connected to your local SQL Server instance.
-- Safety: This file creates missing objects. It does not drop existing data.

USE master;
GO

IF DB_ID(N'NorthstarRetail_ERP') IS NULL
BEGIN
    PRINT 'Creating database NorthstarRetail_ERP.';
    CREATE DATABASE NorthstarRetail_ERP;
END
ELSE
BEGIN
    PRINT 'Database NorthstarRetail_ERP already exists; leaving it in place.';
END;
GO

USE NorthstarRetail_ERP;
GO

IF SCHEMA_ID(N'erp') IS NULL
    EXEC(N'CREATE SCHEMA erp AUTHORIZATION dbo;');
GO

IF SCHEMA_ID(N'audit') IS NULL
    EXEC(N'CREATE SCHEMA audit AUTHORIZATION dbo;');
GO

IF OBJECT_ID(N'audit.source_load_batch', N'U') IS NULL
BEGIN
    CREATE TABLE audit.source_load_batch
    (
        batch_id            VARCHAR(80)  NOT NULL PRIMARY KEY,
        process_name        VARCHAR(100) NOT NULL,
        started_at_utc      DATETIME2(3) NOT NULL CONSTRAINT DF_source_load_started DEFAULT SYSUTCDATETIME(),
        finished_at_utc     DATETIME2(3) NULL,
        status              VARCHAR(20)  NOT NULL,
        source_file_count   INT          NULL,
        loaded_row_count    BIGINT       NULL,
        error_message       NVARCHAR(2000) NULL
    );
END;
GO

SELECT DB_NAME() AS current_database, SCHEMA_ID(N'erp') AS erp_schema_id;
GO
