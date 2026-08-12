import azure.functions as func
import json
import os
import logging

from connectors.sentinel_connector_cloudsec import SentinelConnector
from connectors.defender_connector_cloudsec import DefenderConnector
from connectors.compute_connector_cloudsec import ComputeConnector
from connectors.network_connector_cloudsec import NetworkConnector
from services.incident_analysis_cloudsec import TimelineBuilder, RiskAnalyzer
from services.report_generator_cloudsec import ReportGenerator
from services.action_logger_cloudsec import ActionLogger
from connectors.azure_config_cloudsec import utc_now_iso

app = func.FunctionApp()

sentinel = SentinelConnector()
defender = DefenderConnector()
compute = ComputeConnector()
network = NetworkConnector()
timeline_builder = TimelineBuilder()
risk_analyzer = RiskAnalyzer()
report_generator = ReportGenerator()


# =============================================================================
# PHASE 1: DETECTION LAYER
# =============================================================================

@app.route(route="GetSentinelIncident", methods=["POST"])
def GetSentinelIncident(req: func.HttpRequest):
    body = req.get_json()
    incident_id = body.get("incident_id", "TEST-001")
    result = sentinel.get_incident(incident_id)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Failed to retrieve incident", "detail": result}), status_code=500, mimetype="application/json")


@app.route(route="GetIncidentEntities", methods=["POST"])
def GetIncidentEntities(req: func.HttpRequest):
    body = req.get_json()
    incident_id = body.get("incident_id", "TEST-001")
    result = sentinel.get_incident_entities(incident_id)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Failed to retrieve entities", "detail": result}), status_code=500, mimetype="application/json")


# =============================================================================
# PHASE 2: ENRICHMENT LAYER
# =============================================================================

@app.route(route="GetVMContext", methods=["POST"])
def GetVMContext(req: func.HttpRequest):
    body = req.get_json()
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")
    result = compute.get_vm_context(vm_name, resource_group)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Failed to retrieve VM context"}), status_code=500, mimetype="application/json")


@app.route(route="GetDefenderAlertDetails", methods=["POST"])
def GetDefenderAlertDetails(req: func.HttpRequest):
    body = req.get_json()
    alert_id = body.get("alert_id", "ALERT-001")
    result = defender.get_alert_details(alert_id)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Failed to retrieve alert"}), status_code=500, mimetype="application/json")


@app.route(route="GetSecurityRecommendations", methods=["POST"])
def GetSecurityRecommendations(req: func.HttpRequest):
    body = req.get_json()
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")
    result = defender.get_security_recommendations(vm_name, resource_group)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Failed to retrieve recommendations"}), status_code=500, mimetype="application/json")


# =============================================================================
# PHASE 3: INVESTIGATION LAYER
# =============================================================================

@app.route(route="CollectVMEvidence", methods=["POST"])
def CollectVMEvidence(req: func.HttpRequest):
    body = req.get_json()
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")
    result = compute.collect_vm_evidence(vm_name, resource_group)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Failed to collect evidence"}), status_code=500, mimetype="application/json")


@app.route(route="BuildIncidentTimeline", methods=["POST"])
def BuildIncidentTimeline(req: func.HttpRequest):
    body = req.get_json()
    incident_id = body.get("incident_id", "TEST-001")
    alert_id = body.get("alert_id", "ALERT-001")
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")

    incident_result = sentinel.get_incident(incident_id)
    incident_data = incident_result["data"] if incident_result["success"] else {}
    alert_result = defender.get_alert_details(alert_id)
    alert_data = alert_result["data"] if alert_result["success"] else {}
    evidence_result = compute.collect_vm_evidence(vm_name, resource_group)
    evidence_data = evidence_result["data"] if evidence_result["success"] else None

    timeline = timeline_builder.build(incident_id, incident_data, alert_data, evidence_data)
    return func.HttpResponse(json.dumps(timeline), status_code=200, mimetype="application/json")


