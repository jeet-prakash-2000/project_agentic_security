import json
import time

import requests

from config import keyvault

CHAT_TIMEOUT = 90

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


def chat(agent, messages):
    from gateway import tools as tool_registry

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
