import json
import datetime
from ..connectors.azure_config_cloudsec import utc_now_iso


class TimelineBuilder:
    """Builds a chronological incident timeline from multiple data sources."""

    def build(self, incident_id, incident_data, alert_data, evidence_data):
        events = []

        if incident_data.get("created_time"):
            events.append({
                "time": incident_data["created_time"],
                "phase": "Detection",
                "event": "Sentinel incident created",
                "detail": f"Incident {incident_id} generated with severity {incident_data.get('severity', 'Unknown')}",
            })

        if alert_data.get("detection_time"):
            events.append({
                "time": alert_data["detection_time"],
                "phase": "Detection",
                "event": "Defender alert triggered",
                "detail": f"Alert: {alert_data.get('alert_name', 'Unknown')} ({alert_data.get('mitre_technique', 'N/A')})",
            })

        if evidence_data:
            for indicator in evidence_data.get("suspicious_indicators", []):
                if indicator["severity"] in ("Critical", "High"):
                    events.append({
                        "time": evidence_data.get("collected_at", utc_now_iso()),
                        "phase": "Investigation",
                        "event": indicator["type"].replace("_", " ").title(),
                        "detail": indicator["detail"],
                    })

        events.append({
            "time": utc_now_iso(),
            "phase": "Containment",
            "event": "Containment initiated",
            "detail": "VM isolation and IP blocking executed based on investigation findings",
        })

        events.sort(key=lambda e: e["time"])

        return {
            "incident_id": incident_id,
            "timeline": events,
            "total_events": len(events),
            "generated_at": utc_now_iso(),
        }


class RiskAnalyzer:
    """Analyzes incident risk and provides recommended actions."""

    def analyze(self, incident_data, alert_data, evidence_data):
        base_score = 0

        severity_score = {"Low": 20, "Medium": 50, "High": 75, "Critical": 95}
        base_score = severity_score.get(incident_data.get("severity", "Low"), 20)

        if alert_data:
            alert_severity = alert_data.get("severity", "Low")
            alert_weight = severity_score.get(alert_severity, 20) * 0.3
            base_score += alert_weight

        if evidence_data:
            indicators = evidence_data.get("suspicious_indicators", [])
            for ind in indicators:
                if ind["severity"] == "Critical":
                    base_score += 20
                elif ind["severity"] == "High":
                    base_score += 10

            c2_found = any("c2" in ind.get("type", "").lower() for ind in indicators)
            if c2_found:
                base_score += 15

        risk_score = min(int(base_score), 100)

        if risk_score >= 85:
            confidence = "High"
            recommended_action = "Immediate Containment"
        elif risk_score >= 60:
            confidence = "High"
            recommended_action = "Containment"
        elif risk_score >= 35:
            confidence = "Medium"
            recommended_action = "Investigate Further"
        else:
            confidence = "Low"
            recommended_action = "Monitor"

        return {
            "incident_id": incident_data.get("incident_id", "UNKNOWN"),
            "risk_score": risk_score,
            "risk_level": self._risk_level(risk_score),
            "confidence": confidence,
            "recommended_action": recommended_action,
            "factors": {
                "incident_severity": incident_data.get("severity", "Unknown"),
                "alert_severity": alert_data.get("severity", "N/A") if alert_data else "N/A",
                "suspicious_indicators": len(evidence_data.get("suspicious_indicators", [])) if evidence_data else 0,
            },
            "analyzed_at": utc_now_iso(),
        }

    def _risk_level(self, score):
        if score >= 85:
            return "Critical"
        if score >= 60:
            return "High"
        if score >= 35:
            return "Medium"
        return "Low"
