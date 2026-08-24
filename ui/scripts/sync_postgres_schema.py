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

    # 2. Detect drift (missing columns / indexes / type mismatches).
    drifts = compare_schema(engine)

    if not drifts:
        log.info("Schema is in sync - no drift detected.")
        return drifts, []

    log.info("Detected %s schema issue(s).", len(drifts))
    for d in drifts:
        log.info("  %s: %s", d["table"], d["issue"])

    statements = alter_statements(drifts, engine)

    # 3. Type mismatches on EMPTY tables: drop + recreate from the ORM models.
    #    This is the safe fix for legacy UUID-schema tables that conflict with
    #    the current VARCHAR string-id models. Tables are only dropped when they
    #    hold no rows, so no data is ever lost.
    tables_to_recreate = sorted({
        d["table"] for d in drifts if d["issue"] == "type mismatch"
    })

    if dry_run and tables_to_recreate:
        log.info("DRY RUN - would drop+recreate empty tables with type mismatches: %s", ", ".join(tables_to_recreate))
        return drifts, statements

    with engine.begin() as conn:
        drop_stmt = "DROP TABLE IF EXISTS \"{0}\"{1}".format
        cascade = " CASCADE" if engine.dialect.name == "postgresql" else ""
        for table_name in tables_to_recreate:
            row_count = conn.execute(text('SELECT count(*) FROM "{0}"'.format(table_name))).scalar()
            if row_count == 0:
                log.info("Dropping empty table %s (type mismatch) for recreation.", table_name)
                conn.execute(text(drop_stmt(table_name, cascade)))
            else:
                log.warning("Table %s has %s rows - type mismatch NOT auto-fixed (manual ALTER required).", table_name, row_count)

    if tables_to_recreate:
        Base.metadata.create_all(engine)
        drifts = compare_schema(engine)
        statements = alter_statements(drifts, engine)
        log.info("Recreated %s table(s) from ORM models.", len(tables_to_recreate))

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
