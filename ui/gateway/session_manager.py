import json
import os
import threading
import time
import uuid

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.abspath(os.path.join(SERVICE_DIR, "..", "config"))
SESSIONS_FILE = os.path.join(CONFIG_DIR, "sessions.json")

_lock = threading.Lock()

MAX_CONVERSATIONS = 100
MAX_MESSAGES = 50


def _load():
    if not os.path.exists(SESSIONS_FILE):
        return {"conversations": []}
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return {"conversations": []}
        return data
    except Exception:
        return {"conversations": []}


def _save(data):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def get_or_create(conversation_id, user_id="anonymous"):
    now = time.time()
    conversation_id = conversation_id or "conv-" + uuid.uuid4().hex[:12]

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
                "user_id": user_id,
                "created": now,
                "updated": now,
                "messages": [],
            }
            conversations.insert(0, existing)
            data["conversations"] = conversations
            _save(data)

    return existing


def add_message(conversation_id, role, content, user_id="anonymous"):
    now = time.time()
    conversation_id = conversation_id or "conv-" + uuid.uuid4().hex[:12]

    with _lock:
        data = _load()
        conversations = data.get("conversations", [])

        conversation = None
        for item in conversations:
            if item.get("id") == conversation_id:
                conversation = item
                break

        if conversation is None:
            conversation = {
                "id": conversation_id,
                "user_id": user_id,
                "created": now,
                "updated": now,
                "messages": [],
            }
            conversations.insert(0, conversation)
            data["conversations"] = conversations

        conversation["updated"] = now
        conversation.setdefault("messages", []).append(
            {
                "role": role,
                "content": content,
                "timestamp": now,
            }
        )

        if len(conversation["messages"]) > MAX_MESSAGES:
            conversation["messages"] = conversation["messages"][-MAX_MESSAGES:]

        if len(conversations) > MAX_CONVERSATIONS:
            data["conversations"] = conversations[:MAX_CONVERSATIONS]

        _save(data)

    return conversation_id


def get_messages(conversation_id, limit=None):
    with _lock:
        data = _load()
        for conversation in data.get("conversations", []):
            if conversation.get("id") == conversation_id:
                messages = conversation.get("messages", [])
                if limit:
                    messages = messages[-limit:]
                return list(messages)
    return []


def list_conversations(user_id=None):
    with _lock:
        data = _load()
        conversations = data.get("conversations", [])
        result = []
        for conversation in conversations:
            if user_id and conversation.get("user_id") != user_id:
                continue
            result.append(
                {
                    "id": conversation.get("id", ""),
                    "user_id": conversation.get("user_id", ""),
                    "created": conversation.get("created"),
                    "updated": conversation.get("updated"),
                    "message_count": len(conversation.get("messages", [])),
                }
            )
        return result
