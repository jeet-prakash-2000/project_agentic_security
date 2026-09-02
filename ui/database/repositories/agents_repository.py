"""Agents repository (table ``agents``, formerly ``agents.json``)."""

from database.models import Agent
from database.repositories.base import BaseRepository


class AgentsRepository(BaseRepository):
    model = Agent

    def list_agents(self):
        """Return all registered agents, connected first."""
        return (
            self.session.query(Agent)
            .order_by(Agent.connected.desc())
            .all()
        )

    def get_connected(self):
        return (
            self.session.query(Agent)
            .filter(Agent.connected.is_(True))
            .first()
        )

    def create(self, data):
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
        self.session.add(agent)
        self.session.commit()
        return agent

    def update(self, agent_id, **fields):
        agent = self.session.get(Agent, agent_id)
        if agent is None:
            return None
        for key, value in fields.items():
            if hasattr(agent, key):
                setattr(agent, key, value)
        self.session.commit()
        return agent

    def set_connected(self, agent_id, connected=True):
        self.session.query(Agent).update({Agent.connected: False})
        self.session.commit()
        if agent_id:
            self.update(agent_id, connected=bool(connected))
        return self.get(agent_id)
