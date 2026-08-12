import json
from .azure_config_cloudsec import mock_azure_response


class ComputeConnector:
    """Connector for Azure Compute (VM) operations."""

    def get_vm_context(self, vm_name, resource_group):
        return mock_azure_response(
            "Compute.GetVMContext",
            {"vm_name": vm_name, "resource_group": resource_group},
            {
                "vm_name": vm_name,
                "resource_group": resource_group,
                "location": "centralindia",
                "os_type": "Linux",
                "os_version": "Ubuntu 22.04 LTS",
                "vm_size": "Standard_D2s_v3",
                "power_state": "VM running",
                "private_ip": "10.0.1.10",
                "public_ip": None,
                "network_interfaces": ["nic-agentic-vm-01"],
                "nsg_rules": [
                    {
                        "name": "AllowSSH",
                        "priority": 100,
                        "direction": "Inbound",
                        "protocol": "TCP",
                        "source": "*",
                        "destination": "*",
                        "destination_port": "22",
                        "access": "Allow",
                    }
                ],
                "risk_score": 90,
            },
        )

    def collect_vm_evidence(self, vm_name, resource_group):
        return mock_azure_response(
            "Compute.CollectVMEvidence",
            {"vm_name": vm_name, "resource_group": resource_group},
            {
                "vm_name": vm_name,
                "resource_group": resource_group,
                "collected_at": "2026-07-20T09:10:00Z",
                "running_processes": [
                    {"pid": 1234, "name": "sshd", "user": "root", "cpu_pct": 0.1, "mem_pct": 0.3},
                    {"pid": 5678, "name": "nginx", "user": "www-data", "cpu_pct": 2.1, "mem_pct": 5.2},
                    {"pid": 9012, "name": "bash", "user": "azureuser", "cpu_pct": 8.7, "mem_pct": 12.4},
                    {"pid": 3456, "name": "python3", "user": "azureuser", "cpu_pct": 15.3, "mem_pct": 22.1},
                    {"pid": 7890, "name": "unknown_binary", "user": "root", "cpu_pct": 45.2, "mem_pct": 35.8},
                ],
                "network_connections": [
                    {"local_addr": "10.0.1.10:443", "remote_addr": "203.0.113.42:8443", "state": "ESTABLISHED", "process": "unknown_binary"},
                    {"local_addr": "10.0.1.10:22", "remote_addr": "10.0.0.5:55221", "state": "ESTABLISHED", "process": "sshd"},
                    {"local_addr": "10.0.1.10:80", "remote_addr": "10.0.2.15:52341", "state": "ESTABLISHED", "process": "nginx"},
                ],
                "open_ports": [
                    {"port": 22, "protocol": "tcp", "process": "sshd"},
                    {"port": 80, "protocol": "tcp", "process": "nginx"},
                    {"port": 443, "protocol": "tcp", "process": "unknown_binary"},
                    {"port": 8443, "protocol": "tcp", "process": "unknown_binary"},
                ],
                "logged_in_users": [
                    {"username": "azureuser", "terminal": "pts/0", "login_time": "2026-07-20T08:55:00Z", "from": "10.0.0.5"},
                    {"username": "root", "terminal": "pts/1", "login_time": "2026-07-20T09:02:00Z", "from": "203.0.113.42"},
                ],
                "services": [
                    {"name": "sshd", "status": "active", "startup": "enabled"},
                    {"name": "nginx", "status": "active", "startup": "enabled"},
                    {"name": "cron", "status": "active", "startup": "enabled"},
                    {"name": "unknown_service", "status": "active", "startup": "enabled"},
                ],
                "suspicious_indicators": [
                    {"type": "unknown_process", "detail": "Process 'unknown_binary' running as root with high CPU (45%)", "severity": "High"},
                    {"type": "c2_connection", "detail": "Established connection to known malicious IP 203.0.113.42:8443", "severity": "Critical"},
                    {"type": "privileged_login", "detail": "Root login from external IP 203.0.113.42", "severity": "High"},
                    {"type": "unknown_service", "detail": "Unrecognized service 'unknown_service' enabled at startup", "severity": "Medium"},
                    {"type": "suspicious_port", "detail": "Unknown process listening on port 8443", "severity": "Medium"},
                ],
            },
        )

    def stop_vm(self, vm_name, resource_group):
        return mock_azure_response(
            "Compute.StopVM",
            {"vm_name": vm_name, "resource_group": resource_group},
            {
                "vm_name": vm_name,
                "resource_group": resource_group,
                "action": "deallocate",
                "power_state": "VM deallocated",
                "completed_at": "2026-07-20T09:20:00Z",
            },
        )

    def validate_vm_health(self, vm_name, resource_group):
        return mock_azure_response(
            "Compute.ValidateVMHealth",
            {"vm_name": vm_name, "resource_group": resource_group},
            {
                "vm_name": vm_name,
                "resource_group": resource_group,
                "power_state": "VM running",
                "defender_status": "Healthy",
                "connectivity": "Reachable",
                "boot_diagnostics": "Normal",
                "disk_encryption": "Enabled",
                "status": "Healthy",
                "validated_at": "2026-07-20T09:45:00Z",
            },
        )

    def run_security_scan(self, vm_name, resource_group):
        return mock_azure_response(
            "Compute.RunSecurityScan",
            {"vm_name": vm_name, "resource_group": resource_group},
            {
                "vm_name": vm_name,
                "resource_group": resource_group,
                "scan_type": "Defender for Cloud malware scan",
                "status": "Completed",
                "findings": [
                    {"type": "malware", "detail": "No malware detected", "severity": "Clean"},
                    {"type": "vulnerability", "detail": "3 critical OS patches missing", "severity": "High"},
                    {"type": "misconfiguration", "detail": "Password authentication enabled for SSH", "severity": "Medium"},
                ],
                "completed_at": "2026-07-20T09:38:00Z",
            },
        )

    def remove_persistence(self, vm_name, resource_group):
        return mock_azure_response(
            "Compute.RemovePersistence",
            {"vm_name": vm_name, "resource_group": resource_group},
            {
                "vm_name": vm_name,
                "resource_group": resource_group,
                "checks_performed": {
                    "startup_scripts": {"found": 1, "removed": 1, "details": ["/etc/init.d/unknown_service removed"]},
                    "cron_jobs": {"found": 1, "removed": 1, "details": ["Malicious cron job for root user removed"]},
                    "services": {"found": 1, "removed": 1, "details": ["unknown_service stopped and disabled"]},
                    "ssh_keys": {"found": 1, "removed": 1, "details": ["Unauthorized key in /root/.ssh/authorized_keys removed"]},
                },
                "completed_at": "2026-07-20T09:40:00Z",
            },
        )

    def patch_vm(self, vm_name, resource_group):
        return mock_azure_response(
            "Compute.PatchVM",
            {"vm_name": vm_name, "resource_group": resource_group},
            {
                "vm_name": vm_name,
                "resource_group": resource_group,
                "patches_applied": [
                    {"id": "KB-5021234", "description": "Linux kernel security update", "status": "Installed"},
                    {"id": "KB-5025678", "description": "OpenSSL security patch", "status": "Installed"},
                    {"id": "KB-5029012", "description": "Systemd security update", "status": "Installed"},
                ],
                "reboot_required": True,
                "completed_at": "2026-07-20T09:42:00Z",
            },
        )
