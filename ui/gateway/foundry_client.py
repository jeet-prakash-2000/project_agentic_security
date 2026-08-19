import json
import time

import requests

from config import keyvault

CHAT_TIMEOUT = 90

AGENTS_API_VERSION = "2025-05-01"

# Tool schemas in Azure AI Foundry Responses API format (flat function objects).
TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "run_compliance_assessment",
        "description": "Run a compliance assessment against the firewall and return the compliance results summary.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "run_full_assessment",
        "description": "Run the full firewall assessment and return detailed results.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "executive_summary",
        "description": "Generate an executive summary of the latest firewall assessment.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "generate_excel_report",
        "description": "Generate an Excel report of the firewall assessment results.",
        "parameters": {"type": "object", "properties": {}},
    },
]


def _post(url, api_key, payload):
    response = requests.post(
        url,
        headers={"api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=CHAT_TIMEOUT,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Azure AI Foundry returned HTTP {status}: {body}".format(
                status=response.status_code,
                body=response.text[:300],
            )
        )

    return response.json()


def _resolve_api_key(agent):
    return keyvault.get_secret("foundry-api-key") or agent.get("api_key", "")


def _system_prompt(agent):
    agent_type = (agent.get("type") or "").lower()
    agent_name = agent.get("name", "")
    if "firewall" in agent_type or "firewall" in agent_name.lower():
        return (
            "You are the Firewall Auditor, an AI security agent specialized in Palo Alto Networks firewall compliance. "
            "You have live access to a Palo Alto firewall (vmpafw01, PAN-OS 10.2.10-h9) and perform assessments across "
            "44 controls spanning inventory, health, HA, security policy, threat prevention, network segmentation, VPN, "
            "logging, administration, and backup. "
            "Use the `run_compliance_assessment` tool to get live assessment data, and `run_full_assessment` for detailed results. "
            "Use `executive_summary` for management-ready summaries and `generate_excel_report` to produce downloadable workbooks. "
            "When users ask about security posture, call the appropriate tool to get real data instead of guessing. "
            "Format responses with clear headings, bullet points, and severity indicators. "
            "Always reference the actual assessment data and offer to run a fresh assessment if needed."
        )
    if "cloud" in agent_type or "incident" in agent_type or "cloud" in agent_name.lower():
        return (
            "You are the Cloud Incident Response Agent, an AI security agent specialized in Azure cloud security incident response. "
            "Provide structured incident response guidance."
        )
    return (
        "You are an AI security agent on the LTM Security Platform. "
        "Provide concise, actionable security guidance. Format responses with clear headings and bullet points."
    )


def _normalize_messages(messages):
    return [
        {"role": m.get("role", "user"), "content": m.get("content", "")}
        for m in messages
        if m.get("role") in ("user", "assistant")
    ]


def _merge_usage(total, usage):
    for key in ("total_tokens", "prompt_tokens", "completion_tokens", "input_tokens", "output_tokens"):
        value = usage.get(key)
        if value:
            total[key] = total.get(key, 0) + value


def _call_tool(tool_registry, function_call):
    name = function_call.get("name", "")
    arguments = function_call.get("arguments") or "{}"
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError:
        args = {}
    try:
        result = tool_registry.call_tool(name, **args)
        return json.dumps(result, default=str)
    except Exception as error:
        return json.dumps({"error": str(error)})


def _extract_reply(data):
    content_parts = []
    function_calls = []
    for item in data.get("output") or []:
        item_type = item.get("type")
        if item_type == "message":
            for part in item.get("content") or []:
                if part.get("type") in ("output_text", "text"):
                    text = (part.get("text") or "").strip()
                    if text:
                        content_parts.append(text)
        elif item_type == "function_call":
            function_calls.append(item)
    content = "\n\n".join(content_parts).strip() or None
    return content, function_calls


def _function_call_item(function_call):
    return {
        "type": "function_call",
        "id": function_call.get("id", ""),
        "call_id": function_call.get("call_id", ""),
        "name": function_call.get("name", ""),
        "arguments": function_call.get("arguments", "{}"),
    }


def _responses_url(agent_endpoint):
    endpoint = agent_endpoint.rstrip("/")
    if endpoint.endswith("/openai/v1/responses"):
        return endpoint
    if endpoint.endswith("/openai/v1"):
        return endpoint + "/responses"
    return endpoint + "/openai/v1/responses"


def _entra_headers():
    from azure.identity import DefaultAzureCredential

    credential = DefaultAzureCredential()
    token = credential.get_token(
        "https://management.azure.com/.default"
    ).token
    return {
        "Authorization": "Bearer {0}".format(token),
        "Content-Type": "application/json",
    }


def _invoke_agent(agent, messages):
    """Invoke the Foundry Agent (assistant) server-side via the Agents API.

    The agent executes its connected tools (the firewall functions) server-side
    and returns the result, so the client never needs the individual function
    keys. Requires Azure Entra authentication (Managed Identity on Azure, or a
    service principal via environment variables locally).
    """
    base = (agent.get("agent_endpoint") or "").rstrip("/")
    agent_ref = (agent.get("agent_id") or "").strip()
    if not base or not agent_ref:
        raise ValueError("Agent is missing the agent endpoint or agent id.")

    headers = _entra_headers()
    params = {"api-version": AGENTS_API_VERSION}

    resp = requests.get(
        "{0}/assistants".format(base),
        params=params,
        headers=headers,
        timeout=CHAT_TIMEOUT,
    )
    resp.raise_for_status()
    assistants = (
        resp.json().get("data")
        or resp.json().get("value")
        or []
    )
    assistant = None
    for item in assistants:
        if item.get("name") == agent_ref or item.get("id") == agent_ref:
            assistant = item
            break
    if assistant is None:
        raise RuntimeError(
            "Agent '{0}' was not found.".format(agent_ref)
        )

    resp = requests.post(
        "{0}/threads".format(base),
        params=params,
        headers=headers,
        json={},
        timeout=CHAT_TIMEOUT,
    )
    resp.raise_for_status()
    thread_id = resp.json()["id"]

    text = ""
    for message in reversed(messages):
        if message.get("role") == "user":
            text = message.get("content") or ""
            break

    requests.post(
        "{0}/threads/{1}/messages".format(base, thread_id),
        params=params,
        headers=headers,
        json={"role": "user", "content": text},
        timeout=CHAT_TIMEOUT,
    ).raise_for_status()

    resp = requests.post(
        "{0}/threads/{1}/runs".format(base, thread_id),
        params=params,
        headers=headers,
        json={"assistant_id": assistant["id"]},
        timeout=CHAT_TIMEOUT,
    )
    resp.raise_for_status()
    run_id = resp.json()["id"]

    for _ in range(60):
        resp = requests.get(
            "{0}/threads/{1}/runs/{2}".format(base, thread_id, run_id),
            params=params,
            headers=headers,
            timeout=CHAT_TIMEOUT,
        )
        resp.raise_for_status()
        status = resp.json().get("status")
        if status == "completed":
            break
        if status in ("failed", "cancelled", "expired"):
            raise RuntimeError(
                "Agent run ended with status '{0}'.".format(status)
            )
        time.sleep(2)

    resp = requests.get(
        "{0}/threads/{1}/messages".format(base, thread_id),
        params=params,
        headers=headers,
        timeout=CHAT_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    reply = ""
    for message in data.get("data") or []:
        if message.get("role") != "assistant":
            continue
        for part in message.get("content") or []:
            if part.get("type") == "text":
                text_block = part.get("text") or {}
                reply += (
                    text_block.get("value")
                    if isinstance(text_block, dict)
                    else str(part.get("text") or "")
                )

    return {
        "reply": reply or None,
        "usage": {},
        "latency_ms": 0,
        "model": agent.get("model", ""),
    }


def chat(agent, messages):
    from gateway import tools as tool_registry

    if agent.get("agent_id"):
        try:
            result = _invoke_agent(agent, messages)
            if result.get("reply"):
                return result
        except Exception:
            pass

    agent_endpoint = (agent.get("agent_endpoint") or "").rstrip("/")
    api_key = _resolve_api_key(agent)
    model = agent.get("model", "gpt-5.1")

    if not agent_endpoint:
        raise ValueError("Agent is missing the agent endpoint.")
    if not api_key:
        raise ValueError("Agent is missing the API key.")

    conversation = _normalize_messages(messages)
    sys_prompt = _system_prompt(agent)
    url = _responses_url(agent_endpoint)

    started = time.monotonic()

    payload = {"model": model, "input": conversation, "tools": TOOL_SCHEMAS}
    if sys_prompt:
        payload["instructions"] = sys_prompt

    data = _post(url, api_key, payload)
    content, function_calls = _extract_reply(data)
    total_usage = dict(data.get("usage") or {})

    max_rounds = 3
    while function_calls and max_rounds > 0:
        max_rounds -= 1

        next_input = list(conversation)
        for function_call in function_calls:
            next_input.append(_function_call_item(function_call))
        for function_call in function_calls:
            next_input.append({
                "type": "function_call_output",
                "call_id": function_call.get("call_id") or function_call.get("id"),
                "output": _call_tool(tool_registry, function_call),
            })

        payload = {"model": model, "input": next_input, "tools": TOOL_SCHEMAS}
        if sys_prompt:
            payload["instructions"] = sys_prompt

        data = _post(url, api_key, payload)
        content, function_calls = _extract_reply(data)
        _merge_usage(total_usage, data.get("usage") or {})

    if content is None:
        content = "Assessment completed. Check the outputs above for detailed results."

    latency_ms = int((time.monotonic() - started) * 1000)

    return {
        "reply": content,
        "usage": total_usage,
        "latency_ms": latency_ms,
        "model": data.get("model") or model,
    }
