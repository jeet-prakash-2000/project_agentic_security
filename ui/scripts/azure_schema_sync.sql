-- ============================================================
-- Azure PostgreSQL schema synchronization for LTM Security Platform
-- Target: ltm-security-postgres.postgres.database.azure.com / ltm_security
--
-- Idempotent: safe to run multiple times. Adds missing tables, columns, and
-- indexes. Never drops data.
--
-- Run (in psql / Azure Cloud Shell / pgAdmin):
--   psql "postgresql://Jeet:<password>@ltm-security-postgres.postgres.database.azure.com:5432/ltm_security?sslmode=require" -f azure_schema_sync.sql
-- ============================================================

-- ------------------------------------------------------------
-- Tables (created only if they do not exist)
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id            VARCHAR(64) PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(512) NOT NULL,
    role          VARCHAR(64),
    created       FLOAT
);

CREATE TABLE IF NOT EXISTS agents (
    id             VARCHAR(64) PRIMARY KEY,
    name           VARCHAR(255) NOT NULL,
    type           VARCHAR(64),
    model          VARCHAR(64),
    agent_endpoint VARCHAR(512),
    api_key        VARCHAR(512),
    connected      BOOLEAN,
    created_at     VARCHAR(64),
    agent_id       VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS conversations (
    id      VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64),
    title   VARCHAR(255),
    created FLOAT,
    updated FLOAT
);

CREATE TABLE IF NOT EXISTS messages (
    id              SERIAL PRIMARY KEY,
    conversation_id VARCHAR(64) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(16) NOT NULL,
    content         TEXT,
    tool            VARCHAR(64),
    ts              FLOAT,
    meta            JSON
);

CREATE TABLE IF NOT EXISTS insights (
    id         VARCHAR(64) PRIMARY KEY,
    user_id    VARCHAR(64),
    agent_id   VARCHAR(64),
    agent_name VARCHAR(255),
    agent_type VARCHAR(64),
    model      VARCHAR(64),
    data       JSON
);

CREATE TABLE IF NOT EXISTS reports_history (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(255),
    type         VARCHAR(64),
    generated_by VARCHAR(255),
    ts           FLOAT,
    status       VARCHAR(32),
    size         VARCHAR(32),
    download_url VARCHAR(512)
);

CREATE TABLE IF NOT EXISTS assessment_history (
    id               SERIAL PRIMARY KEY,
    assessment_id    VARCHAR(64),
    executed_at      FLOAT,
    compliance_score FLOAT,
    security_score   FLOAT,
    critical_findings INTEGER,
    high_findings    INTEGER,
    medium_findings  INTEGER,
    low_findings     INTEGER,
    total_findings   INTEGER
);

CREATE TABLE IF NOT EXISTS assessment_stats (
    id                INTEGER PRIMARY KEY,
    assessments_run   INTEGER,
    last_assessment_ts FLOAT
);

CREATE TABLE IF NOT EXISTS telemetry_metrics (
    agent_id VARCHAR(64) PRIMARY KEY,
    requests INTEGER,
    errors   INTEGER,
    first_ts FLOAT,
    last_ts  FLOAT
);

CREATE TABLE IF NOT EXISTS telemetry_history (
    id         SERIAL PRIMARY KEY,
    agent_id   VARCHAR(64),
    agent_name VARCHAR(255),
    label      VARCHAR(255),
    ts         FLOAT,
    nodes      JSON
);

CREATE TABLE IF NOT EXISTS findings (
    id           SERIAL PRIMARY KEY,
    assessment_id VARCHAR(64),
    control      VARCHAR(255),
    status       VARCHAR(32),
    risk         VARCHAR(32),
    metric       VARCHAR(255),
    observed     TEXT,
    expected     TEXT,
    finding      TEXT,
    remediation  TEXT,
    risk_score   FLOAT
);

-- ------------------------------------------------------------
-- Missing columns (idempotent; the primary drift fix, e.g.
-- agents.agent_endpoint which previously did not exist)
-- ------------------------------------------------------------

ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(512) NOT NULL DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(64);
ALTER TABLE users ADD COLUMN IF NOT EXISTS created FLOAT;

ALTER TABLE agents ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS type VARCHAR(64);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS model VARCHAR(64);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_endpoint VARCHAR(512);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS api_key VARCHAR(512);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS connected BOOLEAN;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS created_at VARCHAR(64);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_id VARCHAR(255);

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS user_id VARCHAR(64);
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS created FLOAT;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS updated FLOAT;

ALTER TABLE messages ADD COLUMN IF NOT EXISTS conversation_id VARCHAR(64);
ALTER TABLE messages ADD COLUMN IF NOT EXISTS role VARCHAR(16);
ALTER TABLE messages ADD COLUMN IF NOT EXISTS content TEXT;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS tool VARCHAR(64);
ALTER TABLE messages ADD COLUMN IF NOT EXISTS ts FLOAT;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS meta JSON;

