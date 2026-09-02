"""Report history service backed by ``reports_history`` (formerly reports_history.json)."""

import time

from database.db import get_session
from database.repositories import ReportsRepository

DEMO_REPORTS = [
    {
        "name": "Assessment_Workbook_Aug_2026",
        "type": "Workbook",
        "generated_by": "Firewall Auditor",
        "ts": None,
        "status": "Completed",
        "size": "2.4 MB",
        "download_url": "reports/PaloAlto_Assessment.xlsx",
    },
    {
        "name": "Executive_Summary_Aug_2026",
        "type": "Executive Summary",
        "generated_by": "Firewall Auditor",
        "ts": None,
        "status": "Completed",
        "size": "184 KB",
        "download_url": None,
    },
    {
        "name": "Executive_Summary_Jul_2026",
        "type": "Executive Summary",
        "generated_by": "Firewall Auditor",
        "ts": None,
        "status": "Failed",
        "size": None,
        "download_url": None,
    },
]


def _repo():
    return ReportsRepository(get_session())


def append_report(report):
    _repo().append_report(report)


def _seed_demo():
    if _repo().count() > 0:
        return
    now = time.time()
    offsets = (5 * 86400, 6 * 86400, 30 * 86400)
    for index, report in enumerate(DEMO_REPORTS):
        _repo().append_report(
            {
                "name": report["name"],
                "type": report["type"],
                "generated_by": report["generated_by"],
                "ts": now - offsets[index],
                "status": report["status"],
                "size": report["size"],
                "download_url": report["download_url"],
            }
        )


def list_reports():
    _seed_demo()
    reports = _repo().list_reports()
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