@app.route(route="AnalyzeRisk", methods=["POST"])
def AnalyzeRisk(req: func.HttpRequest):
    body = req.get_json()
    incident_id = body.get("incident_id", "TEST-001")
    alert_id = body.get("alert_id", "ALERT-001")
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")

    incident_result = sentinel.get_incident(incident_id)
    incident_data = incident_result["data"] if incident_result["success"] else {}
    alert_result = defender.get_alert_details(alert_id)
    alert_data = alert_result["data"] if alert_result["success"] else {}
    evidence_result = compute.collect_vm_evidence(vm_name, resource_group)
    evidence_data = evidence_result["data"] if evidence_result["success"] else None

    analysis = risk_analyzer.analyze(incident_data, alert_data, evidence_data)
    return func.HttpResponse(json.dumps(analysis), status_code=200, mimetype="application/json")


# =============================================================================
# PHASE 5: CONTAINMENT LAYER
# =============================================================================

@app.route(route="IsolateAzureVM", methods=["POST"])
def IsolateAzureVM(req: func.HttpRequest):
    body = req.get_json()
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")
    result = network.isolate_vm(vm_name, resource_group)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Containment failed"}), status_code=500, mimetype="application/json")


@app.route(route="StopAzureVM", methods=["POST"])
def StopAzureVM(req: func.HttpRequest):
    body = req.get_json()
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")
    result = compute.stop_vm(vm_name, resource_group)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Failed to stop VM"}), status_code=500, mimetype="application/json")


@app.route(route="BlockMaliciousIP", methods=["POST"])
def BlockMaliciousIP(req: func.HttpRequest):
    body = req.get_json()
    ip_address = body.get("ip_address")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")

    if not ip_address:
        return func.HttpResponse(json.dumps({"error": "ip_address is required"}), status_code=400, mimetype="application/json")

    result = network.block_malicious_ip(ip_address, resource_group)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Failed to block IP"}), status_code=500, mimetype="application/json")


# =============================================================================
# PHASE 6: ERADICATION LAYER
# =============================================================================

@app.route(route="RunSecurityScan", methods=["POST"])
def RunSecurityScan(req: func.HttpRequest):
    body = req.get_json()
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")
    result = compute.run_security_scan(vm_name, resource_group)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Security scan failed"}), status_code=500, mimetype="application/json")


@app.route(route="RemovePersistence", methods=["POST"])
def RemovePersistence(req: func.HttpRequest):
    body = req.get_json()
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")
    result = compute.remove_persistence(vm_name, resource_group)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Persistence removal failed"}), status_code=500, mimetype="application/json")


@app.route(route="PatchVM", methods=["POST"])
def PatchVM(req: func.HttpRequest):
    body = req.get_json()
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")
    result = compute.patch_vm(vm_name, resource_group)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Patch deployment failed"}), status_code=500, mimetype="application/json")


# =============================================================================
# PHASE 7: RECOVERY LAYER
# =============================================================================

@app.route(route="RestoreVMConnectivity", methods=["POST"])
def RestoreVMConnectivity(req: func.HttpRequest):
    body = req.get_json()
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")
    result = network.restore_vm_connectivity(vm_name, resource_group)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Recovery failed"}), status_code=500, mimetype="application/json")


@app.route(route="ValidateVMHealth", methods=["POST"])
def ValidateVMHealth(req: func.HttpRequest):
    body = req.get_json()
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")
    result = compute.validate_vm_health(vm_name, resource_group)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Health validation failed"}), status_code=500, mimetype="application/json")


# =============================================================================
# PHASE 8: REPORTING LAYER
# =============================================================================

@app.route(route="GenerateIncidentSummary", methods=["POST"])
def GenerateIncidentSummary(req: func.HttpRequest):
    body = req.get_json()
    incident_id = body.get("incident_id", "TEST-001")

    incident_result = sentinel.get_incident(incident_id)
    incident_data = incident_result["data"] if incident_result["success"] else {}

    action_log = body.get("action_log", ["VM isolated", "Evidence collected", "Risk assessment completed"])
    status = body.get("status", "Contained")

    summary = report_generator.generate_summary(incident_id, incident_data, action_log, status)
    return func.HttpResponse(json.dumps(summary), status_code=200, mimetype="application/json")


