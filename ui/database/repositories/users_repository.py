"""Users repository (table ``users``, formerly ``users.json``)."""

from database.models import User
from database.repositories.base import BaseRepository


class UsersRepository(BaseRepository):
    model = User

    def by_email(self, email):
        email = (email or "").strip().lower()
        return (
            self.session.query(User)
            .filter(User.email == email)
            .first()
        )

    def list_users(self):
        return (
            self.session.query(User)
            .order_by(User.created.desc())
            .all()
        )

    def create(self, data):
        user = User(
            id=data.get("id"),
            name=data.get("name"),
            email=(data.get("email") or "").strip().lower(),
            password_hash=data.get("password_hash"),
            role=data.get("role") or "Security Administrator",
            created=data.get("created"),
        )
        self.session.add(user)
        self.session.commit()
        return user
