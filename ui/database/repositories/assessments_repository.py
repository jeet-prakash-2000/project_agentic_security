"""Assessment history and stats repository."""

from database.models import AssessmentHistory, AssessmentStats
from database.repositories.base import BaseRepository


class AssessmentsRepository(BaseRepository):
    model = AssessmentHistory

    def compliance_trend(self, limit=30):
        """Return (executed_at, compliance_score) ordered by time.

        This is the data source for the Compliance Trend chart.
        """
        rows = (
            self.session.query(
                AssessmentHistory.executed_at,
                AssessmentHistory.compliance_score,
                AssessmentHistory.security_score,
                AssessmentHistory.assessment_id,
            )
            .order_by(AssessmentHistory.executed_at.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "executed_at": row.executed_at,
                "compliance_score": row.compliance_score,
                "security_score": row.security_score,
                "assessment_id": row.assessment_id,
            }
            for row in rows
        ]

    def record(self, data):
        entry = AssessmentHistory(
            assessment_id=data.get("assessment_id")
            or data.get("run_id"),
            executed_at=data.get("executed_at")
            or data.get("ts"),
            compliance_score=data.get("compliance_score")
            or data.get("compliance_pct"),
            security_score=data.get("security_score"),
            critical_findings=(
                (data.get("severity") or {}).get("critical", 0)
            ),
            high_findings=(data.get("severity") or {}).get("high", 0),
            medium_findings=(data.get("severity") or {}).get("medium", 0),
            low_findings=(data.get("severity") or {}).get("low", 0),
            total_findings=data.get("finding_count")
            or sum((data.get("severity") or {}).values()),
        )
        return self.add(entry)

    def stats(self):
        return self.session.query(AssessmentStats).get(1)

    def upsert_stats(self, data):
        stats = AssessmentStats(
            id=1,
            assessments_run=data.get("assessments_run") or 0,
            last_assessment_ts=data.get("last_assessment_ts"),
        )
        return self.upsert(stats)
