"""Optional PostgreSQL persistence for the cloudsec function app.

Records every incident-response action and full run into PostgreSQL when
``DATABASE_URL`` is configured for the Function App. Writes are guarded: any
database failure is logged and never affects the HTTP result.

Tables:
* ``agent_activity_logs`` - one row per containment/recovery/eradication action
* ``incident_runs``       - one row per ``RunFullIncidentResponse`` run
"""

import logging
import os
import time

log = logging.getLogger("cloudsec-dbwriter")

INCIDENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS incident_runs (
    id BIGSERIAL PRIMARY KEY,
    incident_id VARCHAR(255),
    vm_name VARCHAR(255),
    risk_score DOUBLE PRECISION,
    risk_level VARCHAR(64),
    recommended_action VARCHAR(512),
    status VARCHAR(64),
    stages JSONB,
    action_log JSONB,
    errors JSONB,
    completed_at DOUBLE PRECISION,
    created_at DOUBLE PRECISION
)
"""

ACTIVITY_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_activity_logs (
    id BIGSERIAL PRIMARY KEY,
    agent_id VARCHAR(64),
    run_id VARCHAR(64),
    activity VARCHAR(128),
    function_name VARCHAR(255),
    status VARCHAR(32) DEFAULT 'Completed',
    message TEXT,
    ts DOUBLE PRECISION,
    meta JSONB
)
"""


def _database_url():
    return (os.environ.get("DATABASE_URL") or "").strip()


def _connect():
    import psycopg2

    return psycopg2.connect(_database_url(), sslmode="require", connect_timeout=10)


def _ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute(ACTIVITY_SCHEMA)
        cur.execute(INCIDENT_SCHEMA)
    conn.commit()


def _with_connection(fn):
    url = _database_url()
    if not url:
        log.info("DATABASE_URL not configured - skipping PostgreSQL write.")
        return None
    try:
        conn = _connect()
        try:
            _ensure_schema(conn)
            result = fn(conn)
            conn.commit()
            return result
        finally:
            conn.close()
    except Exception as exc:  # never break the function result
        log.warning("PostgreSQL write failed (ignored): %s", exc)
        return None


def log_activity(agent_id, run_id, activity, function_name, status="Completed", message=None):
    """Insert one ``agent_activity_logs`` row for a cloudsec action."""

    def _run(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_activity_logs
                    (agent_id, run_id, activity, function_name, status, message, ts)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    agent_id or "cloudsec-agent",
                    run_id,
                    activity,
                    function_name,
                    status,
                    str(message)[:2000] if message is not None else None,
                    time.time(),
                ),
            )

    return _with_connection(_run)


def record_incident_run(incident_id, vm_name, risk_score, risk_level,
                        recommended_action, status, stages, action_log,
                        errors=None, completed_at=None):
    """Insert one ``incident_runs`` row for a full incident response run."""

    def _run(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO incident_runs
                    (incident_id, vm_name, risk_score, risk_level, recommended_action,
                     status, stages, action_log, errors, completed_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    incident_id,
                    vm_name,
                    risk_score,
                    risk_level,
                    recommended_action,
                    status,
                    json_dumps(stages),
                    json_dumps(action_log),
                    json_dumps(errors),
                    completed_at or time.time(),
                    time.time(),
                ),
            )

    return _with_connection(_run)


def json_dumps(value):
    import json

    if value is None:
        return None
    return json.dumps(value, default=str)
