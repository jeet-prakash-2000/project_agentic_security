"""Production-grade migration of JSON documents into PostgreSQL.

The application is now PostgreSQL-only: these JSON documents under
``ui/config/`` were the pre-migration storage layer and this script moves them
into their relational tables via the repository layer.

Usage::

    export DATABASE_URL="postgresql://Jeet:<password>@ltm-security-postgres.postgres.database.azure.com:5432/ltm_security?sslmode=require"
    python scripts/migrate_json_to_postgres.py

Behaviour
---------
* Calls ``database.db.create_all()`` before migrating.
* Migrates each document through the corresponding repository (no JSON bridge).
* Idempotent: skips documents whose destination tables already hold rows.
* Validates source JSON row counts against destination database counts.
* Writes ``migration_report.json`` with per-document results, timings, errors.
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


def _count(model):
    from database.db import get_session

    return get_session().query(model).count()


# ------------------------------------------------------------
# Repository-backed savers (each is idempotent by design)
# ------------------------------------------------------------

def _save_users(session, data):
    from database.models import User
    from database.repositories import UsersRepository

    repo = UsersRepository(session)
    for item in data.get("users", []):
        repo.create(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "email": item.get("email"),
                "password_hash": item.get("password_hash"),
                "role": item.get("role") or "Security Analyst",
                "created": item.get("created"),
            }
        )


def _save_agents(session, data):
    from database.repositories import AgentsRepository

    repo = AgentsRepository(session)
    for item in data.get("agents", []):
        repo.create(item)


def _save_sessions(session, data):
    from database.repositories import ConversationsRepository

    repo = ConversationsRepository(session)
    for conv in data.get("conversations", []):
        conv_id = conv.get("id")
        existing = repo.get(conv_id)
        if existing is None:
            repo.create_conversation(
                conv_id,
                user_id=conv.get("user_id") or "anonymous",
                created=conv.get("created") or conv.get("updated"),
            )
            if conv.get("title"):
                repo.touch(conv_id, title=conv.get("title"))
        for msg in conv.get("messages", []):
            if not isinstance(msg, dict):
                continue
            repo.add_message(
                conv_id,
                {
                    "role": msg.get("role") or "user",
                    "content": msg.get("content") or "",
                    "ts": msg.get("ts") or conv.get("updated"),
                    "tool": msg.get("tool"),
                    **{
                        k: v
                        for k, v in msg.items()
                        if k not in ("role", "content", "ts", "tool")
                    },
                },
            )


def _save_insights(session, data):
    from database.models import Insight
    from database.repositories import InsightsRepository

    repo = InsightsRepository(session)
    for conv in data.get("conversations", []):
        payload = {
            "created": conv.get("created"),
            "updated": conv.get("updated"),
            "turns": conv.get("turns") or [],
        }
        row = Insight(
            id=conv.get("id"),
            user_id=conv.get("user_id"),
            agent_id=conv.get("agent_id"),
            agent_name=conv.get("agent_name"),
            agent_type=conv.get("agent_type"),
            model=conv.get("model"),
            data=payload,
        )
        session.add(row)
    session.commit()


def _save_reports(session, data):
    from database.repositories import ReportsRepository

    repo = ReportsRepository(session)
    for report in data.get("reports", []):
        repo.append_report(report)


def _save_assessment_history(session, data):
    from database.repositories import AssessmentsRepository

    repo = AssessmentsRepository(session)
    for snapshot in data.get("snapshots", []):
        repo.record(snapshot, replace_recent=False)


def _save_assessment_stats(session, data):
    from database.models import AssessmentStats

    session.merge(
        AssessmentStats(
            id=1,
            assessments_run=int((data or {}).get("assessments_run", 0) or 0),
            last_assessment_ts=(data or {}).get("last_assessment_ts"),
        )
    )
    session.commit()


def _save_telemetry_metrics(session, data):
    from database.models import TelemetryMetric

    agents = ((data or {}).get("agents") or {})
    for agent_id, entry in agents.items():
        session.merge(
            TelemetryMetric(
                agent_id=agent_id,
                requests=int(entry.get("requests", 0) or 0),
                errors=int(entry.get("errors", 0) or 0),
                first_ts=entry.get("first_ts"),
                last_ts=entry.get("last_ts"),
            )
        )
    session.commit()


def _save_telemetry_history(session, data):
    from database.repositories import TelemetryRepository

    repo = TelemetryRepository(session)
    for snapshot in data.get("snapshots", []):
        repo.add_history(snapshot)


SAVERS = {
    "users": _save_users,
    "agents": _save_agents,
    "sessions": _save_sessions,
    "insights": _save_insights,
    "reports_history": _save_reports,
    "assessment_history": _save_assessment_history,
    "assessment_stats": _save_assessment_stats,
    "telemetry_metrics": _save_telemetry_metrics,
    "telemetry_history": _save_telemetry_history,
}


def _documents():
    """Document descriptors: JSON file, db count validator, json reader."""
    from database import models

    return [
        {
            "name": "users",
            "file": "users.json",
            "db_count": lambda: _count(models.User),
            "json_count": lambda d: len((d or {}).get("users", [])),
        },
        {
            "name": "agents",
            "file": "agents.json",
            "db_count": lambda: _count(models.Agent),
            "json_count": lambda d: len((d or {}).get("agents", [])),
        },
        {
            "name": "sessions",
            "file": "sessions.json",
            "db_count": lambda: _count(models.Conversation),
            "db_count_secondary": lambda: _count(models.Message),
            "json_count": lambda d: len((d or {}).get("conversations", [])),
            "json_count_secondary": lambda d: sum(
                len(c.get("messages", [])) for c in (d or {}).get("conversations", [])
            ),
        },
        {
            "name": "insights",
            "file": "insights.json",
            "db_count": lambda: _count(models.Insight),
            "json_count": lambda d: len((d or {}).get("conversations", [])),
        },
        {
            "name": "reports_history",
            "file": "reports_history.json",
            "db_count": lambda: _count(models.ReportHistory),
            "json_count": lambda d: len((d or {}).get("reports", [])),
        },
        {
            "name": "assessment_history",
            "file": "assessment_history.json",
            "db_count": lambda: _count(models.AssessmentHistory),
            "json_count": lambda d: len((d or {}).get("snapshots", [])),
        },
        {
            "name": "assessment_stats",
            "file": "assessment_stats.json",
            "db_count": lambda: _count(models.AssessmentStats),
            "json_count": lambda d: 1 if d else 0,
        },
        {
            "name": "telemetry_metrics",
            "file": "telemetry_metrics.json",
            "db_count": lambda: _count(models.TelemetryMetric),
            "json_count": lambda d: len(((d or {}).get("agents") or {})),
        },
        {
            "name": "telemetry_history",
            "file": "telemetry_history.json",
            "db_count": lambda: _count(models.TelemetryHistory),
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
    existing = doc["db_count"]()

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
        saver(session, data)
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
            "db_count": doc["db_count"](),
            "match": False,
            "note": "failed - rolled back",
        }

    after = doc["db_count"]()
    secondary = None
    if "db_count_secondary" in doc:
        secondary = {
            "json": doc["json_count_secondary"](data),
            "db": doc["db_count_secondary"](),
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


def _check_pks(issues, table, ids):
    nulls = [i for i in ids if i is None or (isinstance(i, str) and not i.strip())]
    dup_count = len(ids) - len({i for i in ids if i is not None})
    if nulls:
        issues.append({"type": "NULL primary key", "detail": "{} has {} NULL id(s)".format(table, len(nulls))})
    if dup_count:
        issues.append({"type": "duplicate primary key", "detail": "{} has {} duplicate id(s)".format(table, dup_count)})


def _validate_source_data():
    """Detect data-quality issues in the source JSON before migrating."""
    issues = []

    users = load_json("users.json")
    if users is not None:
        _check_pks(issues, "users", [u.get("id") for u in users.get("users", [])])

    agents = load_json("agents.json")
    if agents is not None:
        _check_pks(issues, "agents", [a.get("id") for a in agents.get("agents", [])])

    sessions = load_json("sessions.json")
    if sessions is not None:
        convs = sessions.get("conversations", [])
        _check_pks(issues, "conversations", [c.get("id") for c in convs])
        for conv in convs:
            for field in ("created", "updated"):
                value = conv.get(field)
                if value is not None and not isinstance(value, (int, float)):
                    issues.append({"type": "invalid timestamp", "detail": "conversation {} {}".format(conv.get("id"), field)})
            for msg in conv.get("messages", []):
                ts = msg.get("ts")
                if ts is not None and not isinstance(ts, (int, float)):
                    issues.append({"type": "invalid timestamp", "detail": "message in conversation {}".format(conv.get("id"))})

    insights = load_json("insights.json")
    if insights is not None:
        _check_pks(issues, "insights", [i.get("id") for i in insights.get("conversations", [])])

    telemetry = load_json("telemetry_metrics.json")
    if telemetry is not None:
        _check_pks(issues, "telemetry_metrics", list((telemetry.get("agents") or {}).keys()))

    return issues


def _migrate_findings(session, report):
    """Migrate historical findings when a findings.json document exists."""
    from database import models
    from database.repositories import FindingsRepository

    data = load_json("findings.json")
    if data is None:
        log.info("Skip findings: findings.json not present (no historical finding data).")
        return {
            "file": "findings.json",
            "json_count": 0,
            "migrated": 0,
            "skipped": 0,
            "db_count": _count(models.Finding),
            "match": True,
            "note": "no source file",
        }

    json_count = len((data or {}).get("findings", []))
    existing = _count(models.Finding)
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
            "db_count": _count(models.Finding),
            "match": False,
            "note": "failed - rolled back",
        }

    after = _count(models.Finding)
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
    import argparse

    parser = argparse.ArgumentParser(description="Migrate JSON documents into PostgreSQL")
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Synchronize the schema first (add missing columns/tables/indexes) before migrating",
    )
    args = parser.parse_args()

    from database.db import create_all, get_session
    from database.schema_validation import alter_statements, compare_schema

    report = {
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "schema": {"issues": 0, "columns_added": 0, "details": []},
        "data_validation": {"issues": []},
        "documents": [],
        "errors": [],
    }

    data_issues = _validate_source_data()
    report["data_validation"]["issues"] = data_issues
    if data_issues:
        log.warning("Source data validation found %s issue(s):", len(data_issues))
        for issue in data_issues:
            log.warning("  [%s] %s", issue["type"], issue["detail"])

    # ---- Pre-migration schema validation ---------------------------------
    try:
        create_all()  # creates missing tables only
        engine = get_session().get_bind()
    except Exception as exc:
        report["errors"].append(str(exc))
        log.error("Migration aborted: %s", exc)
        _write_report(report)
        return 1

    drifts = compare_schema(engine)
    if drifts:
        repair = alter_statements(drifts, engine)
        report["schema"]["issues"] = len(drifts)
        report["schema"]["details"] = drifts
        log.warning("Schema drift detected (%s issue(s)).", len(drifts))
        for d in drifts:
            log.warning("  %s: %s", d["table"], d["issue"])

        if args.sync:
            log.info("--sync: applying %s repair statement(s).", len(repair))
            try:
                from sqlalchemy import text

                with engine.begin() as conn:
                    for statement in repair:
                        conn.execute(text(statement))
                report["schema"]["columns_added"] = sum(
                    1 for d in drifts if d["issue"] == "missing column"
                )
                log.info("Schema synchronized.")
            except Exception as exc:
                report["errors"].append("schema sync failed: {}".format(exc))
                log.error("Schema sync failed: %s", exc)
                _write_report(report)
                return 1
        else:
            log.error("Migration BLOCKED - schema mismatch. Repair SQL:")
            for statement in repair:
                print(statement)
            log.error("Run 'python scripts/sync_postgres_schema.py' or retry with --sync.")
            _write_report(report)
            return 2

    try:
        session = get_session()
    except Exception as exc:
        report["errors"].append(str(exc))
        _write_report(report)
        return 1

    for doc in _documents():
        saver = SAVERS.get(doc["name"])
        if saver is None:
            report["errors"].append("{}: no saver registered".format(doc["name"]))
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
