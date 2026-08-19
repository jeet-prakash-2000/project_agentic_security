"""Agents repository."""

from database.models import Agent
from database.repositories.base import BaseRepository


class AgentsRepository(BaseRepository):
    model = Agent

    def connected(self):
        return (
            self.session.query(Agent)
            .filter(Agent.connected.is_(True))
            .first()
        )

    def upsert_from_dict(self, data):
        agent = Agent(
            id=data.get("id"),
            name=data.get("name"),
            type=data.get("type"),
            model=data.get("model"),
            agent_endpoint=data.get("agent_endpoint"),
            api_key=data.get("api_key"),
            connected=bool(data.get("connected", False)),
            created_at=data.get("created_at"),
            agent_id=data.get("agent_id"),
        )
        return self.upsert(agent)
