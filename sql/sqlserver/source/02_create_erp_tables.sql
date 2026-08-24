-- Dialect: SQL Server / T-SQL
-- Purpose: Create the normalized ERP source tables.
-- Run in: SSMS query window connected to NorthstarRetail_ERP.
-- Idempotency: each table and index is created only when missing.

USE NorthstarRetail_ERP;
GO

IF OBJECT_ID(N'erp.product_categories', N'U') IS NULL
BEGIN
    CREATE TABLE erp.product_categories
    (
        category_id         INT NOT NULL CONSTRAINT PK_product_categories PRIMARY KEY,
        category_name       NVARCHAR(100) NOT NULL,
        parent_category_id  INT NULL,
        created_at          DATETIME2(3) NOT NULL,
        updated_at          DATETIME2(3) NOT NULL,
        CONSTRAINT FK_product_categories_parent FOREIGN KEY (parent_category_id)
            REFERENCES erp.product_categories(category_id)
    );
END;
GO

IF OBJECT_ID(N'erp.suppliers', N'U') IS NULL
BEGIN
    CREATE TABLE erp.suppliers
    (
        supplier_id         INT NOT NULL CONSTRAINT PK_suppliers PRIMARY KEY,
        supplier_code       VARCHAR(20) NOT NULL,
        supplier_name       NVARCHAR(150) NOT NULL,
        country_code        CHAR(2) NOT NULL,
        lead_time_days      INT NOT NULL,
        active_flag         BIT NOT NULL,
        created_at          DATETIME2(3) NOT NULL,
        updated_at          DATETIME2(3) NOT NULL,
        CONSTRAINT UQ_suppliers_supplier_code UNIQUE (supplier_code),
        CONSTRAINT CK_suppliers_lead_time CHECK (lead_time_days >= 0)
    );
END;
GO

IF OBJECT_ID(N'erp.products', N'U') IS NULL
BEGIN
    CREATE TABLE erp.products
    (
        product_id          INT NOT NULL CONSTRAINT PK_products PRIMARY KEY,
        sku                 VARCHAR(30) NOT NULL,
        product_name        NVARCHAR(200) NOT NULL,
        category_id         INT NOT NULL,
        supplier_id         INT NOT NULL,
        brand               NVARCHAR(100) NOT NULL,
        unit_cost           DECIMAL(12,2) NOT NULL,
        list_price          DECIMAL(12,2) NOT NULL,
        currency_code       CHAR(3) NOT NULL,
        active_flag         BIT NOT NULL,
        created_at          DATETIME2(3) NOT NULL,
        updated_at          DATETIME2(3) NOT NULL,
        CONSTRAINT UQ_products_sku UNIQUE (sku),
        CONSTRAINT FK_products_category FOREIGN KEY (category_id) REFERENCES erp.product_categories(category_id),
        CONSTRAINT FK_products_supplier FOREIGN KEY (supplier_id) REFERENCES erp.suppliers(supplier_id),
        CONSTRAINT CK_products_amounts CHECK (unit_cost >= 0 AND list_price >= 0)
    );
END;
GO

IF OBJECT_ID(N'erp.stores', N'U') IS NULL
BEGIN
    CREATE TABLE erp.stores
    (
        store_id            INT NOT NULL CONSTRAINT PK_stores PRIMARY KEY,
        store_code          VARCHAR(20) NOT NULL,
        store_name          NVARCHAR(150) NOT NULL,
        region              VARCHAR(30) NOT NULL,
        state_code          CHAR(2) NOT NULL,
        city                NVARCHAR(100) NOT NULL,
        open_date           DATE NOT NULL,
        active_flag         BIT NOT NULL,
        created_at          DATETIME2(3) NOT NULL,
        updated_at          DATETIME2(3) NOT NULL,
        CONSTRAINT UQ_stores_store_code UNIQUE (store_code)
    );
END;
GO

IF OBJECT_ID(N'erp.employees', N'U') IS NULL
BEGIN
    CREATE TABLE erp.employees
    (
        employee_id         INT NOT NULL CONSTRAINT PK_employees PRIMARY KEY,
        employee_number     VARCHAR(20) NOT NULL,
        store_id            INT NULL,
        manager_employee_id INT NULL,
        first_name          NVARCHAR(80) NOT NULL,
        last_name           NVARCHAR(80) NOT NULL,
        job_title           NVARCHAR(100) NOT NULL,
        hire_date           DATE NOT NULL,
        active_flag         BIT NOT NULL,
        created_at          DATETIME2(3) NOT NULL,
        updated_at          DATETIME2(3) NOT NULL,
        CONSTRAINT UQ_employees_number UNIQUE (employee_number),
        CONSTRAINT FK_employees_store FOREIGN KEY (store_id) REFERENCES erp.stores(store_id),
        CONSTRAINT FK_employees_manager FOREIGN KEY (manager_employee_id) REFERENCES erp.employees(employee_id)
    );
