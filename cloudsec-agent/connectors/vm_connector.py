from azure.mgmt.compute import (
    ComputeManagementClient
)

from connectors.auth import (
    credential,
    SUBSCRIPTION_ID
)


compute_client = (
    ComputeManagementClient(
        credential,
        SUBSCRIPTION_ID
    )
)


def get_vm_context(
    vm_name: str,
    resource_group: str
):

    vm = (
        compute_client
        .virtual_machines
        .get(
            resource_group,
            vm_name
        )
    )

    instance_view = (
        compute_client
        .virtual_machines
        .instance_view(
            resource_group,
            vm_name
        )
    )

    power_state = "Unknown"

    for status in instance_view.statuses:

        if (
            status.code and
            status.code.startswith(
                "PowerState/"
            )
        ):

            power_state = (
                status.display_status
            )

            break

    return {

        "vm_name":
            vm.name,

        "resource_group":
            resource_group,

        "location":
            vm.location,

        "size":
            vm.hardware_profile.vm_size,

        "os_type":
            str(
                vm.storage_profile
                .os_disk
                .os_type
            ),

        "power_state":
            power_state
    }


def get_vm_instance_view(
    vm_name: str,
    resource_group: str
):

    instance_view = (
        compute_client
        .virtual_machines
        .instance_view(
            resource_group,
            vm_name
        )
    )

    statuses = []

    for status in instance_view.statuses:

        statuses.append({

            "code":
                status.code,

            "display_status":
                status.display_status,

            "message":
                getattr(
                    status,
                    "message",
                    None
                )
        })

    return {

        "vm_name":
            vm_name,

        "resource_group":
            resource_group,

        "statuses":
            statuses
    }


def start_vm(
    vm_name: str,
    resource_group: str
):

    poller = (
        compute_client
        .virtual_machines
        .begin_start(
            resource_group,
            vm_name
        )
    )

    poller.result()

    return {

        "status":
            "success",

        "operation":
            "start",

        "vm_name":
            vm_name,

        "message":
            f"{vm_name} started successfully"
    }


def stop_vm(
    vm_name: str,
    resource_group: str
):

    poller = (
        compute_client
        .virtual_machines
        .begin_power_off(
            resource_group,
            vm_name
        )
    )

    poller.result()

    return {

        "status":
            "success",

        "operation":
            "stop",

        "vm_name":
            vm_name,

        "message":
            f"{vm_name} stopped successfully"
    }


def restart_vm(
    vm_name: str,
    resource_group: str
):

    poller = (
        compute_client
        .virtual_machines
        .begin_restart(
            resource_group,
            vm_name
        )
    )

    poller.result()

    return {

        "status":
            "success",

        "operation":
            "restart",

        "vm_name":
            vm_name,

        "message":
            f"{vm_name} restarted successfully"
    }