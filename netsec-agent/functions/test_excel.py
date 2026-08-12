from reports.excel_report import ExcelReport

sample_data = {
    "inventory": {
        "hostname": "vmpafw01",
        "model": "PA-VM",
        "version": "10.2.10-h9"
    },
    "summary": {
        "total_controls": 44,
        "compliant": 6,
        "non_compliant": 18,
        "not_assessed": 20
    },
    "findings": [],
    "health_status": {
        "cpu_usage": 25.8,
        "memory_usage": 28.21
    },
    "policy_configuration": {
        "security_rules": []
    },
    "routing_configuration": {
        "virtual_routers": ["VR1"],
        "bgp_enabled": True,
        "ospf_enabled": True
    },
    "vpn_configuration": {
        "ike_gateways": ["Cisco_Secure_Access01"]
    },
    "administration_configuration": {
        "https_enabled": True
    }
}

report = ExcelReport()

file_name = report.generate(sample_data)

print(file_name)