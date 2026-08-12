class FindingsGenerator:

    REMEDIATION_MAP = {

        "PA-01":
            "Upgrade to a supported PAN-OS release.",

        "PA-02":
            "Apply security patches to address reported CVEs.",

        "PA-06":
            "Investigate high CPU utilization and optimize firewall processing.",

        "PA-07":
            "Review session usage and increase capacity if needed.",

        "PA-08":
            "Investigate memory usage and optimize enabled features.",

        "PA-10":
            "Reduce log disk usage or increase log storage.",

        "PA-11":
            "Enable HA and verify peer connectivity.",

        "PA-12":
            "Restore HA synchronization between peers.",

        "PA-15":
            "Enable path and link monitoring.",

        "PA-16":
            "Remove Any-Any rules or apply strict security profiles.",

        "PA-17":
            "Review and remove unused security rules.",

        "PA-18":
            "Document all security rules with descriptions and ownership.",

        "PA-19":
            "Implement explicit default deny rule with logging enabled.",

        "PA-21":
            "Increase App-ID usage and reduce application=any rules.",

        "PA-23":
            "Review shadowed rules and optimize rule order.",

        "PA-24":
            "Enable Threat Prevention and apply profiles to all allow rules.",

        "PA-26":
            "Enable DNS sinkhole for Anti-Spyware protection.",

        "PA-27":
            "Enable WildFire and file forwarding.",

        "PA-28":
            "Enable URL Filtering and block malicious categories.",

        "PA-29":
            "Enable DNS Security service.",

        "PA-31":
            "Implement SSL decryption policy.",

        "PA-36":
            "Implement additional network segmentation zones.",

        "PA-42":
            "Review routing table and remove route leakage.",

        "PA-43":
            "Enable MFA for all VPN users.",

        "PA-45":
            "Enable VPN tunnel monitoring.",

        "PA-48":
            "Enable traffic logging on all security policies.",

        "PA-49":
            "Forward logs to SIEM.",

        "PA-50":
            "Increase retention period to at least 90 days.",

        "PA-53":
            "Disable or secure default administrator account.",

        "PA-55":
            "Disable insecure management protocols.",

        "PA-56":
            "Restrict management access to approved networks.",

        "PA-57":
            "Reduce administrator session timeout to 30 minutes or less.",

        "PA-58":
            "Configure at least two NTP servers.",

        "PA-59":
            "Migrate to SNMPv3 and remove weaker protocols.",

        "PA-60":
            "Integrate device with Panorama.",

        "PA-61":
            "Apply Zone Protection Profiles to external zones.",

        "PA-62":
            "Configure DoS protection policies.",

        "PA-63":
            "Enable packet attack protections.",

        "PA-64":
            "Implement daily configuration backups.",

        "PA-67":
            "Retain at least 10 configuration snapshots."
    }

    def generate(
        self,
        compliance_results
    ):

        findings = []

        for result in compliance_results:

            if result["status"] == "COMPLIANT":
                continue

            findings.append({

                "control":
                    result["control"],

                "status":
                    result["status"],

                "risk":
                    result["risk"],

                "metric":
                    result["metric"],

                "observed":
                    result["observed"],

                "expected":
                    result["expected"],

                "operator":
                    result.get("operator", ""),

                "finding":
                    self._build_finding(
                        result
                    ),

                "remediation":
                    self.REMEDIATION_MAP.get(
                        result["control"],
                        "Review configuration and align with security baseline."
                    )
            })

        return findings

    def _build_finding(
        self,
        result
    ):

        return (
            f"Observed value "
            f"'{result['observed']}' "
            f"does not meet expected baseline "
            f"'{result['expected']}'."
        )