import json

from ..connectors.azure_config_cloudsec import ist_now_iso

try:
    from dbwriter import log_activity as _db_log_activity
except Exception:  # dbwriter optional
    _db_log_activity = None


class ActionLogger:
    """Tracks all actions taken during an incident response lifecycle.

    Every action is also mirrored to the PostgreSQL ``agent_activity_logs``
    table (guarded - a database failure never affects incident response).
    """

    def __init__(self, run_id=None):
        self.actions = []
        self.run_id = run_id

    def record(self, phase, action, detail, status="completed"):
        entry = {
            "phase": phase,
            "action": action,
            "detail": detail,
            "status": status,
            "timestamp": ist_now_iso(),
        }
        self.actions.append(entry)
        self._persist(entry)
        return entry

    def _persist(self, entry):
        if _db_log_activity is None:
            return
        db_status = "Completed" if entry.get("status") == "completed" else "Failed"
        try:
            _db_log_activity(
                agent_id="cloudsec-agent",
                run_id=self.run_id,
                activity=(entry.get("phase") or "action").lower(),
                function_name=entry.get("action") or "",
                status=db_status,
                message=entry.get("detail") or "",
            )
        except Exception:
            pass

    def to_summary(self):
        return [f"[{a['phase']}] {a['detail']}" for a in self.actions]

    def to_dict(self):
        return {
            "total_actions": len(self.actions),
            "actions": self.actions,
            "containment": [a for a in self.actions if a["phase"] == "Containment"],
            "recovery": [a for a in self.actions if a["phase"] == "Recovery"],
            "eradication": [a for a in self.actions if a["phase"] == "Eradication"],
        }
