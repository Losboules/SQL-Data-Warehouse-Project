-- Dialect: SQL Server / T-SQL
-- Purpose: create the local serving warehouse NorthstarRetail_DW.
-- Run in: SSMS connected to your local SQL Server instance.
-- Safety: creates missing objects; it does not drop populated tables.

USE master;
GO
IF DB_ID(N'NorthstarRetail_DW') IS NULL CREATE DATABASE NorthstarRetail_DW;
GO
USE NorthstarRetail_DW;
GO
IF SCHEMA_ID(N'dw') IS NULL EXEC(N'CREATE SCHEMA dw AUTHORIZATION dbo;');
IF SCHEMA_ID(N'stg') IS NULL EXEC(N'CREATE SCHEMA stg AUTHORIZATION dbo;');
IF SCHEMA_ID(N'audit') IS NULL EXEC(N'CREATE SCHEMA audit AUTHORIZATION dbo;');
IF SCHEMA_ID(N'semantic') IS NULL EXEC(N'CREATE SCHEMA semantic AUTHORIZATION dbo;');
GO

IF OBJECT_ID(N'audit.etl_batch', N'U') IS NULL
CREATE TABLE audit.etl_batch
(
    batch_id VARCHAR(80) PRIMARY KEY,
    process_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at_utc DATETIME2(3) NOT NULL,
    finished_at_utc DATETIME2(3) NULL,
    error_message NVARCHAR(2000) NULL
);
GO
IF OBJECT_ID(N'audit.reconciliation_result', N'U') IS NULL
CREATE TABLE audit.reconciliation_result
(
    reconciliation_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    batch_id VARCHAR(80) NOT NULL,
    check_name VARCHAR(150) NOT NULL,
    source_value DECIMAL(38,6) NULL,
    target_value DECIMAL(38,6) NULL,
    difference_value DECIMAL(38,6) NULL,
    status VARCHAR(20) NOT NULL,
    checked_at_utc DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID(N'dw.dim_date', N'U') IS NULL
CREATE TABLE dw.dim_date
(
    date_key INT NOT NULL PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_number TINYINT NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    week_number TINYINT NOT NULL,
    month_number TINYINT NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    quarter_number TINYINT NOT NULL,
    calendar_year SMALLINT NOT NULL,
    is_weekend BIT NOT NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL
);
GO

IF OBJECT_ID(N'dw.dim_customer', N'U') IS NULL
CREATE TABLE dw.dim_customer
(
    customer_key BIGINT NOT NULL PRIMARY KEY,
    customer_number VARCHAR(25) NOT NULL,
    first_name NVARCHAR(80) NULL,
    last_name NVARCHAR(80) NULL,
    email NVARCHAR(255) NULL,
    state_code VARCHAR(10) NULL,
    loyalty_tier VARCHAR(20) NULL,
    signup_date DATE NULL,
    effective_start_date DATE NOT NULL,
    effective_end_date DATE NOT NULL,
    is_current BIT NOT NULL,
    record_hash CHAR(64) NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL
);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID(N'dw.dim_customer') AND name=N'IX_dim_customer_business_current')
CREATE INDEX IX_dim_customer_business_current ON dw.dim_customer(customer_number, is_current) INCLUDE (customer_key, effective_start_date, effective_end_date);
GO

IF OBJECT_ID(N'dw.dim_product', N'U') IS NULL
CREATE TABLE dw.dim_product
(
    product_key BIGINT NOT NULL PRIMARY KEY,
    sku VARCHAR(30) NOT NULL,
    product_name NVARCHAR(200) NULL,
    category_name NVARCHAR(100) NULL,
    brand NVARCHAR(100) NULL,
    supplier_code VARCHAR(20) NULL,
    unit_cost DECIMAL(12,2) NULL,
    list_price DECIMAL(12,2) NULL,
    effective_start_date DATE NOT NULL,
    effective_end_date DATE NOT NULL,
    is_current BIT NOT NULL,
    record_hash CHAR(64) NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL
);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID(N'dw.dim_product') AND name=N'IX_dim_product_business_current')
CREATE INDEX IX_dim_product_business_current ON dw.dim_product(sku, is_current) INCLUDE (product_key, effective_start_date, effective_end_date);
GO

