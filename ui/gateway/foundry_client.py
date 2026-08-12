import json
import time

import requests

from config import keyvault

CHAT_TIMEOUT = 90

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "run_compliance_assessment",
            "description": "Run a compliance assessment against the firewall and return the compliance results summary.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_full_assessment",
            "description": "Run the full firewall assessment and return detailed results.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "executive_summary",
            "description": "Generate an executive summary of the latest firewall assessment.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_excel_report",
            "description": "Generate an Excel report of the firewall assessment results.",
            "parameters": {"type": "object", "properties": {}},
        },
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
            "Azure OpenAI returned HTTP {status}: {body}".format(
                status=response.status_code,
                body=response.text[:300],
            )
        )

    return response.json()


def _resolve_api_key(agent):
    return keyvault.get_secret("foundry-api-key") or agent.get("api_key", "")


def _extract_reply(data):
    choices = data.get("choices") or []
    if not choices:
        return None, None
    msg = choices[0].get("message") or {}
    content = (msg.get("content") or "").strip() or None
    tool_calls = msg.get("tool_calls") or None
    return content, tool_calls


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


def chat(agent, messages):
    from gateway import tools as tool_registry

    llm_endpoint = (agent.get("llm_endpoint") or "").rstrip("/")
    api_key = _resolve_api_key(agent)
    model = agent.get("model", "gpt-5.1")

    if not llm_endpoint or not api_key:
        raise ValueError("Agent is missing the Azure OpenAI endpoint or API key.")

    url = llm_endpoint + "/chat/completions"

    conversation = [
        {"role": m.get("role", "user"), "content": m.get("content", "")}
        for m in messages
        if m.get("role") in ("user", "assistant", "system")
    ]

    sys_prompt = _system_prompt(agent)
    if sys_prompt:
        conversation.insert(0, {"role": "system", "content": sys_prompt})

    started = time.monotonic()
    total_usage = {}

    # First LLM call — may return tool_calls
    data = _post(url, api_key, {
        "model": model,
        "messages": conversation,
        "tools": TOOL_SCHEMAS,
    })

    content, tool_calls = _extract_reply(data)
    usage = data.get("usage") or {}
    total_usage = dict(usage)

    # Handle tool calls — loop until LLM stops requesting tools
    max_rounds = 3
    while tool_calls and max_rounds > 0:
        max_rounds -= 1

        assistant_msg = {
            "role": "assistant",
            "tool_calls": tool_calls,
        }
        if content:
            assistant_msg["content"] = content
        conversation.append(assistant_msg)

        for tc in tool_calls:
            fn = tc.get("function") or {}
            tool_name = fn.get("name", "")
            args_str = fn.get("arguments") or "{}"
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                args = {}

            try:
                tool_result = tool_registry.call_tool(tool_name, **args)
                result_text = json.dumps(tool_result, default=str)
            except Exception as e:
                result_text = json.dumps({"error": str(e)})

            conversation.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": result_text,
            })

        data = _post(url, api_key, {
            "model": model,
            "messages": conversation,
            "tools": TOOL_SCHEMAS,
        })

        content, tool_calls = _extract_reply(data)
        usage = data.get("usage") or {}
        if usage.get("total_tokens"):
            total_usage["total_tokens"] = total_usage.get("total_tokens", 0) + usage.get("total_tokens", 0)
            total_usage["prompt_tokens"] = total_usage.get("prompt_tokens", 0) + usage.get("prompt_tokens", 0)
            total_usage["completion_tokens"] = total_usage.get("completion_tokens", 0) + usage.get("completion_tokens", 0)

    if content is None:
        content = "Assessment completed. Check the outputs above for detailed results."

    latency_ms = int((time.monotonic() - started) * 1000)

    return {
        "reply": content,
        "usage": total_usage,
        "latency_ms": latency_ms,
        "model": data.get("model") or model,
    }
