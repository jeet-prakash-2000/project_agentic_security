import json
from .azure_config_cloudsec import mock_azure_response


class NetworkConnector:
    """Connector for Azure Network operations."""

    def isolate_vm(self, vm_name, resource_group):
        return mock_azure_response(
            "Network.IsolateVM",
            {"vm_name": vm_name, "resource_group": resource_group},
            {
                "vm_name": vm_name,
                "resource_group": resource_group,
                "action": "containment",
                "isolation_nsg": f"nsg-isolate-{vm_name}",
                "rules_applied": [
                    {"name": "DenyAllInbound", "priority": 100, "direction": "Inbound", "access": "Deny", "protocol": "*", "source": "*", "destination": "*"},
                    {"name": "DenyAllOutbound", "priority": 100, "direction": "Outbound", "access": "Deny", "protocol": "*", "source": "*", "destination": "*"},
                ],
                "result": f"VM {vm_name} isolated. All network traffic blocked.",
                "completed_at": "2026-07-20T09:05:00Z",
            },
        )

    def restore_vm_connectivity(self, vm_name, resource_group):
        return mock_azure_response(
            "Network.RestoreVMConnectivity",
            {"vm_name": vm_name, "resource_group": resource_group},
            {
                "vm_name": vm_name,
                "resource_group": resource_group,
                "action": "recovery",
                "isolation_nsg_removed": True,
                "original_nsg_restored": True,
                "result": f"VM {vm_name} connectivity fully restored to pre-incident state.",
                "completed_at": "2026-07-20T09:30:00Z",
            },
        )

    def block_malicious_ip(self, ip_address, resource_group):
        return mock_azure_response(
            "Network.BlockMaliciousIP",
            {"ip_address": ip_address, "resource_group": resource_group},
            {
                "ip_address": ip_address,
                "resource_group": resource_group,
                "action": "block",
                "nsg_rule": {
                    "name": f"BlockMaliciousIP-{ip_address.replace('.', '-')}",
                    "priority": 200,
                    "direction": "Inbound",
                    "access": "Deny",
                    "protocol": "*",
                    "source": ip_address,
                    "destination": "*",
                },
                "result": f"Malicious IP {ip_address} blocked at NSG level.",
                "completed_at": "2026-07-20T09:06:00Z",
            },
        )