ALTER TABLE insights ADD COLUMN IF NOT EXISTS user_id VARCHAR(64);
ALTER TABLE insights ADD COLUMN IF NOT EXISTS agent_id VARCHAR(64);
ALTER TABLE insights ADD COLUMN IF NOT EXISTS agent_name VARCHAR(255);
ALTER TABLE insights ADD COLUMN IF NOT EXISTS agent_type VARCHAR(64);
ALTER TABLE insights ADD COLUMN IF NOT EXISTS model VARCHAR(64);
ALTER TABLE insights ADD COLUMN IF NOT EXISTS data JSON;

ALTER TABLE reports_history ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE reports_history ADD COLUMN IF NOT EXISTS type VARCHAR(64);
ALTER TABLE reports_history ADD COLUMN IF NOT EXISTS generated_by VARCHAR(255);
ALTER TABLE reports_history ADD COLUMN IF NOT EXISTS ts FLOAT;
ALTER TABLE reports_history ADD COLUMN IF NOT EXISTS status VARCHAR(32);
ALTER TABLE reports_history ADD COLUMN IF NOT EXISTS size VARCHAR(32);
ALTER TABLE reports_history ADD COLUMN IF NOT EXISTS download_url VARCHAR(512);

ALTER TABLE assessment_history ADD COLUMN IF NOT EXISTS assessment_id VARCHAR(64);
ALTER TABLE assessment_history ADD COLUMN IF NOT EXISTS executed_at FLOAT;
ALTER TABLE assessment_history ADD COLUMN IF NOT EXISTS compliance_score FLOAT;
ALTER TABLE assessment_history ADD COLUMN IF NOT EXISTS security_score FLOAT;
ALTER TABLE assessment_history ADD COLUMN IF NOT EXISTS critical_findings INTEGER;
ALTER TABLE assessment_history ADD COLUMN IF NOT EXISTS high_findings INTEGER;
ALTER TABLE assessment_history ADD COLUMN IF NOT EXISTS medium_findings INTEGER;
ALTER TABLE assessment_history ADD COLUMN IF NOT EXISTS low_findings INTEGER;
ALTER TABLE assessment_history ADD COLUMN IF NOT EXISTS total_findings INTEGER;

ALTER TABLE assessment_stats ADD COLUMN IF NOT EXISTS assessments_run INTEGER;
ALTER TABLE assessment_stats ADD COLUMN IF NOT EXISTS last_assessment_ts FLOAT;

ALTER TABLE telemetry_metrics ADD COLUMN IF NOT EXISTS requests INTEGER;
ALTER TABLE telemetry_metrics ADD COLUMN IF NOT EXISTS errors INTEGER;
ALTER TABLE telemetry_metrics ADD COLUMN IF NOT EXISTS first_ts FLOAT;
ALTER TABLE telemetry_metrics ADD COLUMN IF NOT EXISTS last_ts FLOAT;

ALTER TABLE telemetry_history ADD COLUMN IF NOT EXISTS agent_id VARCHAR(64);
ALTER TABLE telemetry_history ADD COLUMN IF NOT EXISTS agent_name VARCHAR(255);
ALTER TABLE telemetry_history ADD COLUMN IF NOT EXISTS label VARCHAR(255);
ALTER TABLE telemetry_history ADD COLUMN IF NOT EXISTS ts FLOAT;
ALTER TABLE telemetry_history ADD COLUMN IF NOT EXISTS nodes JSON;

ALTER TABLE findings ADD COLUMN IF NOT EXISTS assessment_id VARCHAR(64);
ALTER TABLE findings ADD COLUMN IF NOT EXISTS control VARCHAR(255);
ALTER TABLE findings ADD COLUMN IF NOT EXISTS status VARCHAR(32);
ALTER TABLE findings ADD COLUMN IF NOT EXISTS risk VARCHAR(32);
ALTER TABLE findings ADD COLUMN IF NOT EXISTS metric VARCHAR(255);
ALTER TABLE findings ADD COLUMN IF NOT EXISTS observed TEXT;
ALTER TABLE findings ADD COLUMN IF NOT EXISTS expected TEXT;
ALTER TABLE findings ADD COLUMN IF NOT EXISTS finding TEXT;
ALTER TABLE findings ADD COLUMN IF NOT EXISTS remediation TEXT;
ALTER TABLE findings ADD COLUMN IF NOT EXISTS risk_score FLOAT;

-- ------------------------------------------------------------
-- Missing indexes
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages (conversation_id);
CREATE INDEX IF NOT EXISTS ix_assessment_history_assessment_id ON assessment_history (assessment_id);
CREATE INDEX IF NOT EXISTS ix_assessment_history_executed_at ON assessment_history (executed_at);
CREATE INDEX IF NOT EXISTS ix_findings_assessment_id ON findings (assessment_id);
CREATE INDEX IF NOT EXISTS ix_findings_control ON findings (control);
