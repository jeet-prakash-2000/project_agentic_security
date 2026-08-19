"""Findings repository (per-assessment finding detail)."""

from database.models import Finding
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

    def replace_for_assessment(self, assessment_id, findings):
        self.session.query(Finding).filter(
            Finding.assessment_id == assessment_id
        ).delete()
        for data in findings or []:
            self.session.add(
                Finding(
                    assessment_id=assessment_id,
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
