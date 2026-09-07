"""Insights repository (table ``insights``, formerly ``insights.json``).

Each row is one chat conversation; the rich ``data`` JSON payload keeps
``created``, ``updated`` and the ordered ``turns`` list (token usage per
assistant turn) used by the Insights dashboard.
"""

from database.models import Insight
from database.repositories.base import BaseRepository

MAX_ROWS = 200


class InsightsRepository(BaseRepository):
    model = Insight

    def get(self, conversation_id):
        return self.session.get(Insight, conversation_id)

    def list_conversations(self, user_id=None):
        query = self.session.query(Insight)
        if user_id:
            query = query.filter(Insight.user_id == user_id)
        return query.all()

    def recent(self, limit=50):
        rows = self.session.query(Insight).all()
        rows.sort(
            key=lambda row: ((row.data or {}).get("updated") or 0),
            reverse=True,
        )
        return rows[:limit]

    def claim_legacy(self, user_id, legacy=("anonymous", "demo")):
        """Reassign unowned insight rows to the given user (bootstrap)."""
        from sqlalchemy import or_

        result = (
            self.session.query(Insight)
            .filter(
                or_(
                    Insight.user_id.is_(None),
                    Insight.user_id.in_(list(legacy)),
                )
            )
            .update({Insight.user_id: user_id}, synchronize_session=False)
        )
        self.session.commit()
        return int(result or 0)

    def record(self, data):
        """Insert or update one conversation insight row.

        ``data`` carries id/agent/user metadata plus the ``turns`` list.
        """
        conversation_id = data.get("id")
        row = self.session.get(Insight, conversation_id)
        if row is None:
            row = Insight(
                id=conversation_id,
                user_id=data.get("user_id"),
                agent_id=data.get("agent_id"),
                agent_name=data.get("agent_name"),
                agent_type=data.get("agent_type"),
                model=data.get("model"),
                data={
                    "created": data.get("created"),
                    "updated": data.get("updated"),
                    "turns": data.get("turns") or [],
                },
            )
            self.session.add(row)
        else:
            payload = dict(row.data or {})
            turns = payload.get("turns") or []
            turns = (turns + (data.get("turns") or []))[-500:]
            payload["turns"] = turns
            payload["updated"] = data.get("updated")
            row.data = payload
            if data.get("agent_name"):
                row.agent_name = data.get("agent_name")
        self._trim()
        self.session.commit()
        return row

    def _trim(self):
        """Keep only the newest MAX_ROWS conversations."""
        from sqlalchemy import func

        total = (
            self.session.query(func.count(Insight.id)).scalar() or 0
        )
        if total <= MAX_ROWS:
            return
        rows = self.session.query(Insight).all()
        rows.sort(
            key=lambda r: ((r.data or {}).get("updated") or 0),
            reverse=True,
        )
        for stale in rows[MAX_ROWS:]:
            self.session.delete(stale)
