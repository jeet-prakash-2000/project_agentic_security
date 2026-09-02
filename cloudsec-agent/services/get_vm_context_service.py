import logging

from services.common import (
    success_response,
    error_response,
    get_body
)

from connectors.vm_connector import (
    get_vm_context
)


def get_vm_context_service(req):

    try:

        body = get_body(req)

        vm_name = body.get(
            "vm_name"
        )

        resource_group = body.get(
            "resource_group"
        )

        if not vm_name:

            return error_response(
                "vm_name is required",
                400
            )

        if not resource_group:

            return error_response(
                "resource_group is required",
                400
            )

        result = get_vm_context(
            vm_name,
            resource_group
        )

        return success_response(
            result
        )

    except Exception as ex:

        logging.exception(ex)

        return error_response(ex)