IF OBJECT_ID(N'dw.dim_store', N'U') IS NULL
CREATE TABLE dw.dim_store
(
    store_key INT NOT NULL PRIMARY KEY,
    store_code VARCHAR(20) NOT NULL,
    store_name NVARCHAR(150) NULL,
    region VARCHAR(30) NULL,
    state_code VARCHAR(10) NULL,
    city NVARCHAR(100) NULL,
    open_date DATE NULL,
    active_flag BIT NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL
);
GO

IF OBJECT_ID(N'dw.dim_employee', N'U') IS NULL
CREATE TABLE dw.dim_employee
(
    employee_key INT NOT NULL PRIMARY KEY,
    employee_number VARCHAR(20) NOT NULL,
    employee_name NVARCHAR(170) NULL,
    job_title NVARCHAR(100) NULL,
    store_code VARCHAR(20) NULL,
    active_flag BIT NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL
);
GO

IF OBJECT_ID(N'dw.dim_supplier', N'U') IS NULL
CREATE TABLE dw.dim_supplier
(
    supplier_key INT NOT NULL PRIMARY KEY,
    supplier_code VARCHAR(20) NOT NULL,
    supplier_name NVARCHAR(150) NULL,
    country_code VARCHAR(10) NULL,
    lead_time_days INT NULL,
    active_flag BIT NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL
);
GO

IF OBJECT_ID(N'dw.dim_promotion', N'U') IS NULL
CREATE TABLE dw.dim_promotion
(
    promotion_key INT NOT NULL PRIMARY KEY,
    promotion_code VARCHAR(30) NOT NULL,
    promotion_name NVARCHAR(150) NULL,
    discount_type VARCHAR(30) NULL,
    discount_value DECIMAL(12,4) NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    channel_code VARCHAR(20) NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL
);
GO

IF OBJECT_ID(N'dw.dim_channel', N'U') IS NULL
CREATE TABLE dw.dim_channel
(
    channel_key INT NOT NULL PRIMARY KEY,
    channel_code VARCHAR(30) NOT NULL,
    channel_name VARCHAR(80) NOT NULL,
    channel_group VARCHAR(80) NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL
);
GO

IF OBJECT_ID(N'dw.dim_campaign', N'U') IS NULL
CREATE TABLE dw.dim_campaign
(
    campaign_key INT NOT NULL PRIMARY KEY,
    campaign_code VARCHAR(30) NOT NULL,
    campaign_name NVARCHAR(200) NULL,
    channel VARCHAR(40) NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    budget_amount DECIMAL(14,2) NULL,
    currency_code VARCHAR(3) NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL
);
GO

IF OBJECT_ID(N'dw.fact_sales', N'U') IS NULL
CREATE TABLE dw.fact_sales
(
    sales_key BIGINT NOT NULL PRIMARY KEY,
    order_item_id BIGINT NOT NULL UNIQUE,
    order_id BIGINT NOT NULL,
    order_number VARCHAR(30) NOT NULL,
    order_date_key INT NOT NULL,
    customer_key BIGINT NOT NULL,
    product_key BIGINT NOT NULL,
    store_key INT NOT NULL,
    employee_key INT NOT NULL,
    promotion_key INT NOT NULL,
    channel_key INT NOT NULL,
    quantity INT NOT NULL,
    gross_sales_amount DECIMAL(16,2) NOT NULL,
    discount_amount DECIMAL(16,2) NOT NULL,
    net_sales_amount DECIMAL(16,2) NOT NULL,
    tax_amount DECIMAL(16,2) NOT NULL,
    unit_cost_amount DECIMAL(16,2) NOT NULL,
    cost_of_goods_sold DECIMAL(16,2) NOT NULL,
    gross_profit_amount DECIMAL(16,2) NOT NULL,
    currency_code VARCHAR(3) NOT NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL,
    CONSTRAINT FK_fact_sales_date FOREIGN KEY (order_date_key) REFERENCES dw.dim_date(date_key),
    CONSTRAINT FK_fact_sales_customer FOREIGN KEY (customer_key) REFERENCES dw.dim_customer(customer_key),
    CONSTRAINT FK_fact_sales_product FOREIGN KEY (product_key) REFERENCES dw.dim_product(product_key),
    CONSTRAINT FK_fact_sales_store FOREIGN KEY (store_key) REFERENCES dw.dim_store(store_key),
    CONSTRAINT FK_fact_sales_employee FOREIGN KEY (employee_key) REFERENCES dw.dim_employee(employee_key),
    CONSTRAINT FK_fact_sales_promotion FOREIGN KEY (promotion_key) REFERENCES dw.dim_promotion(promotion_key),
    CONSTRAINT FK_fact_sales_channel FOREIGN KEY (channel_key) REFERENCES dw.dim_channel(channel_key)
);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID(N'dw.fact_sales') AND name=N'IX_fact_sales_date_product')
CREATE INDEX IX_fact_sales_date_product ON dw.fact_sales(order_date_key, product_key) INCLUDE (net_sales_amount, gross_profit_amount, quantity);
GO

