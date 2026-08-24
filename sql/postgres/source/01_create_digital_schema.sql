-- Dialect: PostgreSQL SQL
-- Purpose: create the digital source schema and tables.
-- Run in: pgAdmin Query Tool connected to database northstar_digital.
-- Idempotency: CREATE IF NOT EXISTS avoids replacing existing objects.

CREATE SCHEMA IF NOT EXISTS digital;
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS audit.source_load_batch
(
    batch_id            varchar(80) PRIMARY KEY,
    process_name        varchar(100) NOT NULL,
    started_at_utc      timestamptz NOT NULL DEFAULT now(),
    finished_at_utc     timestamptz NULL,
    status              varchar(20) NOT NULL,
    source_file_count   integer NULL,
    loaded_row_count    bigint NULL,
    error_message       text NULL
);

CREATE TABLE IF NOT EXISTS digital.web_users
(
    web_user_id         bigint PRIMARY KEY,
    customer_id         integer NULL,
    anonymous_cookie_id varchar(64) NOT NULL,
    email_hash          char(64) NULL,
    created_at          timestamptz NOT NULL,
    updated_at          timestamptz NOT NULL,
    CONSTRAINT uq_web_users_cookie UNIQUE (anonymous_cookie_id)
);

CREATE TABLE IF NOT EXISTS digital.campaigns
(
    campaign_id         integer PRIMARY KEY,
    campaign_code       varchar(30) NOT NULL UNIQUE,
    campaign_name       varchar(200) NOT NULL,
    channel             varchar(40) NOT NULL,
    start_date          date NOT NULL,
    end_date            date NOT NULL,
    budget_amount       numeric(14,2) NOT NULL,
    currency_code       varchar(3) NOT NULL,
    created_at          timestamptz NOT NULL,
    updated_at          timestamptz NOT NULL,
    CONSTRAINT ck_campaign_dates CHECK (end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS digital.web_sessions
(
    session_id          bigint PRIMARY KEY,
    web_user_id         bigint NULL REFERENCES digital.web_users(web_user_id),
    session_start_utc   timestamptz NOT NULL,
    session_end_utc     timestamptz NULL,
    source_channel      varchar(40) NOT NULL,
    campaign_id         integer NULL REFERENCES digital.campaigns(campaign_id),
    device_type         varchar(30) NOT NULL,
    country_code        varchar(10) NOT NULL,
    converted_order_id  bigint NULL,
    created_at          timestamptz NOT NULL,
    CONSTRAINT ck_session_end CHECK (session_end_utc IS NULL OR session_end_utc >= session_start_utc)
);

CREATE TABLE IF NOT EXISTS digital.web_events
(
    event_id            bigint PRIMARY KEY,
    session_id          bigint NOT NULL REFERENCES digital.web_sessions(session_id),
    event_timestamp     timestamptz NOT NULL,
    event_type          varchar(50) NOT NULL,
    page_url            text NULL,
    product_id          integer NULL,
    order_id            bigint NULL,
    event_properties    jsonb NULL,
    created_at          timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS digital.campaign_touchpoints
(
    touchpoint_id       bigint PRIMARY KEY,
    web_user_id         bigint NULL REFERENCES digital.web_users(web_user_id),
    session_id          bigint NULL REFERENCES digital.web_sessions(session_id),
    campaign_id         integer NOT NULL REFERENCES digital.campaigns(campaign_id),
    touchpoint_timestamp timestamptz NOT NULL,
    touchpoint_type     varchar(40) NOT NULL,
    attribution_weight  numeric(8,6) NOT NULL,
    created_at          timestamptz NOT NULL,
    CONSTRAINT ck_touchpoint_weight CHECK (attribution_weight >= 0 AND attribution_weight <= 1)
);

CREATE TABLE IF NOT EXISTS digital.marketing_spend
(
    spend_id            bigint PRIMARY KEY,
    spend_date          date NOT NULL,
    campaign_id         integer NOT NULL REFERENCES digital.campaigns(campaign_id),
    channel             varchar(40) NOT NULL,
    spend_amount        numeric(14,2) NOT NULL,
    impressions         bigint NOT NULL,
    clicks              bigint NOT NULL,
    currency_code       varchar(3) NOT NULL,
    created_at          timestamptz NOT NULL,
    CONSTRAINT uq_marketing_spend_grain UNIQUE (spend_date, campaign_id, channel),
    CONSTRAINT ck_spend_nonnegative CHECK (spend_amount >= 0 AND impressions >= 0 AND clicks >= 0)
);

CREATE INDEX IF NOT EXISTS ix_web_sessions_start ON digital.web_sessions(session_start_utc);
CREATE INDEX IF NOT EXISTS ix_web_events_session_time ON digital.web_events(session_id, event_timestamp);
CREATE INDEX IF NOT EXISTS ix_marketing_spend_date ON digital.marketing_spend(spend_date);

SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('digital', 'audit')
ORDER BY table_schema, table_name;
