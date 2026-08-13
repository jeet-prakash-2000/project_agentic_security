import os
import time

from flask import Flask
from flask import render_template
from flask import jsonify
from flask import url_for
from flask import request
from flask import redirect
from flask import send_file
from flask import session
from flask import g

from config import settings as platform_settings
from services import assessment_service
from services import agents_service
from services import dashboard_service
from services import insights_service
from services import report_history_service
from services import system_status_service
from services import telemetry_map_service
from services import firewall_data_service
from services import timeutil
from services import users_service
from gateway.agent_gateway import gateway
from gateway import session_manager

app = Flask(__name__)
app.secret_key = platform_settings.SECRET_KEY


# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = users_service.get_user(user_id)
    if not user:
        session.pop("user_id", None)
        return None
    return users_service.public_user(user_id)


def current_user_id():
    return session.get("user_id") or "anonymous"


@app.before_request
def require_authentication():
    if request.endpoint in ("login", "signup", "logout", "static"):
        return None

    if not session.get("user_id"):
        if request.path.startswith("/api/"):
            return jsonify({"error": "unauthorized"}), 401
        return redirect(url_for("login", next=request.path))

    g.user = current_user()
    return None


@app.context_processor
def inject_current_user():
    return {"current_user": current_user()}


# --------------------------------------------------
# AUTO CSS LOADER
# --------------------------------------------------

def render_with_css(template_name, **context):

    css_filename = (
        os.path.splitext(template_name)[0]
        + ".css"
    )

    css_path = os.path.join(
        app.static_folder,
        "css",
        css_filename
    )

    if os.path.exists(css_path):
        context["page_css"] = css_filename
    else:
        context["page_css"] = None

    return render_template(
        template_name,
        **context
    )

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def file_size_label(path):
    try:
        size_bytes = (
            os.path.getsize(path)
            if path and os.path.exists(path)
            else 0
        )
    except Exception:
        return "—"
    if not size_bytes:
        return "—"
    if size_bytes >= 1024 * 1024:
        return "{0:.2f} MB".format(size_bytes / (1024 * 1024))
    return "{0:.0f} KB".format(size_bytes / 1024)


def format_report_ts(ts):
    try:
        return timeutil.format_ist(ts)
    except (TypeError, ValueError, OverflowError):
        return "—"


app.add_template_filter(format_report_ts, "report_ts")


def initials(name):
    parts = (name or "").strip().split()
    letters = "".join(p[0] for p in parts if p).upper()
    return letters[:2] or "U"


app.add_template_filter(initials, "initials")


def render_reports(**context):
    context["reports"] = report_history_service.list_reports()
    return render_with_css("reports.html", **context)

# --------------------------------------------------
# AUTH ROUTES (login / signup / logout)
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    error = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        user = users_service.authenticate(email, password)
        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("workspace"))
        error = "Invalid email or password."

    return render_template("login.html", mode="login", error=error)


