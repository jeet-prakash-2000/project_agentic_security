import json
import os
import datetime


SUBSCRIPTION_ID = os.getenv(
    "AZURE_SUBSCRIPTION_ID",
    "d9fd032b-1860-443b-a0a4-10f67bf0dd44"
)

DEFAULT_RESOURCE_GROUP = os.getenv(
    "AZURE_RESOURCE_GROUP",
    "LTIM-CLOUDSEC-AGENTIC-RG01"
)

DEFAULT_LOCATION = os.getenv("AZURE_LOCATION", "centralindia")


def utc_now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def mock_azure_response(endpoint, params, success_data):
    return {
        "endpoint": endpoint,
        "parameters": params,
        "success": True,
        "data": success_data,
        "note": "Simulated response. Replace with live Azure SDK call for production.",
    }


def resolve_sdk_call():
    use_sdk = os.getenv("AZURE_USE_SDK", "").lower() in ("1", "true", "yes")
    if use_sdk:
        try:
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()
            return credential, True
        except Exception:
            pass
    return None, False
