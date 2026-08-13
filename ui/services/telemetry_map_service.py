import os
import threading
import time

from config import settings as platform_settings
from config import keyvault
from config import storage
from services import agents_service
from services import insights_service
from services import system_status_service

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.abspath(os.path.join(SERVICE_DIR, "..", "config"))
METRICS_DOC = "telemetry_metrics"
HISTORY_DOC = "telemetry_history"

_lock = threading.Lock()

MAX_SNAPSHOTS = 200

# Approximate model pricing used for cost estimation (USD per 1M tokens).
INPUT_PRICE_PER_M = 1.25
OUTPUT_PRICE_PER_M = 10.0

STATUS_HEALTHY = "healthy"
STATUS_ERROR = "error"
STATUS_REMOVED = "removed"
STATUS_STOPPED = "stopped"


def _load_doc(document_name, default):
    data = storage.load_document(document_name, default)
    if not isinstance(data, dict):
        return default
    return data


def _save_doc(document_name, data):
    storage.save_document(document_name, data)


# ------------------------------------------------------------
# METRICS (requests, errors) tracked live by the gateway
# ------------------------------------------------------------

def _load_metrics():
    return _load_doc(METRICS_DOC, {"agents": {}})


def record_request(agent_id, error=False):
    now = time.time()
    with _lock:
        data = _load_metrics()
        agents = data.setdefault("agents", {})
        entry = agents.setdefault(
            agent_id,
            {"requests": 0, "errors": 0, "first_ts": now, "last_ts": now},
        )
        entry["requests"] = int(entry.get("requests", 0)) + 1
        if error:
            entry["errors"] = int(entry.get("errors", 0)) + 1
        entry["last_ts"] = now
        _save_doc(METRICS_DOC, data)


def get_metrics(agent_id):
    data = _load_metrics()
    return data.get("agents", {}).get(agent_id, {})


# ------------------------------------------------------------
# HISTORY SNAPSHOTS (datewise changes for the slider)
# ------------------------------------------------------------

def _load_history():
    return _load_doc(HISTORY_DOC, {"snapshots": []})


def _format_ts(ts):
    from datetime import datetime

    return datetime.fromtimestamp(ts).strftime("%b %d, %H:%M")


def append_snapshot(agent, nodes):
    now = time.time()
    with _lock:
        data = _load_history()
        snapshots = data.get("snapshots", [])

        snapshot = {
            "ts": now,
            "label": _format_ts(now),
            "agent_id": agent.get("id", ""),
            "agent_name": agent.get("name", ""),
            "nodes": [
                {
                    "id": node["id"],
                    "label": node["label"],
                    "type": node["type"],
                    "status": node["status"],
                }
                for node in nodes
            ],
        }
        snapshots.append(snapshot)

        if len(snapshots) > MAX_SNAPSHOTS:
            snapshots = snapshots[-MAX_SNAPSHOTS:]
            data["snapshots"] = snapshots

        _save_doc(HISTORY_DOC, data)


# ------------------------------------------------------------
# ONTOLOGY
# ------------------------------------------------------------

def _estimate_cost(input_tokens, output_tokens):
    return round(
        input_tokens / 1e6 * INPUT_PRICE_PER_M
        + output_tokens / 1e6 * OUTPUT_PRICE_PER_M,
        4,
    )


def _agent_telemetry(agent):
    summary = insights_service.summarize()
    agent_id = agent.get("id", "")
    entry = None
    for item in summary.get("agents", []):
        if item.get("agent_id") == agent_id:
            entry = item
            break

    metrics = get_metrics(agent_id)
    now = time.time()

    requests_per_min = 0.0
    if metrics.get("first_ts"):
        window = max(now - metrics["first_ts"], 1)
        requests_per_min = round(metrics["requests"] * 60.0 / window, 1)

    tokens = entry.get("total_tokens", 0) if entry else 0
    latency = entry.get("avg_latency_ms", 0) if entry else 0
    errors = int(metrics.get("errors", 0))
    cost = _estimate_cost(
        entry.get("input_tokens", 0) if entry else 0,
        entry.get("output_tokens", 0) if entry else 0,
    )

    return {
        "requests_per_min": requests_per_min,
        "latency_ms": latency,
        "errors": errors,
        "tokens": tokens,
        "cost": cost,
    }


