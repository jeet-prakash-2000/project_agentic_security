"""Users service backed by the ``users`` table (formerly ``users.json``)."""

import threading
import time
import uuid

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from database.db import get_session
from database.repositories import UsersRepository

_lock = threading.Lock()


def _public(user):
    if not user:
        return None
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created": user.created,
    }


def _repo():
    return UsersRepository(get_session())


def find_by_email(email):
    return _repo().by_email(email)


def get_user(user_id):
    return _repo().get(user_id)


def public_user(user_id):
    return _public(get_user(user_id))


def create_user(name, email, password, role=None):
    name = (name or "").strip()
    email = (email or "").strip().lower()
    password = password or ""

    if not name or not email or not password:
        raise ValueError("Name, email, and password are required.")
    if "@" not in email or "." not in email:
        raise ValueError("Enter a valid email address.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")

    with _lock:
        if find_by_email(email):
            raise ValueError("An account with this email already exists.")
        user = _repo().create(
            {
                "id": "usr-" + uuid.uuid4().hex[:16],
                "name": name,
                "email": email,
                "password_hash": generate_password_hash(password),
                "role": role or "Security Administrator",
                "created": time.time(),
            }
        )

    return _public(user)


def authenticate(email, password):
    user = find_by_email(email)
    if not user:
        return None
    if not check_password_hash(user.password_hash or "", password or ""):
        return None
    return _public(user)


def list_users():
    return [_public(user) for user in _repo().list_users()]
