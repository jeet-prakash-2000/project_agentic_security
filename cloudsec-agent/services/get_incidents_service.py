import logging

from services.common import (
    success_response,
    error_response,
    get_body
)

from connectors.sentinel_connector import (
    get_incidents_by_period
)


def get_incidents_service(req):

    try:

        body = get_body(req)

        period = body.get(
            "period",
            "daily"
        )

        incidents = get_incidents_by_period(
            period
        )

        return success_response(
            incidents
        )

    except Exception as ex:

        logging.exception(ex)

        