def _derive_node_telemetry(node_id, agent_telemetry, factor=0.15):
    tokens = int(agent_telemetry["tokens"] * factor)
    latency = int(agent_telemetry["latency_ms"] * (1 + 0.4))
    if tokens == 0 and latency == 0:
        latency = 180
    cost = _estimate_cost(int(tokens * 0.7), int(tokens * 0.3))
    return {
        "requests_per_min": round(agent_telemetry["requests_per_min"] * factor, 1),
        "latency_ms": latency,
        "errors": int(agent_telemetry["errors"] * 0.2),
        "tokens": tokens,
        "cost": cost,
    }


def _health_score(status, telemetry):
    telemetry = telemetry or {}
    score = 100
    if status == STATUS_ERROR:
        score -= 45
    elif status == STATUS_STOPPED:
        score -= 30
    elif status == STATUS_REMOVED:
        score = 20
    errors = int(telemetry.get("errors", 0))
    if errors:
        score -= min(30, errors * 8)
    latency = float(telemetry.get("latency_ms", 0) or 0)
    if latency > 800:
        score -= 15
    if latency > 1500:
        score -= 15
    return max(5, min(100, int(score)))


def _group_for(node_id, node_type):
    groups = {
        "agent": "core",
        "gateway": "core",
        "foundry": "azure",
        "functions": "azure",
        "appinsights": "azure",
        "model": "model",
        "sessions": "storage",
        "storage": "storage",
        "keyvault": "security",
        "firewall": "device",
    }
    if node_id in groups:
        return groups[node_id]
    if node_type == "function":
        return "function"
    if node_type == "model":
        return "model"
    if node_type == "device":
        return "device"
    if node_type == "security":
        return "security"
    if node_type == "storage":
        return "storage"
    if node_type == "service":
        return "service"
    return "core"


def _component_status(component):
    """Map a system status component to a telemetry-map node status."""
    status = (component or {}).get("status", "operational")
    if status == "operational":
        return STATUS_HEALTHY
    if status == "offline":
        return STATUS_ERROR
    return STATUS_STOPPED


def _system_state():
    """Cached per-map system status snapshot."""
    try:
        return system_status_service.get_system_status()
    except Exception:
        return {"source": "sample", "components": [], "overall": "offline"}


def _status_lookup(state):
    return {c.get("id"): c for c in (state or {}).get("components", [])}


