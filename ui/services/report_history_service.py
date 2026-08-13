import os
import threading
import time

from config import storage

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.abspath(os.path.join(SERVICE_DIR, "..", "config"))
REPORTS_DOC = "reports_history"

_lock = threading.Lock()

MAX_REPORTS = 50


def _load():
    data = storage.load_document(REPORTS_DOC, {"reports": []})
    if not isinstance(data, dict):
        return {"reports": []}
    return data


def _save(data):
    storage.save_document(REPORTS_DOC, data)


def append_report(report):
    with _lock:
        data = _load()
        reports = data.setdefault("reports", [])
        reports.insert(0, report)
        if len(reports) > MAX_REPORTS:
            data["reports"] = reports[:MAX_REPORTS]
        _save(data)


def _seed_demo():
    with _lock:
        data = _load()
        reports = data.get("reports", [])
        if reports:
            return

        demo = [
            {
                "name": "Assessment_Workbook_Aug_2026",
                "type": "Workbook",
                "generated_by": "Firewall Auditor",
                "ts": time.time() - 5 * 86400,
                "status": "Completed",
                "size": "2.4 MB",
                "download_url": "reports/PaloAlto_Assessment.xlsx",
            },
            {
                "name": "Executive_Summary_Aug_2026",
                "type": "Executive Summary",
                "generated_by": "Firewall Auditor",
                "ts": time.time() - 6 * 86400,
                "status": "Completed",
                "size": "184 KB",
                "download_url": None,
            },
            {
                "name": "Executive_Summary_Jul_2026",
                "type": "Executive Summary",
                "generated_by": "Firewall Auditor",
                "ts": time.time() - 30 * 86400,
                "status": "Failed",
                "size": None,
                "download_url": None,
            },
        ]
        data["reports"] = demo
        _save(data)


def list_reports():
    _seed_demo()
    return _load().get("reports", [])
