import logging

from services.common import (
    success_response,
    error_response,
    get_body
)

from connectors.sentinel_connector import (
    get_incident
)


def get_incident_service(req):

    try:

        body = get_body(req)

        incident_id = body.get(
            "incident_id"
        )

        if not incident_id:

            return error_response(
                "incident_id is required",
                400
            )

        result = get_incident(
            incident_id
        )

        return success_response(
            result
        )

    except Exception as ex:

        logging.exception(ex)

        return error_response(ex)