import logging

from services.common import (
    success_response,
    error_response,
    get_body
)

from connectors.network_connector import (
    restore_vm_connectivity
)


def reconnect_vm_service(req):

    try:

        body = get_body(req)

        result = restore_vm_connectivity(
            body["vm_name"],
            body["resource_group"]
        )

        return success_response(
            result
        )

    except Exception as ex:

        logging.exception(ex)

        return error_response(ex)