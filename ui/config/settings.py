import os

from config import keyvault

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "ltm-security-platform-dev-secret-key-change-me",
)

BASE_URL = keyvault.get_secret(
    "firewall-function-url",
    default=(
        "https://network-security-firewall-agent-frcrcqg0ejaddte2."
        "southindia-01.azurewebsites.net/api"
    ),
)

FUNCTION_KEY = keyvault.get_secret(
    "firewall-function-key",
    default="PLACEHOLDER_REPLACE_WITH_YOUR_FUNCTION_KEY",
)

FULL_ASSESSMENT_KEY = keyvault.get_secret(
    "firewall-full-assessment-key",
    default="PLACEHOLDER_REPLACE_WITH_YOUR_FULL_ASSESSMENT_KEY",
)

EXCEL_KEY = keyvault.get_secret(
    "firewall-excel-key",
    default="PLACEHOLDER_REPLACE_WITH_YOUR_EXCEL_KEY",
)

EXECUTIVE_SUMMARY_KEY = keyvault.get_secret(
    "firewall-executive-summary-key",
    default="PLACEHOLDER_REPLACE_WITH_YOUR_EXECUTIVE_SUMMARY_KEY",
)

LIVE_ENABLED = True

LIVE_TIMEOUT = 60

CACHE_TTL = 120

SAMPLE_ASSESSMENT_ENABLED = True

APP_INSIGHTS_CONNECTION_STRING = keyvault.get_secret(
    "app-insights-connection-string",
    default=(
        "InstrumentationKey=d0289f46-5019-4176-856c-cd30b5dc2114;"
        "IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;"
        "LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/;"
        "ApplicationId=2eee2d29-508b-4621-a9ba-6f2ae6c6b5de"
    ),
)

APP_INSIGHTS_ENABLED = True
