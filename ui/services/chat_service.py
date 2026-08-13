from gateway import foundry_client
from gateway.agent_gateway import gateway


def chat(agent, messages):
    return foundry_client.chat(agent, messages)


def send_message(messages, conversation_id=None, agent_id=None, user_id=None):
    result = gateway.chat(
        user_id=user_id or "anonymous",
        messages=messages,
        conversation_id=conversation_id,
        agent_id=agent_id,
    )
    return result


def send_single_message(message, conversation_id=None, agent_id=None, user_id=None):
    return gateway.chat(
        user_id=user_id or "anonymous",
        message=message,
        conversation_id=conversation_id,
        agent_id=agent_id,
    )