@app.route("/signup", methods=["POST"], endpoint="signup")
def signup():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    password = request.form.get("password") or ""

    try:
        user = users_service.create_user(name, email, password)
    except ValueError as e:
        return render_template("login.html", mode="signup", error=str(e), form={"name": name, "email": email}), 400

    session_manager.claim_anonymous_conversations(user["id"])
    session["user_id"] = user["id"]
    return redirect(url_for("workspace"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --------------------------------------------------
# HOME (AI Workspace is the primary landing page)
# --------------------------------------------------

@app.route("/")
def home():

    return redirect(
        url_for("workspace")
    )

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    connected = agents_service.get_connected_agent()

    return render_with_css(
        "dashboard.html",

        total_controls="-",
        compliant="-",
        non_compliant="-",
        not_assessed="-",
        base_model=(connected or {}).get("model", "gpt-5.1")
    )

# --------------------------------------------------
# WORKSPACE
# --------------------------------------------------

@app.route("/workspace")
def workspace():

    return render_with_css(
        "workspace.html"
    )

# --------------------------------------------------
# FINDINGS
# --------------------------------------------------

@app.route("/findings")
def findings():

    return render_with_css(
        "findings.html"
    )

# --------------------------------------------------
# RUN ASSESSMENT
# --------------------------------------------------

@app.route("/run-assessment")
def run_assessment():

    try:

        data = (
            assessment_service
            .get_full_assessment(
                force=True
            )
        )

        return render_with_css(
            "findings.html",

            assessment_source=(
                data.get("_source", "live")
            )
        )

    except Exception as e:

        return render_with_css(
            "findings.html",

            error=str(e)
        )

# --------------------------------------------------
# REPORTS
# --------------------------------------------------

@app.route("/reports")
def reports():

    return render_reports()


# --------------------------------------------------
# EXECUTIVE SUMMARY
# --------------------------------------------------

@app.route("/executive-summary")
def executive_report():

    try:

        result = (
            assessment_service
            .get_executive_summary_pdf(
                force=True
            )
        )

        summary = result["summary"]

        agent = agents_service.get_connected_agent()

        report_history_service.append_report(
            {
                "name": result["filename"].replace(".pdf", ""),
                "type": "Executive Summary",
                "generated_by": (agent or {}).get("name", "Firewall Auditor"),
                "ts": time.time(),
                "status": "Completed",
                "size": file_size_label(result["local_file"]),
                "download_url": result["download_url"],
            }
        )

        return render_reports(
            summary=summary,
            summary_download_url=(
                url_for("static", filename=result["download_url"])
            ),
            assessment_source=(
                summary.get("_source", "live")
            )
        )

    except Exception as e:

        return render_reports(
            summary=None,
            error=str(e)
        )

# --------------------------------------------------
# EXCEL REPORT
# --------------------------------------------------

@app.route("/generate-excel")
def generate_excel():

    try:

        result = (
            assessment_service
            .get_excel_report(
                force=True
            )
        )

        download_url = None

        if (
            result.get("local_file")
            and os.path.exists(
                result["local_file"]
            )
        ):

            download_url = url_for(
                "static",
                filename=result["download_url"]
            )

        agent = agents_service.get_connected_agent()

        size = file_size_label(result.get("local_file"))

        report_history_service.append_report(
            {
                "name": "Assessment_Workbook_{0}".format(
                    timeutil.ist_now().strftime("%b_%Y")
                ),
                "type": "Workbook",
                "generated_by": (agent or {}).get("name", "Firewall Auditor"),
                "ts": time.time(),
                "status": "Completed",
                "size": size,
                "download_url": result["download_url"],
            }
        )

        return render_reports(
            excel_result=result,
            excel_download_url=download_url,
            assessment_source=(
                result.get("_source", "live")
            )
        )

    except Exception as e:

        return render_reports(
            excel_result=None,
            error=str(e)
        )

# --------------------------------------------------
# AGENT INSIGHTS
# --------------------------------------------------

@app.route("/insights")
def insights():

    return render_with_css(
        "insights.html"
    )

# --------------------------------------------------
# TELEMETRY MAP
# --------------------------------------------------

@app.route("/telemetry-map")
def telemetry_map():

    return render_with_css(
        "telemetry_map.html"
    )

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

@app.route("/settings")
def settings():

    return render_with_css(
        "settings.html",

        azure_function_url=platform_settings.BASE_URL,

        live_mode=platform_settings.LIVE_ENABLED
    )

# --------------------------------------------------
# API ROUTES
# --------------------------------------------------

@app.route("/api/compliance")
def api_compliance():

    force = (
        request.args.get(
            "refresh",
            "0"
        )
        == "1"
    )

    try:

        return jsonify(
            assessment_service
            .get_full_assessment(
                force=force
            )
        )

    except Exception as e:

        return jsonify(
            {"error": str(e)}
        ), 500


@app.route("/api/findings")
def api_findings():

    force = (
        request.args.get(
            "refresh",
            "0"
        )
        == "1"
    )

    try:

        return jsonify(
            assessment_service
            .get_posture(
                force=force
            )
        )

    except Exception as e:

        return jsonify(
            {"error": str(e)}
        ), 500


# --- Firewall Data Functions (individual connector calls) ---

@app.route("/api/firewall/inventory")
def api_firewall_inventory():
    try:
        return jsonify(firewall_data_service.get_inventory() or {"error": "No data from firewall"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/firewall/health")
def api_firewall_health():
    try:
        return jsonify(firewall_data_service.get_health_status() or {"error": "No data from firewall"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/firewall/ha")
def api_firewall_ha():
    try:
        return jsonify(firewall_data_service.get_ha_configuration() or {"error": "No data from firewall"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/firewall/policy")
def api_firewall_policy():
    try:
        return jsonify(firewall_data_service.get_policy_configuration() or {"error": "No data from firewall"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/firewall/services")
def api_firewall_services():
    try:
        return jsonify(firewall_data_service.get_security_services() or {"error": "No data from firewall"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/firewall/status")
def api_firewall_status():
    try:
        return jsonify(firewall_data_service.get_full_status())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/firewall/routing")
def api_firewall_routing():
    try:
        return jsonify(firewall_data_service.get_routing_configuration() or {"error": "No data from firewall"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/firewall/vpn")
def api_firewall_vpn():
    try:
        return jsonify(firewall_data_service.get_vpn_configuration() or {"error": "No data from firewall"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/firewall/logging")
def api_firewall_logging():
    try:
        return jsonify(firewall_data_service.get_logging_configuration() or {"error": "No data from firewall"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/firewall/administration")
def api_firewall_administration():
    try:
        return jsonify(firewall_data_service.get_administration_configuration() or {"error": "No data from firewall"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/firewall/zone-protection")
def api_firewall_zone_protection():
    try:
        return jsonify(firewall_data_service.get_zone_protection_configuration() or {"error": "No data from firewall"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/firewall/backup")
def api_firewall_backup():
    try:
        return jsonify(firewall_data_service.get_backup_configuration() or {"error": "No data from firewall"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/summary")
def api_summary():

    try:

        result = (
            assessment_service
            .get_executive_summary_pdf(
                force=True
            )
        )

        summary = result["summary"]

        payload = dict(summary)
        payload["download_url"] = url_for(
            "static",
            filename=result["download_url"]
        )

        agent = agents_service.get_connected_agent()
        report_history_service.append_report({
            "name": result["filename"].replace(".pdf", ""),
            "type": "Executive Summary",
            "generated_by": (agent or {}).get("name", "Firewall Auditor"),
            "ts": time.time(),
            "status": "Completed",
            "size": file_size_label(result["local_file"]),
            "download_url": result["download_url"],
        })

        return jsonify(payload)

    except Exception as e:

        return jsonify(
            {"error": str(e)}
        ), 500


@app.route("/api/excel")
def api_excel():

    try:

        result = (
            assessment_service
            .get_excel_report(
                force=True
            )
        )

        payload = dict(result)

        if result.get("local_file"):

            payload["download_url"] = url_for(
                "static",
                filename=result["download_url"]
            )

        agent = agents_service.get_connected_agent()
        report_history_service.append_report({
            "name": "Assessment_Workbook_{0}".format(timeutil.ist_now().strftime("%b_%Y")),
            "type": "Workbook",
            "generated_by": (agent or {}).get("name", "Firewall Auditor"),
            "ts": time.time(),
            "status": "Completed",
            "size": file_size_label(result.get("local_file")),
            "download_url": result.get("download_url"),
        })

        return jsonify(payload)

    except Exception as e:

        return jsonify(
            {"error": str(e)}
        ), 500


@app.route("/download-workbook")
def download_workbook():

    try:

        result = (
            assessment_service
            .get_excel_report(
                force=True
            )
        )

        local_file = result.get("local_file")
        filename = "PaloAlto_Assessment.xlsx"

        agent = agents_service.get_connected_agent()
        report_history_service.append_report({
            "name": "Assessment_Workbook_{0}".format(timeutil.ist_now().strftime("%b_%Y")),
            "type": "Workbook",
            "generated_by": (agent or {}).get("name", "Firewall Auditor"),
            "ts": time.time(),
            "status": "Completed",
            "size": file_size_label(local_file),
            "download_url": "reports/{0}".format(filename),
        })

        return send_file(
            local_file,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:

        return jsonify(
            {"error": str(e)}
        ), 500


@app.route("/api/agents")
def api_agents():

    return jsonify(
        {"agents": agents_service.list_agents()}
    )


@app.route("/api/agents", methods=["POST"])
def api_agents_add():

    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    endpoint = (payload.get("endpoint") or "").strip()
    api_key = (payload.get("api_key") or "").strip()

    if not name or not endpoint or not api_key:
        return jsonify(
            {"error": "Name, endpoint, and API key are required."}
        ), 400

    agent = agents_service.add_agent(
        name=name,
        type_name=(payload.get("type") or "Custom Agent").strip(),
        endpoint=endpoint,
        api_key=api_key,
        model=(payload.get("model") or "gpt-5.1").strip(),
    )

    return jsonify({"status": "connected", "agent": agent}), 201


@app.route("/api/chat", methods=["POST"])
def api_chat():

    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip() or None
    messages = payload.get("messages")
    conversation_id = (payload.get("conversation_id") or "").strip() or None
    agent_id = (payload.get("agent_id") or "").strip() or None
    tool = payload.get("tool")

    if not message and not messages:
        return jsonify({"error": "message is required."}), 400

    try:
        result = gateway.chat(
            user_id=current_user_id(),
            message=message,
            messages=messages,
            conversation_id=conversation_id,
            agent_id=agent_id,
            tool=tool,
        )
        return jsonify(
            {
                "reply": result.get("reply"),
                "usage": result.get("usage") or {},
                "latency_ms": result.get("latency_ms"),
                "model": result.get("model"),
                "agent": result.get("agent"),
                "conversation_id": result.get("conversation_id"),
            }
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/tools")
def api_tools():

    return jsonify(
        {"tools": gateway.tools()}
    )


@app.route("/api/conversations")
def api_conversations():

    return jsonify(
        {"conversations": gateway.conversations(user_id=current_user_id())}
    )


@app.route("/api/conversations/<conversation_id>/messages", methods=["GET"])
def api_conversation_messages(conversation_id):

    messages = session_manager.get_messages(
        conversation_id,
        user_id=current_user_id(),
    )
    return jsonify({"messages": messages})


@app.route("/api/conversations/<conversation_id>/messages", methods=["POST"])
def api_conversation_messages_add(conversation_id):

    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages") or []
    session_manager.add_messages(
        conversation_id,
        messages,
        user_id=current_user_id(),
    )
    return jsonify({"status": "ok"})


@app.route("/api/conversations/<conversation_id>/clear", methods=["POST"])
def api_conversation_clear(conversation_id):

    session_manager.clear_conversation(
        conversation_id,
        user_id=current_user_id(),
    )
    return jsonify({"status": "ok"})


@app.route("/api/me")
def api_me():

    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"user": user})


@app.route("/api/insights")
def api_insights():

    return jsonify(insights_service.summarize())


@app.route("/api/insights/conversation/<conversation_id>")
def api_insights_conversation(conversation_id):

    summary = insights_service.summarize_conversation(conversation_id)
    return jsonify({"conversation": summary})


@app.route("/api/dashboard")
def api_dashboard():

    try:

        return jsonify(
            dashboard_service.get_dashboard()
        )

    except Exception as e:

        return jsonify(
            {"error": str(e)}
        ), 500


@app.route("/api/reports")
def api_reports():

    return jsonify(
        {"reports": report_history_service.list_reports()}
    )


@app.route("/api/system-status")
def api_system_status():

    return jsonify(
        system_status_service.get_system_status()
    )


@app.route("/api/telemetry-map")
def api_telemetry_map():

    agent_id = (request.args.get("agent_id") or "").strip() or None

    return jsonify(
        telemetry_map_service.build_map(agent_id=agent_id)
    )


@app.route("/api/telemetry-map/history")
def api_telemetry_map_history():

    agent_id = (request.args.get("agent_id") or "").strip() or None

    return jsonify(
        telemetry_map_service.get_history(agent_id=agent_id)
    )


# --------------------------------------------------
# START
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8003,
        debug=True
    )