@app.route(route="GenerateTechnicalReport", methods=["POST"])
def GenerateTechnicalReport(req: func.HttpRequest):
    body = req.get_json()
    incident_id = body.get("incident_id", "TEST-001")
    alert_id = body.get("alert_id", "ALERT-001")
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")

    incident_result = sentinel.get_incident(incident_id)
    incident_data = incident_result["data"] if incident_result["success"] else {}
    alert_result = defender.get_alert_details(alert_id)
    alert_data = alert_result["data"] if alert_result["success"] else {}
    evidence_result = compute.collect_vm_evidence(vm_name, resource_group)
    evidence_data = evidence_result["data"] if evidence_result["success"] else None

    timeline = timeline_builder.build(incident_id, incident_data, alert_data, evidence_data)
    risk = risk_analyzer.analyze(incident_data, alert_data, evidence_data)

    actions = {
        "containment": ["VM isolated via NSG", "Malicious IP blocked"],
        "recovery": ["Connectivity restored", "Health validated"],
        "eradication": ["Persistence removed", "Security patches applied", "Malware scan completed"],
    }

    report = report_generator.generate_technical_report(incident_id, incident_data, evidence_data, timeline, risk, actions)
    return func.HttpResponse(json.dumps(report), status_code=200, mimetype="application/json")


@app.route(route="GenerateExecutiveReport", methods=["POST"])
def GenerateExecutiveReport(req: func.HttpRequest):
    body = req.get_json()
    incident_id = body.get("incident_id", "TEST-001")
    alert_id = body.get("alert_id", "ALERT-001")
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")

    incident_result = sentinel.get_incident(incident_id)
    incident_data = incident_result["data"] if incident_result["success"] else {}
    alert_result = defender.get_alert_details(alert_id)
    alert_data = alert_result["data"] if alert_result["success"] else {}
    evidence_result = compute.collect_vm_evidence(vm_name, resource_group)
    evidence_data = evidence_result["data"] if evidence_result["success"] else None

    risk = risk_analyzer.analyze(incident_data, alert_data, evidence_data)
    status = body.get("status", "Contained")
    cost_impact = body.get("cost_impact", "Estimated $1,200 in investigation and recovery effort")

    report = report_generator.generate_executive_report(incident_id, incident_data, risk, status, cost_impact)
    return func.HttpResponse(json.dumps(report), status_code=200, mimetype="application/json")


# =============================================================================
# PHASE 9: INCIDENT CLOSURE
# =============================================================================

@app.route(route="CloseIncident", methods=["POST"])
def CloseIncident(req: func.HttpRequest):
    body = req.get_json()
    incident_id = body.get("incident_id", "TEST-001")
    classification = body.get("classification", "TruePositive")
    comment = body.get("comment", "Incident resolved. VM contained, threat eradicated, connectivity restored after validation.")

    result = sentinel.close_incident(incident_id, classification, comment)

    if result["success"]:
        return func.HttpResponse(json.dumps(result["data"]), status_code=200, mimetype="application/json")
    return func.HttpResponse(json.dumps({"error": "Failed to close incident"}), status_code=500, mimetype="application/json")


# =============================================================================
# PHASE 10: END-TO-END ORCHESTRATION
# =============================================================================

