import json
import os
import sys
import time
from datetime import datetime

import requests

from config import settings
from config import storage

UI_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

FUNCTIONS_ROOT = os.path.abspath(
    os.path.join(UI_ROOT, "..", "netsec-agent", "functions")
)

BASELINE_PATH = os.path.join(
    FUNCTIONS_ROOT,
    "baseline",
    "baseline_rules.json"
)

EXCEL_DIR = os.path.join(
    UI_ROOT,
    "static",
    "reports"
)

EXCEL_FILE = os.path.join(
    EXCEL_DIR,
    "PaloAlto_Assessment.xlsx"
)

STATS_DOC = "assessment_stats"

if FUNCTIONS_ROOT not in sys.path:
    sys.path.insert(0, FUNCTIONS_ROOT)

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

_cache = {
    "assessment": None,
    "ts": 0.0
}


def _load_stats():
    data = storage.load_document(
        STATS_DOC,
        {"assessments_run": 0, "last_assessment_ts": None},
    )
    return data if isinstance(data, dict) else {"assessments_run": 0, "last_assessment_ts": None}


def _save_stats(stats):
    storage.save_document(STATS_DOC, stats)


def get_assessment_stats():
    return _load_stats()


def _record_assessment():
    stats = _load_stats()
    stats["assessments_run"] = int(stats.get("assessments_run", 0)) + 1
    stats["last_assessment_ts"] = time.time()
    _save_stats(stats)


def _live_assessment():

    if not settings.LIVE_ENABLED:
        return None

    try:

        response = requests.get(
            f"{settings.BASE_URL}/run_compliance_assessment",
            params={
                "code": settings.FUNCTION_KEY
            },
            timeout=settings.LIVE_TIMEOUT
        )

        if response.status_code == 200:

            payload = response.json()

            if (
                isinstance(payload, dict)
                and "summary" in payload
            ):

                return payload

        return None

    except Exception:

        return None


def _local_assessment():

    from compliance.compliance_engine import (
        ComplianceEngine
    )

    from compliance.findings_generator import (
        FindingsGenerator
    )

    from sample_assessment import (
        SAMPLE_ASSESSMENT
    )

    with open(
        BASELINE_PATH,
        "r"
    ) as handle:

        baseline = json.load(handle)

    results = (
        ComplianceEngine(baseline)
        .evaluate(SAMPLE_ASSESSMENT)
    )

    findings = (
        FindingsGenerator()
        .generate(results)
    )

    summary = {
        "total_controls":
            len(results),
        "compliant":
            len([
                r
                for r in results
                if r["status"] == "COMPLIANT"
            ]),
        "non_compliant":
            len([
                r
                for r in results
                if r["status"] == "NON_COMPLIANT"
            ]),
        "not_assessed":
            len([
                r
                for r in results
                if r["status"] == "NOT_ASSESSED"
            ])
    }

    data = dict(SAMPLE_ASSESSMENT)

    data["summary"] = summary
    data["findings"] = findings
    data["assessment"] = results

    return data


def _stamp(data, source):

    data["_source"] = source
    data["_collected_at"] = (
        datetime.utcnow().isoformat()
    )

    return data


def get_full_assessment(force=False):

    now = time.time()

    cached = _cache["assessment"]

    if (
        not force
        and cached
        and now - _cache["ts"]
        < settings.CACHE_TTL
    ):

        return cached

    data = _live_assessment()

    if data is None:

        data = _local_assessment()

        data = _stamp(
            data,
            "sample"
        )

    else:

        data = _stamp(
            data,
            "live"
        )

    _record_assessment()

    _cache["assessment"] = data
    _cache["ts"] = now

    return data


def get_summary(force=False):

    data = get_full_assessment(force)

    summary = dict(
        data.get(
            "summary",
            {}
        )
    )

    summary["source"] = (
        data.get("_source", "live")
    )

    summary["collected_at"] = (
        data.get("_collected_at")
    )

    return summary


def get_findings(force=False):

    data = get_full_assessment(force)

    return {
        "findings":
            data.get(
                "findings",
                []
            ),
        "source":
            data.get(
                "_source",
                "live"
            ),
        "collected_at":
            data.get(
                "_collected_at"
            )
    }


def get_executive_summary(force=False):

    from reports.executive_summary import (
        ExecutiveSummary
    )

    data = get_full_assessment(force)

    summary = (
        ExecutiveSummary()
        .generate(data)
    )

    summary["_source"] = (
        data.get("_source", "live")
    )

    summary["_collected_at"] = (
        data.get("_collected_at")
    )

    return summary


def get_excel_report(force=False):

    from reports.excel_report import (
        ExcelReport
    )

    data = get_full_assessment(force)

    os.makedirs(
        EXCEL_DIR,
        exist_ok=True
    )

    (
        ExcelReport()
        .generate(
            data,
            output_file=EXCEL_FILE
        )
    )

    return {
        "status":
            "SUCCESS",
        "message":
            "Excel report generated successfully.",
        "summary":
            data.get(
                "summary",
                {}
            ),
        "local_file":
            EXCEL_FILE,
        "download_url":
            "reports/PaloAlto_Assessment.xlsx",
        "_source":
            data.get(
                "_source",
                "live"
            )
    }
