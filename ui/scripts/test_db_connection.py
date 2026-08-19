"""Test PostgreSQL connectivity.

Usage::

    export DATABASE_URL="postgresql://Jeet:<password>@ltm-security-postgres.postgres.database.azure.com:5432/ltm_security?sslmode=require"
    python scripts/test_db_connection.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def main():
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        print("DATABASE_URL is not set.")
        return 1

    try:
        import psycopg2

        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        print("Connected successfully.")
        print("Server:", str(version).split(" on ")[0])
        return 0
    except Exception as exc:
        print("Connection failed:", type(exc).__name__, str(exc)[:400])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
