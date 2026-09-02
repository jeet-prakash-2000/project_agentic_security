"""Repository classes for PostgreSQL persistence.

Repositories are the only sanctioned data-access layer for services,
gateways and function apps. Each repository wraps a SQLAlchemy session.
"""

from database.repositories.agents_repository import AgentsRepository
from database.repositories.assessments_repository import AssessmentsRepository
from database.repositories.conversations_repository import ConversationsRepository
from database.repositories.findings_repository import FindingsRepository
from database.repositories.insights_repository import InsightsRepository
from database.repositories.reports_repository import ReportsRepository
from database.repositories.telemetry_repository import TelemetryRepository
from database.repositories.users_repository import UsersRepository

__all__ = [
    "AgentsRepository",
    "AssessmentsRepository",
    "ConversationsRepository",
    "FindingsRepository",
    "InsightsRepository",
    "ReportsRepository",
    "TelemetryRepository",
    "UsersRepository",
]
