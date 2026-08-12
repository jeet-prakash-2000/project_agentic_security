import threading
import time

import requests

from config import settings
from config import keyvault
from services import agents_service

CACHE_TTL = 30

STATUS_OPERATIONAL = "operational"
STATUS_DEGRADED = "degraded"
STATUS_OFFLINE = "offline"

_lock = threading.Lock()
_cache = {"ts": 0.0, "data": None}


def _probe_functions():
    """Determine whether the Azure Function App is running and reachable.

    Returns dict:
        {"reachable": bool, "firewall": bool, "latency_ms": int|None}
    """
    if not getattr(settings, "LIVE_ENABLED", False):
        return {"reachable": False, "firewall": False, "latency_ms": None}

    base = (getattr(settings, "BASE_URL", "") or "").rstrip("/")
    if not base:
        return {"reachable": False, "firewall": False, "latency_ms": None}

    started = time.monotonic()
    try:
        # Lightweight inventory probe: requires the app to be running AND the
        # firewall to be reachable for a 200. A 500 means the app is up but the
        # firewall could not be contacted.
        response = requests.get(
            base + "/get_inventory",
            params={"code": getattr(settings, "FUNCTION_KEY", "")},
            timeout=6,
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        return {
            "reachable": True,
            "firewall": response.status_code == 200,
            "latency_ms": latency_ms,
        }
    except Exception:
        latency_ms = int((time.monotonic() - started) * 1000)
        return {"reachable": False, "firewall": False, "latency_ms": latency_ms}


def _probe_agent_connection():
    connected = agents_service.get_connected_agent()
    if not connected:
        return False, None
    return True, connected


def get_system_status(force=False):
    now = time.time()
    with _lock:
        if (
            not force
            and _cache["data"]
            and now - _cache["ts"] < CACHE_TTL
        ):
            return _cache["data"]

    functions = _probe_functions()
    agent_connected, agent = _probe_agent_connection()

    components = []

    components.append(
        {
            "id": "agent",
            "label": "AI Agent",
            "status": STATUS_OPERATIONAL if agent_connected else STATUS_OFFLINE,
            "detail": (
                "Connected" if agent_connected else "No connected agent registered"
            ),
        }
    )

    components.append(
        {
            "id": "functions",
            "label": "Azure Functions",
            "status": (
                STATUS_OPERATIONAL
                if functions["reachable"]
                else STATUS_OFFLINE
            ),
            "detail": (
                "Running and reachable"
                if functions["reachable"]
                else "Function App stopped or unreachable"
            ),
            "latency_ms": functions["latency_ms"],
        }
    )

    components.append(
        {
            "id": "firewall",
            "label": "Palo Alto Firewall",
            "status": (
                STATUS_OPERATIONAL
                if functions["firewall"]
                else (STATUS_DEGRADED if functions["reachable"] else STATUS_OFFLINE)
            ),
            "detail": (
                "Reachable via Function App"
                if functions["firewall"]
                else (
                    "Firewall unreachable from Function App"
                    if functions["reachable"]
                    else "Not reachable — Function App stopped"
                )
            ),
        }
    )

    foundry_configured = bool(
        agent and agent.get("agent_endpoint") and agent.get("api_key")
    )
    components.append(
        {
            "id": "foundry",
            "label": "Azure AI Foundry",
            "status": (
                STATUS_OPERATIONAL
                if foundry_configured
                else STATUS_OFFLINE
            ),
            "detail": (
                "Project endpoint configured"
                if foundry_configured
                else "No Foundry project endpoint configured"
            ),
        }
    )

    model_configured = bool(agent and agent.get("model"))
    components.append(
        {
            "id": "model",
            "label": "LLM Model",
            "status": (
                STATUS_OPERATIONAL
                if model_configured
                else STATUS_OFFLINE
            ),
            "detail": (
                agent.get("model", "Model configured")
                if model_configured
                else "No model assigned"
            ),
        }
    )

    kv_configured = bool(keyvault.VAULT_URL)
    components.append(
        {
            "id": "keyvault",
            "label": "Key Vault",
            "status": (
                STATUS_OPERATIONAL
                if kv_configured
                else STATUS_DEGRADED
            ),
            "detail": (
                "Secrets vault configured"
                if kv_configured
                else "Key Vault not provisioned"
            ),
        }
    )

    ai_configured = bool(getattr(settings, "APP_INSIGHTS_ENABLED", False))
    components.append(
        {
            "id": "appinsights",
            "label": "Application Insights",
            "status": (
                STATUS_OPERATIONAL
                if ai_configured
                else STATUS_DEGRADED
            ),
            "detail": (
                "Telemetry enabled"
                if ai_configured
                else "Application Insights disabled"
            ),
        }
    )

    components.append(
        {
            "id": "gateway",
            "label": "Agent Gateway",
            "status": STATUS_OPERATIONAL,
            "detail": "Local gateway running",
        }
    )

    operational = sum(1 for c in components if c["status"] == STATUS_OPERATIONAL)
    degraded = sum(1 for c in components if c["status"] == STATUS_DEGRADED)
    offline = sum(1 for c in components if c["status"] == STATUS_OFFLINE)
    total = len(components)

    if operational == total:
        overall = STATUS_OPERATIONAL
    elif operational == 0:
        overall = STATUS_OFFLINE
    else:
        overall = STATUS_DEGRADED

    # Live data only when the Function App, firewall, and agent are all
    # running and connected. Otherwise the platform serves sample data.
    source = (
        "live"
        if functions["reachable"] and functions["firewall"] and agent_connected
        else "sample"
    )

    data = {
        "overall": overall,
        "source": source,
        "components": components,
        "counts": {
            "operational": operational,
            "degraded": degraded,
            "offline": offline,
            "total": total,
        },
        "checked_at": now,
    }

    with _lock:
        _cache["data"] = data
        _cache["ts"] = now

    return data
