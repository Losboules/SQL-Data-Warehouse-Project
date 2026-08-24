-- Dialect: SQL Server / T-SQL
-- Purpose: create empty staging tables that mirror warehouse targets.
-- Run after 01_create_warehouse.sql in NorthstarRetail_DW.
USE NorthstarRetail_DW;
GO

DECLARE @table sysname;
DECLARE table_cursor CURSOR LOCAL FAST_FORWARD FOR
SELECT name FROM sys.tables WHERE schema_id = SCHEMA_ID('dw');
OPEN table_cursor;
FETCH NEXT FROM table_cursor INTO @table;
WHILE @@FETCH_STATUS = 0
BEGIN
    DECLARE @stage sysname = N'stg_' + @table;
    IF OBJECT_ID(QUOTENAME('stg') + N'.' + QUOTENAME(@stage), N'U') IS NULL
    BEGIN
        DECLARE @sql nvarchar(max) = N'SELECT TOP (0) * INTO stg.' + QUOTENAME(@stage) + N' FROM dw.' + QUOTENAME(@table) + N';';
        EXEC sys.sp_executesql @sql;
    END;
    FETCH NEXT FROM table_cursor INTO @table;
END;
CLOSE table_cursor;
DEALLOCATE table_cursor;
GO
SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='stg' ORDER BY TABLE_NAME;
