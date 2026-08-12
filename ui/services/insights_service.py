import os
import threading
import time
import uuid

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.abspath(os.path.join(SERVICE_DIR, "..", "config"))
INSIGHTS_FILE = os.path.join(CONFIG_DIR, "insights.json")

_lock = threading.Lock()

# Approximate model pricing used for cost estimation (USD per 1M tokens).
INPUT_PRICE_PER_M = 1.25
OUTPUT_PRICE_PER_M = 10.0


def _estimate_cost(input_tokens, output_tokens):
    return round(
        input_tokens / 1e6 * INPUT_PRICE_PER_M
        + output_tokens / 1e6 * OUTPUT_PRICE_PER_M,
        4,
    )


def _load():
    if not os.path.exists(INSIGHTS_FILE):
        return {"conversations": []}
    try:
        with open(INSIGHTS_FILE, "r", encoding="utf-8") as handle:
            data = json_load(handle)
        if not isinstance(data, dict):
            return {"conversations": []}
        return data
    except Exception:
        return {"conversations": []}


def json_load(handle):
    import json

    return json.load(handle)


def _save(data):
    import json

    with open(INSIGHTS_FILE, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def record_turn(agent, messages, usage, latency_ms, reply="", conversation_id=None):
    now = time.time()
    conversation_id = conversation_id or "conv-" + uuid.uuid4().hex[:12]

    usage = usage or {}
    input_details = usage.get("input_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or {}

    turn = {
        "timestamp": now,
        "message_count": len(messages) if messages else 0,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "cached_tokens": input_details.get("cached_tokens", 0),
        "cache_write_tokens": input_details.get("cache_write_tokens", 0),
        "reasoning_tokens": output_details.get("reasoning_tokens", 0),
        "latency_ms": latency_ms or 0,
        "reply_preview": (reply or "")[:300],
    }

    with _lock:
        data = _load()
        conversations = data.get("conversations", [])
        existing = None
        for conversation in conversations:
            if conversation.get("id") == conversation_id:
                existing = conversation
                break

        if existing is None:
            existing = {
                "id": conversation_id,
                "agent_id": agent.get("id", ""),
                "agent_name": agent.get("name", ""),
                "agent_type": agent.get("type", ""),
                "model": agent.get("model", ""),
                "created": now,
                "updated": now,
                "turns": [],
            }
            conversations.insert(0, existing)
            data["conversations"] = conversations

        existing["updated"] = now
        existing["turns"].append(turn)

        if len(existing["turns"]) > 500:
            existing["turns"] = existing["turns"][-500:]

        if len(conversations) > 200:
            data["conversations"] = conversations[:200]

        _save(data)

    return conversation_id


def summarize():
    data = _load()
    conversations = data.get("conversations", [])

    by_agent = {}
    total = {
        "conversations": 0,
        "turns": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": 0,
        "latency_ms": 0,
        "last_active": None,
    }

    recent = []
    for conversation in conversations:
        agent_id = conversation.get("agent_id") or "unknown"
        agent = by_agent.setdefault(
            agent_id,
            {
                "agent_id": agent_id,
                "agent_name": conversation.get("agent_name", agent_id),
                "agent_type": conversation.get("agent_type", ""),
                "model": conversation.get("model", ""),
                "conversations": 0,
                "turns": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cached_tokens": 0,
                "cache_write_tokens": 0,
                "reasoning_tokens": 0,
                "total_latency_ms": 0,
                "last_active": conversation.get("updated"),
                "created": conversation.get("created"),
            },
        )

        agent["conversations"] += 1
        agent["turns"] += len(conversation.get("turns", []))
        agent["last_active"] = max(
            agent["last_active"] or 0, conversation.get("updated") or 0
        )

        total["conversations"] += 1
        total["turns"] += len(conversation.get("turns", []))
        if conversation.get("updated"):
            total["last_active"] = max(total["last_active"] or 0, conversation["updated"])

        turns = conversation.get("turns", [])
        total["latency_ms"] += sum(t.get("latency_ms", 0) for t in turns)
        for turn in turns:
            total["input_tokens"] += turn.get("input_tokens", 0)
            total["output_tokens"] += turn.get("output_tokens", 0)
            total["total_tokens"] += turn.get("total_tokens", 0)
            total["cached_tokens"] += turn.get("cached_tokens", 0)
            total["cache_write_tokens"] += turn.get("cache_write_tokens", 0)
            total["reasoning_tokens"] += turn.get("reasoning_tokens", 0)

            agent["input_tokens"] += turn.get("input_tokens", 0)
            agent["output_tokens"] += turn.get("output_tokens", 0)
            agent["total_tokens"] += turn.get("total_tokens", 0)
            agent["cached_tokens"] += turn.get("cached_tokens", 0)
            agent["cache_write_tokens"] += turn.get("cache_write_tokens", 0)
            agent["reasoning_tokens"] += turn.get("reasoning_tokens", 0)
            agent["total_latency_ms"] += turn.get("latency_ms", 0)

        recent.append(
            {
                "id": conversation.get("id", ""),
                "agent_name": conversation.get("agent_name", ""),
                "model": conversation.get("model", ""),
                "created": conversation.get("created"),
                "updated": conversation.get("updated"),
                "turn_count": len(conversation.get("turns", [])),
                "last_tokens": (conversation.get("turns", []) or [{}])[-1].get("total_tokens", 0),
                "last_latency_ms": (conversation.get("turns", []) or [{}])[-1].get("latency_ms", 0),
            }
        )

    for agent in by_agent.values():
        agent["avg_latency_ms"] = (
            int(agent["total_latency_ms"] / agent["turns"]) if agent["turns"] else 0
        )
        agent["avg_tokens_per_turn"] = (
            int(agent["total_tokens"] / agent["turns"]) if agent["turns"] else 0
        )
        agent.pop("total_latency_ms", None)
        agent["cost"] = _estimate_cost(
            agent.get("input_tokens", 0), agent.get("output_tokens", 0)
        )

    total["avg_latency_ms"] = (
        int(total["latency_ms"] / total["turns"]) if total["turns"] else 0
    )
    total.pop("latency_ms", None)
    total["cost"] = _estimate_cost(
        total.get("input_tokens", 0), total.get("output_tokens", 0)
    )

    return {
        "agents": sorted(by_agent.values(), key=lambda a: a["last_active"] or 0, reverse=True),
        "totals": total,
        "recent": recent[:50],
    }
