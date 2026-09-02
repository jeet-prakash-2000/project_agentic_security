import logging

from services.common import (
    success_response,
    error_response,
    get_body
)

from connectors.vm_connector import (
    restart_vm
)


def restart_vm_service(req):

    try:

        body = get_body(req)

        result = restart_vm(
            body["vm_name"],
            body["resource_group"]
        )

        return success_response(
            result
        )

    except Exception as ex:

        logging.exception(ex)

        return error_response(ex)