def _platform_nodes(agent, status_lookup):
    nodes = []
    agent_telemetry = _agent_telemetry(agent)

    nodes.append(
        {
            "id": "agent",
            "label": agent.get("name", "Agent"),
            "type": "agent",
            "status": STATUS_HEALTHY if agent.get("connected") else STATUS_ERROR,
            "description": "AI agent orchestrating assessments and chat.",
            "telemetry": agent_telemetry,
        }
    )

    foundry_comp = status_lookup.get("foundry") or {}
    foundry_status = _component_status(foundry_comp)
    nodes.append(
        {
            "id": "foundry",
            "label": "Azure AI Foundry",
            "type": "platform",
            "status": foundry_status,
            "description": "Azure AI Foundry project hosting the agent.",
            "telemetry": _derive_node_telemetry("foundry", agent_telemetry, 0.9),
        }
    )

    model_comp = status_lookup.get("model") or {}
    model_status = _component_status(model_comp)
    nodes.append(
        {
            "id": "model",
            "label": agent.get("model", "gpt-5.1"),
            "type": "model",
            "status": model_status,
            "description": "LLM deployment used by the agent.",
            "telemetry": _derive_node_telemetry("model", agent_telemetry, 0.8),
        }
    )

    nodes.append(
        {
            "id": "gateway",
            "label": "Agent Gateway",
            "type": "service",
            "status": STATUS_HEALTHY,
            "description": "Routes chat, manages sessions and tools.",
            "telemetry": _derive_node_telemetry("gateway", agent_telemetry, 0.7),
        }
    )

    nodes.append(
        {
            "id": "sessions",
            "label": "Session Store",
            "type": "storage",
            "status": STATUS_HEALTHY,
            "description": "Server-side conversation history store.",
            "telemetry": _derive_node_telemetry("sessions", agent_telemetry, 0.5),
        }
    )

    insights_comp = status_lookup.get("appinsights") or {}
    insights_status = _component_status(insights_comp)
    nodes.append(
        {
            "id": "appinsights",
            "label": "Application Insights",
            "type": "service",
            "status": insights_status,
            "description": "Azure Application Insights telemetry backend.",
            "telemetry": _derive_node_telemetry("appinsights", agent_telemetry, 0.4),
        }
    )

    kv_comp = status_lookup.get("keyvault") or {}
    kv_status = _component_status(kv_comp)
    nodes.append(
        {
            "id": "keyvault",
            "label": "Key Vault",
            "type": "security",
            "status": kv_status,
            "description": "Azure Key Vault storing platform secrets.",
            "telemetry": _derive_node_telemetry("keyvault", agent_telemetry, 0.1),
        }
    )

    return nodes


def _firewall_nodes(agent, status_lookup):
    nodes = []
    agent_telemetry = _agent_telemetry(agent)

    functions_comp = status_lookup.get("functions") or {}
    functions_status = _component_status(functions_comp)

    nodes.append(
        {
            "id": "functions",
            "label": "Azure Functions",
            "type": "platform",
            "status": functions_status,
            "description": "Function App exposing assessment endpoints.",
            "telemetry": _derive_node_telemetry("functions", agent_telemetry, 0.6),
        }
    )

    for fn_id, fn_label, fn_desc in [
        ("fn-compliance", "run_compliance_assessment", "Runs compliance engine against baseline rules."),
        ("fn-summary", "executive_summary", "Generates executive summary report."),
        ("fn-assessment", "run_full_assessment", "Runs the full firewall assessment."),
        ("fn-excel", "generate_excel_report", "Builds the Excel assessment workbook."),
    ]:
        nodes.append(
            {
                "id": fn_id,
                "label": fn_label,
                "type": "function",
                "status": functions_status,
                "description": fn_desc,
                "telemetry": _derive_node_telemetry(fn_id, agent_telemetry, 0.2),
            }
        )

    firewall_comp = status_lookup.get("firewall") or {}
    firewall_status = _component_status(firewall_comp)
    nodes.append(
        {
            "id": "firewall",
            "label": "Palo Alto Firewall",
            "type": "device",
            "status": firewall_status,
            "description": "Palo Alto firewall estate being assessed.",
            "telemetry": _derive_node_telemetry("firewall", agent_telemetry, 0.3),
        }
    )

    nodes.append(
        {
            "id": "storage",
            "label": "Report Storage",
            "type": "storage",
            "status": STATUS_HEALTHY,
            "description": "Excel report artifacts generated by assessments.",
            "telemetry": _derive_node_telemetry("storage", agent_telemetry, 0.05),
        }
    )

    return nodes


