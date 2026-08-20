import time

from services import agents_service
from services import assessment_service
from services import insights_service
from services import telemetry_map_service
from gateway.agent_gateway import gateway


def _agent_health_card(agent, stats):
    if not agent:
        return None

    agent_id = agent.get("id", "")

    try:
        map_data = telemetry_map_service.build_map(agent_id=agent_id)
        map_summary = map_data.get("summary") or {}
    except Exception:
        map_summary = {}

    metrics = telemetry_map_service.get_metrics(agent_id)
    requests = int(metrics.get("requests", 0))
    errors = int(metrics.get("errors", 0))
    success_rate = round((1 - errors / requests) * 100, 1) if requests else None

    try:
        tools = len(gateway.tools())
    except Exception:
        tools = 0

    health_score = map_summary.get("avg_health_score")
    status = "Degraded"
    if not agent.get("connected"):
        status = "Offline"
    elif health_score is None or health_score >= 70:
        status = "Healthy"
    elif health_score >= 40:
        status = "Degraded"
    else:
        status = "Faulted"

    insights = insights_service.summarize()
    agent_insight = None
    for item in insights.get("agents", []):
        if item.get("agent_id") == agent_id:
            agent_insight = item
            break

    return {
        "id": agent_id,
        "name": agent.get("name", ""),
        "type": agent.get("type", ""),
        "model": agent.get("model", ""),
        "status": status,
        "connected": bool(agent.get("connected")),
        "tools": tools,
        "success_rate": success_rate,
        "health_score": health_score,
        "last_assessment_ts": (stats or {}).get("last_assessment_ts"),
        "assessments_run": int((stats or {}).get("assessments_run", 0)),
        "avg_latency_ms": (agent_insight or {}).get("avg_latency_ms"),
        "cost": (agent_insight or {}).get("cost"),
        "tokens": (agent_insight or {}).get("total_tokens"),
    }


def get_dashboard():
    connected = agents_service.get_connected_agent()
    stats = assessment_service.get_assessment_stats()

    try:
        assessment = assessment_service.get_full_assessment()
    except Exception:
        assessment = {}

    summary = assessment.get("summary", {})
    findings = assessment.get("findings", [])

    total_controls = int(summary.get("total_controls", 0))
    compliant = int(summary.get("compliant", 0))
    non_compliant = int(summary.get("non_compliant", 0))
    not_assessed = int(summary.get("not_assessed", 0))

    compliance_score = (
        round(compliant / total_controls * 100) if total_controls else 0
    )

    critical = sum(1 for f in findings if (f.get("risk") or "").upper() == "CRITICAL")
    high = sum(1 for f in findings if (f.get("risk") or "").upper() == "HIGH")

    insights = insights_service.summarize()
    totals = insights.get("totals", {})
    total_tokens = int(totals.get("total_tokens", 0))
    total_cost = round(float(totals.get("cost", 0)), 4)

    drivers = []
    for agent in insights.get("agents", []):
        drivers.append(
            {
                "agent_id": agent.get("agent_id", ""),
                "name": agent.get("agent_name", "Agent"),
                "model": agent.get("model", ""),
                "cost": round(float(agent.get("cost", 0)), 4),
                "tokens": int(agent.get("total_tokens", 0)),
            }
        )
    drivers.sort(key=lambda d: d["cost"], reverse=True)

    health_cards = []
    agents = agents_service.list_agents()
    for agent in agents:
        card = _agent_health_card(agent, stats)
        if card:
            health_cards.append(card)
    health_cards.sort(key=lambda c: c.get("connected"), reverse=True)

    scored = [c.get("health_score") for c in health_cards if c.get("health_score") is not None]
    avg_health = round(sum(scored) / len(scored)) if scored else None

    return {
        "compliance": {
            "total_controls": total_controls,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "not_assessed": not_assessed,
            "compliance_score": compliance_score,
            "source": assessment.get("_source", "sample"),
        },
        "findings": {
            "critical": critical,
            "high": high,
            "open": len(findings),
        },
        "cost": {
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "top_drivers": drivers[:3],
        },
        "assessments_run": int((stats or {}).get("assessments_run", 0)),
        "avg_health": avg_health,
        "agents": health_cards,
        "history": assessment_service.get_history(),
        "generated_at": time.time(),
    }
