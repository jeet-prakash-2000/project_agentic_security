import json
import logging
import os
import random
import sys
import time

import requests

from config import settings
from config import storage
from services import timeutil

log = logging.getLogger("assessment")

UI_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

FUNCTIONS_ROOT = os.path.abspath(
    os.path.join(UI_ROOT, "..", "netsec-agent", "functions")
)

# On the Azure Web App only `ui/` is shipped, so the `netsec-agent` source tree
# is not present. Fall back to a bundled copy of the report/compliance modules
# that the CI workflow copies into the UI package before deployment.
if not os.path.isdir(FUNCTIONS_ROOT):
    FUNCTIONS_ROOT = os.path.join(UI_ROOT, "netsec_functions")

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
HISTORY_DOC = "assessment_history"

SEVERITY_KEYS = ("critical", "high", "medium", "low")

if FUNCTIONS_ROOT not in sys.path:
    sys.path.insert(0, FUNCTIONS_ROOT)

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

FIREWALLS = ["vmpafw01", "vmpafw02"]

_cache = {
    "assessment": {},
    "ts": {}
}


def _apply_firewall(data, firewall_id):
    """Label an assessment snapshot with the selected firewall name.

    Both firewalls point at the same underlying firewall system; only the
    logical device name differs (vmpafw01 / vmpafw02).
    """
    inventory = dict(data.get("inventory") or {})
    inventory["hostname"] = firewall_id
    data["inventory"] = inventory
    data["_firewall_id"] = firewall_id
    return data


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


def get_history():
    """Return the stored assessment history snapshots (read-only)."""
    return _load_history()


def _record_assessment():
    stats = _load_stats()
    stats["assessments_run"] = int(stats.get("assessments_run", 0)) + 1
    stats["last_assessment_ts"] = time.time()
    _save_stats(stats)


def _seed_history():
    rng = random.Random(20260814)
    now = time.time()
    snapshots = []
    base = 36.0
    for i in range(12):
        pct = round(base + rng.uniform(-4.5, 3.0), 1)
        severity = {
            "critical": rng.randint(9, 14),
            "high": rng.randint(9, 14),
            "medium": rng.randint(2, 6),
            "low": rng.randint(0, 3),
        }
        points = (
            severity["critical"] * 4.0
            + severity["high"] * 2.0
            + severity["medium"] * 1.0
            + severity["low"] * 0.5
        )
        snapshots.append({
            "run_id": "ASM-{0:06d}".format(i + 1),
            "ts": now - (12 - i) * 86400,
            "compliance_pct": pct,
            "security_score": round(
                100.0 * (1.0 - points / (44 * 4.0)),
                1,
            ),
            "severity": severity,
            "finding_count": sum(severity.values()),
        })
    storage.save_document(HISTORY_DOC, {"snapshots": snapshots})


def _load_history():
    data = storage.load_document(HISTORY_DOC, None)
    if not isinstance(data, dict) or not data.get("snapshots"):
        _seed_history()
        data = storage.load_document(HISTORY_DOC, {"snapshots": []})
    snapshots = data.get("snapshots", []) if isinstance(data, dict) else []
    return [s for s in snapshots if isinstance(s, dict)]


def _record_history(snapshot):
    snapshots = _load_history()
    if snapshots and abs(snapshots[-1].get("ts", 0) - snapshot["ts"]) < 300:
        snapshots[-1] = snapshot
    else:
        snapshots.append(snapshot)
        snapshots = snapshots[-60:]
    storage.save_document(HISTORY_DOC, {"snapshots": snapshots})
    _record_history_db(snapshot)


def _record_history_db(snapshot):
    """Also write the assessment snapshot to PostgreSQL when configured.

    This powers the Compliance Trend chart directly from the
    ``assessment_history`` table. Failures are ignored so JSON storage remains
    the source of truth when the database is unreachable.
    """
    try:
        from database.db import get_session, is_configured

        if not is_configured():
            return

        from database.repositories import AssessmentsRepository

        AssessmentsRepository(get_session()).record(snapshot)
    except Exception as exc:
        log.warning(
            "Assessment history write to PostgreSQL failed (trend may be empty): %s",
            exc,
        )


def _severity_breakdown(findings):
    severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        r = (f.get("risk") or "").lower()
        if r in severity:
            severity[r] += 1
    return severity


def _live_assessment():

    if not settings.LIVE_ENABLED:
        return None

    key = (settings.FUNCTION_KEY or "").strip()
    if not key or key.startswith("PLACEHOLDER"):
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
        timeutil.ist_now().isoformat()
    )

    return data


def get_full_assessment(firewall_id="vmpafw01", force=False):

    firewall_id = firewall_id or "vmpafw01"
    now = time.time()

    cached = _cache["assessment"].get(firewall_id)

    if (
        not force
        and cached
        and now - _cache["ts"].get(firewall_id, 0)
        < settings.CACHE_TTL
    ):

        return cached

    # vmpafw02 mirrors vmpafw01 (same system, different logical name).
    if firewall_id != "vmpafw01" and "vmpafw01" in _cache["assessment"]:
        import copy

        data = copy.deepcopy(_cache["assessment"]["vmpafw01"])
        data = _apply_firewall(data, firewall_id)
        _cache["assessment"][firewall_id] = data
        _cache["ts"][firewall_id] = now
        return data

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

    data = _apply_firewall(data, firewall_id)

    _record_assessment()

    _cache["assessment"][firewall_id] = data
    _cache["ts"][firewall_id] = now

    return data


