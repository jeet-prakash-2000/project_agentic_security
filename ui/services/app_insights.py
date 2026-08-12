import datetime
import threading
import uuid

import requests

from config import settings as platform_settings

TRACK_TIMEOUT = 5


def _parse_connection_string(connection_string):
    parsed = {}
    for part in connection_string.split(";"):
        if "=" not in part:
            continue
        key, _, value = part.partition("=")
        parsed[key.strip()] = value.strip()
    return parsed


def _instrumentation_key():
    value = getattr(platform_settings, "APP_INSIGHTS_CONNECTION_STRING", "") or ""
    if not value:
        return None
    return _parse_connection_string(value).get("InstrumentationKey")


def _ingestion_endpoint():
    value = getattr(platform_settings, "APP_INSIGHTS_CONNECTION_STRING", "") or ""
    if not value:
        return None
    endpoint = _parse_connection_string(value).get("IngestionEndpoint", "")
    return endpoint.rstrip("/") if endpoint else None


def _envelope(event_name, properties, measurements):
    i_key = _instrumentation_key()
    if not i_key:
        return None
    return {
        "ver": 1,
        "name": "Microsoft.ApplicationInsights.Event",
        "time": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "sampleRate": 100,
        "iKey": i_key,
        "tags": {"ai.operation.id": str(uuid.uuid4())},
        "data": {
            "baseType": "EventData",
            "baseData": {
                "name": event_name,
                "properties": properties or {},
                "measurements": measurements or {},
            },
        },
    }


def _send(payload):
    if not getattr(platform_settings, "APP_INSIGHTS_ENABLED", False):
        return
    endpoint = _ingestion_endpoint()
    if not endpoint:
        return
    try:
        requests.post(
            endpoint + "/v2/track",
            json=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=TRACK_TIMEOUT,
        )
    except Exception:
        pass


def track_event(event_name, properties=None, measurements=None):
    envelope = _envelope(event_name, properties, measurements)
    if envelope is None:
        return
    _send([envelope])


def track_agent_chat(agent, usage, latency_ms, conversation_id=None):
    properties = {
        "agent_id": agent.get("id", ""),
        "agent_name": agent.get("name", ""),
        "agent_type": agent.get("type", ""),
        "model": agent.get("model", ""),
        "conversation_id": conversation_id or "",
    }

    usage = usage or {}
    details = usage.get("input_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or {}

    measurements = {
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "cached_tokens": details.get("cached_tokens", 0),
        "cache_write_tokens": details.get("cache_write_tokens", 0),
        "reasoning_tokens": output_details.get("reasoning_tokens", 0),
        "latency_ms": latency_ms or 0,
    }

    track_event(
        "agent.chat.tokens",
        properties=properties,
        measurements=measurements,
    )


def track_agent_error(agent, message, conversation_id=None):
    properties = {
        "agent_id": agent.get("id", ""),
        "agent_name": agent.get("name", ""),
        "conversation_id": conversation_id or "",
        "error": str(message)[:500],
    }
    track_event("agent.chat.error", properties=properties)


def _run_async(target, *args):
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()
