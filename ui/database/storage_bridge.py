"""Bridge between ``config.storage`` document API and PostgreSQL.

Each logical document (``users``, ``agents``, ``sessions``, ...) is stored as one
or more relational tables. This module converts between the JSON document shape
(which the rest of the application depends on) and the SQLAlchemy models.

``load()`` returns the document in its JSON shape, or ``None`` when PostgreSQL is
not configured or unavailable (so callers fall back to the JSON-file backend).
``save()`` replaces the document's rows in PostgreSQL and returns a boolean.
"""

from database.db import get_session, is_configured

_MESSAGE_META_KEYS = ("role", "content", "tool", "ts")


def _session():
    return get_session()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def _load_users(session):
    from database.models import User

    rows = session.query(User).all()
    return {
        "users": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "password_hash": u.password_hash,
                "role": u.role,
                "created": u.created,
            }
            for u in rows
        ]
    }


def _save_users(session, data):
    from database.models import User

    session.query(User).delete()
    for u in data.get("users", []):
        session.add(
            User(
                id=u.get("id"),
                name=u.get("name"),
                email=u.get("email"),
                password_hash=u.get("password_hash"),
                role=u.get("role") or "Security Analyst",
                created=u.get("created"),
            )
        )
    session.commit()


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

def _load_agents(session):
    from database.models import Agent

    rows = session.query(Agent).all()
    return {
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "model": a.model,
                "agent_endpoint": a.agent_endpoint,
                "api_key": a.api_key,
                "connected": bool(a.connected),
                "created_at": a.created_at,
                "agent_id": a.agent_id,
            }
            for a in rows
        ]
    }


def _save_agents(session, data):
    from database.models import Agent

    session.query(Agent).delete()
    for a in data.get("agents", []):
        session.add(
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
        )
    session.commit()


# ---------------------------------------------------------------------------
# Sessions -> conversations + messages
# ---------------------------------------------------------------------------

def _load_sessions(session):
    from database.models import Conversation, Message

    conversations = session.query(Conversation).order_by(Conversation.updated.desc()).all()
    messages = session.query(Message).order_by(Message.ts.asc()).all()

    by_conv = {}
    for m in messages:
        by_conv.setdefault(m.conversation_id, []).append(m)

    return {
        "conversations": [
            {
                "id": c.id,
                "user_id": c.user_id,
                "title": c.title,
                "created": c.created,
                "updated": c.updated,
                "messages": [
                    _message_to_dict(m) for m in by_conv.get(c.id, [])
                ],
            }
            for c in conversations
        ]
    }


def _save_sessions(session, data):
    from database.models import Conversation, Message

    session.query(Message).delete()
    session.query(Conversation).delete()
    for conv in data.get("conversations", []):
        session.add(
            Conversation(
                id=conv.get("id"),
                user_id=conv.get("user_id") or "anonymous",
                title=conv.get("title") or "",
                created=conv.get("created"),
                updated=conv.get("updated"),
            )
        )
        for msg in conv.get("messages", []):
            session.add(_dict_to_message(conv.get("id"), msg))
    session.commit()


def _message_to_dict(m):
    data = {
        "role": m.role,
        "content": m.content or "",
        "tool": m.tool,
        "ts": m.ts,
    }
    if m.meta:
        data.update(m.meta)
    return data


def _dict_to_message(conversation_id, msg):
    from database.models import Message

    return Message(
        conversation_id=conversation_id,
        role=msg.get("role") or "user",
        content=msg.get("content") or "",
        tool=msg.get("tool"),
        ts=msg.get("ts"),
        meta={
            k: v
            for k, v in (msg or {}).items()
            if k not in _MESSAGE_META_KEYS
        }
        or None,
    )


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

def _load_insights(session):
    from database.models import Insight

    rows = session.query(Insight).all()
    conversations = []
    for i in rows:
        item = {
            "id": i.id,
            "user_id": i.user_id,
            "agent_id": i.agent_id,
            "agent_name": i.agent_name,
            "agent_type": i.agent_type,
            "model": i.model,
        }
        extra = i.data or {}
        item.update(extra)
        conversations.append(item)
    return {"conversations": conversations}


def _save_insights(session, data):
    from database.models import Insight

    session.query(Insight).delete()
    for c in data.get("conversations", []):
        base_keys = {
            "id", "user_id", "agent_id", "agent_name", "agent_type", "model"
        }
        extra = {k: v for k, v in c.items() if k not in base_keys}
        session.add(
            Insight(
                id=c.get("id"),
                user_id=c.get("user_id"),
                agent_id=c.get("agent_id"),
                agent_name=c.get("agent_name"),
                agent_type=c.get("agent_type"),
                model=c.get("model"),
                data=extra or None,
            )
        )
    session.commit()


# ---------------------------------------------------------------------------
# Reports history
# ---------------------------------------------------------------------------