END;
GO

IF OBJECT_ID(N'erp.customers', N'U') IS NULL
BEGIN
    CREATE TABLE erp.customers
    (
        customer_id         INT NOT NULL CONSTRAINT PK_customers PRIMARY KEY,
        customer_number     VARCHAR(25) NOT NULL,
        first_name          NVARCHAR(80) NOT NULL,
        last_name           NVARCHAR(80) NOT NULL,
        email               NVARCHAR(255) NULL,
        phone               VARCHAR(40) NULL,
        signup_date         DATE NOT NULL,
        loyalty_tier        VARCHAR(20) NOT NULL,
        marketing_opt_in    BIT NOT NULL,
        created_at          DATETIME2(3) NOT NULL,
        updated_at          DATETIME2(3) NOT NULL
        -- Deliberately no unique constraint on customer_number in the learning source:
        -- controlled duplicate business keys must reach Silver and be handled there.
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'erp.customers') AND name = N'IX_customers_customer_number')
    CREATE INDEX IX_customers_customer_number ON erp.customers(customer_number);
GO

IF OBJECT_ID(N'erp.addresses', N'U') IS NULL
BEGIN
    CREATE TABLE erp.addresses
    (
        address_id          INT NOT NULL CONSTRAINT PK_addresses PRIMARY KEY,
        customer_id         INT NOT NULL,
        address_type        VARCHAR(20) NOT NULL,
        line1               NVARCHAR(200) NOT NULL,
        line2               NVARCHAR(200) NULL,
        city                NVARCHAR(100) NOT NULL,
        state_code          VARCHAR(10) NOT NULL,
        postal_code         VARCHAR(20) NOT NULL,
        country_code        VARCHAR(10) NOT NULL,
        is_default          BIT NOT NULL,
        created_at          DATETIME2(3) NOT NULL,
        updated_at          DATETIME2(3) NOT NULL,
        CONSTRAINT FK_addresses_customer FOREIGN KEY (customer_id) REFERENCES erp.customers(customer_id)
    );
END;
GO

IF OBJECT_ID(N'erp.orders', N'U') IS NULL
BEGIN
    CREATE TABLE erp.orders
    (
        order_id            BIGINT NOT NULL CONSTRAINT PK_orders PRIMARY KEY,
        order_number        VARCHAR(30) NOT NULL,
        customer_id         INT NOT NULL,
        store_id            INT NULL,
        employee_id         INT NULL,
        channel_code        VARCHAR(20) NOT NULL,
        order_timestamp     DATETIME2(3) NOT NULL,
        order_status        VARCHAR(20) NOT NULL,
        promotion_code      VARCHAR(30) NULL,
        currency_code       CHAR(3) NOT NULL,
        created_at          DATETIME2(3) NOT NULL,
        updated_at          DATETIME2(3) NOT NULL,
        CONSTRAINT UQ_orders_order_number UNIQUE (order_number),
        CONSTRAINT FK_orders_customer FOREIGN KEY (customer_id) REFERENCES erp.customers(customer_id),
        CONSTRAINT FK_orders_store FOREIGN KEY (store_id) REFERENCES erp.stores(store_id),
        CONSTRAINT FK_orders_employee FOREIGN KEY (employee_id) REFERENCES erp.employees(employee_id),
        CONSTRAINT CK_orders_channel CHECK (channel_code IN ('STORE', 'ONLINE'))
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'erp.orders') AND name = N'IX_orders_updated_at')
    CREATE INDEX IX_orders_updated_at ON erp.orders(updated_at) INCLUDE (order_id, customer_id, order_timestamp);
GO

IF OBJECT_ID(N'erp.order_items', N'U') IS NULL
BEGIN
    CREATE TABLE erp.order_items
    (
        order_item_id       BIGINT NOT NULL CONSTRAINT PK_order_items PRIMARY KEY,
        order_id            BIGINT NOT NULL,
        line_number         INT NOT NULL,
        product_id          INT NOT NULL,
        quantity            INT NOT NULL,
        unit_price          DECIMAL(12,2) NOT NULL,
        unit_cost           DECIMAL(12,2) NOT NULL,
        discount_amount     DECIMAL(12,2) NOT NULL,
        tax_amount          DECIMAL(12,2) NOT NULL,
        created_at          DATETIME2(3) NOT NULL,
        updated_at          DATETIME2(3) NOT NULL,
        CONSTRAINT UQ_order_items_line UNIQUE (order_id, line_number),
        CONSTRAINT FK_order_items_order FOREIGN KEY (order_id) REFERENCES erp.orders(order_id),
        CONSTRAINT FK_order_items_product FOREIGN KEY (product_id) REFERENCES erp.products(product_id)
        -- No positive-quantity check: controlled impossible quantities are a Silver lesson.
    );
