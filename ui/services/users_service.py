import threading
import time
import uuid

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from config import storage

USERS_DOC = "users"

_lock = threading.Lock()


def _load():
    data = storage.load_document(USERS_DOC, {"users": []})
    if not isinstance(data, dict):
        return {"users": []}
    if not isinstance(data.get("users"), list):
        data["users"] = []
    return data


def _save(data):
    storage.save_document(USERS_DOC, data)


def _public(user):
    if not user:
        return None
    return {
        "id": user.get("id", ""),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "Security Administrator"),
        "created": user.get("created"),
    }


def find_by_email(email):
    email = (email or "").strip().lower()
    for user in _load().get("users", []):
        if (user.get("email") or "").lower() == email:
            return user
    return None


def get_user(user_id):
    for user in _load().get("users", []):
        if user.get("id") == user_id:
            return user
    return None


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
        data = _load()
        user = {
            "id": "usr-" + uuid.uuid4().hex[:16],
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "role": role or "Security Administrator",
            "created": time.time(),
        }
        data.setdefault("users", []).insert(0, user)
        _save(data)

    return _public(user)


def authenticate(email, password):
    user = find_by_email(email)
    if not user:
        return None
    if not check_password_hash(user.get("password_hash", ""), password or ""):
        return None
    return _public(user)


def list_users():
    return [_public(u) for u in _load().get("users", [])]
