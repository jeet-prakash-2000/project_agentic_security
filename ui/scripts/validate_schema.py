"""Pre-migration schema validation utility.

Compares the live PostgreSQL schema against the ORM models and prints a report
in the format::

    TABLE                COLUMN                 DB TYPE    EXPECTED TYPE
    agents               agent_endpoint         MISSING    VARCHAR(512)

Also prints the repair SQL needed to fix the drift.

Usage::

    export DATABASE_URL="postgresql://Jeet:<password>@ltm-security-postgres.postgres.database.azure.com:5432/ltm_security?sslmode=require"
    python scripts/validate_schema.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def main():
    from database.db import check_connection, get_engine
    from database.schema_validation import alter_statements, compare_schema

    ok, message = check_connection()
    if not ok:
        print("DATABASE_UNAVAILABLE:", message)
        return 1

    engine = get_engine()
    drifts = compare_schema(engine)

    print("SCHEMA DRIFT REPORT")
    print("=" * 72)
    print("{0:<20} {1:<24} {2:<12} {3}".format("TABLE", "MISSING COLUMN", "DB TYPE", "EXPECTED TYPE"))
    print("-" * 72)

    if not drifts:
        print("(no drift - schema matches ORM models)")
        print("=" * 72)
        return 0

    for d in drifts:
        print("{0:<20} {1:<24} {2:<12} {3}".format(
            d["table"] or "",
            d["column"] or "",
            d["db_type"] or "",
            d["expected_type"] or "",
        ))
    print("=" * 72)
    print("ISSUES FOUND:", len(drifts))

    statements = alter_statements(drifts, engine)
    if statements:
        print("\nREPAIR SQL:")
        for statement in statements:
            print(statement)

    print("\nRun: python scripts/sync_postgres_schema.py   (to apply)")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