END;
GO

IF OBJECT_ID(N'erp.payments', N'U') IS NULL
BEGIN
    CREATE TABLE erp.payments
    (
        payment_id          BIGINT NOT NULL CONSTRAINT PK_payments PRIMARY KEY,
        order_id            BIGINT NOT NULL,
        payment_timestamp   DATETIME2(3) NOT NULL,
        payment_method      VARCHAR(30) NOT NULL,
        payment_status      VARCHAR(30) NOT NULL,
        amount              DECIMAL(14,2) NOT NULL,
        currency_code       VARCHAR(3) NOT NULL,
        transaction_reference VARCHAR(80) NOT NULL,
        created_at          DATETIME2(3) NOT NULL,
        updated_at          DATETIME2(3) NOT NULL,
        CONSTRAINT UQ_payments_transaction UNIQUE (transaction_reference),
        CONSTRAINT FK_payments_order FOREIGN KEY (order_id) REFERENCES erp.orders(order_id)
    );
END;
GO

IF OBJECT_ID(N'erp.shipments', N'U') IS NULL
BEGIN
    CREATE TABLE erp.shipments
    (
        shipment_id         BIGINT NOT NULL CONSTRAINT PK_shipments PRIMARY KEY,
        order_id            BIGINT NOT NULL,
        carrier             NVARCHAR(100) NOT NULL,
        tracking_number     VARCHAR(100) NOT NULL,
        ship_date           DATE NOT NULL,
        promised_delivery_date DATE NOT NULL,
        actual_delivery_date DATE NULL,
        shipment_status     VARCHAR(30) NOT NULL,
        shipping_cost       DECIMAL(12,2) NOT NULL,
        created_at          DATETIME2(3) NOT NULL,
        updated_at          DATETIME2(3) NOT NULL,
        CONSTRAINT UQ_shipments_tracking UNIQUE (tracking_number),
        CONSTRAINT FK_shipments_order FOREIGN KEY (order_id) REFERENCES erp.orders(order_id)
    );
END;
GO

IF OBJECT_ID(N'erp.inventory_transactions', N'U') IS NULL
BEGIN
    CREATE TABLE erp.inventory_transactions
    (
        inventory_transaction_id BIGINT NOT NULL CONSTRAINT PK_inventory_transactions PRIMARY KEY,
        store_id            INT NOT NULL,
        product_id          INT NOT NULL,
        transaction_timestamp DATETIME2(3) NOT NULL,
        transaction_type    VARCHAR(30) NOT NULL,
        quantity_change     INT NOT NULL,
        reference_type      VARCHAR(30) NULL,
        reference_id        BIGINT NULL,
        created_at          DATETIME2(3) NOT NULL,
        CONSTRAINT FK_inventory_transactions_store FOREIGN KEY (store_id) REFERENCES erp.stores(store_id),
        CONSTRAINT FK_inventory_transactions_product FOREIGN KEY (product_id) REFERENCES erp.products(product_id)
    );
END;
GO

IF OBJECT_ID(N'erp.inventory_snapshots', N'U') IS NULL
BEGIN
    CREATE TABLE erp.inventory_snapshots
    (
        inventory_snapshot_id BIGINT NOT NULL CONSTRAINT PK_inventory_snapshots PRIMARY KEY,
        snapshot_date       DATE NOT NULL,
        store_id            INT NOT NULL,
        product_id          INT NOT NULL,
        quantity_on_hand    INT NOT NULL,
        quantity_reserved   INT NOT NULL,
        reorder_point       INT NOT NULL,
        created_at          DATETIME2(3) NOT NULL,
        CONSTRAINT UQ_inventory_snapshot_grain UNIQUE (snapshot_date, store_id, product_id),
        CONSTRAINT FK_inventory_snapshots_store FOREIGN KEY (store_id) REFERENCES erp.stores(store_id),
        CONSTRAINT FK_inventory_snapshots_product FOREIGN KEY (product_id) REFERENCES erp.products(product_id)
    );
END;
GO

SELECT s.name AS schema_name, t.name AS table_name
FROM sys.tables AS t
JOIN sys.schemas AS s ON s.schema_id = t.schema_id
WHERE s.name IN ('erp', 'audit')
ORDER BY s.name, t.name;
GO