IF OBJECT_ID(N'dw.fact_returns', N'U') IS NULL
CREATE TABLE dw.fact_returns
(
    return_key BIGINT NOT NULL PRIMARY KEY,
    return_id VARCHAR(40) NOT NULL UNIQUE,
    order_item_id BIGINT NULL,
    return_date_key INT NOT NULL,
    customer_key BIGINT NOT NULL,
    product_key BIGINT NOT NULL,
    store_key INT NOT NULL,
    return_quantity INT NOT NULL,
    refund_amount DECIMAL(16,2) NOT NULL,
    return_reason NVARCHAR(100) NULL,
    currency_code VARCHAR(3) NOT NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL
);
GO

IF OBJECT_ID(N'dw.fact_inventory_snapshot', N'U') IS NULL
CREATE TABLE dw.fact_inventory_snapshot
(
    inventory_snapshot_key BIGINT NOT NULL PRIMARY KEY,
    snapshot_date_key INT NOT NULL,
    store_key INT NOT NULL,
    product_key BIGINT NOT NULL,
    quantity_on_hand INT NOT NULL,
    quantity_reserved INT NOT NULL,
    quantity_available AS (quantity_on_hand - quantity_reserved) PERSISTED,
    reorder_point INT NOT NULL,
    stockout_risk_flag BIT NOT NULL,
    inventory_value_amount DECIMAL(18,2) NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL,
    CONSTRAINT UQ_fact_inventory_grain UNIQUE (snapshot_date_key, store_key, product_key)
);
GO

IF OBJECT_ID(N'dw.fact_shipments', N'U') IS NULL
CREATE TABLE dw.fact_shipments
(
    shipment_key BIGINT NOT NULL PRIMARY KEY,
    shipment_id BIGINT NOT NULL UNIQUE,
    order_id BIGINT NOT NULL,
    ship_date_key INT NOT NULL,
    promised_date_key INT NOT NULL,
    delivery_date_key INT NOT NULL,
    customer_key BIGINT NOT NULL,
    store_key INT NOT NULL,
    carrier NVARCHAR(100) NULL,
    delivery_days INT NULL,
    on_time_flag BIT NOT NULL,
    shipping_cost DECIMAL(16,2) NOT NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL
);
GO

IF OBJECT_ID(N'dw.fact_web_sessions', N'U') IS NULL
CREATE TABLE dw.fact_web_sessions
(
    web_session_key BIGINT NOT NULL PRIMARY KEY,
    session_id BIGINT NOT NULL UNIQUE,
    session_date_key INT NOT NULL,
    customer_key BIGINT NOT NULL,
    campaign_key INT NOT NULL,
    channel_key INT NOT NULL,
    session_count INT NOT NULL,
    duration_seconds INT NULL,
    page_view_count INT NULL,
    add_to_cart_count INT NULL,
    converted_flag BIT NOT NULL,
    converted_order_id BIGINT NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL
);
GO

IF OBJECT_ID(N'dw.fact_marketing_spend', N'U') IS NULL
CREATE TABLE dw.fact_marketing_spend
(
    marketing_spend_key BIGINT NOT NULL PRIMARY KEY,
    spend_date_key INT NOT NULL,
    campaign_key INT NOT NULL,
    channel_key INT NOT NULL,
    spend_amount DECIMAL(16,2) NOT NULL,
    impressions BIGINT NOT NULL,
    clicks BIGINT NOT NULL,
    currency_code VARCHAR(3) NOT NULL,
    load_timestamp_utc DATETIME2(3) NOT NULL,
    batch_id VARCHAR(80) NOT NULL,
    source_system VARCHAR(30) NOT NULL,
    CONSTRAINT UQ_fact_marketing_grain UNIQUE (spend_date_key, campaign_key, channel_key)
);
GO

