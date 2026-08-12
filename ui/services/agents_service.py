import json
import os
import re
import uuid

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.abspath(os.path.join(SERVICE_DIR, "..", "config"))
AGENTS_FILE = os.path.join(CONFIG_DIR, "agents.json")


def _load():
    if not os.path.exists(AGENTS_FILE):
        return []
    try:
        with open(AGENTS_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data.get("agents", []) or []
    except Exception:
        return []


def _save(agents):
    with open(AGENTS_FILE, "w", encoding="utf-8") as handle:
        json.dump({"agents": agents}, handle, indent=2)


def list_agents(include_key=False):
    agents = _load()
    result = []
    for agent in agents:
        item = dict(agent)
        if not include_key:
            item["api_key"] = mask_key(agent.get("api_key", ""))
        result.append(item)
    return result


def get_agent(agent_id):
    for agent in _load():
        if agent.get("id") == agent_id:
            return agent
    return None


def get_connected_agent():
    for agent in _load():
        if agent.get("connected"):
            return agent
    return None


def mask_key(key):
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return "••••••••" + key[-4:]


def slugify(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
    return slug.strip("-") or "agent"


def add_agent(name, type_name, endpoint, api_key, model="gpt-5.1", llm_endpoint=None, connected=True):
    agents = _load()
    agent_id = slugify(name)

    if any(a.get("id") == agent_id for a in agents):
        for agent in agents:
            if agent.get("id") == agent_id:
                agent.update(
                    {
                        "name": name,
                        "type": type_name,
                        "model": model,
                        "agent_endpoint": endpoint,
                        "llm_endpoint": llm_endpoint,
                        "api_key": api_key,
                        "connected": connected,
                    }
                )
        _save(agents)
        return get_agent(agent_id)

    agent = {
        "id": agent_id,
        "name": name,
        "type": type_name,
        "model": model,
        "agent_endpoint": endpoint,
        "llm_endpoint": llm_endpoint,
        "api_key": api_key,
        "connected": connected,
        "created_at": _now(),
    }

    if connected:
        for existing in agents:
            existing["connected"] = False

    agents.insert(0, agent)
    _save(agents)
    return agent


def set_connected(agent_id, connected=True):
    agents = _load()
    for agent in agents:
        agent["connected"] = agent.get("id") == agent_id and connected
    _save(agents)


def remove_agent(agent_id):
    agents = _load()
    remaining = [a for a in agents if a.get("id") != agent_id]
    _save(remaining)
    return len(remaining) != len(agents)


def _now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
