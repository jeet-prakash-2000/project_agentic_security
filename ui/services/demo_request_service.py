"""Demo request lead capture for the public landing page."""

import threading
import time

from database.db import get_session
from database.repositories import DemoRequestsRepository

_lock = threading.Lock()

VALID_ROLES = (
    "Security / SOC Analyst",
    "Compliance / Audit",
    "Cloud / Infrastructure",
    "Security Leadership",
    "Executive",
    "Other",
)


def _public(lead):
    if not lead:
        return None
    return {
        "id": lead.id,
        "name": lead.name,
        "email": lead.email,
        "company": lead.company,
        "role": lead.role,
        "message": lead.message,
        "status": lead.status or "new",
        "created": lead.created,
    }


def _repo():
    return DemoRequestsRepository(get_session())


def create_lead(name, email, company, role, message):
    name = (name or "").strip()
    email = (email or "").strip().lower()
    company = (company or "").strip()
    role = (role or "").strip() or "Other"
    message = (message or "").strip()

    if not name or not email or not message:
        raise ValueError("Name, email, and a short message are required.")
    if "@" not in email or "." not in email:
        raise ValueError("Enter a valid work email address.")
    if len(name) > 255 or len(email) > 255:
        raise ValueError("Name and email are too long.")
    if len(message) > 4000:
        raise ValueError("Please keep your message under 4000 characters.")

    with _lock:
        lead = _repo().create(
            {
                "name": name,
                "email": email,
                "company": company[:255],
                "role": role if role in VALID_ROLES else "Other",
                "message": message,
                "status": "new",
                "created": time.time(),
            }
        )

    return _public(lead)


def list_leads(limit=200):
    return [_public(lead) for lead in _repo().list_leads(limit=limit)]
