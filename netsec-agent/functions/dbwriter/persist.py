"""Optional PostgreSQL persistence for the network-security function app.

The Firewall UI is the composition root that records assessment history,
stats and findings into PostgreSQL (through its repository layer). This
module lets the function app additionally:

* write an **audit row** to ``agent_activity_logs`` for every invocation
* optionally persist full assessment runs + findings to ``assessment_history``
  / ``findings`` when ``DB_PERSIST_ASSESSMENTS`` is enabled (default off so the
  UI-driven path does not double-record each run)

Every call is guarded: when ``DATABASE_URL`` is not configured or the write
fails, the function result is unaffected (failures are logged).
"""

import logging
import os
import time

log = logging.getLogger("netsec-dbwriter")


def _database_url():
    return (os.environ.get("DATABASE_URL") or "").strip()


def _connect():
    import psycopg2

    return psycopg2.connect(_database_url(), sslmode="require", connect_timeout=10)


def _ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
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
        )
        if os.environ.get("DB_PERSIST_ASSESSMENTS", "").lower() in ("1", "true"):
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS assessment_history (
                    id BIGSERIAL PRIMARY KEY,
                    firewall_name VARCHAR(64) DEFAULT 'vmpafw01',
                    assessment_id VARCHAR(64),
                    executed_at DOUBLE PRECISION,
                    compliance_score DOUBLE PRECISION,
                    security_score DOUBLE PRECISION,
                    control_count INTEGER DEFAULT 0,
                    status VARCHAR(32) DEFAULT 'Completed',
                    critical_findings INTEGER DEFAULT 0,
                    high_findings INTEGER DEFAULT 0,
                    medium_findings INTEGER DEFAULT 0,
                    low_findings INTEGER DEFAULT 0,
                    total_findings INTEGER DEFAULT 0,
                    payload JSONB
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS findings (
                    id BIGSERIAL PRIMARY KEY,
                    assessment_id VARCHAR(64),
                    firewall_name VARCHAR(64) DEFAULT 'vmpafw01',
                    control VARCHAR(255),
                    status VARCHAR(32),
                    risk VARCHAR(32),
                    metric VARCHAR(255),
                    observed TEXT,
                    expected TEXT,
                    finding TEXT,
                    remediation TEXT,
                    risk_score DOUBLE PRECISION
                )
                """
            )
    conn.commit()


def _severity_counts(findings):
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for finding in findings or []:
        risk = (finding.get("risk") or "").lower()
        if risk in counts:
            counts[risk] += 1
    return counts


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
    """Insert one ``agent_activity_logs`` row."""

    def _run(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_activity_logs
                    (agent_id, run_id, activity, function_name, status, message, ts)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    agent_id,
                    run_id,
                    activity,
                    function_name,
                    status,
                    str(message)[:2000] if message is not None else None,
                    time.time(),
                ),
            )

    return _with_connection(_run)


def persist_assessment(firewall_name, data, function_name="run_full_assessment"):
    """Optionally persist one full assessment run (findings + history row).

    Disabled by default to avoid double-recording runs that the Firewall UI
    already persists. Enable with ``DB_PERSIST_ASSESSMENTS=true``.
    """
    if os.environ.get("DB_PERSIST_ASSESSMENTS", "").lower() not in ("1", "true"):
        return None

    summary = data.get("summary") or {}
    findings = data.get("findings") or []
    severity = _severity_counts(findings)
    run_id = "ns-{0}-{1:.0f}".format(firewall_name, time.time() * 1000)
    executed_at = time.time()

    def _run(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO findings
                    (assessment_id, firewall_name, control, status, risk, metric,
                     observed, expected, finding, remediation, risk_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        run_id,
                        firewall_name,
                        f.get("control"),
                        f.get("status"),
                        f.get("risk"),
                        f.get("metric"),
                        f.get("observed"),
                        f.get("expected"),
                        f.get("finding"),
                        f.get("remediation"),
                        f.get("risk_score"),
                    )
                    for f in findings
                ],
            )
            cur.execute(
                """
                INSERT INTO assessment_history
                    (firewall_name, assessment_id, executed_at, compliance_score,
                     security_score, status, critical_findings, high_findings,
                     medium_findings, low_findings, total_findings)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    firewall_name,
                    run_id,
                    executed_at,
                    summary.get("compliance_pct"),
                    data.get("security_score"),
                    "Completed",
                    severity["critical"],
                    severity["high"],
                    severity["medium"],
                    severity["low"],
                    len(findings),
                ),
            )

    return _with_connection(_run)
