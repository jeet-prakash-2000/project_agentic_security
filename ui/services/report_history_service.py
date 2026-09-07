"""Report history service backed by ``reports_history`` (formerly reports_history.json).

Report rows are owned by a user (``user_id``) so history is never shared
between accounts. Legacy rows created before multi-tenancy are reclaimed to
the seeded administrator at startup.
"""

from database.db import get_session
from database.repositories import ReportsRepository


def _repo():
    return ReportsRepository(get_session())


def append_report(report, user_id=None):
    _repo().append_report(report, user_id=user_id)


def list_reports(user_id=None):
    reports = _repo().list_reports(user_id=user_id)
    return [
        {
            "name": report.name,
            "type": report.type,
            "generated_by": report.generated_by,
            "ts": report.ts,
            "status": report.status,
            "size": report.size,
            "download_url": report.download_url,
        }
        for report in reports
    ]
