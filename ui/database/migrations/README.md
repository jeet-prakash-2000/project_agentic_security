# Database Migrations

The LTM Security Platform persists data in PostgreSQL (via SQLAlchemy) when the
`DATABASE_URL` environment variable is set.

## Schema creation

The schema is created from the SQLAlchemy models in `database/models.py`:

```bash
cd ui
export DATABASE_URL="postgresql://Jeet:<password>@ltm-security-postgres.postgres.database.azure.com:5432/ltm_security?sslmode=require"
python -c "from database.db import create_all; create_all()"
```

This creates the following tables:

| Table               | Source JSON document      |
|---------------------|---------------------------|
| `users`             | `config/users.json`       |
| `agents`            | `config/agents.json`      |
| `conversations`     | `config/sessions.json`    |
| `messages`          | `config/sessions.json`    |
| `insights`          | `config/insights.json`    |
| `reports_history`   | `config/reports_history.json` |
| `assessment_history`| `config/assessment_history.json` |
| `assessment_stats`  | `config/assessment_stats.json` |
| `telemetry_metrics` | `config/telemetry_metrics.json` |
| `telemetry_history` | `config/telemetry_history.json` |
| `findings`          | (per-assessment findings) |

## One-time data migration

Migrate the existing JSON documents into PostgreSQL:

```bash
cd ui
python scripts/migrate_json_to_postgres.py
```

The script is idempotent and migrates in dependency order (users/agents first,
then conversations + messages, then the remaining documents).

## Compliance trend from SQL

Every assessment run is written to `assessment_history` (see
`services/assessment_service.py`). The chart can read directly from:

```sql
SELECT executed_at, compliance_score
FROM assessment_history
ORDER BY executed_at;
```

## Alembic (optional)

`alembic` is included in `requirements.txt` for future schema evolution. To
initialise it:

```bash
cd ui
alembic init -t generic database/migrations
```

Then point `alembic.ini` `sqlalchemy.url` at `DATABASE_URL` and autogenerate an
initial revision against `database/models.py`.
