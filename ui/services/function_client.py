import time
from datetime import datetime

import requests

from config import settings

TIMEOUT = 60


def _get(endpoint, key=None):
    response = requests.get(
        f"{settings.BASE_URL}/{endpoint}",
        params={"code": key or settings.FUNCTION_KEY},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _refresh_cache(data):
    """Update assessment_service cache so Security Ops page shows latest results."""
    import services.assessment_service as a
    data["_source"] = "live"
    data["_collected_at"] = datetime.utcnow().isoformat()
    a._cache["assessment"] = data
    a._cache["ts"] = time.time()
    a._record_assessment()


def run_compliance_assessment():
    data = _get("run_compliance_assessment")
    if isinstance(data, dict) and "findings" in data:
        _refresh_cache(data)
    return data


def executive_summary():
    return _get("executive_summary", key=settings.EXECUTIVE_SUMMARY_KEY)


def run_full_assessment():
    return _get("run_full_assessment", key=settings.FULL_ASSESSMENT_KEY)


def generate_excel_report():
    return _get("generate_excel_report", key=settings.EXCEL_KEY)
