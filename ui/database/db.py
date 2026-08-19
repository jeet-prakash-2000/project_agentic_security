"""SQLAlchemy engine and session management for the LTM Security Platform.

The PostgreSQL connection string is read from the ``DATABASE_URL`` environment
variable, e.g.::

    postgresql://Jeet:<password>@ltm-security-postgres.postgres.database.azure.com:5432/ltm_security?sslmode=require

When ``DATABASE_URL`` is not set, the database layer is inactive and the
application continues to use its JSON-file storage (see ``config/storage.py``).
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()

Base = declarative_base()

_engine = None
_session_factory = None


def is_configured():
    return bool(DATABASE_URL)


def get_engine():
    global _engine
    if _engine is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not configured.")
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=280,
        )
    return _engine


def get_session():
    global _session_factory
    if _session_factory is None:
        _session_factory = scoped_session(
            sessionmaker(bind=get_engine(), expire_on_commit=False)
        )
    return _session_factory()


def remove_session():
    if _session_factory is not None:
        _session_factory.remove()


def create_all():
    # Import models so they register with the metadata before creating tables.
    from database import models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())


def drop_all():
    from database import models  # noqa: F401

    Base.metadata.drop_all(bind=get_engine())
