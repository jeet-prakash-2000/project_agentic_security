"""SQLAlchemy ORM models for the LTM Security Platform.

Each model maps a JSON document (previously stored under ``config/``) to a
PostgreSQL table. JSON documents and their tables:

* ``users.json``                  -> ``users``
* ``agents.json``                 -> ``agents``
* ``sessions.json``               -> ``conversations`` + ``messages``
* ``insights.json``               -> ``insights``
* ``reports_history.json``        -> ``reports_history``
* ``assessment_history.json``     -> ``assessment_history``
* ``assessment_stats.json``       -> ``assessment_stats``
* ``telemetry_metrics.json``      -> ``telemetry_metrics``
* ``telemetry_history.json``      -> ``telemetry_history``
"""

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.types import JSON

from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(512), nullable=False)
    role = Column(String(64), default="Security Analyst")
    created = Column(Float)


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(64))
    model = Column(String(64))
    agent_endpoint = Column(String(512))
    api_key = Column(String(512))
    connected = Column(Boolean, default=False)
    created_at = Column(String(64))
    agent_id = Column(String(255))


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), default="anonymous")
    title = Column(String(255), default="")
    created = Column(Float)
    updated = Column(Float)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        String(64),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(16), nullable=False)
    content = Column(Text, default="")
    tool = Column(String(64))
    ts = Column(Float)
    meta = Column(JSON)


class Insight(Base):
    __tablename__ = "insights"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64))
    agent_id = Column(String(64))
    agent_name = Column(String(255))
    agent_type = Column(String(64))
    model = Column(String(64))
    data = Column(JSON)


class ReportHistory(Base):
    __tablename__ = "reports_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    type = Column(String(64))
    generated_by = Column(String(255))
    ts = Column(Float)
    status = Column(String(32))
    size = Column(String(32))
    download_url = Column(String(512))


class AssessmentHistory(Base):
    __tablename__ = "assessment_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(String(64), index=True)
    executed_at = Column(Float, index=True)
    compliance_score = Column(Float)
    security_score = Column(Float)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)
    total_findings = Column(Integer, default=0)


class AssessmentStats(Base):
    __tablename__ = "assessment_stats"

    id = Column(Integer, primary_key=True, default=1)
    assessments_run = Column(Integer, default=0)
    last_assessment_ts = Column(Float)


class TelemetryMetric(Base):
    __tablename__ = "telemetry_metrics"

    agent_id = Column(String(64), primary_key=True)
    requests = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    first_ts = Column(Float)
    last_ts = Column(Float)


class TelemetryHistory(Base):
    __tablename__ = "telemetry_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(64))
    agent_name = Column(String(255))
    label = Column(String(255))
    ts = Column(Float)
    nodes = Column(JSON)


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(String(64), index=True)
    control = Column(String(255), index=True)
    status = Column(String(32))
    risk = Column(String(32))
    metric = Column(String(255))
    observed = Column(Text)
    expected = Column(Text)
    finding = Column(Text)
    remediation = Column(Text)
    risk_score = Column(Float)