@app.route(route="RunFullIncidentResponse", methods=["POST"])
def RunFullIncidentResponse(req: func.HttpRequest):
    body = req.get_json()
    incident_id = body.get("incident_id", "TEST-001")
    alert_id = body.get("alert_id", "ALERT-001")
    vm_name = body.get("vm_name", "agentic-vm-01")
    resource_group = body.get("resource_group", "LTIM-CLOUDSEC-AGENTIC-RG01")

    logger = ActionLogger()
    response_stages = {}
    errors = []

    def safe_call(stage_name, func_name, result_dict):
        try:
            response_stages[stage_name] = result_dict["data"] if result_dict.get("success") else result_dict
            logger.record(stage_name.split("_")[-1] if "_" in stage_name else stage_name, func_name, "Completed")
        except Exception as e:
            errors.append({"stage": stage_name, "error": str(e)})
            response_stages[stage_name] = {"error": str(e)}
            logger.record(stage_name, func_name, f"Failed: {e}", "failed")

    safe_call("Detection_GetIncident", "GetSentinelIncident", sentinel.get_incident(incident_id))
    safe_call("Detection_GetEntities", "GetIncidentEntities", sentinel.get_incident_entities(incident_id))
    safe_call("Enrichment_GetDefenderAlert", "GetDefenderAlertDetails", defender.get_alert_details(alert_id))
    safe_call("Enrichment_GetVMContext", "GetVMContext", compute.get_vm_context(vm_name, resource_group))
    safe_call("Enrichment_SecurityRecommendations", "GetSecurityRecommendations", defender.get_security_recommendations(vm_name, resource_group))
    safe_call("Investigation_CollectEvidence", "CollectVMEvidence", compute.collect_vm_evidence(vm_name, resource_group))

    incident_data = sentinel.get_incident(incident_id)
    alert_data = defender.get_alert_details(alert_id)
    evidence_data = compute.collect_vm_evidence(vm_name, resource_group)

    incident_data = incident_data["data"] if incident_data["success"] else {}
    alert_data = alert_data["data"] if alert_data["success"] else {}
    evidence_data = evidence_data["data"] if evidence_data["success"] else None

    timeline = timeline_builder.build(incident_id, incident_data, alert_data, evidence_data)
    response_stages["Investigation_Timeline"] = timeline

    risk = risk_analyzer.analyze(incident_data, alert_data, evidence_data)
    response_stages["Decision_RiskAnalysis"] = risk

    should_contain = risk["risk_score"] >= 60

    if should_contain:
        safe_call("Containment_IsolateVM", "IsolateAzureVM", network.isolate_vm(vm_name, resource_group))
        entities = sentinel.get_incident_entities(incident_id)
        entities_data = entities["data"] if entities["success"] else {}
        malicious_ips = [e["address"] for e in entities_data.get("entities", []) if e.get("type") == "malicious-ip"]
        for ip in malicious_ips:
            safe_call(f"Containment_BlockIP_{ip}", "BlockMaliciousIP", network.block_malicious_ip(ip, resource_group))

        safe_call("Eradication_SecurityScan", "RunSecurityScan", compute.run_security_scan(vm_name, resource_group))
        safe_call("Eradication_RemovePersistence", "RemovePersistence", compute.remove_persistence(vm_name, resource_group))
        safe_call("Eradication_PatchVM", "PatchVM", compute.patch_vm(vm_name, resource_group))

        safe_call("Recovery_RestoreConnectivity", "RestoreVMConnectivity", network.restore_vm_connectivity(vm_name, resource_group))
        safe_call("Recovery_ValidateHealth", "ValidateVMHealth", compute.validate_vm_health(vm_name, resource_group))

        response_stages["Reporting_Summary"] = report_generator.generate_summary(incident_id, incident_data, logger.to_summary(), risk["recommended_action"])
        safe_call("Closure_CloseIncident", "CloseIncident", sentinel.close_incident(
            incident_id, "TruePositive",
            f"Automated incident response completed. Risk score: {risk['risk_score']}. Action: {risk['recommended_action']}."
        ))
    else:
        response_stages["Decision_Note"] = "Risk below containment threshold. Monitoring only."
        response_stages["Reporting_Summary"] = report_generator.generate_summary(incident_id, incident_data, logger.to_summary(), "Monitoring")

    return func.HttpResponse(json.dumps(dict(
        incident_id=incident_id, vm_name=vm_name,
        risk_score=risk["risk_score"], risk_level=risk["risk_level"],
        recommended_action=risk["recommended_action"],
        stages=response_stages, action_log=logger.to_dict(),
        errors=errors, completed_at=utc_now_iso()
    )), status_code=200, mimetype="application/json")
