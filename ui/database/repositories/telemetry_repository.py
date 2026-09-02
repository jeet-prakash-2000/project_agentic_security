"""Telemetry metrics and history repository.

Tables ``telemetry_metrics`` (live per-agent request/error counters) and
``telemetry_history`` (dated map snapshots used by the telemetry slider).
"""

import time

from database.models import TelemetryHistory, TelemetryMetric
from database.repositories.base import BaseRepository


class TelemetryRepository(BaseRepository):
    model = TelemetryMetric

    # -- metrics ------------------------------------------------------------

    def metrics(self, agent_id=None):
        query = self.session.query(TelemetryMetric)
        if agent_id:
            query = query.filter(TelemetryMetric.agent_id == agent_id)
        return query.all()

    def metric(self, agent_id):
        return self.session.get(TelemetryMetric, agent_id)

    def record_request(self, agent_id, error=False):
        row = self.session.get(TelemetryMetric, agent_id)
        if row is None:
            row = TelemetryMetric(
                agent_id=agent_id,
                requests=1,
                errors=1 if error else 0,
                first_ts=time.time(),
                last_ts=time.time(),
            )
            self.session.add(row)
        else:
            row.requests = int(row.requests or 0) + 1
            if error:
                row.errors = int(row.errors or 0) + 1
            row.last_ts = time.time()
        self.session.commit()
        return row

    # -- history ------------------------------------------------------------

    def list_history(self, agent_id=None):
        query = self.session.query(TelemetryHistory)
        if agent_id:
            query = query.filter(TelemetryHistory.agent_id == agent_id)
        return (
            query.order_by(TelemetryHistory.ts.asc())
            .all()
        )

    def latest_history(self, agent_id, limit=1):
        query = (
            self.session.query(TelemetryHistory)
            .filter(TelemetryHistory.agent_id == agent_id)
            .order_by(TelemetryHistory.ts.desc())
            .limit(limit)
        )
        return query.all()

    def has_history(self, agent_id):
        return self.count_history(agent_id) > 0

    def count_history(self, agent_id):
        from sqlalchemy import func

        return (
            self.session.query(func.count(TelemetryHistory.id))
            .filter(TelemetryHistory.agent_id == agent_id)
            .scalar()
            or 0
        )

    def add_history(self, data):
        entry = TelemetryHistory(
            agent_id=data.get("agent_id"),
            agent_name=data.get("agent_name"),
            label=data.get("label"),
            ts=data.get("ts"),
            nodes=data.get("nodes"),
        )
        self.session.add(entry)
        self.session.commit()
        return entry

    def truncate_history(self, agent_id=None, keep=200):
        """Keep only the most recent ``keep`` snapshots for an agent."""
        from sqlalchemy import func

        rows = (
            self.session.query(
                TelemetryHistory.id,
                func.row_number().over(
                    order_by=TelemetryHistory.ts.desc(),
                    partition_by=TelemetryHistory.agent_id,
                ).label("rn"),
            )
        )
        if agent_id:
            rows = rows.filter(TelemetryHistory.agent_id == agent_id)
        sub = rows.subquery()
        stale = (
            self.session.query(sub.c.id)
            .filter(sub.c.rn > keep)
            .all()
        )
        if stale:
            ids = [row[0] for row in stale]
            self.session.query(TelemetryHistory).filter(
                TelemetryHistory.id.in_(ids)
            ).delete(synchronize_session=False)
            self.session.commit()
