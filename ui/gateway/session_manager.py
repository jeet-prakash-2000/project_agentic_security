import os
import threading
import time
import uuid

from config import storage

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.abspath(os.path.join(SERVICE_DIR, "..", "config"))
SESSIONS_DOC = "sessions"

_lock = threading.Lock()

MAX_CONVERSATIONS = 100
MAX_MESSAGES = 50


def _load():
    data = storage.load_document(SESSIONS_DOC, {"conversations": []})
    if not isinstance(data, dict):
        return {"conversations": []}
    return data


def _save(data):
    storage.save_document(SESSIONS_DOC, data)


def _now():
    return time.time()


def get_or_create(conversation_id, user_id="anonymous"):
    now = _now()
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
                "title": "",
                "created": now,
                "updated": now,
                "messages": [],
            }
            conversations.insert(0, existing)
            data["conversations"] = conversations
            _save(data)

    return existing


def _ensure_conversation(data, conversations, conversation_id, user_id, now):
    conversation = None
    for item in conversations:
        if item.get("id") == conversation_id:
            conversation = item
            break

    if conversation is None:
        conversation = {
            "id": conversation_id,
            "user_id": user_id,
            "title": "",
            "created": now,
            "updated": now,
            "messages": [],
        }
        conversations.insert(0, conversation)
        data["conversations"] = conversations

    return conversation


def _normalize_message(role, content, meta):
    message = dict(meta or {})
    message["role"] = role
    message["content"] = content or ""
    message["ts"] = message.get("ts") or _now()
    return message


def add_message(conversation_id, role, content, user_id="anonymous", meta=None):
    now = _now()
    conversation_id = conversation_id or "conv-" + uuid.uuid4().hex[:12]

    with _lock:
        data = _load()
        conversations = data.get("conversations", [])

        conversation = _ensure_conversation(
            data, conversations, conversation_id, user_id, now
        )

        message = _normalize_message(role, content, meta)

        conversation["updated"] = now
        conversation.setdefault("messages", []).append(message)

        if (
            role == "user"
            and not (conversation.get("title") or "").strip()
        ):
            conversation["title"] = (content or "").strip()[:60]

        if len(conversation["messages"]) > MAX_MESSAGES:
            conversation["messages"] = conversation["messages"][-MAX_MESSAGES:]

        if len(conversations) > MAX_CONVERSATIONS:
            data["conversations"] = conversations[:MAX_CONVERSATIONS]

        _save(data)

    return conversation_id


def add_messages(conversation_id, messages, user_id="anonymous"):
    """Bulk-append full message metadata supplied by the client."""
    now = _now()
    conversation_id = conversation_id or "conv-" + uuid.uuid4().hex[:12]
    messages = messages or []

    with _lock:
        data = _load()
        conversations = data.get("conversations", [])

        conversation = _ensure_conversation(
            data, conversations, conversation_id, user_id, now
        )

        for item in messages:
            if not isinstance(item, dict):
                continue
            role = item.get("role") or "user"
            message = _normalize_message(
                role, item.get("content"), {k: v for k, v in item.items() if k not in ("role", "content")}
            )
            conversation.setdefault("messages", []).append(message)
            if role == "user" and not (conversation.get("title") or "").strip():
                conversation["title"] = (item.get("content") or "").strip()[:60]

        conversation["updated"] = now

        if len(conversation["messages"]) > MAX_MESSAGES:
            conversation["messages"] = conversation["messages"][-MAX_MESSAGES:]

        _save(data)

    return conversation_id


def get_conversation(conversation_id, user_id=None):
    with _lock:
        data = _load()
        for conversation in data.get("conversations", []):
            if conversation.get("id") != conversation_id:
                continue
            if user_id and conversation.get("user_id") != user_id:
                return None
            return conversation
    return None


def get_messages(conversation_id, limit=None, user_id=None):
    conversation = get_conversation(conversation_id, user_id=user_id)
    if not conversation:
        return []
    messages = conversation.get("messages", [])
    if limit:
        messages = messages[-limit:]
    return list(messages)


def _conversation_title(conversation):
    title = (conversation.get("title") or "").strip()
    if title:
        return title
    for message in conversation.get("messages", []):
        if message.get("role") == "user" and (message.get("content") or "").strip():
            return message["content"].strip()[:60]
    return "New chat"


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
                    "title": _conversation_title(conversation),
                    "created": conversation.get("created"),
                    "updated": conversation.get("updated"),
                    "message_count": len(conversation.get("messages", [])),
                }
            )
        return result


def clear_conversation(conversation_id, user_id=None):
    with _lock:
        data = _load()
        conversations = data.get("conversations", [])
        for conversation in conversations:
            if conversation.get("id") != conversation_id:
                continue
            if user_id and conversation.get("user_id") != user_id:
                return False
            conversation["messages"] = []
            conversation["title"] = ""
            conversation["updated"] = _now()
            _save(data)
            return True
    return False


def claim_anonymous_conversations(user_id):
    """Reassign legacy conversations that have no owner to the given user.

    Called once when an account is created so that pre-existing chat history
    becomes visible from the sidebar. Conversations already owned by a user
    are left untouched.
    """
    if not user_id:
        return 0

    claimed = 0
    with _lock:
        data = _load()
        for conversation in data.get("conversations", []):
            if not conversation.get("user_id") or conversation.get("user_id") == "anonymous":
                conversation["user_id"] = user_id
                claimed += 1
        if claimed:
            _save(data)

    return claimed
