"""Conversations and messages repository.

Tables ``conversations`` + ``messages`` (formerly ``sessions.json``). Messages
are immutable rows ordered by timestamp; ``meta`` (JSON) preserves the rich
per-message payload the UI expects (tool, usage, html, cardTitle, ...).
"""

import time

from sqlalchemy import func, or_

from database.models import Conversation, Message
from database.repositories.base import BaseRepository


class ConversationsRepository(BaseRepository):
    model = Conversation

    # -- conversations ------------------------------------------------------

    def list_recent(self, user_id=None, limit=100):
        query = self.session.query(Conversation)
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        return (
            query.order_by(Conversation.updated.desc())
            .limit(limit)
            .all()
        )

    def message_count_for(self, conversation_id):
        return (
            self.session.query(func.count(Message.id))
            .filter(Message.conversation_id == conversation_id)
            .scalar()
            or 0
        )

    def message_counts(self, conversation_ids):
        if not conversation_ids:
            return {}
        rows = (
            self.session.query(
                Message.conversation_id, func.count(Message.id)
            )
            .filter(Message.conversation_id.in_(conversation_ids))
            .group_by(Message.conversation_id)
            .all()
        )
        return dict(rows)

    def create_conversation(self, conversation_id, user_id="anonymous", created=None):
        now = created if created is not None else time.time()
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id or "anonymous",
            title="",
            created=now,
            updated=now,
        )
        self.session.add(conversation)
        self.session.commit()
        return conversation

    def touch(self, conversation_id, title=None):
        conversation = self.session.get(Conversation, conversation_id)
        if conversation is None:
            return None
        if title is not None:
            conversation.title = title
        conversation.updated = time.time()
        self.session.commit()
        return conversation

    def clear_messages(self, conversation_id):
        conversation = self.session.get(Conversation, conversation_id)
        if conversation is None:
            return None
        self.session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).delete()
        conversation.title = ""
        conversation.updated = time.time()
        self.session.commit()
        return conversation

    def claim_anonymous(self, user_id, legacy=("anonymous", "demo")):
        if not user_id:
            return 0
        result = (
            self.session.query(Conversation)
            .filter(
                or_(
                    Conversation.user_id.is_(None),
                    Conversation.user_id.in_(list(legacy)),
                )
            )
            .update({Conversation.user_id: user_id}, synchronize_session=False)
        )
        self.session.commit()
        return int(result or 0)

    # -- messages -----------------------------------------------------------

    def messages(self, conversation_id, limit=None):
        query = (
            self.session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.ts.asc(), Message.id.asc())
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def add_message(self, conversation_id, data):
        meta = {
            k: v
            for k, v in (data or {}).items()
            if k not in ("role", "content", "ts")
        }
        message = Message(
            conversation_id=conversation_id,
            role=data.get("role") or "user",
            content=data.get("content") or "",
            tool=meta.pop("tool", None),
            ts=data.get("ts"),
            meta=meta or None,
        )
        self.session.add(message)
        self.session.commit()
        return message

    def _last_user_content(self, conversation_id):
        message = (
            self.session.query(Message.content)
            .filter(
                Message.conversation_id == conversation_id,
                Message.role == "user",
            )
            .order_by(Message.ts.desc())
            .first()
        )
        return message[0] if message else None

    def infer_title(self, conversation):
        title = (conversation.title or "").strip()
        if title:
            return title
        content = self._last_user_content(conversation.id)
        if content and content.strip():
            return content.strip()[:60]
        return "New chat"
