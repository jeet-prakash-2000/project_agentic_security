"""Conversation session manager backed by PostgreSQL.

Tables ``conversations`` + ``messages`` replace ``sessions.json``. The public
API is unchanged so routes and the UI behave exactly as before:

* get_or_create / get_conversation return a conversation dict
* messages keep their rich per-message payload (tool/usage/html/cardTitle ...)
  preserved in the ``meta`` JSONB column
"""

import threading
import time
import uuid

from database.db import get_session
from database.repositories import ConversationsRepository

_lock = threading.Lock()

MAX_CONVERSATIONS = 100
MAX_MESSAGES = 50


def _repo():
    return ConversationsRepository(get_session())


def _now():
    return time.time()


def _conversation_dict(repo, conversation):
    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "title": conversation.title or "",
        "created": conversation.created,
        "updated": conversation.updated,
        "messages": [
            _message_dict(message)
            for message in repo.messages(conversation.id)
        ],
    }


def _message_dict(message):
    meta = dict(message.meta or {})
    if message.tool:
        meta["tool"] = message.tool
    meta["role"] = message.role
    meta["content"] = message.content or ""
    meta["ts"] = message.ts
    return meta


def get_or_create(conversation_id, user_id="anonymous"):
    conversation_id = conversation_id or "conv-" + uuid.uuid4().hex[:12]

    with _lock:
        repo = _repo()
        conversation = repo.get(conversation_id)
        if conversation is None:
            conversation = repo.create_conversation(conversation_id, user_id)

    return _conversation_dict(repo, conversation)


def _ensure_conversation(repo, conversation_id, user_id, now):
    conversation = repo.get(conversation_id)
    if conversation is None:
        conversation = repo.create_conversation(
            conversation_id, user_id or "anonymous", created=now
        )
    return conversation


def _trim_messages(repo, conversation_id, keep=MAX_MESSAGES):
    messages = repo.messages(conversation_id)
    if len(messages) > keep:
        for stale in messages[:-keep]:
            repo.delete(stale)


def _set_title(repo, conversation, role, content):
    if role == "user" and not (conversation.title or "").strip():
        repo.touch(conversation.id, title=(content or "").strip()[:60])
    else:
        repo.touch(conversation.id)


def _can_append(conversation, user_id=None):
    """True when ``user_id`` may keep writing into this conversation.

    A real (signed-in) account may only write to its own conversations.
    Anonymous/legacy placeholders may continue ownerless history only.
    """
    owner = conversation.user_id
    if user_id and user_id != "anonymous":
        return owner == user_id
    return owner in (None, "anonymous", "demo")


def add_message(conversation_id, role, content, user_id="anonymous", meta=None):
    now = _now()
    conversation_id = conversation_id or "conv-" + uuid.uuid4().hex[:12]

    with _lock:
        repo = _repo()
        conversation = _ensure_conversation(repo, conversation_id, user_id, now)
        if not _can_append(conversation, user_id):
            return None

        message = dict(meta or {})
        message["role"] = role
        message["content"] = content or ""
        message["ts"] = message.get("ts") or now

        repo.add_message(conversation_id, message)
        _set_title(repo, conversation, role, content)
        _trim_messages(repo, conversation_id)

    return conversation_id


def add_messages(conversation_id, messages, user_id="anonymous"):
    """Bulk-append full message metadata supplied by the client.

    Returns the conversation id, or ``None`` when the conversation belongs to
    another account (nothing is written).
    """
    now = _now()
    conversation_id = conversation_id or "conv-" + uuid.uuid4().hex[:12]
    messages = messages or []

    with _lock:
        repo = _repo()
        existing = repo.get(conversation_id)
        if existing is not None:
            if not _can_append(existing, user_id):
                return None
            conversation = existing
        else:
            conversation = _ensure_conversation(repo, conversation_id, user_id, now)

        for item in messages:
            if not isinstance(item, dict):
                continue
            role = item.get("role") or "user"
            message = {
                k: v
                for k, v in item.items()
                if k not in ("role", "content")
            }
            message["role"] = role
            message["content"] = item.get("content") or ""
            message["ts"] = message.get("ts") or now
            repo.add_message(conversation_id, message)
            _set_title(repo, conversation, role, item.get("content"))

        _trim_messages(repo, conversation_id)

    return conversation_id


def get_conversation(conversation_id, user_id=None):
    repo = _repo()
    conversation = repo.get(conversation_id)
    if conversation is None:
        return None
    if user_id and user_id != "anonymous" and conversation.user_id != user_id:
        return None
    return _conversation_dict(repo, conversation)


def owns_conversation(conversation_id, user_id=None):
    """True when the caller may read this conversation."""
    conversation = _repo().get(conversation_id)
    if conversation is None:
        return False
    return _can_append(conversation, user_id)


def get_messages(conversation_id, limit=None, user_id=None):
    conversation = get_conversation(conversation_id, user_id=user_id)
    if not conversation:
        return []
    messages = conversation.get("messages", [])
    if limit:
        messages = messages[-limit:]
    return list(messages)


def list_conversations(user_id=None):
    repo = _repo()
    conversations = repo.list_recent(user_id=user_id)
    ids = [conversation.id for conversation in conversations]
    counts = repo.message_counts(ids)

    result = []
    for conversation in conversations:
        result.append(
            {
                "id": conversation.id,
                "user_id": conversation.user_id,
                "title": repo.infer_title(conversation),
                "created": conversation.created,
                "updated": conversation.updated,
                "message_count": int(counts.get(conversation.id, 0) or 0),
            }
        )

    result.sort(
        key=lambda c: c.get("updated") or 0,
        reverse=True,
    )
    return result[:MAX_CONVERSATIONS]


def clear_conversation(conversation_id, user_id=None):
    with _lock:
        repo = _repo()
        conversation = repo.get(conversation_id)
        if conversation is None:
            return False
        if user_id and conversation.user_id != user_id:
            return False
        repo.clear_messages(conversation_id)
        return True


def truncate_conversation(conversation_id, keep, user_id=None):
    """Drop trailing messages so the newest ``keep`` rows remain."""
    with _lock:
        repo = _repo()
        conversation = repo.get(conversation_id)
        if conversation is None:
            return False
        if user_id and conversation.user_id != user_id:
            return False
        removed = repo.truncate_messages(conversation_id, keep)
        return removed is not None


def claim_anonymous_conversations(user_id):
    """Reassign legacy conversations that have no owner to the given user.

    Called once when an account is created so that pre-existing chat history
    becomes visible from the sidebar. Conversations already owned by a user
    are left untouched.
    """
    if not user_id:
        return 0
    return _repo().claim_anonymous(user_id)
