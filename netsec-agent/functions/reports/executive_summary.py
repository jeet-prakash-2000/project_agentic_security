from reports.risk_summary import (
    RiskSummary
)


class ExecutiveSummary:

    def generate(
        self,
        assessment_result
    ):

        inventory = (
            assessment_result.get(
                "inventory",
                {}
            )
        )

        summary = (
            assessment_result.get(
                "summary",
                {}
            )
        )

        findings = (
            assessment_result.get(
                "findings",
                []
            )
        )

        assessment = (
            assessment_result.get(
                "assessment",
                []
            )
        )

        overall_risk = (
            RiskSummary
            .calculate_overall_risk(
                assessment
            )
        )

        top_findings = []

        critical_findings = [

            finding

            for finding in findings

            if finding.get(
                "risk"
            )
            == "CRITICAL"

        ]

        top_findings.extend(
            critical_findings[:5]
        )

        remediation_priorities = []

        for finding in top_findings:

            remediation = finding.get(
                "remediation"
            )

            if (
                remediation
                and remediation
                not in remediation_priorities
            ):

                remediation_priorities.append(
                    remediation
                )

        return {

            "device": {

                "hostname":
                    inventory.get(
                        "hostname"
                    ),

                "model":
                    inventory.get(
                        "model"
                    ),

                "version":
                    inventory.get(
                        "version"
                    )
            },

            "summary": {

                "overall_risk":
                    overall_risk,

                "total_controls":
                    summary.get(
                        "total_controls",
                        0
                    ),

                "compliant":
                    summary.get(
                        "compliant",
                        0
                    ),

                "non_compliant":
                    summary.get(
                        "non_compliant",
                        0
                    ),

                "not_assessed":
                    summary.get(
                        "not_assessed",
                        0
                    )
            },

            "top_findings":
                top_findings,

            "remediation_priorities":
                remediation_priorities
        }