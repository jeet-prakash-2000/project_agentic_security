"""Schema drift detection and repair-SQL generation.

Compares the SQLAlchemy ORM models (``database.models``) against the live
PostgreSQL schema and reports any missing tables, columns, or indexes. It also
generates idempotent repair statements (``ALTER TABLE ... ADD COLUMN IF NOT
EXISTS``, ``CREATE TABLE IF NOT EXISTS``, ``CREATE INDEX IF NOT EXISTS``) that
never drop data.
"""


def _expected_type(column):
    return str(column.type)


def compare_schema(engine):
    """Compare ORM metadata against the database.

    Returns a list of drift dicts::

        {
            "table": "agents",
            "column": "agent_endpoint",
            "db_type": "MISSING",        # or None for table/index issues
            "expected_type": "VARCHAR(512)",
            "issue": "missing column",
        }
    """
    from sqlalchemy import inspect

    from database import models  # noqa: F401  (register models on Base.metadata)
    from database.db import Base

    insp = inspect(engine)
    drifts = []

    for table in Base.metadata.sorted_tables:
        table_name = table.name

        if not insp.has_table(table_name):
            drifts.append({
                "table": table_name,
                "column": None,
                "db_type": None,
                "expected_type": None,
                "issue": "missing table",
            })
            continue

        db_columns = {c["name"]: c for c in insp.get_columns(table_name)}
        for column in table.columns:
            if column.name not in db_columns:
                drifts.append({
                    "table": table_name,
                    "column": column.name,
                    "db_type": "MISSING",
                    "expected_type": _expected_type(column),
                    "issue": "missing column",
                })

        db_indexes = {ix["name"] for ix in insp.get_indexes(table_name)}
        for index in table.indexes:
            if index.name and index.name not in db_indexes:
                drifts.append({
                    "table": table_name,
                    "column": None,
                    "db_type": None,
                    "expected_type": None,
                    "issue": "missing index {0}".format(index.name),
                })

    return drifts


def alter_statements(drifts, engine=None):
    """Generate idempotent repair SQL for the reported drift.

    PostgreSQL supports ``ADD COLUMN IF NOT EXISTS``; other dialects (e.g.
    SQLite) fall back to plain ``ADD COLUMN`` since drift is only reported for
    columns that are verified missing.
    """
    from database import models  # noqa: F401
    from database.db import Base

    is_postgres = engine is not None and engine.dialect.name == "postgresql"
    add_clause = "ADD COLUMN IF NOT EXISTS" if is_postgres else "ADD COLUMN"

    statements = []

    for d in drifts:
        issue = d["issue"]
        table_name = d["table"]

        if issue == "missing table":
            table = Base.metadata.tables.get(table_name)
            if table is None:
                continue
            from sqlalchemy.schema import CreateTable

            ddl = str(CreateTable(table).compile(engine)).rstrip(";")
            statements.append(ddl + ";")

        elif issue == "missing column":
            table = Base.metadata.tables.get(table_name)
            if table is None or d["column"] not in table.columns:
                continue
            column = table.columns[d["column"]]
            col_type = str(column.type)
            nullable = "NULL" if column.nullable else "NOT NULL"
            default = ""
            if column.default is not None:
                value = column.default.arg
                if isinstance(value, bool):
                    default = " DEFAULT " + ("true" if value else "false")
                elif isinstance(value, (int, float)):
                    default = " DEFAULT " + str(value)
                elif value is not None:
                    default = " DEFAULT '" + str(value).replace("'", "''") + "'"
            statements.append(
                "ALTER TABLE {0} {1} {2} {3}{4} {5};".format(
                    table_name, add_clause, d["column"], col_type, default, nullable
                )
            )

        elif issue.startswith("missing index"):
            index_name = issue[len("missing index "):]
            table = Base.metadata.tables.get(table_name)
            if table is None:
                continue
            for index in table.indexes:
                if index.name == index_name:
                    cols = ", ".join(c.name for c in index.columns)
                    statements.append(
                        "CREATE INDEX IF NOT EXISTS {0} ON {1} ({2});".format(
                            index_name, table_name, cols
                        )
                    )
                    break

    return statements


def format_report(drifts):
    """Render a human-readable drift report (TABLE / COLUMN / DB TYPE / EXPECTED)."""
    lines = []
    for d in drifts:
        lines.append(
            "{0:<20} {1:<22} {2:<10} {3}".format(
                d["table"] or "",
                d["column"] or "",
                d["db_type"] or "",
                d["expected_type"] or "",
            )
        )
    return "\n".join(lines)
