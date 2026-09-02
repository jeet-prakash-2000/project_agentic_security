"""Assessment history and stats repository.

Tables ``assessment_history`` (one row per assessment run) and
``assessment_stats`` (single aggregate row). Replaces
``assessment_history.json`` / ``assessment_stats.json``.
"""

import time

from sqlalchemy import func

from database.models import AssessmentHistory, AssessmentStats
from database.repositories.base import BaseRepository


class AssessmentsRepository(BaseRepository):
    model = AssessmentHistory

    # -- history ------------------------------------------------------------

    def list_history(self, firewall_name=None, limit=200):
        query = self.session.query(AssessmentHistory)
        if firewall_name:
            query = query.filter(AssessmentHistory.firewall_name == firewall_name)
        return (
            query.order_by(AssessmentHistory.executed_at.asc())
            .limit(limit)
            .all()
        )

    def latest_for_firewall(self, firewall_name):
        return (
            self.session.query(AssessmentHistory)
            .filter(AssessmentHistory.firewall_name == firewall_name)
            .order_by(AssessmentHistory.executed_at.desc())
            .first()
        )

    def find_by_assessment_id(self, assessment_id):
        return (
            self.session.query(AssessmentHistory)
            .filter(AssessmentHistory.assessment_id == assessment_id)
            .first()
        )

    def count(self):
        return self.session.query(func.count(AssessmentHistory.id)).scalar() or 0

    def record(self, data, replace_recent=True):
        """Insert one history row (or update the most recent row for the same
        firewall when it was written <300s ago).

        Mirrors the JSON-era behaviour where a repeat snapshot inside a 5
        minute window replaced the previous one so repeated dashboard reads
        never inflate the trend.
        """
        firewall_name = data.get("firewall_name") or "vmpafw01"
        ts = data.get("ts") or data.get("executed_at") or time.time()
        assessment_id = data.get("assessment_id") or data.get("run_id")
        severity = data.get("severity") or {}
        finding_count = data.get("finding_count") or sum(severity.values())

        if replace_recent:
            recent = (
                self.session.query(AssessmentHistory)
                .filter(AssessmentHistory.firewall_name == firewall_name)
                .order_by(AssessmentHistory.executed_at.desc())
                .first()
            )
            if recent is not None and abs((recent.executed_at or 0) - ts) < 300:
                recent.assessment_id = assessment_id or recent.assessment_id
                recent.executed_at = ts
                recent.compliance_score = data.get("compliance_pct", recent.compliance_score)
                recent.security_score = data.get("security_score", recent.security_score)
                recent.critical_findings = int(severity.get("critical", 0))
                recent.high_findings = int(severity.get("high", 0))
                recent.medium_findings = int(severity.get("medium", 0))
                recent.low_findings = int(severity.get("low", 0))
                recent.total_findings = int(finding_count or 0)
                self.session.commit()
                return recent

        entry = AssessmentHistory(
            firewall_name=firewall_name,
            assessment_id=assessment_id,
            executed_at=ts,
            compliance_score=data.get("compliance_pct"),
            security_score=data.get("security_score"),
            critical_findings=int(severity.get("critical", 0)),
            high_findings=int(severity.get("high", 0)),
            medium_findings=int(severity.get("medium", 0)),
            low_findings=int(severity.get("low", 0)),
            total_findings=int(finding_count or 0),
            status="Completed",
            control_count=int(data.get("control_count", 0) or 0),
            payload=data.get("payload"),
        )
        self.session.add(entry)
        self.session.commit()
        return entry

    def compliance_trend(self, limit=30):
        """Return history rows ordered by time (chart data source)."""
        rows = (
            self.session.query(AssessmentHistory)
            .order_by(AssessmentHistory.executed_at.asc())
            .limit(limit)
            .all()
        )
        return rows

    # -- stats --------------------------------------------------------------

    def stats(self):
        return self.session.get(AssessmentStats, 1)

    def ensure_stats(self):
        row = self.session.get(AssessmentStats, 1)
        if row is None:
            row = AssessmentStats(id=1, assessments_run=0, last_assessment_ts=None)
            self.session.add(row)
            self.session.commit()
        return row

    def increment_run(self):
        row = self.ensure_stats()
        row.assessments_run = int(row.assessments_run or 0) + 1
        row.last_assessment_ts = time.time()
        self.session.commit()
        return row

    def stats_as_dict(self):
        row = self.ensure_stats()
        return {
            "assessments_run": int(row.assessments_run or 0),
            "last_assessment_ts": row.last_assessment_ts,
        }

    # -- seeding ------------------------------------------------------------

    def seed_history(self, rows):
        """Insert seed/demo snapshot rows when the table is empty."""
        if self.count() > 0:
            return 0
        for data in rows:
            self.record(
                {
                    "run_id": data.get("run_id"),
                    "ts": data.get("ts"),
                    "compliance_pct": data.get("compliance_pct"),
                    "security_score": data.get("security_score"),
                    "severity": data.get("severity"),
                    "finding_count": data.get("finding_count"),
                    "firewall_name": data.get("firewall_name", "vmpafw01"),
                },
                replace_recent=False,
            )
        return len(rows)
