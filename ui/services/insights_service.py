"""Insights service backed by the ``insights`` table.

Each row is one chat conversation; the ``data`` JSONB payload holds
``created``/``updated`` and the ordered ``turns`` list. Output shapes match
the previous ``insights.json`` documents so the Insights UI contract is
unchanged.
"""

import threading
import time
import uuid

from database.db import get_session
from database.repositories import InsightsRepository

_lock = threading.Lock()

INPUT_PRICE_PER_M = 1.25
OUTPUT_PRICE_PER_M = 10.0

MAX_TURNS = 500
MAX_CONVERSATIONS = 200
MAX_SERIES_POINTS = 800


def _estimate_cost(input_tokens, output_tokens):
    return round(
        input_tokens / 1e6 * INPUT_PRICE_PER_M
        + output_tokens / 1e6 * OUTPUT_PRICE_PER_M,
        4,
    )


def _repo():
    return InsightsRepository(get_session())


def _to_dict(row):
    data = row.data or {}
    return {
        "id": row.id,
        "agent_id": row.agent_id or "",
        "agent_name": row.agent_name or "",
        "agent_type": row.agent_type or "",
        "model": row.model or "",
        "user_id": row.user_id,
        "created": data.get("created"),
        "updated": data.get("updated"),
        "turns": data.get("turns") or [],
    }


def _all_conversations(user_id=None):
    return [
        _to_dict(row)
        for row in _repo().list_conversations(user_id=user_id)
    ]


def record_turn(agent, messages, usage, latency_ms, reply="", conversation_id=None, user_id=None):
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
        repo = _repo()
        existing_row = repo.get(conversation_id)
        if existing_row is not None:
            existing = _to_dict(existing_row)
            existing["updated"] = now
            existing["turns"] = (existing.get("turns") or []) + [turn]
            existing["turns"] = existing["turns"][-MAX_TURNS:]
        else:
            existing = {
                "id": conversation_id,
                "agent_id": agent.get("id", ""),
                "agent_name": agent.get("name", ""),
                "agent_type": agent.get("type", ""),
                "model": agent.get("model", ""),
                "user_id": user_id,
                "created": now,
                "updated": now,
                "turns": [turn],
            }
        repo.record(existing)

    return conversation_id


def summarize(user_id=None):
    conversations = sorted(
        _all_conversations(user_id=user_id),
        key=lambda c: (c.get("updated") or 0),
        reverse=True,
    )

    by_agent = {}
    series_map = {}
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
        series = series_map.setdefault(agent_id, [])
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

            series.append(
                {
                    "ts": turn.get("timestamp") or conversation.get("updated"),
                    "input": turn.get("input_tokens", 0),
                    "output": turn.get("output_tokens", 0),
                    "total": turn.get("total_tokens", 0),
                    "latency_ms": turn.get("latency_ms", 0),
                }
            )

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
        points = sorted(
            series_map.get(agent["agent_id"], []),
            key=lambda p: p["ts"] or 0,
        )
        agent["series"] = points[-MAX_SERIES_POINTS:]

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


def summarize_conversation(conversation_id, user_id=None):
    row = _repo().get(conversation_id)
    conversation = _to_dict(row) if row is not None else None
    if conversation is None:
        return None
    if user_id and conversation.get("user_id") not in (None, user_id):
        return None

    turns = conversation.get("turns", [])
    input_tokens = sum(t.get("input_tokens", 0) for t in turns)
    output_tokens = sum(t.get("output_tokens", 0) for t in turns)
    total_tokens = sum(t.get("total_tokens", 0) for t in turns)
    cached_tokens = sum(t.get("cached_tokens", 0) for t in turns)
    reasoning_tokens = sum(t.get("reasoning_tokens", 0) for t in turns)
    total_latency_ms = sum(t.get("latency_ms", 0) for t in turns)

    return {
        "id": conversation_id,
        "agent_id": conversation.get("agent_id", ""),
        "agent_name": conversation.get("agent_name", ""),
        "agent_type": conversation.get("agent_type", ""),
        "model": conversation.get("model", ""),
        "created": conversation.get("created"),
        "updated": conversation.get("updated"),
        "turns": len(turns),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_tokens": cached_tokens,
        "reasoning_tokens": reasoning_tokens,
        "avg_latency_ms": int(total_latency_ms / len(turns)) if turns else 0,
        "cost": _estimate_cost(input_tokens, output_tokens),
    }
