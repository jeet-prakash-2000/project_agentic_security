from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font


class ExcelReport:

    def generate(
        self,
        assessment_result,
        output_file="PaloAlto_Assessment.xlsx"
    ):

        workbook = Workbook()

        self._build_dashboard(
            workbook,
            assessment_result
        )

        self._build_findings(
            workbook,
            assessment_result
        )

        self._build_health(
            workbook,
            assessment_result
        )

        self._build_policy(
            workbook,
            assessment_result
        )

        self._build_routing(
            workbook,
            assessment_result
        )

        self._build_vpn(
            workbook,
            assessment_result
        )

        self._build_administration(
            workbook,
            assessment_result
        )

        workbook.save(
            output_file
        )

        return output_file

    def _format_header(
        self,
        worksheet,
        row
    ):

       for cell in worksheet[row]:

          Font(
                bold=True
              )

    def _build_dashboard(
        self,
        workbook,
        data
    ):

        ws = workbook.active

        ws.title = "Executive Dashboard"

        inventory = data.get(
            "inventory",
            {}
        )

        summary = data.get(
            "summary",
            {}
        )

        ws.append([
            "Palo Alto Security Assessment"
        ])

        ws.append([])

        ws.append([
            "Generated",
            str(datetime.now())
        ])

        ws.append([
            "Hostname",
            inventory.get(
                "hostname"
            )
        ])

        ws.append([
            "Model",
            inventory.get(
                "model"
            )
        ])

        ws.append([
            "Version",
            inventory.get(
                "version"
            )
        ])

        ws.append([])

        ws.append([
            "Metric",
            "Value"
        ])

        self._format_header(
            ws,
            ws.max_row
        )

        ws.append([
            "Total Controls",
            summary.get(
                "total_controls",
                0
            )
        ])

        ws.append([
            "Compliant",
            summary.get(
                "compliant",
                0
            )
        ])

        ws.append([
            "Non-Compliant",
            summary.get(
                "non_compliant",
                0
            )
        ])

        ws.append([
            "Not Assessed",
            summary.get(
                "not_assessed",
                0
            )
        ])

    def _build_findings(
        self,
        workbook,
        data
    ):

        ws = workbook.create_sheet(
            "Findings"
        )

        ws.append([
            "Control",
            "Risk",
            "Status",
            "Metric",
            "Observed",
            "Expected",
            "Finding",
            "Remediation"
        ])

        self._format_header(
            ws,
            1
        )

        for finding in data.get(
            "findings",
            []
        ):

            ws.append([

                finding.get(
                    "control"
                ),

                finding.get(
                    "risk"
                ),

                finding.get(
                    "status"
                ),

                finding.get(
                    "metric"
                ),

                str(
                    finding.get(
                        "observed"
                    )
                ),

                str(
                    finding.get(
                        "expected"
                    )
                ),

                finding.get(
                    "finding"
                ),

                finding.get(
                    "remediation"
                )
            ])

    def _build_health(
        self,
        workbook,
        data
    ):

        ws = workbook.create_sheet(
            "Health"
        )

        ws.append([
            "Metric",
            "Value"
        ])

        self._format_header(
            ws,
            1
        )

        health = data.get(
            "health_status",
            {}
        )

        for key, value in health.items():

            ws.append([
                key,
                value
            ])

    def _build_policy(
        self,
        workbook,
        data
    ):

        ws = workbook.create_sheet(
            "Policy Analysis"
        )

        ws.append([
            "Name",
            "Action",
            "Source",
            "Destination",
            "Application",
            "Service",
            "Description",
            "Disabled"
        ])

        self._format_header(
            ws,
            1
        )

        policy = data.get(
            "policy_configuration",
            {}
        )

        rules = policy.get(
            "security_rules",
            []
        )

        for rule in rules:

            ws.append([

                rule.get(
                    "name"
                ),

                rule.get(
                    "action"
                ),

                ",".join(
                    rule.get(
                        "source",
                        []
                    )
                ),

                ",".join(
                    rule.get(
                        "destination",
                        []
                    )
                ),

                ",".join(
                    rule.get(
                        "application",
                        []
                    )
                ),

                ",".join(
                    rule.get(
                        "service",
                        []
                    )
                ),

                rule.get(
                    "description"
                ),

                rule.get(
                    "disabled"
                )
            ])

    def _build_routing(
        self,
        workbook,
        data
    ):

        ws = workbook.create_sheet(
            "Routing"
        )

        routing = data.get(
            "routing_configuration",
            {}
        )

        ws.append([
            "Metric",
            "Value"
        ])

        self._format_header(
            ws,
            1
        )

        ws.append([
            "Virtual Routers",
            ",".join(
                routing.get(
                    "virtual_routers",
                    []
                )
            )
        ])

        ws.append([
            "BGP Enabled",
            routing.get(
                "bgp_enabled",
                False
            )
        ])

        ws.append([
            "OSPF Enabled",
            routing.get(
                "ospf_enabled",
                False
            )
        ])

    def _build_vpn(
        self,
        workbook,
        data
    ):

        ws = workbook.create_sheet(
            "VPN"
        )

        vpn = data.get(
            "vpn_configuration",
            {}
        )

        ws.append([
            "Metric",
            "Value"
        ])

        self._format_header(
            ws,
            1
        )

        ws.append([
            "GlobalProtect Enabled",
            vpn.get(
                "globalprotect_enabled",
                False
            )
        ])

        ws.append([
            "MFA Enabled",
            vpn.get(
                "mfa_enabled",
                False
            )
        ])

        ws.append([
            "Tunnel Monitoring",
            vpn.get(
                "tunnel_monitoring",
                False
            )
        ])

        ws.append([
            "IKE Gateways",
            ",".join(
                vpn.get(
                    "ike_gateways",
                    []
                )
            )
        ])

    def _build_administration(
        self,
        workbook,
        data
    ):

        ws = workbook.create_sheet(
            "Administration"
        )

        admin = data.get(
            "administration_configuration",
            {}
        )

        ws.append([
            "Metric",
            "Value"
        ])

        self._format_header(
            ws,
            1
        )

        for key, value in admin.items():

            ws.append([
                key,
                str(value)
            ])