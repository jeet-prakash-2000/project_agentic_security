import os

from azure.identity import DefaultAzureCredential


credential = DefaultAzureCredential()

SUBSCRIPTION_ID = os.getenv(
    "AZURE_SUBSCRIPTION_ID"
)

if not SUBSCRIPTION_ID:
    raise RuntimeError(
        "AZURE_SUBSCRIPTION_ID is not configured."
    )


def get_management_token():

    return credential.get_token(
        "https://management.azure.com/.default"
    ).token


def get_log_analytics_token():

    return credential.get_token(
        "https://api.loganalytics.io/.default"
    ).token