-- Unknown members. Key 0 means the source value is missing, invalid, or late arriving.
IF NOT EXISTS (SELECT 1 FROM dw.dim_customer WHERE customer_key = 0)
INSERT dw.dim_customer(customer_key, customer_number, first_name, last_name, email, state_code, loyalty_tier, signup_date, effective_start_date, effective_end_date, is_current, record_hash, load_timestamp_utc, batch_id, source_system)
VALUES (0, 'UNKNOWN', 'Unknown', 'Unknown', NULL, NULL, 'Unknown', NULL, '19000101', '99991231', 1, NULL, SYSUTCDATETIME(), 'SYSTEM', 'SYSTEM');
IF NOT EXISTS (SELECT 1 FROM dw.dim_product WHERE product_key = 0)
INSERT dw.dim_product(product_key, sku, product_name, category_name, brand, supplier_code, unit_cost, list_price, effective_start_date, effective_end_date, is_current, record_hash, load_timestamp_utc, batch_id, source_system)
VALUES (0, 'UNKNOWN', 'Unknown Product', 'Unknown', 'Unknown', 'UNKNOWN', NULL, NULL, '19000101', '99991231', 1, NULL, SYSUTCDATETIME(), 'SYSTEM', 'SYSTEM');
IF NOT EXISTS (SELECT 1 FROM dw.dim_store WHERE store_key = 0)
INSERT dw.dim_store VALUES (0, 'UNKNOWN', 'Unknown Store', 'Unknown', NULL, NULL, NULL, 0, SYSUTCDATETIME(), 'SYSTEM', 'SYSTEM');
IF NOT EXISTS (SELECT 1 FROM dw.dim_employee WHERE employee_key = 0)
INSERT dw.dim_employee VALUES (0, 'UNKNOWN', 'Unknown Employee', NULL, NULL, 0, SYSUTCDATETIME(), 'SYSTEM', 'SYSTEM');
IF NOT EXISTS (SELECT 1 FROM dw.dim_supplier WHERE supplier_key = 0)
INSERT dw.dim_supplier VALUES (0, 'UNKNOWN', 'Unknown Supplier', NULL, NULL, 0, SYSUTCDATETIME(), 'SYSTEM', 'SYSTEM');
IF NOT EXISTS (SELECT 1 FROM dw.dim_promotion WHERE promotion_key = 0)
INSERT dw.dim_promotion VALUES (0, 'NONE', 'No Promotion', NULL, NULL, NULL, NULL, NULL, SYSUTCDATETIME(), 'SYSTEM', 'SYSTEM');
IF NOT EXISTS (SELECT 1 FROM dw.dim_channel WHERE channel_key = 0)
INSERT dw.dim_channel VALUES (0, 'UNKNOWN', 'Unknown Channel', 'Unknown', SYSUTCDATETIME(), 'SYSTEM', 'SYSTEM');
IF NOT EXISTS (SELECT 1 FROM dw.dim_campaign WHERE campaign_key = 0)
INSERT dw.dim_campaign VALUES (0, 'NONE', 'No Campaign', NULL, NULL, NULL, NULL, NULL, SYSUTCDATETIME(), 'SYSTEM', 'SYSTEM');
GO

SELECT s.name AS schema_name, t.name AS table_name
FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id
WHERE s.name IN ('dw','audit','stg')
ORDER BY s.name,t.name;

