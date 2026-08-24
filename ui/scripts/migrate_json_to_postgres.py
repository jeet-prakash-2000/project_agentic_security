"""Production-grade one-time migration of JSON documents into PostgreSQL.

Usage::

    export DATABASE_URL="postgresql://Jeet:<password>@ltm-security-postgres.postgres.database.azure.com:5432/ltm_security?sslmode=require"
    python scripts/migrate_json_to_postgres.py

Behaviour
---------
* Calls ``database.db.create_all()`` before migrating.
* Reuses the SAVERS from ``database.storage_bridge`` (single source of truth for
  document -> relational conversion).
* Wraps each document in a SQLAlchemy transaction and rolls back on failure.
* Skips documents whose destination tables are already populated (idempotent,
  no duplicate records inserted).
* Validates source JSON row counts against destination database counts.
* Migrates findings when a historical ``findings.json`` exists.
* Writes ``migration_report.json`` with per-document results, timings and errors.

The migration only moves data; application behaviour is unchanged.
"""

import json
import logging
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CONFIG_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "config")
)
REPORT_PATH = os.path.join(os.path.dirname(__file__), "migration_report.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("migration")


def load_json(name):
    path = os.path.join(CONFIG_DIR, name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _count(session, model):
    return session.query(model).count()


def _documents():
    """Document descriptors for the storage_bridge SAVERS.

    Each entry provides the storage document name, JSON file, a db-count
    validator and a json-count reader so the migration can be validated.
    """
    from database import models

    return [
        {
            "name": "users",
            "file": "users.json",
            "db_count": lambda s: _count(s, models.User),
            "json_count": lambda d: len((d or {}).get("users", [])),
        },
        {
            "name": "agents",
            "file": "agents.json",
            "db_count": lambda s: _count(s, models.Agent),
            "json_count": lambda d: len((d or {}).get("agents", [])),
        },
        {
            "name": "sessions",
            "file": "sessions.json",
            "db_count": lambda s: _count(s, models.Conversation),
            "db_count_secondary": lambda s: _count(s, models.Message),
            "json_count": lambda d: len((d or {}).get("conversations", [])),
            "json_count_secondary": lambda d: sum(
                len(c.get("messages", [])) for c in (d or {}).get("conversations", [])
            ),
        },
        {
            "name": "insights",
            "file": "insights.json",
            "db_count": lambda s: _count(s, models.Insight),
            "json_count": lambda d: len((d or {}).get("conversations", [])),
        },
        {
            "name": "reports_history",
            "file": "reports_history.json",
            "db_count": lambda s: _count(s, models.ReportHistory),
            "json_count": lambda d: len((d or {}).get("reports", [])),
        },
        {
            "name": "assessment_history",
            "file": "assessment_history.json",
            "db_count": lambda s: _count(s, models.AssessmentHistory),
            "json_count": lambda d: len((d or {}).get("snapshots", [])),
        },
        {
            "name": "assessment_stats",
            "file": "assessment_stats.json",
            "db_count": lambda s: _count(s, models.AssessmentStats),
            "json_count": lambda d: 1 if d else 0,
        },
        {
            "name": "telemetry_metrics",
            "file": "telemetry_metrics.json",
            "db_count": lambda s: _count(s, models.TelemetryMetric),
            "json_count": lambda d: len(((d or {}).get("agents") or {})),
        },
        {
            "name": "telemetry_history",
            "file": "telemetry_history.json",
            "db_count": lambda s: _count(s, models.TelemetryHistory),
            "json_count": lambda d: len((d or {}).get("snapshots", [])),
        },
    ]


def _migrate_document(session, doc, saver, report):
    name = doc["name"]
    start = time.time()
    data = load_json(doc["file"])

    if data is None:
        log.info("Skip %s: %s not present.", name, doc["file"])
        return {"file": doc["file"], "json_count": 0, "migrated": 0, "skipped": 0, "db_count": 0, "match": True, "note": "no source file"}

    json_count = doc["json_count"](data)
    existing = doc["db_count"](session)

    if existing > 0:
        log.info("Skip %s: destination already populated (%s rows) - no duplicates.", name, existing)
        return {
            "file": doc["file"],
            "json_count": json_count,
            "migrated": 0,
            "skipped": json_count,
            "db_count": existing,
            "match": json_count == existing,
            "note": "already migrated (duplicates skipped)",
        }

    try:
        saver(session, data)  # storage_bridge SAVER commits on success
        session.commit()
    except Exception as exc:
        session.rollback()
        log.error("Rolled back %s: %s", name, exc)
        report["errors"].append("{}: {}".format(name, exc))
        return {
            "file": doc["file"],
            "json_count": json_count,
            "migrated": 0,
            "skipped": 0,
            "db_count": doc["db_count"](session),
            "match": False,
            "note": "failed - rolled back",
        }

    after = doc["db_count"](session)
    secondary = None
    if "db_count_secondary" in doc:
        secondary = {
            "json": doc["json_count_secondary"](data),
            "db": doc["db_count_secondary"](session),
        }
    match = json_count == after and (secondary is None or secondary["json"] == secondary["db"])

    log.info(
        "Migrated %s: json=%s db=%s%s (%.2fs)",
        name, json_count, after,
        " msgs={}/{}".format(secondary["json"], secondary["db"]) if secondary else "",
        time.time() - start,
    )
    return {
        "file": doc["file"],
        "json_count": json_count,
        "migrated": json_count,
        "skipped": 0,
        "db_count": after,
        "secondary": secondary,
        "match": match,
        "note": "ok",
    }


def _migrate_findings(session, report):
    """Migrate historical findings when a findings.json document exists.

    There is normally no separate findings.json (findings are derived from the
    assessment), so this is a no-op unless historical finding data is present.
    """
    from database import models

    data = load_json("findings.json")
    if data is None:
        log.info("Skip findings: findings.json not present (no historical finding data).")
        return {
            "file": "findings.json",
            "json_count": 0,
            "migrated": 0,
            "skipped": 0,
            "db_count": _count(session, models.Finding),
            "match": True,
            "note": "no source file",
        }

    from database.repositories import FindingsRepository

    json_count = len((data or {}).get("findings", []))
    existing = _count(session, models.Finding)
    if existing > 0:
        return {
            "file": "findings.json",
            "json_count": json_count,
            "migrated": 0,
            "skipped": json_count,
            "db_count": existing,
            "match": json_count == existing,
            "note": "already migrated (duplicates skipped)",
        }

    try:
        FindingsRepository(session).replace_for_assessment(
            assessment_id="historical",
            findings=data.get("findings", []),
        )
        session.commit()
    except Exception as exc:
        session.rollback()
        report["errors"].append("findings: {}".format(exc))
        return {
            "file": "findings.json",
            "json_count": json_count,
            "migrated": 0,
            "skipped": 0,
            "db_count": _count(session, models.Finding),
            "match": False,
            "note": "failed - rolled back",
        }

    after = _count(session, models.Finding)
    log.info("Migrated findings: json=%s db=%s", json_count, after)
    return {
        "file": "findings.json",
        "json_count": json_count,
        "migrated": json_count,
        "skipped": 0,
        "db_count": after,
        "match": json_count == after,
        "note": "ok",
    }


def main():
    from database.db import create_all, get_session
    from database import storage_bridge

    report = {
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "documents": [],
        "errors": [],
    }

    try:
        create_all()
        session = get_session()
    except Exception as exc:
        report["errors"].append(str(exc))
        log.error("Migration aborted: %s", exc)
        _write_report(report)
        return 1

    saver_map = storage_bridge.SAVERS

    for doc in _documents():
        saver = saver_map.get(doc["name"])
        if saver is None:
            report["errors"].append("{}: no saver in storage_bridge".format(doc["name"]))
            continue
        result = _migrate_document(session, doc, saver, report)
        report["documents"].append(result)

    report["documents"].append(_migrate_findings(session, report))

    failures = [d for d in report["documents"] if not d["match"]]
    report["finish_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report["validation"] = {
        "passed": not failures,
        "failures": [d["file"] for d in failures],
    }
    report["totals"] = {
        "json_records": sum(d["json_count"] for d in report["documents"]),
        "migrated": sum(d["migrated"] for d in report["documents"]),
        "skipped": sum(d["skipped"] for d in report["documents"]),
    }

    _write_report(report)
    log.info("Migration complete. Report written to %s", REPORT_PATH)
    return 0 if not failures and not report["errors"] else 2


def _write_report(report):
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
