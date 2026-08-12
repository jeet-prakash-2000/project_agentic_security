import json
from .azure_config_cloudsec import mock_azure_response


class DefenderConnector:
    """Connector for Microsoft Defender for Cloud operations."""

    def get_alert_details(self, alert_id):
        return mock_azure_response(
            "Defender.GetAlertDetails",
            {"alert_id": alert_id},
            {
                "alert_id": alert_id,
                "alert_name": "Suspicious Outbound Connection",
                "severity": "High",
                "provider": "Microsoft Defender for Cloud",
                "mitre_technique": "T1071",
                "mitre_tactic": "Command and Control",
                "recommended_action": "Contain VM and investigate network traffic",
                "status": "Active",
                "detection_time": "2026-07-20T09:00:00Z",
                "entities": {
                    "vm": "agentic-vm-01",
                    "ip": "10.0.1.10",
                    "malicious_ip": "203.0.113.42",
                },
            },
        )

    def get_security_recommendations(self, vm_name, resource_group):
        return mock_azure_response(
            "Defender.GetSecurityRecommendations",
            {"vm_name": vm_name, "resource_group": resource_group},
            {
                "vm_name": vm_name,
                "resource_group": resource_group,
                "secure_score_current": 62,
                "secure_score_max": 100,
                "recommendations": [
                    {
                        "id": "REC-001",
                        "title": "Vulnerabilities in container security configurations should be remediated",
                        "severity": "High",
                        "secure_score_impact": 8,
                        "remediation": "Update container base images and scan for vulnerabilities",
                    },
                    {
                        "id": "REC-002",
                        "title": "Management ports of virtual machines should be protected with just-in-time network access control",
                        "severity": "High",
                        "secure_score_impact": 12,
                        "remediation": "Enable JIT VM Access in Microsoft Defender for Cloud",
                    },
                    {
                        "id": "REC-003",
                        "title": "System updates should be installed on your machines",
                        "severity": "Medium",
                        "secure_score_impact": 5,
                        "remediation": "Install pending OS and security updates",
                    },
                    {
                        "id": "REC-004",
                        "title": "Endpoint protection should be installed on your machines",
                        "severity": "Medium",
                        "secure_score_impact": 4,
                        "remediation": "Ensure Microsoft Defender Antivirus is enabled",
                    },
                ],
            },
        )
