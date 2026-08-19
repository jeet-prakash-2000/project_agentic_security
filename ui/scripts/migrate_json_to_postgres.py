"""Migrate the JSON documents under ``config/`` into PostgreSQL.

Usage::

    export DATABASE_URL="postgresql://Jeet:<password>@ltm-security-postgres.postgres.database.azure.com:5432/ltm_security?sslmode=require"
    python scripts/migrate_json_to_postgres.py

The script is idempotent: for each table it clears existing rows and repopulates
them from the corresponding JSON file. Migration order follows the dependency
graph (users/agents -> conversations+messages -> the remaining documents).
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


def migrate_users(session):
    from database.models import User

    data = load_json("users.json")
    if not data:
        print("skip users.json (missing)")
        return
    users = [
        User(
            id=u.get("id"),
            name=u.get("name"),
            email=u.get("email"),
            password_hash=u.get("password_hash"),
            role=u.get("role") or "Security Analyst",
            created=u.get("created"),
        )
        for u in data.get("users", [])
    ]
    session.query(User).delete()
    session.add_all(users)
    session.commit()
    print("migrated users:", len(users))


def migrate_agents(session):
    from database.models import Agent

    data = load_json("agents.json")
    if not data:
        print("skip agents.json (missing)")
        return
    agents = [
        Agent(
            id=a.get("id"),
            name=a.get("name"),
            type=a.get("type"),
            model=a.get("model"),
            agent_endpoint=a.get("agent_endpoint"),
            api_key=a.get("api_key"),
            connected=bool(a.get("connected", False)),
            created_at=a.get("created_at"),
            agent_id=a.get("agent_id"),
        )
        for a in data.get("agents", [])
    ]
    session.query(Agent).delete()
    session.add_all(agents)
    session.commit()
    print("migrated agents:", len(agents))


def migrate_conversations(session):
    from database.models import Conversation, Message

    data = load_json("sessions.json")
    if not data:
        print("skip sessions.json (missing)")
        return

    session.query(Message).delete()
    session.query(Conversation).delete()

    conversations = []
    messages = []
    for conv in data.get("conversations", []):
        conversations.append(
            Conversation(
                id=conv.get("id"),
                user_id=conv.get("user_id") or "anonymous",
                title=conv.get("title") or "",
                created=conv.get("created"),
                updated=conv.get("updated"),
            )
        )
        for msg in conv.get("messages", []):
            messages.append(
                Message(
                    conversation_id=conv.get("id"),
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

    session.add_all(conversations)
    session.add_all(messages)
    session.commit()
    print(
        "migrated conversations:",
        len(conversations),
        "| messages:",
        len(messages),
    )


def migrate_insights(session):
    from database.models import Insight

    data = load_json("insights.json")
    if not data:
        print("skip insights.json (missing)")
        return
    insights = [
        Insight(
            id=i.get("id"),
            user_id=i.get("user_id"),
            agent_id=i.get("agent_id"),
            agent_name=i.get("agent_name"),
            agent_type=i.get("agent_type"),
            model=i.get("model"),
        )
        for i in data.get("conversations", [])
    ]
    session.query(Insight).delete()
    session.add_all(insights)
    session.commit()
    print("migrated insights:", len(insights))


def migrate_reports_history(session):
    from database.models import ReportHistory

    data = load_json("reports_history.json")
    if not data:
        print("skip reports_history.json (missing)")
        return
    reports = [
        ReportHistory(
            name=r.get("name"),
            type=r.get("type"),
            generated_by=r.get("generated_by"),
            ts=r.get("ts"),
            status=r.get("status") or "Completed",
            size=r.get("size"),
            download_url=r.get("download_url"),
        )
        for r in data.get("reports", [])
    ]
    session.query(ReportHistory).delete()
    session.add_all(reports)
    session.commit()
    print("migrated reports_history:", len(reports))


def migrate_assessment_history(session):
    from database.models import AssessmentHistory

    data = load_json("assessment_history.json")
    if not data:
        print("skip assessment_history.json (missing)")
        return
    entries = []
    for s in data.get("snapshots", []):
        severity = s.get("severity") or {}
        entries.append(
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
                total_findings=s.get("finding_count")
                or sum(severity.values()),
            )
        )
    session.query(AssessmentHistory).delete()
    session.add_all(entries)
    session.commit()
    print("migrated assessment_history:", len(entries))


def migrate_assessment_stats(session):
    from database.models import AssessmentStats

    data = load_json("assessment_stats.json")
    if not data:
        print("skip assessment_stats.json (missing)")
        return
    stats = AssessmentStats(
        id=1,
        assessments_run=data.get("assessments_run") or 0,
        last_assessment_ts=data.get("last_assessment_ts"),
    )
    session.merge(stats)
    session.commit()
    print("migrated assessment_stats:", data.get("assessments_run"), "runs")


def migrate_telemetry_metrics(session):
    from database.models import TelemetryMetric

    data = load_json("telemetry_metrics.json")
    if not data:
        print("skip telemetry_metrics.json (missing)")
        return
    metrics = [
        TelemetryMetric(
            agent_id=agent_id,
            requests=m.get("requests") or 0,
            errors=m.get("errors") or 0,
            first_ts=m.get("first_ts"),
            last_ts=m.get("last_ts"),
        )
        for agent_id, m in (data.get("agents") or {}).items()
    ]
    session.query(TelemetryMetric).delete()
    session.add_all(metrics)
    session.commit()
    print("migrated telemetry_metrics:", len(metrics))


def migrate_telemetry_history(session):
    from database.models import TelemetryHistory

    data = load_json("telemetry_history.json")
    if not data:
        print("skip telemetry_history.json (missing)")
        return
    entries = [
        TelemetryHistory(
            agent_id=s.get("agent_id"),
            agent_name=s.get("agent_name"),
            label=s.get("label"),
            ts=s.get("ts"),
            nodes=s.get("nodes"),
        )
        for s in data.get("snapshots", [])
    ]
    session.query(TelemetryHistory).delete()
    session.add_all(entries)
    session.commit()
    print("migrated telemetry_history:", len(entries))


def main():
    from database.db import create_all, get_session

    create_all()
    session = get_session()

    # Easiest documents first, per the migration plan.
    migrate_users(session)
    migrate_agents(session)
    migrate_conversations(session)
    migrate_insights(session)
    migrate_reports_history(session)
    migrate_assessment_history(session)
    migrate_assessment_stats(session)
    migrate_telemetry_metrics(session)
    migrate_telemetry_history(session)

    print("Migration complete.")


if __name__ == "__main__":
    main()
