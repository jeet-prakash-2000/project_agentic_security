"""Findings repository (table ``findings``, per-assessment finding rows)."""

from sqlalchemy import func

from database.models import AssessmentHistory, Finding
from database.repositories.base import BaseRepository


class FindingsRepository(BaseRepository):
    model = Finding

    def for_assessment(self, assessment_id):
        return (
            self.session.query(Finding)
            .filter(Finding.assessment_id == assessment_id)
            .order_by(Finding.risk_score.desc())
            .all()
        )

    def latest_for_firewall(self, firewall_id, limit=500):
        """Findings of the most recent assessment row for a firewall.

        ``assessment_id`` on the findings rows matches ``assessment_id`` on
        ``assessment_history``; NULL/empty assessment ids are ignored.
        """
        latest = (
            self.session.query(Finding.assessment_id)
            .join(
                AssessmentHistory,
                Finding.assessment_id == AssessmentHistory.assessment_id,
            )
            .filter(Finding.firewall_name == firewall_id)
            .order_by(AssessmentHistory.executed_at.desc())
            .first()
        )
        if latest is None:
            return []
        return self.for_assessment(latest[0])[:limit]

    def replace_for_assessment(self, assessment_id, findings, firewall_name=None):
        self.session.query(Finding).filter(
            Finding.assessment_id == assessment_id
        ).delete()
        for data in findings or []:
            self.session.add(
                Finding(
                    assessment_id=assessment_id,
                    firewall_name=firewall_name or "vmpafw01",
                    control=data.get("control"),
                    status=data.get("status"),
                    risk=data.get("risk"),
                    metric=data.get("metric"),
                    observed=str(data.get("observed", "")),
                    expected=str(data.get("expected", "")),
                    finding=data.get("finding"),
                    remediation=data.get("remediation"),
                    risk_score=data.get("risk_score"),
                )
            )
        self.session.commit()

    def count_all(self):
        return self.session.query(func.count(Finding.id)).scalar() or 0
