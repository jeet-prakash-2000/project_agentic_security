"""Telemetry metrics and history repository."""

from database.models import TelemetryHistory, TelemetryMetric
from database.repositories.base import BaseRepository


class TelemetryRepository(BaseRepository):
    model = TelemetryMetric

    def metrics(self, agent_id=None):
        query = self.session.query(TelemetryMetric)
        if agent_id:
            query = query.filter(TelemetryMetric.agent_id == agent_id)
        return query.all()

    def upsert_metric(self, data):
        metric = TelemetryMetric(
            agent_id=data.get("agent_id"),
            requests=data.get("requests") or 0,
            errors=data.get("errors") or 0,
            first_ts=data.get("first_ts"),
            last_ts=data.get("last_ts"),
        )
        return self.upsert(metric)

    def history(self, limit=100):
        return (
            self.session.query(TelemetryHistory)
            .order_by(TelemetryHistory.ts.desc())
            .limit(limit)
            .all()
        )

    def add_history(self, data):
        entry = TelemetryHistory(
            agent_id=data.get("agent_id"),
            agent_name=data.get("agent_name"),
            label=data.get("label"),
            ts=data.get("ts"),
            nodes=data.get("nodes"),
        )
        return self.add(entry)
