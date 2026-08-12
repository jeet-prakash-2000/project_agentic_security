SAMPLE_ASSESSMENT = {
    "inventory": {
        "hostname": "edge-fw-01",
        "model": "PA-3220",
        "version": "10.2.3",
        "serial": "007201234567"
    },
    "health_status": {
        "version": "10.2.3",
        "critical_cves": 3,
        "content_update_hours": 6,
        "wildfire_update_minutes": 3,
        "cpu_usage": 62,
        "session_utilization": 84,
        "memory_usage": 71,
        "disk_usage": 55
    },
    "ha_configuration": {
        "ha_enabled": False,
        "config_sync": "unsynchronized",
        "link_monitoring": True
    },
    "policy_configuration": {
        "any_any_rules": 12,
        "unused_rule_percent": 18,
        "documented_rule_percent": 40,
        "default_deny_present": True,
        "appid_rule_percent": 55,
        "shadowed_rules": 4,
        "security_rules": [
            {
                "name": "Allow-Web",
                "action": "allow",
                "source": ["trust"],
                "destination": ["untrust"],
                "application": ["web-browsing", "ssl"],
                "service": ["tcp-443"],
                "description": "Outbound web access",
                "disabled": False
            },
            {
                "name": "Any-Any",
                "action": "allow",
                "source": ["any"],
                "destination": ["any"],
                "application": ["any"],
                "service": ["application-default"],
                "description": "",
                "disabled": False
            }
        ]
    },
    "security_services": {
        "threat_prevention": False,
        "dns_sinkhole_enabled": False,
        "wildfire_enabled": True,
        "url_filtering_enabled": True,
        "dns_security_enabled": False,
        "ssl_decryption_enabled": False,
        "tls_minimum_version": "1.1"
    },
    "routing_configuration": {
        "zone_count": 3,
        "stale_nat_rules": 0,
        "route_leaks": 1,
        "virtual_routers": ["default"],
        "bgp_enabled": True,
        "ospf_enabled": False
    },
    "vpn_configuration": {
        "globalprotect_enabled": True,
        "mfa_enabled": False,
        "tunnel_monitoring": True,
        "ike_gateways": ["GP-Gateway", "SiteA-IKE"]
    },
    "logging_configuration": {
        "traffic_logging_enabled": False,
        "siem_enabled": False,
        "retention_days": 30
    },
    "administration_configuration": {
        "default_admin_disabled": False,
        "https_enabled": True,
        "management_acl_enabled": False,
        "admin_timeout_minutes": 45,
        "ntp_server_count": 2,
        "snmp_version": "v2c",
        "panorama_managed": False
    },
    "zone_protection_configuration": {
        "zone_protection_enabled": False,
        "dos_protection_enabled": True,
        "packet_attack_protection": True
    },
    "backup_configuration": {
        "scheduled_backups": False,
        "versioned_configs": True
    }
}