def _load_reports_history(session):
    from database.models import ReportHistory

    rows = session.query(ReportHistory).order_by(ReportHistory.ts.desc()).all()
    return {
        "reports": [
            {
                "name": r.name,
                "type": r.type,
                "generated_by": r.generated_by,
                "ts": r.ts,
                "status": r.status,
                "size": r.size,
                "download_url": r.download_url,
            }
            for r in rows
        ]
    }


def _save_reports_history(session, data):
    from database.models import ReportHistory

    session.query(ReportHistory).delete()
    for r in data.get("reports", []):
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


# ---------------------------------------------------------------------------
# Assessment history
# ---------------------------------------------------------------------------

def _load_assessment_history(session):
    from database.models import AssessmentHistory

    rows = session.query(AssessmentHistory).order_by(AssessmentHistory.executed_at.asc()).all()
    return {
        "snapshots": [
            {
                "run_id": a.assessment_id,
                "ts": a.executed_at,
                "compliance_pct": a.compliance_score,
                "security_score": a.security_score,
                "severity": {
                    "critical": a.critical_findings,
                    "high": a.high_findings,
                    "medium": a.medium_findings,
                    "low": a.low_findings,
                },
                "finding_count": a.total_findings,
            }
            for a in rows
        ]
    }


def _save_assessment_history(session, data):
    from database.models import AssessmentHistory

    session.query(AssessmentHistory).delete()
    for s in data.get("snapshots", []):
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


# ---------------------------------------------------------------------------
# Assessment stats
# ---------------------------------------------------------------------------

def _load_assessment_stats(session):
    from database.models import AssessmentStats

    stats = session.query(AssessmentStats).get(1)
    if stats is None:
        return None
    return {
        "assessments_run": stats.assessments_run,
        "last_assessment_ts": stats.last_assessment_ts,
    }


def _save_assessment_stats(session, data):
    from database.models import AssessmentStats

    session.merge(
        AssessmentStats(
            id=1,
            assessments_run=data.get("assessments_run") or 0,
            last_assessment_ts=data.get("last_assessment_ts"),
        )
    )
    session.commit()


# ---------------------------------------------------------------------------
# Telemetry metrics
# ---------------------------------------------------------------------------

def _load_telemetry_metrics(session):
    from database.models import TelemetryMetric

    rows = session.query(TelemetryMetric).all()
    return {
        "agents": {
            m.agent_id: {
                "requests": m.requests,
                "errors": m.errors,
                "first_ts": m.first_ts,
                "last_ts": m.last_ts,
            }
            for m in rows
        }
    }


def _save_telemetry_metrics(session, data):
    from database.models import TelemetryMetric

    session.query(TelemetryMetric).delete()
    for agent_id, m in (data.get("agents") or {}).items():
        session.add(
            TelemetryMetric(
                agent_id=agent_id,
                requests=m.get("requests") or 0,
                errors=m.get("errors") or 0,
                first_ts=m.get("first_ts"),
                last_ts=m.get("last_ts"),
            )
        )
    session.commit()


# ---------------------------------------------------------------------------
# Telemetry history
# ---------------------------------------------------------------------------

def _load_telemetry_history(session):
    from database.models import TelemetryHistory

    rows = session.query(TelemetryHistory).order_by(TelemetryHistory.ts.desc()).all()
    return {
        "snapshots": [
            {
                "agent_id": t.agent_id,
                "agent_name": t.agent_name,
                "label": t.label,
                "ts": t.ts,
                "nodes": t.nodes,
            }
            for t in rows
        ]
    }


def _save_telemetry_history(session, data):
    from database.models import TelemetryHistory

    session.query(TelemetryHistory).delete()
    for s in data.get("snapshots", []):
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

LOADERS = {
    "users": _load_users,
    "agents": _load_agents,
    "sessions": _load_sessions,
    "insights": _load_insights,
    "reports_history": _load_reports_history,
    "assessment_history": _load_assessment_history,
    "assessment_stats": _load_assessment_stats,
    "telemetry_metrics": _load_telemetry_metrics,
    "telemetry_history": _load_telemetry_history,
}

SAVERS = {
    "users": _save_users,
    "agents": _save_agents,
    "sessions": _save_sessions,
    "insights": _save_insights,
    "reports_history": _save_reports_history,
    "assessment_history": _save_assessment_history,
    "assessment_stats": _save_assessment_stats,
    "telemetry_metrics": _save_telemetry_metrics,
    "telemetry_history": _save_telemetry_history,
}


def load(document_name):
    if not is_configured():
        return None
    loader = LOADERS.get(document_name)
    if not loader:
        return None
    try:
        return loader(_session())
    except Exception:
        return None


def save(document_name, data):
    if not is_configured():
        return False
    saver = SAVERS.get(document_name)
    if not saver:
        return False
    try:
        saver(_session(), data)
        return True
    except Exception:
        return False
