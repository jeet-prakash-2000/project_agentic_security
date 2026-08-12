import json
import os
import threading
import time

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.abspath(os.path.join(SERVICE_DIR, "..", "config"))
REPORTS_FILE = os.path.join(CONFIG_DIR, "reports_history.json")

_lock = threading.Lock()

MAX_REPORTS = 50


def _load():
    if not os.path.exists(REPORTS_FILE):
        return {"reports": []}
    try:
        with open(REPORTS_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return {"reports": []}
        return data
    except Exception:
        return {"reports": []}


def _save(data):
    with open(REPORTS_FILE, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


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
