"""SQLAlchemy engine and session management for the LTM Security Platform.

PostgreSQL is the single source of truth. The connection string is read from
the ``DATABASE_URL`` environment variable (configured through Azure App
Service Configuration > Application Settings), for example::

    postgresql://Jeet:<password>@ltm-security-postgres.postgres.database.azure.com:5432/ltm_security?sslmode=require

Unlike the earlier hybrid architecture there is **no JSON fallback**: the
application fails fast at startup when ``DATABASE_URL`` is missing.
"""

import contextlib
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()

Base = declarative_base()

_engine = None
_session_factory = None

ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
    "pool_size": int(os.environ.get("DB_POOL_SIZE", "5")),
    "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "10")),
}


def get_database_url():
    """Return the configured PostgreSQL connection string."""
    if DATABASE_URL:
        return DATABASE_URL
    from config import settings as platform_settings

    return (getattr(platform_settings, "DATABASE_URL", "") or "").strip()


def is_configured():
    return bool(get_database_url())


def init_engine(database_url=None, **kwargs):
    """Create (or replace) the engine. Useful for tests/overrides."""
    global _engine, _session_factory
    url = (database_url or get_database_url()).strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set the DATABASE_URL environment "
            "variable (Azure App Service > Configuration > Application Settings)."
        )
    options = dict(ENGINE_OPTIONS)
    options.update(kwargs)
    _engine = create_engine(url, **options)
    _session_factory = scoped_session(
        sessionmaker(bind=_engine, expire_on_commit=False)
    )
    return _engine


def get_engine():
    global _engine
    if _engine is None:
        init_engine()
    return _engine


def get_session():
    if _session_factory is None:
        get_engine()
    return _session_factory()


@contextlib.contextmanager
def session_scope():
    """Transactional session context manager (commits or rolls back)."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        remove_session()


def remove_session():
    if _session_factory is not None:
        _session_factory.remove()


def dispose_engine():
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def check_connection():
    """Return ``(ok, message)`` after attempting a database connection.

    Used for startup validation; never raises.
    """
    if not is_configured():
        return False, "DATABASE_URL is not configured."
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "PostgreSQL connected."
    except Exception as exc:
        return False, "PostgreSQL unavailable: {0}".format(str(exc)[:200])


def missing_tables():
    """Return the list of ORM tables that do not exist in PostgreSQL."""
    from database import models  # noqa: F401  (register models on Base.metadata)

    inspector = __import__("sqlalchemy").inspect(get_engine())
    existing = set(inspector.get_table_names())
    return [table.name for table in Base.metadata.sorted_tables if table.name not in existing]


def create_all():
    """Create any tables that are missing (never alters existing ones)."""
    from database import models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())


def drop_all():
    from database import models  # noqa: F401

    Base.metadata.drop_all(bind=get_engine())
