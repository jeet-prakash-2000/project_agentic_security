import json
from ..connectors.azure_config_cloudsec import ist_now_iso


class ReportGenerator:
    """Generates incident response reports at multiple detail levels."""

    def generate_summary(self, incident_id, incident_data, action_log, status):
        return {
            "incident_id": incident_id,
            "severity": incident_data.get("severity", "Unknown"),
            "title": incident_data.get("title", "Unknown Incident"),
            "vm_name": incident_data.get("vm_name", "N/A"),
            "executive_summary": {
                "finding": "Suspicious outbound communication detected and contained",
                "impact": f"VM {incident_data.get('vm_name', 'N/A')} isolated to prevent data exfiltration",
                "actions_taken": action_log,
                "current_status": status,
                "recommendation": "Conduct root cause analysis and apply security patches before restoring connectivity",
            },
            "generated_at": ist_now_iso(),
        }

    def generate_technical_report(self, incident_id, incident_data, evidence, timeline, risk, actions):
        return {
            "incident_id": incident_id,
            "report_type": "Technical Incident Report",
            "severity": incident_data.get("severity", "Unknown"),
            "indicators": evidence.get("suspicious_indicators", []) if evidence else [],
            "timeline": timeline.get("timeline", []) if timeline else [],
            "evidence": {
                "processes": evidence.get("running_processes", []) if evidence else [],
                "connections": evidence.get("network_connections", []) if evidence else [],
                "users": evidence.get("logged_in_users", []) if evidence else [],
                "services": evidence.get("services", []) if evidence else [],
            } if evidence else {},
            "risk_assessment": risk or {},
            "containment_actions": actions.get("containment", []),
            "recovery_actions": actions.get("recovery", []),
            "eradication_actions": actions.get("eradication", []),
            "generated_at": ist_now_iso(),
        }

    def generate_executive_report(self, incident_id, incident_data, risk, status, cost_impact):
        return {
            "incident_id": incident_id,
            "report_type": "Executive Incident Report",
            "prepared_for": "CISO / Security Leadership",
            "incident_overview": {
                "title": incident_data.get("title", "Unknown Incident"),
                "severity": incident_data.get("severity", "Unknown"),
                "affected_asset": incident_data.get("vm_name", "N/A"),
                "detection_source": "Microsoft Sentinel & Defender for Cloud",
            },
            "risk_summary": {
                "risk_score": risk.get("risk_score", 0) if risk else 0,
                "risk_level": risk.get("risk_level", "Unknown") if risk else "Unknown",
                "confidence": risk.get("confidence", "Unknown") if risk else "Unknown",
            },
            "business_impact": {
                "service_disruption": "Contained VM isolated from network",
                "data_exposure_risk": "Potential - outbound C2 communication detected",
                "estimated_cost_impact": cost_impact,
                "recovery_time_estimate": "2-4 hours",
            },
            "current_status": status,
            "generated_at": ist_now_iso(),
        }