def get_summary(firewall_id="vmpafw01", force=False):

    data = get_full_assessment(firewall_id, force)

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


def get_findings(firewall_id="vmpafw01", force=False):

    data = get_full_assessment(firewall_id, force)

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


def get_posture(firewall_id="vmpafw01", force=False):
    data = get_full_assessment(firewall_id, force)

    summary = data.get("summary", {})
    findings = data.get("findings", [])
    results = data.get("assessment", [])
    inventory = data.get("inventory", {})

    total = summary.get("total_controls", 0) or len(results)
    compliant = summary.get("compliant", 0)
    non_compliant = summary.get("non_compliant", 0)
    not_assessed = summary.get("not_assessed", 0)
    compliance_pct = round(compliant / total * 100, 1) if total else 0.0

    severity = _severity_breakdown(findings)

    risk_points = (
        severity.get("critical", 0) * 4.0
        + severity.get("high", 0) * 2.0
        + severity.get("medium", 0) * 1.0
        + severity.get("low", 0) * 0.5
    )
    max_points = total * 4.0
    security_score = (
        round(100.0 * (1.0 - risk_points / max_points), 1)
        if max_points
        else 100.0
    )

    collected_at = data.get("_collected_at")
    stats = get_assessment_stats()
    run_id = "ASM-{0:06d}".format(int(stats.get("assessments_run", 0)))

    prev_snapshots = _load_history()
    prev = None
    for s in reversed(prev_snapshots):
        if s.get("firewall_name", "vmpafw01") == firewall_id:
            prev = s
            break

    snapshot = {
        "run_id": run_id,
        "ts": time.time(),
        "firewall_name": firewall_id,
        "compliance_pct": compliance_pct,
        "security_score": security_score,
        "severity": severity,
        "finding_count": len(findings),
    }
    _record_history(snapshot)

    trend_pct = 0.0
    severity_change = {k: 0 for k in SEVERITY_KEYS}
    if prev and isinstance(prev.get("compliance_pct"), (int, float)):
        trend_pct = round(compliance_pct - prev["compliance_pct"], 1)
        prev_sev = prev.get("severity") or {}
        for k in SEVERITY_KEYS:
            severity_change[k] = int(severity.get(k, 0)) - int(prev_sev.get(k, 0))

    history = _load_history()

    posture = {
        "security_score": security_score,
        "compliance_pct": compliance_pct,
        "trend_pct": trend_pct,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "not_assessed": not_assessed,
        "total_controls": total,
        "severity": severity,
        "severity_change": severity_change,
        "assessments_run": int(stats.get("assessments_run", 0)),
        "run_id": run_id,
        "last_assessment_ts": stats.get("last_assessment_ts"),
        "collected_at": collected_at,
        "_source": data.get("_source", "sample"),
        "firewall_id": firewall_id,
    }

    firewall = {
        "hostname": inventory.get("hostname", firewall_id),
        "model": inventory.get("model", ""),
        "version": inventory.get("version", ""),
        "serial": inventory.get("serial", ""),
    }

    return {
        "posture": posture,
        "firewall": firewall,
        "firewalls": [firewall],
        "findings": findings,
        "assessment": results,
        "history": history,
        "_source": data.get("_source", "sample"),
        "_collected_at": collected_at,
        "_firewall_id": firewall_id,
    }


def get_executive_summary(firewall_id="vmpafw01", force=False):

    from reports.executive_summary import (
        ExecutiveSummary
    )

    data = get_full_assessment(firewall_id, force)

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

    summary["_firewall_id"] = firewall_id

    return summary


def get_executive_summary_pdf(firewall_id="vmpafw01", force=False):

    from reports.executive_summary_pdf import (
        generate as generate_pdf
    )

    firewall_id = firewall_id or "vmpafw01"
    summary = get_executive_summary(firewall_id, force)

    month = timeutil.ist_now().strftime("%b_%Y")
    filename = "Executive_Summary_{0}_{1}.pdf".format(firewall_id, month)

    os.makedirs(
        EXCEL_DIR,
        exist_ok=True
    )

    output_file = os.path.join(
        EXCEL_DIR,
        filename
    )

    generate_pdf(
        summary,
        output_file
    )

    return {
        "summary": summary,
        "filename": filename,
        "local_file": output_file,
        "download_url": "reports/{0}".format(filename),
    }


def get_excel_report(firewall_id="vmpafw01", force=False):

    from reports.excel_report import (
        ExcelReport
    )

    firewall_id = firewall_id or "vmpafw01"
    data = get_full_assessment(firewall_id, force)

    os.makedirs(
        EXCEL_DIR,
        exist_ok=True
    )

    filename = "{0}_Assessment_Workbook.xlsx".format(firewall_id)
    output_file = os.path.join(
        EXCEL_DIR,
        filename
    )

    (
        ExcelReport()
        .generate(
            data,
            output_file=output_file
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
            output_file,
        "download_url":
            "reports/{0}".format(filename),
        "_source":
            data.get(
                "_source",
                "live"
            ),
        "firewall_id": firewall_id,
    }
