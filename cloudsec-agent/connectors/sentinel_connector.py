import os
import re
import requests

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from connectors.auth import (
    get_management_token,
    SUBSCRIPTION_ID
)


RESOURCE_GROUP = os.getenv(
    "SENTINEL_RESOURCE_GROUP"
)

WORKSPACE_NAME = os.getenv(
    "SENTINEL_WORKSPACE_NAME"
)

API_VERSION = "2023-02-01-preview"


class SentinelConnector:

    def _headers(self):

        return {
            "Authorization": (
                f"Bearer {get_management_token()}"
            ),
            "Content-Type":
                "application/json"
        }

    def _incidents_url(self):

        return (
            "https://management.azure.com"
            f"/subscriptions/{SUBSCRIPTION_ID}"
            f"/resourceGroups/{RESOURCE_GROUP}"
            "/providers/Microsoft.OperationalInsights"
            f"/workspaces/{WORKSPACE_NAME}"
            "/providers/Microsoft.SecurityInsights"
            "/incidents"
        )

    def _extract_vm_name(
        self,
        incident
    ):

        properties = (
            incident.get(
                "properties",
                {}
            )
        )

        title = properties.get(
            "title",
            ""
        )

        description = properties.get(
            "description",
            ""
        )

        text = (
            f"{title} {description}"
        )

        match = re.search(
            r"CloudSec-[A-Za-z0-9\-]+",
            text
        )

        if match:
            return match.group()

        match = re.search(
            r"VM:\s*([^\n]+)",
            description
        )

        if match:
            return match.group(1).strip()

        return None

    def _extract_resource_group(
        self,
        incident
    ):

        properties = (
            incident.get(
                "properties",
                {}
            )
        )

        description = properties.get(
            "description",
            ""
        )

        match = re.search(
            r"Resource Group:\s*([^\n]+)",
            description
        )

        if match:
            return match.group(1).strip()

        return None

    def list_incidents(self):

        url = (
            f"{self._incidents_url()}"
            f"?api-version={API_VERSION}"
        )

        response = requests.get(
            url,
            headers=self._headers(),
            timeout=60
        )

        response.raise_for_status()

        return response.json().get(
            "value",
            []
        )

    def get_incidents_by_period(
        self,
        period
    ):

        incidents = self.list_incidents()

        now = datetime.now(
            timezone.utc
        )

        period = (
            period or "daily"
        ).lower()

        if period == "daily":

            cutoff = (
                now -
                timedelta(days=1)
            )

        elif period == "weekly":

            cutoff = (
                now -
                timedelta(days=7)
            )

        elif period == "monthly":

            cutoff = (
                now -
                timedelta(days=30)
            )

        else:

            raise ValueError(
                "period must be daily, weekly or monthly"
            )

        results = []

        for incident in incidents:

            properties = (
                incident.get(
                    "properties",
                    {}
                )
            )

            created_time = (
                properties.get(
                    "createdTimeUtc"
                )
            )

            if not created_time:
                continue

            created_dt = (
                datetime.fromisoformat(
                    created_time.replace(
                        "Z",
                        "+00:00"
                    )
                )
            )

            if created_dt < cutoff:
                continue

            results.append({

                "incident_id":
                    incident.get(
                        "name"
                    ),

                "incident_number":
                    properties.get(
                        "incidentNumber"
                    ),

                "title":
                    properties.get(
                        "title"
                    ),

                "severity":
                    properties.get(
                        "severity"
                    ),

                "status":
                    properties.get(
                        "status"
                    ),

                "created_time":
                    created_time
            })

        return sorted(
            results,
            key=lambda x: (
                x.get(
                    "incident_number"
                ) or 0
            ),
            reverse=True
        )

    def get_incident(
        self,
        incident_id
    ):

        incidents = (
            self.list_incidents()
        )

        target_incident = None

        if str(
            incident_id
        ).isdigit():

            incident_number = int(
                incident_id
            )

            for incident in incidents:

                properties = (
                    incident.get(
                        "properties",
                        {}
                    )
                )

                if (
                    properties.get(
                        "incidentNumber"
                    )
                    ==
                    incident_number
                ):

                    target_incident = (
                        incident
                    )

                    break

        else:

            for incident in incidents:

                if (
                    incident.get(
                        "name"
                    )
                    ==
                    incident_id
                ):

                    target_incident = (
                        incident
                    )

                    break

        if not target_incident:

            raise Exception(
                f"Incident {incident_id} not found"
            )

        properties = (
            target_incident.get(
                "properties",
                {}
            )
        )

        return {

            "incident_id":
                target_incident.get(
                    "name"
                ),

            "incident_number":
                properties.get(
                    "incidentNumber"
                ),

            "title":
                properties.get(
                    "title"
                ),

            "description":
                properties.get(
                    "description"
                ),

            "severity":
                properties.get(
                    "severity"
                ),

            "status":
                properties.get(
                    "status"
                ),

            "created_time":
                properties.get(
                    "createdTimeUtc"
                ),

            "last_modified_time":
                properties.get(
                    "lastModifiedTimeUtc"
                ),

            "vm_name":
                self._extract_vm_name(
                    target_incident
                ),

            "resource_group":
                self._extract_resource_group(
                    target_incident
                )
        }

    def generate_incident_summary(
        self,
        incident_id
    ):

        incident = (
            self.get_incident(
                incident_id
            )
        )

        summary = f"""
Incident Number: {incident['incident_number']}

Title: {incident['title']}

Severity: {incident['severity']}

Status: {incident['status']}

VM Name: {incident['vm_name']}

Resource Group: {incident['resource_group']}

Description:
{incident['description']}
"""

        return {

            "incident_id":
                incident[
                    "incident_id"
                ],

            "incident_number":
                incident[
                    "incident_number"
                ],

            "summary":
                summary.strip()
        }


_connector = SentinelConnector()


def get_incidents_by_period(
    period
):

    return (
        _connector
        .get_incidents_by_period(
            period
        )
    )


def get_incident(
    incident_id
):

    return (
        _connector
        .get_incident(
            incident_id
        )
    )


def generate_incident_summary(
    incident_id
):

    return (
        _connector
        .generate_incident_summary(
            incident_id
        )
    )