-- Complete conformance constraints and the key-0 date member used by late/not-yet-delivered facts.
IF NOT EXISTS (SELECT 1 FROM dw.dim_date WHERE date_key = 0)
INSERT dw.dim_date(date_key, full_date, day_number, day_name, week_number, month_number, month_name, quarter_number, calendar_year, is_weekend, load_timestamp_utc, batch_id, source_system)
VALUES (0, '19000101', 1, 'Unknown', 1, 1, 'Unknown', 1, 1900, 0, SYSUTCDATETIME(), 'SYSTEM', 'SYSTEM');
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dw.dim_store') AND name = N'UX_dim_store_code')
CREATE UNIQUE INDEX UX_dim_store_code ON dw.dim_store(store_code);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dw.dim_employee') AND name = N'UX_dim_employee_number')
CREATE UNIQUE INDEX UX_dim_employee_number ON dw.dim_employee(employee_number);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dw.dim_supplier') AND name = N'UX_dim_supplier_code')
CREATE UNIQUE INDEX UX_dim_supplier_code ON dw.dim_supplier(supplier_code);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dw.dim_promotion') AND name = N'UX_dim_promotion_code')
CREATE UNIQUE INDEX UX_dim_promotion_code ON dw.dim_promotion(promotion_code);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dw.dim_channel') AND name = N'UX_dim_channel_code')
CREATE UNIQUE INDEX UX_dim_channel_code ON dw.dim_channel(channel_code);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dw.dim_campaign') AND name = N'UX_dim_campaign_code')
CREATE UNIQUE INDEX UX_dim_campaign_code ON dw.dim_campaign(campaign_code);
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_returns_date')
ALTER TABLE dw.fact_returns ADD CONSTRAINT FK_fact_returns_date FOREIGN KEY (return_date_key) REFERENCES dw.dim_date(date_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_returns_customer')
ALTER TABLE dw.fact_returns ADD CONSTRAINT FK_fact_returns_customer FOREIGN KEY (customer_key) REFERENCES dw.dim_customer(customer_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_returns_product')
ALTER TABLE dw.fact_returns ADD CONSTRAINT FK_fact_returns_product FOREIGN KEY (product_key) REFERENCES dw.dim_product(product_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_returns_store')
ALTER TABLE dw.fact_returns ADD CONSTRAINT FK_fact_returns_store FOREIGN KEY (store_key) REFERENCES dw.dim_store(store_key);

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_inventory_date')
ALTER TABLE dw.fact_inventory_snapshot ADD CONSTRAINT FK_fact_inventory_date FOREIGN KEY (snapshot_date_key) REFERENCES dw.dim_date(date_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_inventory_store')
ALTER TABLE dw.fact_inventory_snapshot ADD CONSTRAINT FK_fact_inventory_store FOREIGN KEY (store_key) REFERENCES dw.dim_store(store_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_inventory_product')
ALTER TABLE dw.fact_inventory_snapshot ADD CONSTRAINT FK_fact_inventory_product FOREIGN KEY (product_key) REFERENCES dw.dim_product(product_key);

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_shipments_ship_date')
ALTER TABLE dw.fact_shipments ADD CONSTRAINT FK_fact_shipments_ship_date FOREIGN KEY (ship_date_key) REFERENCES dw.dim_date(date_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_shipments_promised_date')
ALTER TABLE dw.fact_shipments ADD CONSTRAINT FK_fact_shipments_promised_date FOREIGN KEY (promised_date_key) REFERENCES dw.dim_date(date_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_shipments_delivery_date')
ALTER TABLE dw.fact_shipments ADD CONSTRAINT FK_fact_shipments_delivery_date FOREIGN KEY (delivery_date_key) REFERENCES dw.dim_date(date_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_shipments_customer')
ALTER TABLE dw.fact_shipments ADD CONSTRAINT FK_fact_shipments_customer FOREIGN KEY (customer_key) REFERENCES dw.dim_customer(customer_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_shipments_store')
ALTER TABLE dw.fact_shipments ADD CONSTRAINT FK_fact_shipments_store FOREIGN KEY (store_key) REFERENCES dw.dim_store(store_key);

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_web_sessions_date')
ALTER TABLE dw.fact_web_sessions ADD CONSTRAINT FK_fact_web_sessions_date FOREIGN KEY (session_date_key) REFERENCES dw.dim_date(date_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_web_sessions_customer')
ALTER TABLE dw.fact_web_sessions ADD CONSTRAINT FK_fact_web_sessions_customer FOREIGN KEY (customer_key) REFERENCES dw.dim_customer(customer_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_web_sessions_campaign')
ALTER TABLE dw.fact_web_sessions ADD CONSTRAINT FK_fact_web_sessions_campaign FOREIGN KEY (campaign_key) REFERENCES dw.dim_campaign(campaign_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_web_sessions_channel')
ALTER TABLE dw.fact_web_sessions ADD CONSTRAINT FK_fact_web_sessions_channel FOREIGN KEY (channel_key) REFERENCES dw.dim_channel(channel_key);

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_marketing_spend_date')
ALTER TABLE dw.fact_marketing_spend ADD CONSTRAINT FK_fact_marketing_spend_date FOREIGN KEY (spend_date_key) REFERENCES dw.dim_date(date_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_marketing_spend_campaign')
ALTER TABLE dw.fact_marketing_spend ADD CONSTRAINT FK_fact_marketing_spend_campaign FOREIGN KEY (campaign_key) REFERENCES dw.dim_campaign(campaign_key);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_fact_marketing_spend_channel')
ALTER TABLE dw.fact_marketing_spend ADD CONSTRAINT FK_fact_marketing_spend_channel FOREIGN KEY (channel_key) REFERENCES dw.dim_channel(channel_key);
GO
