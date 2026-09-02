import logging

from services.common import (
    success_response,
    error_response,
    get_body
)

from connectors.vm_connector import (
    get_vm_instance_view
)


def get_vm_instance_view_service(req):

    try:

        body = get_body(req)

        result = get_vm_instance_view(
            body["vm_name"],
            body["resource_group"]
        )

        return success_response(
            result
        )

    except Exception as ex:

        logging.exception(ex)

        return error_response(ex)