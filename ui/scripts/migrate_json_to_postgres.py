"""One-time migration of JSON documents into PostgreSQL.

Usage::

    export DATABASE_URL="postgresql://Jeet:<password>@ltm-security-postgres.postgres.database.azure.com:5432/ltm_security?sslmode=require"
    python scripts/migrate_json_to_postgres.py

The script:

* reads every record from the JSON files under ``config/``,
* inserts them into the corresponding PostgreSQL tables (deduplicating by
  natural key and logging skipped duplicates),
* verifies JSON record counts against database record counts,
* writes ``migration_report.json`` with a full summary.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CONFIG_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "config")
)
REPORT_PATH = os.path.join(os.path.dirname(__file__), "migration_report.json")


def load_json(name):
    path = os.path.join(CONFIG_DIR, name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _exists(session, model, pk):
    return session.get(model, pk) is not None


def migrate_users(session):
    from database.models import User

    data = load_json("users.json")
    records = (data or {}).get("users", [])
    migrated, skipped = 0, 0
    for u in records:
        if not u.get("id"):
            skipped += 1
            continue
        if _exists(session, User, u["id"]):
            skipped += 1
            continue
        session.add(
            User(
                id=u["id"],
                name=u.get("name"),
                email=u.get("email"),
                password_hash=u.get("password_hash"),
                role=u.get("role") or "Security Analyst",
                created=u.get("created"),
            )
        )
        migrated += 1
    session.commit()
    db_count = session.query(User).count()
    return _result("users.json", len(records), migrated, skipped, db_count)


def migrate_agents(session):
    from database.models import Agent

    data = load_json("agents.json")
    records = (data or {}).get("agents", [])
    migrated, skipped = 0, 0
    for a in records:
        if not a.get("id"):
            skipped += 1
            continue
        if _exists(session, Agent, a["id"]):
            skipped += 1
            continue
        session.add(
            Agent(
                id=a["id"],
                name=a.get("name"),
                type=a.get("type"),
                model=a.get("model"),
                agent_endpoint=a.get("agent_endpoint"),
                api_key=a.get("api_key"),
                connected=bool(a.get("connected", False)),
                created_at=a.get("created_at"),
                agent_id=a.get("agent_id"),
            )
        )
        migrated += 1
    session.commit()
    db_count = session.query(Agent).count()
    return _result("agents.json", len(records), migrated, skipped, db_count)


def migrate_sessions(session):
    from database.models import Conversation, Message

    data = load_json("sessions.json")
    conversations = (data or {}).get("conversations", [])
    conv_migrated = conv_skipped = msg_migrated = msg_skipped = 0
    for conv in conversations:
        conv_id = conv.get("id")
        if not conv_id:
            conv_skipped += 1
            msg_skipped += len(conv.get("messages", []))
            continue
        if _exists(session, Conversation, conv_id):
            conv_skipped += 1
            msg_skipped += len(conv.get("messages", []))
            continue
        session.add(
            Conversation(
                id=conv_id,
                user_id=conv.get("user_id") or "anonymous",
                title=conv.get("title") or "",
                created=conv.get("created"),
                updated=conv.get("updated"),
            )
        )
        conv_migrated += 1
        for msg in conv.get("messages", []):
            session.add(
                Message(
                    conversation_id=conv_id,
                    role=msg.get("role") or "user",
                    content=msg.get("content") or "",
                    tool=msg.get("tool"),
                    ts=msg.get("ts"),
                    meta={
                        k: v
                        for k, v in msg.items()
                        if k not in ("role", "content", "tool", "ts")
                    }
                    or None,
                )
            )
            msg_migrated += 1
    session.commit()

    conv_db = session.query(Conversation).count()
    msg_db = session.query(Message).count()
    return [
        _result(
            "sessions.json (conversations)",
            len(conversations),
            conv_migrated,
            conv_skipped,
            conv_db,
        ),
        _result(
            "sessions.json (messages)",
            sum(len(c.get("messages", [])) for c in conversations),
            msg_migrated,
            msg_skipped,
            msg_db,
        ),
    ]


def migrate_insights(session):
    from database.models import Insight

    data = load_json("insights.json")
    records = (data or {}).get("conversations", [])
    migrated, skipped = 0, 0
    for c in records:
        if not c.get("id"):
            skipped += 1
            continue
        if _exists(session, Insight, c["id"]):
            skipped += 1
            continue
        base = {"id", "user_id", "agent_id", "agent_name", "agent_type", "model"}
        session.add(
            Insight(
                id=c["id"],
                user_id=c.get("user_id"),
                agent_id=c.get("agent_id"),
                agent_name=c.get("agent_name"),
                agent_type=c.get("agent_type"),
                model=c.get("model"),
                data={k: v for k, v in c.items() if k not in base} or None,
            )
        )
        migrated += 1
    session.commit()
    db_count = session.query(Insight).count()
    return _result("insights.json", len(records), migrated, skipped, db_count)


def migrate_reports_history(session):
    from database.models import ReportHistory

    data = load_json("reports_history.json")
    records = (data or {}).get("reports", [])
    existing = session.query(ReportHistory).count()
    if existing:
        return _result(
            "reports_history.json",
            len(records),
            0,
            len(records),
            existing,
        )
    for r in records:
        session.add(
            ReportHistory(
                name=r.get("name"),
                type=r.get("type"),
                generated_by=r.get("generated_by"),
                ts=r.get("ts"),
                status=r.get("status") or "Completed",
                size=r.get("size"),
                download_url=r.get("download_url"),
            )
        )
    session.commit()
    db_count = session.query(ReportHistory).count()
    return _result("reports_history.json", len(records), len(records), 0, db_count)


def migrate_assessment_history(session):
    from database.models import AssessmentHistory

    data = load_json("assessment_history.json")
    records = (data or {}).get("snapshots", [])
    existing = session.query(AssessmentHistory).count()
    if existing:
        return _result(
            "assessment_history.json",
            len(records),
            0,
            len(records),
            existing,
        )
    for s in records:
        severity = s.get("severity") or {}
        session.add(
            AssessmentHistory(
                assessment_id=s.get("run_id") or s.get("assessment_id"),
                executed_at=s.get("ts") or s.get("executed_at"),
                compliance_score=s.get("compliance_pct")
                if s.get("compliance_pct") is not None
                else s.get("compliance_score"),
                security_score=s.get("security_score"),
                critical_findings=severity.get("critical", 0),
                high_findings=severity.get("high", 0),
                medium_findings=severity.get("medium", 0),
                low_findings=severity.get("low", 0),
                total_findings=s.get("finding_count") or sum(severity.values()),
            )
        )
    session.commit()
    db_count = session.query(AssessmentHistory).count()
    return _result(
        "assessment_history.json", len(records), len(records), 0, db_count
    )


def migrate_assessment_stats(session):
    from database.models import AssessmentStats

    data = load_json("assessment_stats.json")
    if not data:
        return _result("assessment_stats.json", 0, 0, 0, 0)
    session.merge(
        AssessmentStats(
            id=1,
            assessments_run=data.get("assessments_run") or 0,
            last_assessment_ts=data.get("last_assessment_ts"),
        )
    )
    session.commit()
    db_count = session.query(AssessmentStats).count()
    return _result("assessment_stats.json", 1, 1, 0, db_count)


def migrate_telemetry_metrics(session):
    from database.models import TelemetryMetric

    data = load_json("telemetry_metrics.json")
    agents = (data or {}).get("agents", {})
    migrated, skipped = 0, 0
    for agent_id, m in agents.items():
        if _exists(session, TelemetryMetric, agent_id):
            skipped += 1
            continue
        session.add(
            TelemetryMetric(
                agent_id=agent_id,
                requests=m.get("requests") or 0,
                errors=m.get("errors") or 0,
                first_ts=m.get("first_ts"),
                last_ts=m.get("last_ts"),
            )
        )
        migrated += 1
    session.commit()
    db_count = session.query(TelemetryMetric).count()
    return _result(
        "telemetry_metrics.json", len(agents), migrated, skipped, db_count
    )


def migrate_telemetry_history(session):
    from database.models import TelemetryHistory

    data = load_json("telemetry_history.json")
    records = (data or {}).get("snapshots", [])
    existing = session.query(TelemetryHistory).count()
    if existing:
        return _result(
            "telemetry_history.json",
            len(records),
            0,
            len(records),
            existing,
        )
    for s in records:
        session.add(
            TelemetryHistory(
                agent_id=s.get("agent_id"),
                agent_name=s.get("agent_name"),
                label=s.get("label"),
                ts=s.get("ts"),
                nodes=s.get("nodes"),
            )
        )
    session.commit()
    db_count = session.query(TelemetryHistory).count()
    return _result(
        "telemetry_history.json", len(records), len(records), 0, db_count
    )


def _result(file, json_count, migrated, skipped, db_count):
    return {
        "file": file,
        "json_count": json_count,
        "migrated": migrated,
        "skipped": skipped,
        "db_count": db_count,
        "match": (json_count == db_count),
    }


def main():
    from database.db import create_all, get_session

    start = time.time()
    report = {
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start)),
        "files": [],
        "errors": [],
    }

    try:
        create_all()
        session = get_session()
    except Exception as exc:
        report["errors"].append(str(exc))
        report["finish_time"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time())
        )
        _write_report(report)
        print("Migration failed:", exc)
        return 1

    results = []
    for fn in (
        migrate_users,
        migrate_agents,
        migrate_sessions,
        migrate_insights,
        migrate_reports_history,
        migrate_assessment_history,
        migrate_assessment_stats,
        migrate_telemetry_metrics,
        migrate_telemetry_history,
    ):
        try:
            out = fn(session)
            if isinstance(out, list):
                results.extend(out)
            else:
                results.append(out)
        except Exception as exc:
            report["errors"].append(str(exc))

    for r in results:
        print(
            "Migrated {migrated} / skipped {skipped} / json {json_count} "
            "/ db {db_count}  <- {file}".format(**r)
        )

    failures = [r for r in results if not r["match"]]
    if failures:
        print("\nVALIDATION FAILURES:")
        for r in failures:
            print(
                "  {file}: json={json_count} db={db_count} (migrated "
                "{migrated}, skipped {skipped})".format(**r)
            )

    report["finish_time"] = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time())
    )
    report["files"] = results
    report["totals"] = {
        "json_records": sum(r["json_count"] for r in results),
        "migrated": sum(r["migrated"] for r in results),
        "skipped": sum(r["skipped"] for r in results),
    }
    report["validation"] = {
        "passed": not failures,
        "failures": [r["file"] for r in failures],
    }

    _write_report(report)
    print("\nMigration report written to:", REPORT_PATH)
    return 0 if not failures else 2


def _write_report(report):
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
