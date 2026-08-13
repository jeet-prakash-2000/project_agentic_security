import json
from ..connectors.azure_config_cloudsec import ist_now_iso


class ActionLogger:
    """Tracks all actions taken during an incident response lifecycle."""

    def __init__(self):
        self.actions = []

    def record(self, phase, action, detail, status="completed"):
        entry = {
            "phase": phase,
            "action": action,
            "detail": detail,
            "status": status,
            "timestamp": ist_now_iso(),
        }
        self.actions.append(entry)
        return entry

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
