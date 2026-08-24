"""Validate the JSON -> PostgreSQL migration.

Reads every JSON document under ``config/`` and compares its record count
against the corresponding PostgreSQL table count.

Usage::

    export DATABASE_URL="postgresql://Jeet:<password>@ltm-security-postgres.postgres.database.azure.com:5432/ltm_security?sslmode=require"
    python scripts/validate_migration.py

Exit code 0 = all counts match, 2 = validation failures, 1 = connection/config error.
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CONFIG_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "config")
)


def load_json(name):
    path = os.path.join(CONFIG_DIR, name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _count(session, model):
    return session.query(model).count()


def _validators():
    from database import models

    return [
        ("users.json", "users", lambda s: _count(s, models.User), lambda d: len((d or {}).get("users", []))),
        ("agents.json", "agents", lambda s: _count(s, models.Agent), lambda d: len((d or {}).get("agents", []))),
        ("sessions.json", "conversations", lambda s: _count(s, models.Conversation), lambda d: len((d or {}).get("conversations", []))),
        ("sessions.json", "messages", lambda s: _count(s, models.Message), lambda d: sum(len(c.get("messages", [])) for c in (d or {}).get("conversations", []))),
        ("insights.json", "insights", lambda s: _count(s, models.Insight), lambda d: len((d or {}).get("conversations", []))),
        ("reports_history.json", "reports_history", lambda s: _count(s, models.ReportHistory), lambda d: len((d or {}).get("reports", []))),
        ("assessment_history.json", "assessment_history", lambda s: _count(s, models.AssessmentHistory), lambda d: len((d or {}).get("snapshots", []))),
        ("assessment_stats.json", "assessment_stats", lambda s: _count(s, models.AssessmentStats), lambda d: 1 if d else 0),
        ("telemetry_metrics.json", "telemetry_metrics", lambda s: _count(s, models.TelemetryMetric), lambda d: len(((d or {}).get("agents") or {}))),
        ("telemetry_history.json", "telemetry_history", lambda s: _count(s, models.TelemetryHistory), lambda d: len((d or {}).get("snapshots", []))),
        ("findings.json", "findings", lambda s: _count(s, models.Finding), lambda d: len((d or {}).get("findings", []))),
    ]


def main():
    from database.db import check_connection, create_all, get_session

    ok, message = check_connection()
    if not ok:
        print("DATABASE UNAVAILABLE:", message)
        return 1

    try:
        create_all()
        session = get_session()
    except Exception as exc:
        print("Failed to prepare database:", exc)
        return 1

    failures = 0
    for file, table, db_count_fn, json_count_fn in _validators():
        data = load_json(file)
        json_count = json_count_fn(data)
        db_count = db_count_fn(session)
        match = json_count == db_count
        status = "OK " if match else "FAIL"
        print("[{}] {} -> {} : json={} db={}".format(status, file, table, json_count, db_count))
        if not match:
            failures += 1

    print("")
    if failures:
        print("VALIDATION FAILURES:", failures)
        return 2
    print("Validation passed: all JSON records are present in PostgreSQL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
