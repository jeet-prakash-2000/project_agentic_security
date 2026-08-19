"""Reports history repository."""

from database.models import ReportHistory
from database.repositories.base import BaseRepository


class ReportsRepository(BaseRepository):
    model = ReportHistory

    def recent(self, limit=100):
        return (
            self.session.query(ReportHistory)
            .order_by(ReportHistory.ts.desc())
            .limit(limit)
            .all()
        )

    def append_report(self, data):
        report = ReportHistory(
            name=data.get("name"),
            type=data.get("type"),
            generated_by=data.get("generated_by"),
            ts=data.get("ts"),
            status=data.get("status") or "Completed",
            size=data.get("size"),
            download_url=data.get("download_url"),
        )
        return self.add(report)
