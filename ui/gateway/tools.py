from services import function_client
from services import report_history_service
from services import agents_service
import time

TOOLS = {
    "run_compliance_assessment": {
        "name": "run_compliance_assessment",
        "description": (
            "Run a compliance assessment against the firewall and return "
            "the compliance results summary."
        ),
        "handler": function_client.run_compliance_assessment,
    },
    "run_full_assessment": {
        "name": "run_full_assessment",
        "description": (
            "Run the full firewall assessment and return detailed results."
        ),
        "handler": function_client.run_full_assessment,
    },
    "executive_summary": {
        "name": "executive_summary",
        "description": (
            "Generate an executive summary of the latest firewall assessment."
        ),
        "handler": function_client.executive_summary,
    },
    "generate_excel_report": {
        "name": "generate_excel_report",
        "description": (
            "Generate an Excel report of the firewall assessment results."
        ),
        "handler": function_client.generate_excel_report,
    },
}


def list_tools():
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
        }
        for tool in TOOLS.values()
    ]


def call_tool(name, **kwargs):
    tool = TOOLS.get(name)
    if tool is None:
        raise ValueError("Unknown tool: {name}".format(name=name))
    result = tool["handler"](**kwargs)
    _record_tool_report(name, result)
    return result


def _report_owner():
    """Best-effort current account for tool-generated report history rows.

    Tool handlers run synchronously inside the requesting account's session,
    so the Flask session carries the owner when available; otherwise the row
    stays ownerless and is reclaimed to the administrator on the next boot.
    """
    try:
        from flask import session as flask_session

        user_id = flask_session.get("user_id")
        if user_id and user_id != "anonymous":
            return user_id
    except Exception:
        pass
    return None


def _record_tool_report(name, result):
    if name not in ("executive_summary", "generate_excel_report"):
        return
    owner = _report_owner()
    agent = agents_service.get_connected_agent()
    if name == "executive_summary":
        report_history_service.append_report({
            "name": "Executive_Summary_{0}".format(time.strftime("%b_%Y")),
            "type": "Executive Summary",
            "generated_by": (agent or {}).get("name", "Firewall Auditor"),
            "ts": time.time(),
            "status": "Completed",
            "size": "—",
            "download_url": None,
        }, user_id=owner)
    elif name == "generate_excel_report":
        size = "—"
        if isinstance(result, dict):
            size = result.get("size", "—")
        report_history_service.append_report({
            "name": "Assessment_Workbook_{0}".format(time.strftime("%b_%Y")),
            "type": "Workbook",
            "generated_by": (agent or {}).get("name", "Firewall Auditor"),
            "ts": time.time(),
            "status": "Completed",
            "size": size,
            "download_url": result.get("download_url") if isinstance(result, dict) else None,
        }, user_id=owner)
