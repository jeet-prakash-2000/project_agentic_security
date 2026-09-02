import logging

from services.common import (
    success_response,
    error_response,
    get_body
)

from connectors.network_connector import (
    isolate_vm
)


def isolate_vm_service(req):

    try:

        body = get_body(req)

        result = isolate_vm(
            body["vm_name"],
            body["resource_group"]
        )

        return success_response(
            result
        )

    except Exception as ex:

        logging.exception(ex)

        return error_response(ex)