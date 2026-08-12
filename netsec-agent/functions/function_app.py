import json
import os

import azure.functions as func

from connectors.paloalto.paloalto_connector import (
    PaloAltoConnector
)

from compliance.compliance_engine import (
    ComplianceEngine
)

from compliance.findings_generator import (
    FindingsGenerator
)

from reports.executive_summary import (
    ExecutiveSummary
)

from reports.excel_report import (
    ExcelReport
)

app = func.FunctionApp()


FIREWALL_IP = os.environ.get("PA_FIREWALL_HOST", "10.1.0.5")
USERNAME = os.environ.get("PA_USERNAME", "fwadmin")
PASSWORD = os.environ.get("PA_PASSWORD", "")


def get_connector():

    return PaloAltoConnector(
        hostname=FIREWALL_IP,
        username=USERNAME,
        password=PASSWORD
    )


def load_baseline_rules():

    with open(
        "baseline/baseline_rules.json",
        "r"
    ) as f:

        return json.load(f)


def success_response(data):

    return func.HttpResponse(
        json.dumps(
            data,
            indent=2,
            default=str
        ),
        mimetype="application/json",
        status_code=200
    )


def error_response(error):

    return func.HttpResponse(
        json.dumps(
            {
                "status": "ERROR",
                "message": str(error)
            }
        ),
        mimetype="application/json",
        status_code=500
    )


def build_compliance_assessment():

    connector = get_connector()

    assessment_data = (
        connector.run_full_assessment()
    )

    baseline_rules = (
        load_baseline_rules()
    )

    compliance_engine = (
        ComplianceEngine(
            baseline_rules
        )
    )

    compliance_results = (
        compliance_engine.evaluate(
            assessment_data
        )
    )

    findings_generator = (
        FindingsGenerator()
    )

    findings = (
        findings_generator.generate(
            compliance_results
        )
    )

    summary = {

        "total_controls":
            len(
                compliance_results
            ),

        "compliant":
            len([
                r
                for r in compliance_results
                if r["status"]
                == "COMPLIANT"
            ]),

        "non_compliant":
            len([
                r
                for r in compliance_results
                if r["status"]
                == "NON_COMPLIANT"
            ]),

        "not_assessed":
            len([
                r
                for r in compliance_results
                if r["status"]
                == "NOT_ASSESSED"
            ])
    }

    return {

        "inventory":
            assessment_data.get(
                "inventory",
                {}
            ),

        "health_status":
            assessment_data.get(
                "health_status",
                {}
            ),

        "ha_configuration":
            assessment_data.get(
                "ha_configuration",
                {}
            ),

        "policy_configuration":
            assessment_data.get(
                "policy_configuration",
                {}
            ),

        "security_services":
            assessment_data.get(
                "security_services",
                {}
            ),

        "routing_configuration":
            assessment_data.get(
                "routing_configuration",
                {}
            ),

        "vpn_configuration":
            assessment_data.get(
                "vpn_configuration",
                {}
            ),

        "logging_configuration":
            assessment_data.get(
                "logging_configuration",
                {}
            ),

        "administration_configuration":
            assessment_data.get(
                "administration_configuration",
                {}
            ),

        "zone_protection_configuration":
            assessment_data.get(
                "zone_protection_configuration",
                {}
            ),

        "backup_configuration":
            assessment_data.get(
                "backup_configuration",
                {}
            ),

        "summary":
            summary,

        "findings":
            findings,

        "assessment":
            compliance_results
    }


@app.route(
    route="get_inventory",
    auth_level=func.AuthLevel.FUNCTION
)
def get_inventory(
    req: func.HttpRequest
):

    try:

        return success_response(
            get_connector().get_inventory()
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="get_health_status",
    auth_level=func.AuthLevel.FUNCTION
)
def get_health_status(
    req: func.HttpRequest
):

    try:

        return success_response(
            get_connector().get_health_status()
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="get_ha_configuration",
    auth_level=func.AuthLevel.FUNCTION
)
def get_ha_configuration(
    req: func.HttpRequest
):

    try:

        return success_response(
            get_connector().get_ha_configuration()
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="get_policy_configuration",
    auth_level=func.AuthLevel.FUNCTION
)
def get_policy_configuration(
    req: func.HttpRequest
):

    try:

        return success_response(
            get_connector().get_policy_configuration()
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="get_security_services",
    auth_level=func.AuthLevel.FUNCTION
)
def get_security_services(
    req: func.HttpRequest
):

    try:

        return success_response(
            get_connector().get_security_services()
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="get_routing_configuration",
    auth_level=func.AuthLevel.FUNCTION
)
def get_routing_configuration(
    req: func.HttpRequest
):

    try:

        return success_response(
            get_connector().get_routing_configuration()
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="get_vpn_configuration",
    auth_level=func.AuthLevel.FUNCTION
)
def get_vpn_configuration(
    req: func.HttpRequest
):

    try:

        return success_response(
            get_connector().get_vpn_configuration()
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="get_logging_configuration",
    auth_level=func.AuthLevel.FUNCTION
)
def get_logging_configuration(
    req: func.HttpRequest
):

    try:

        return success_response(
            get_connector().get_logging_configuration()
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="get_administration_configuration",
    auth_level=func.AuthLevel.FUNCTION
)
def get_administration_configuration(
    req: func.HttpRequest
):

    try:

        return success_response(
            get_connector().get_administration_configuration()
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="get_zone_protection_configuration",
    auth_level=func.AuthLevel.FUNCTION
)
def get_zone_protection_configuration(
    req: func.HttpRequest
):

    try:

        return success_response(
            get_connector().get_zone_protection_configuration()
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="get_backup_configuration",
    auth_level=func.AuthLevel.FUNCTION
)
def get_backup_configuration(
    req: func.HttpRequest
):

    try:

        return success_response(
            get_connector().get_backup_configuration()
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="run_full_assessment",
    auth_level=func.AuthLevel.FUNCTION
)
def run_full_assessment(
    req: func.HttpRequest
):

    try:

        connector = get_connector()

        result = (
            connector.run_full_assessment()
        )

        return success_response(
            result
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="run_compliance_assessment",
    auth_level=func.AuthLevel.FUNCTION
)
def run_compliance_assessment(
    req: func.HttpRequest
):

    try:

        result = (
            build_compliance_assessment()
        )

        return success_response(
            result
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="executive_summary",
    auth_level=func.AuthLevel.FUNCTION
)
def executive_summary(
    req: func.HttpRequest
):

    try:

        assessment_result = (
            build_compliance_assessment()
        )

        summary = (
            ExecutiveSummary()
            .generate(
                assessment_result
            )
        )

        return success_response(
            summary
        )

    except Exception as e:

        return error_response(e)


@app.route(
    route="generate_excel_report",
    auth_level=func.AuthLevel.FUNCTION
)
def generate_excel_report(
    req: func.HttpRequest
):

    try:

        assessment_result = (
            build_compliance_assessment()
        )

        report_generator = (
            ExcelReport()
        )

        report_file = (
            report_generator.generate(
                assessment_result,
                output_file=
                "/tmp/PaloAlto_Assessment.xlsx"
            )
        )

        return success_response({

            "status":
                "SUCCESS",

            "report_file":
                report_file,

            "message":
                "Excel report generated successfully.",

            "summary":
                assessment_result.get(
                    "summary",
                    {}
                )
        })

    except Exception as e:

        return error_response(
            e
        )