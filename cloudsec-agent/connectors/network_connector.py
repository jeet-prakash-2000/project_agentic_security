from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import (
    NetworkSecurityGroup,
    SecurityRule
)

from connectors.auth import (
    credential,
    SUBSCRIPTION_ID
)

compute_client = ComputeManagementClient(
    credential,
    SUBSCRIPTION_ID
)

network_client = NetworkManagementClient(
    credential,
    SUBSCRIPTION_ID
)

ISOLATION_NSG_NAME = "cloudsec-isolation-nsg"


def get_primary_nic(
    resource_group: str,
    vm_name: str
):
    vm = compute_client.virtual_machines.get(
        resource_group,
        vm_name
    )

    nic_id = (
        vm.network_profile
        .network_interfaces[0]
        .id
    )

    nic_name = nic_id.split("/")[-1]

    return network_client.network_interfaces.get(
        resource_group,
        nic_name
    )


def get_network_interface(
    resource_group: str,
    nic_name: str
):
    nic = network_client.network_interfaces.get(
        resource_group,
        nic_name
    )

    return {
        "id": nic.id,
        "name": nic.name,
        "location": nic.location,
        "private_ip": (
            nic.ip_configurations[0].private_ip_address
            if nic.ip_configurations
            else None
        )
    }


def create_isolation_nsg(
    resource_group: str,
    location: str,
    nsg_name: str = ISOLATION_NSG_NAME
):
    try:
        existing = (
            network_client
            .network_security_groups
            .get(
                resource_group,
                nsg_name
            )
        )
        return existing

    except Exception:
        pass

    nsg = (
        network_client
        .network_security_groups
        .begin_create_or_update(
            resource_group,
            nsg_name,
            NetworkSecurityGroup(
                location=location
            )
        )
        .result()
    )

    return nsg


def block_all_traffic(
    resource_group: str,
    nsg_name: str
):

    inbound_rule = SecurityRule(
        protocol="*",
        source_port_range="*",
        destination_port_range="*",
        source_address_prefix="*",
        destination_address_prefix="*",
        access="Deny",
        priority=300,
        direction="Inbound"
    )

    outbound_rule = SecurityRule(
        protocol="*",
        source_port_range="*",
        destination_port_range="*",
        source_address_prefix="*",
        destination_address_prefix="*",
        access="Deny",
        priority=301,
        direction="Outbound"
    )

    try:
        (
            network_client
            .security_rules
            .begin_create_or_update(
                resource_group,
                nsg_name,
                "deny-all-inbound",
                inbound_rule
            )
            .result()
        )
    except Exception:
        pass

    try:
        (
            network_client
            .security_rules
            .begin_create_or_update(
                resource_group,
                nsg_name,
                "deny-all-outbound",
                outbound_rule
            )
            .result()
        )
    except Exception:
        pass

    return {
        "status": "success",
        "message": "All traffic blocked"
    }


def attach_nsg_to_nic(
    resource_group: str,
    nic_name: str,
    nsg_id: str
):
    nic = (
        network_client
        .network_interfaces
        .get(
            resource_group,
            nic_name
        )
    )

    nic.network_security_group = {
        "id": nsg_id
    }

    (
        network_client
        .network_interfaces
        .begin_create_or_update(
            resource_group,
            nic_name,
            nic
        )
        .result()
    )

    return {
        "status": "success",
        "nic_name": nic_name
    }


def isolate_vm(
    vm_name: str,
    resource_group: str
):
    nic = get_primary_nic(
        resource_group,
        vm_name
    )

    nsg = create_isolation_nsg(
        resource_group,
        nic.location
    )

    block_all_traffic(
        resource_group,
        nsg.name
    )

    attach_nsg_to_nic(
        resource_group,
        nic.name,
        nsg.id
    )

    return {
        "status": "success",
        "action": "containment",
        "vm_name": vm_name,
        "nic_name": nic.name,
        "nsg_name": nsg.name,
        "message": "VM isolated successfully"
    }


def restore_vm_connectivity(
    vm_name: str,
    resource_group: str
):
    nic = get_primary_nic(
        resource_group,
        vm_name
    )

    nic.network_security_group = None

    (
        network_client
        .network_interfaces
        .begin_create_or_update(
            resource_group,
            nic.name,
            nic
        )
        .result()
    )

    return {
        "status": "success",
        "action": "recovery",
        "vm_name": vm_name,
        "nic_name": nic.name,
        "message": "Connectivity restored successfully"
    }
