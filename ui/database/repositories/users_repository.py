"""Users repository."""

from database.models import User
from database.repositories.base import BaseRepository


class UsersRepository(BaseRepository):
    model = User

    def by_email(self, email):
        return (
            self.session.query(User)
            .filter(User.email == email)
            .first()
        )

    def upsert_from_dict(self, data):
        user = User(
            id=data.get("id"),
            name=data.get("name"),
            email=data.get("email"),
            password_hash=data.get("password_hash"),
            role=data.get("role") or "Security Analyst",
            created=data.get("created"),
        )
        return self.upsert(user)
