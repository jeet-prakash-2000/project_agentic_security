import logging

from services.common import (
    success_response,
    error_response,
    get_body
)

from connectors.sentinel_connector import (
    generate_incident_summary
)


def generate_summary_service(req):

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

        summary = (
            generate_incident_summary(
                incident_id
            )
        )

        return success_response(
            summary
        )

    except Exception as ex:

        logging.exception(ex)

        return error_response(ex)