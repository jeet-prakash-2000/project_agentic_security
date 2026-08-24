"""Synchronize the PostgreSQL schema with the SQLAlchemy ORM models.

Connects to PostgreSQL, inspects the live schema, adds missing tables, columns,
and indexes. Never drops data. Run with ``--dry-run`` to only print the repair
SQL without applying it.

Usage::

    export DATABASE_URL="postgresql://Jeet:<password>@ltm-security-postgres.postgres.database.azure.com:5432/ltm_security?sslmode=require"
    python scripts/sync_postgres_schema.py            # apply
    python scripts/sync_postgres_schema.py --dry-run  # print only
"""

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("schema-sync")


def sync_schema(dry_run=False):
    from sqlalchemy import text

    from database import models  # noqa: F401
    from database.db import Base, create_all, get_engine
    from database.schema_validation import alter_statements, compare_schema

    engine = get_engine()

    # 1. Create any missing tables (never alters existing ones).
    create_all()

    # 2. Detect remaining drift (missing columns / indexes).
    drifts = compare_schema(engine)

    if not drifts:
        log.info("Schema is in sync - no drift detected.")
        return drifts, []

    log.info("Detected %s schema issue(s).", len(drifts))
    for d in drifts:
        log.info("  %s: %s", d["table"], d["issue"])

    statements = alter_statements(drifts, engine)

    if dry_run:
        log.info("DRY RUN - repair SQL not applied:")
        print("\n".join(statements))
        return drifts, statements

    with engine.begin() as conn:
        for statement in statements:
            log.info("Applying: %s", statement[:80])
            conn.execute(text(statement))

    log.info("Schema synchronized. %s statement(s) applied.", len(statements))
    return drifts, statements


def main():
    parser = argparse.ArgumentParser(description="Sync PostgreSQL schema with ORM models")
    parser.add_argument("--dry-run", action="store_true", help="Print repair SQL without applying")
    args = parser.parse_args()

    from database.db import check_connection

    ok, message = check_connection()
    if not ok:
        log.error("DATABASE_UNAVAILABLE: %s", message)
        return 1

    try:
        sync_schema(dry_run=args.dry_run)
    except Exception as exc:
        log.error("Schema sync failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
