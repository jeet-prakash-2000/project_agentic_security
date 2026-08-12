import json
from .azure_config_cloudsec import mock_azure_response


class SentinelConnector:
    """Connector for Microsoft Sentinel incident operations."""

    def get_incident(self, incident_id):
        return mock_azure_response(
            "Sentinel.GetIncident",
            {"incident_id": incident_id},
            {
                "incident_id": incident_id,
                "title": "Agentic AI Test Incident",
                "severity": "High",
                "status": "New",
                "vm_name": "agentic-vm-01",
                "resource_group": "LTIM-CLOUDSEC-AGENTIC-RG01",
                "description": "Suspicious outbound communication detected.",
                "owner": "SecOps Team",
                "provider": "Microsoft Sentinel",
                "created_time": "2026-07-20T09:00:00Z",
            },
        )

    def get_incident_entities(self, incident_id):
        return mock_azure_response(
            "Sentinel.GetIncidentEntities",
            {"incident_id": incident_id},
            {
                "incident_id": incident_id,
                "entities": [
                    {
                        "type": "host",
                        "hostName": "agentic-vm-01",
                        "dnsDomain": "centralindia.cloudapp.azure.com",
                    },
                    {
                        "type": "ip",
                        "address": "10.0.1.10",
                        "location": "centralindia",
                    },
                    {
                        "type": "account",
                        "name": "azureuser",
                        "aadUserId": "aad-azureuser",
                    },
                    {
                        "type": "malicious-ip",
                        "address": "203.0.113.42",
                        "threatType": "C2 Communication",
                    },
                ],
                "entity_count": 4,
                "severity": "High",
            },
        )

    def close_incident(self, incident_id, classification, comment):
        return mock_azure_response(
            "Sentinel.CloseIncident",
            {
                "incident_id": incident_id,
                "classification": classification,
                "comment": comment,
            },
            {
                "incident_id": incident_id,
                "status": "Closed",
                "classification": classification,
                "closed_time": "2026-07-20T10:30:00Z",
                "comment": comment,
            },
        )
