"""One-time bootstrap for the multi-tenant user model.

Runs after schema reconciliation at startup and is idempotent:

* Seeds the primary administrator (``Jeet Prakash``) when it does not exist.
* Reclaims data created before multi-tenancy (conversations, insights and
  reports without an owner or owned by the legacy ``anonymous``/``demo``
  placeholders) and binds it to the seeded administrator so historical work
  stays visible without ever being visible to newly registered accounts.
"""

import logging
import time

from werkzeug.security import generate_password_hash

from database.db import get_session
from database.repositories import (
    ConversationsRepository,
    InsightsRepository,
    ReportsRepository,
    UsersRepository,
)

log = logging.getLogger("bootstrap")

ADMIN_USER_ID = "usr-admin"
ADMIN_NAME = "Jeet Prakash"
ADMIN_EMAIL = "jeet.prakashparaida@ltm.com"
ADMIN_PASSWORD = "Jeet@12345"
ADMIN_ROLE = "Admin"

# Legacy owner markers used before real user accounts existed.
LEGACY_OWNERS = ("anonymous", "demo")


def ensure_admin_user():
    """Create the seeded administrator account (idempotent)."""
    from services import users_service

    existing = users_service.find_by_email(ADMIN_EMAIL)
    if existing is not None:
        changed = False
        if (existing.role or "") not in users_service.ADMIN_ROLES:
            users_service.set_role(existing.id, ADMIN_ROLE)
            changed = True
        if (existing.status or "approved") != "approved":
            users_service.set_status(existing.id, "approved")
            changed = True
        return existing.id if not changed else existing.id

    repo = UsersRepository(get_session())
    user = repo.create(
        {
            "id": ADMIN_USER_ID,
            "name": ADMIN_NAME,
            "email": ADMIN_EMAIL,
            "password_hash": generate_password_hash(ADMIN_PASSWORD),
            "role": ADMIN_ROLE,
            "status": "approved",
            "created": time.time(),
        }
    )
    log.info("Seeded administrator account %s (%s).", user.id, user.email)
    return user.id


def reclaim_legacy_data(user_id):
    """Reassign pre-multi-tenancy data to the given user.

    Returns a dict of how many rows were reclaimed per table.
    """
    if not user_id:
        return {}
    counts = {}
    try:
        counts["conversations"] = ConversationsRepository(
            get_session()
        ).claim_anonymous(user_id, legacy=LEGACY_OWNERS)
    except Exception as exc:
        log.warning("Conversation legacy reclaim failed: %s", exc)
    try:
        counts["insights"] = InsightsRepository(get_session()).claim_legacy(
            user_id, legacy=LEGACY_OWNERS
        )
    except Exception as exc:
        log.warning("Insights legacy reclaim failed: %s", exc)
    try:
        counts["reports"] = ReportsRepository(get_session()).claim_legacy(
            user_id, legacy=LEGACY_OWNERS
        )
    except Exception as exc:
        log.warning("Reports legacy reclaim failed: %s", exc)
    return counts


def run_bootstrap():
    """Seed the administrator and reclaim legacy rows. Never raises."""
    try:
        admin_id = ensure_admin_user()
    except Exception as exc:
        log.warning("Admin seed failed: %s", exc)
        return

    try:
        counts = reclaim_legacy_data(admin_id)
    except Exception as exc:
        log.warning("Legacy data reclaim failed: %s", exc)
        return

    if any(counts.values()):
        log.info("Legacy data reclaimed to %s: %s", admin_id, counts)