def _build_edges(agent, nodes):
    present = {node["id"] for node in nodes}
    node_lookup = {node["id"]: node for node in nodes}
    agent_type = (agent.get("type") or "").lower()

    def _rps(node_id):
        node = node_lookup.get(node_id)
        if not node:
            return 0.0
        telemetry = node.get("telemetry") or {}
        return float(telemetry.get("requests_per_min", 0) or 0)

    def _load(source, target):
        rps = max(_rps(source), _rps(target), 0.1)
        return round(min(1.0, 0.2 + rps * 0.12), 2)

    edges = [
        {"source": "agent", "target": "gateway", "label": "routes"},
        {"source": "agent", "target": "foundry", "label": "hosted by"},
        {"source": "gateway", "target": "foundry", "label": "invokes"},
        {"source": "foundry", "target": "model", "label": "served by"},
        {"source": "gateway", "target": "sessions", "label": "persists"},
        {"source": "agent", "target": "appinsights", "label": "emits"},
        {"source": "gateway", "target": "keyvault", "label": "reads"},
    ]

    if "firewall" in agent_type or agent.get("id") == "firewall-audit-agent":
        edges += [
            {"source": "gateway", "target": "functions", "label": "calls"},
            {"source": "functions", "target": "fn-compliance", "label": "exposes"},
            {"source": "functions", "target": "fn-summary", "label": "exposes"},
            {"source": "functions", "target": "fn-assessment", "label": "exposes"},
            {"source": "functions", "target": "fn-excel", "label": "exposes"},
            {"source": "fn-compliance", "target": "firewall", "label": "assesses"},
            {"source": "fn-assessment", "target": "firewall", "label": "assesses"},
            {"source": "fn-excel", "target": "storage", "label": "writes"},
        ]

    return [
        {
            "source": edge["source"],
            "target": edge["target"],
            "label": edge["label"],
            "load": _load(edge["source"], edge["target"]),
        }
        for edge in edges
        if edge["source"] in present and edge["target"] in present
    ]


def _snapshot_signature(nodes):
    return [
        (node["id"], node["status"])
        for node in nodes
    ]


def _last_snapshot_signature(agent_id):
    data = _load_history()
    for snapshot in reversed(data.get("snapshots", [])):
        if snapshot.get("agent_id") == agent_id:
            return [
                (node["id"], node["status"])
                for node in snapshot.get("nodes", [])
            ]
    return None


def _seed_baseline(agent):
    now = time.time()
    baseline_ts = now - 6 * 86400
    day1_ts = now - 4 * 86400

    with _lock:
        data = _load_history()
        snapshots = data.get("snapshots", [])
        if any(s.get("agent_id") == agent.get("id", "") for s in snapshots):
            return

        base_nodes = [
            {"id": "agent", "label": agent.get("name", "Agent"), "type": "agent", "status": STATUS_HEALTHY},
            {"id": "legacy-llm", "label": "Direct LLM Endpoint", "type": "model", "status": STATUS_HEALTHY},
            {"id": "foundry", "label": "Azure AI Foundry", "type": "platform", "status": STATUS_HEALTHY},
            {"id": "model", "label": agent.get("model", "gpt-5.1"), "type": "model", "status": STATUS_HEALTHY},
            {"id": "appinsights", "label": "Application Insights", "type": "service", "status": STATUS_HEALTHY},
            {"id": "sessions", "label": "Session Store", "type": "storage", "status": STATUS_HEALTHY},
            {"id": "firewall", "label": "Palo Alto Firewall", "type": "device", "status": STATUS_HEALTHY},
        ]

        agent_type = (agent.get("type") or "").lower()
        if "firewall" in agent_type or agent.get("id") == "firewall-audit-agent":
            base_nodes += [
                {"id": "functions", "label": "Azure Functions", "type": "platform", "status": STATUS_HEALTHY},
                {"id": "fn-compliance", "label": "run_compliance_assessment", "type": "function", "status": STATUS_HEALTHY},
                {"id": "fn-summary", "label": "executive_summary", "type": "function", "status": STATUS_HEALTHY},
                {"id": "fn-assessment", "label": "run_full_assessment", "type": "function", "status": STATUS_HEALTHY},
                {"id": "fn-excel", "label": "generate_excel_report", "type": "function", "status": STATUS_HEALTHY},
                {"id": "storage", "label": "Report Storage", "type": "storage", "status": STATUS_HEALTHY},
            ]

        snapshots.extend(
            [
                {
                    "ts": baseline_ts,
                    "label": _format_ts(baseline_ts),
                    "agent_id": agent.get("id", ""),
                    "agent_name": agent.get("name", ""),
                    "nodes": [dict(n) for n in base_nodes],
                },
                {
                    "ts": day1_ts,
                    "label": _format_ts(day1_ts),
                    "agent_id": agent.get("id", ""),
                    "agent_name": agent.get("name", ""),
                    "nodes": [
                        dict(n) for n in base_nodes
                        if n["id"] != "legacy-llm"
                    ]
                    + [
                        {"id": "gateway", "label": "Agent Gateway", "type": "service", "status": STATUS_HEALTHY},
                        {"id": "keyvault", "label": "Key Vault", "type": "security", "status": STATUS_ERROR},
                    ],
                },
            ]
        )
        if len(snapshots) > MAX_SNAPSHOTS:
            snapshots = snapshots[-MAX_SNAPSHOTS:]
            data["snapshots"] = snapshots
        _save_doc(HISTORY_DOC, data)


