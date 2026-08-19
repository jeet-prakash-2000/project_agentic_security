"""Conversations and messages repository."""

from database.models import Conversation, Message
from database.repositories.base import BaseRepository


class ConversationsRepository(BaseRepository):
    model = Conversation

    def list_recent(self, user_id=None, limit=100):
        query = self.session.query(Conversation)
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        return (
            query.order_by(Conversation.updated.desc())
            .limit(limit)
            .all()
        )

    def messages(self, conversation_id, limit=None):
        query = (
            self.session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.ts.asc())
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def upsert_conversation(self, data):
        conversation = Conversation(
            id=data.get("id"),
            user_id=data.get("user_id") or "anonymous",
            title=data.get("title") or "",
            created=data.get("created"),
            updated=data.get("updated"),
        )
        return self.upsert(conversation)

    def add_message(self, conversation_id, data):
        message = Message(
            conversation_id=conversation_id,
            role=data.get("role") or "user",
            content=data.get("content") or "",
            tool=data.get("tool"),
            ts=data.get("ts"),
            meta={
                k: v
                for k, v in (data or {}).items()
                if k not in ("role", "content", "tool", "ts")
            }
            or None,
        )
        return self.add(message)