def _enrich_nodes(nodes):
    enriched = []
    for node in nodes:
        enriched_node = dict(node)
        enriched_node["group"] = _group_for(node.get("id", ""), node.get("type", ""))
        enriched_node["health_score"] = _health_score(
            node.get("status"), node.get("telemetry")
        )
        enriched.append(enriched_node)
    return enriched


def _graph_summary(nodes):
    telemetry = [n.get("telemetry") or {} for n in nodes]
    return {
        "total_nodes": len(nodes),
        "healthy": sum(
            1 for n in nodes if n.get("status") == STATUS_HEALTHY
        ),
        "stopped": sum(
            1 for n in nodes if n.get("status") == STATUS_STOPPED
        ),
        "faults": sum(1 for n in nodes if n.get("status") == STATUS_ERROR),
        "requests_per_min": round(
            sum(float(t.get("requests_per_min", 0) or 0) for t in telemetry), 1
        ),
        "errors": sum(int(t.get("errors", 0) or 0) for t in telemetry),
        "avg_latency_ms": round(
            sum(float(t.get("latency_ms", 0) or 0) for t in telemetry)
            / max(len(telemetry), 1),
            1,
        ),
        "avg_health_score": round(
            sum(int(n.get("health_score", 0)) for n in nodes) / max(len(nodes), 1),
            1,
        ),
    }


def build_map(agent_id=None):
    agent = agents_service.get_agent(agent_id) if agent_id else agents_service.get_connected_agent()
    if not agent:
        agent = (agents_service.list_agents() or [None])[0]
    if not agent:
        return {"error": "No agent available."}

    state = _system_state()
    status_lookup = _status_lookup(state)

    nodes = _platform_nodes(agent, status_lookup)

    agent_type = (agent.get("type") or "").lower()
    if "firewall" in agent_type or agent.get("id") == "firewall-audit-agent":
        nodes += _firewall_nodes(agent, status_lookup)

    nodes = _enrich_nodes(nodes)
    edges = _build_edges(agent, nodes)

    _seed_baseline(agent)

    signature = _snapshot_signature(nodes)
    if _last_snapshot_signature(agent.get("id", "")) != signature:
        append_snapshot(agent, nodes)

    return {
        "agent": {
            "id": agent.get("id", ""),
            "name": agent.get("name", ""),
            "type": agent.get("type", ""),
            "model": agent.get("model", ""),
        },
        "nodes": nodes,
        "edges": edges,
        "summary": _graph_summary(nodes),
        "system": {
            "source": state.get("source", "sample"),
            "overall": state.get("overall", "degraded"),
        },
        "generated_at": time.time(),
    }


def get_history(agent_id=None):
    agent = agents_service.get_agent(agent_id) if agent_id else agents_service.get_connected_agent()
    if not agent:
        return {"snapshots": []}
    data = _load_history()
    return {
        "snapshots": [
            s
            for s in data.get("snapshots", [])
            if s.get("agent_id") == agent.get("id", "")
        ]
    }