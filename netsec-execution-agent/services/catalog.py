"""Playbook catalogue driving the NetSec Execution Agent.

Each playbook maps a workbook sheet to one bulk operation module and defines
the template columns plus sample rows used by ``build_template``.
"""

from netsec_execution.services import objects
from netsec_execution.services import network
from netsec_execution.services import policies

_SAMPLE = "sample-"


def _sample_domains():
    return "198.51.100.10/32, 198.51.100.11/32"


def _columns(*cols):
    return list(cols)


def _build_playbooks():
    playbooks = []

    # ------------------------------------------------------------------
    # OBJECTS
    # ------------------------------------------------------------------
    playbooks.append(
        {
            "id": "objects-addresses",
            "title": "Address Objects",
            "category": "Objects",
            "sheet": "Addresses",
            "summary": (
                "Bulk create, update or delete shared address objects "
                "(ip-netmask, ip-range or fqdn) from the Addresses sheet."
            ),
            "apply": objects.apply_addresses,
            "columns": _columns(
                "Action", "Name", "Address Type", "Address Value", "Description", "Tags"
            ),
            "examples": [
                {
                    "Action": "create", "Name": _SAMPLE + "web",
                    "Address Type": "ip-netmask", "Address Value": "198.51.100.10/32",
                    "Description": "sample web server",
                }
            ],
            "column_widths": {"A": 10, "B": 24, "C": 14, "D": 26, "E": 26, "F": 26},
        }
    )
    playbooks.append(
        {
            "id": "objects-address-groups",
            "title": "Address Groups",
            "category": "Objects",
            "sheet": "Address Groups",
            "summary": (
                "Bulk create, update or delete static address groups (member "
                "addresses or other groups)."
            ),
            "apply": objects.apply_address_groups,
            "columns": _columns("Action", "Name", "Group Type", "Members", "Description", "Tags"),
            "examples": [
                {
                    "Action": "create", "Name": _SAMPLE + "web-tier",
                    "Group Type": "static", "Members": "sample-web, sample-api",
                    "Description": "sample web tier group",
                }
            ],
            "column_widths": {"A": 10, "B": 24, "C": 12, "D": 34, "E": 26, "F": 26},
        }
    )
    playbooks.append(
        {
            "id": "objects-services",
            "title": "Service Objects",
            "category": "Objects",
            "sheet": "Services",
            "summary": (
                "Bulk create, update or delete TCP/UDP/SCTP service objects "
                "(protocol + port)."
            ),
            "apply": objects.apply_services,
            "columns": _columns(
                "Action", "Name", "Protocol", "Port", "Source Port", "Description", "Tags"
            ),
            "examples": [
                {
                    "Action": "create", "Name": _SAMPLE + "-https", "Protocol": "tcp",
                    "Port": "443", "Description": "sample HTTPS service",
                }
            ],
            "column_widths": {"A": 10, "B": 24, "C": 10, "D": 10, "E": 14, "F": 26, "G": 26},
        }
    )
    playbooks.append(
        {
            "id": "objects-service-groups",
            "title": "Service Groups",
            "category": "Objects",
            "sheet": "Service Groups",
            "summary": "Bulk create, update or delete service groups.",
            "apply": objects.apply_service_groups,
            "columns": _columns("Action", "Name", "Members", "Description", "Tags"),
            "examples": [
                {
                    "Action": "create", "Name": _SAMPLE + "-web-services",
                    "Members": "sample-https, sample-http",
                    "Description": "sample web service group",
                }
            ],
            "column_widths": {"A": 10, "B": 24, "C": 34, "D": 26, "E": 26},
        }
    )

    # ------------------------------------------------------------------
    # NETWORK
    # ------------------------------------------------------------------
    playbooks.append(
        {
            "id": "network-zones",
            "title": "Security Zones",
            "category": "Network",
            "sheet": "Zones",
            "summary": (
                "Bulk create, update or delete zones including layer3/layer2 "
                "interface membership, zone-protection and log settings."
            ),
            "apply": network.apply_zones,
            "columns": _columns(
                "Action", "Name", "Type", "Interfaces",
                "Zone Protection Profile", "Log Setting", "Enable User Identification",
            ),
            "examples": [
                {
                    "Action": "create", "Name": _SAMPLE + "-zone",
                    "Type": "layer3", "Interfaces": "ethernet1/2",
                }
            ],
            "column_widths": {"A": 10, "B": 20, "C": 12, "D": 30, "E": 24, "F": 24, "G": 20},
        }
    )
    playbooks.append(
        {
            "id": "network-virtual-routers",
            "title": "Virtual Routers",
            "category": "Network",
            "sheet": "Virtual Routers",
            "summary": (
                "Bulk create, update or delete virtual routers and their "
                "layer3 interface membership."
            ),
            "apply": network.apply_virtual_routers,
            "columns": _columns("Action", "Name", "Interfaces", "Description"),
            "examples": [
                {
                    "Action": "create", "Name": _SAMPLE + "-vr",
                    "Interfaces": "ethernet1/1, ethernet1/2",
                    "Description": "sample virtual router",
                }
            ],
            "column_widths": {"A": 10, "B": 22, "C": 34, "D": 26},
        }
    )
    playbooks.append(
        {
            "id": "network-static-routes",
            "title": "Static Routes",
            "category": "Network",
            "sheet": "Static Routes",
            "summary": (
                "Bulk create, update or delete static IPv4/IPv6 unicast routes "
                "on a virtual router."
            ),
            "apply": network.apply_static_routes,
            "columns": _columns(
                "Action", "Name", "Virtual Router", "Version", "Destination",
                "Next Hop Type", "Next Hop", "Interface", "Metric",
                "Admin Distance", "Description",
            ),
            "examples": [
                {
                    "Action": "create", "Name": _SAMPLE + "-default",
                    "Virtual Router": "default", "Version": "ipv4",
                    "Destination": "0.0.0.0/0", "Next Hop Type": "ip-address",
                    "Next Hop": "192.0.2.1", "Interface": "ethernet1/1",
                    "Metric": "10",
                }
            ],
            "column_widths": {
                "A": 10, "B": 22, "C": 18, "D": 10, "E": 18, "F": 14, "G": 18,
                "H": 16, "I": 10, "J": 14, "K": 26,
            },
        }
    )
    playbooks.append(
        {
            "id": "network-interface-mgmt",
            "title": "Interface Management Profiles",
            "category": "Network",
            "sheet": "Interface Management Profiles",
            "summary": (
                "Bulk create, update or delete interface management profiles "
                "(ping/telnet/ssh/https/http/snmp access)."
            ),
            "apply": network.apply_interface_management_profiles,
            "columns": _columns(
                "Action", "Name", "Ping", "Telnet", "SSH", "HTTPS", "HTTP",
                "SNMP", "Response Pages",
            ),
            "examples": [
                {
                    "Action": "create", "Name": _SAMPLE + "-mgmt",
                    "Ping": "yes", "SSH": "yes", "HTTPS": "yes",
                }
            ],
            "column_widths": {
                "A": 10, "B": 26, "C": 8, "D": 8, "E": 8, "F": 8, "G": 8,
                "H": 8, "I": 16,
            },
        }
    )
    playbooks.append(
        {
            "id": "network-interfaces",
            "title": "Layer3 Interfaces",
            "category": "Network",
            "sheet": "Interfaces",
            "summary": (
                "Bulk assign IP addresses, an interface management profile and "
                "MTU to layer3 ethernet interfaces."
            ),
            "apply": network.apply_interfaces,
            "columns": _columns(
                "Action", "Interface", "IP Addresses", "Management Profile", "MTU", "Description"
            ),
            "examples": [
                {
                    "Action": "update", "Interface": "ethernet1/1",
                    "IP Addresses": "10.0.0.1/24", "Management Profile": "ALLOW-PING-SSH",
                }
            ],
            "column_widths": {
                "A": 10, "B": 16, "C": 34, "D": 26, "E": 8, "F": 26,
            },
        }
    )

    # ------------------------------------------------------------------
    # SECURITY & NAT
    # ------------------------------------------------------------------
    playbooks.append(
        {
            "id": "policies-security-rules",
            "title": "Security Policies",
            "category": "Security & NAT",
            "sheet": "Security Rules",
            "summary": (
                "Bulk create, update or delete security rules with zone, "
                "source/destination, application, service and action columns."
            ),
            "apply": policies.apply_security_rules,
            "columns": _columns(
                "Action", "Name", "Description", "From", "To", "Source",
                "Destination", "Users", "Applications", "Services", "Categories",
                "Rule Action", "Log Setting", "Disabled",
            ),
            "examples": [
                {
                    "Action": "create", "Name": _SAMPLE + "-allow-web",
                    "From": "trust", "To": "untrust", "Source": "any",
                    "Destination": "sample-web", "Applications": "web-browsing",
                    "Services": "application-default", "Rule Action": "allow",
                }
            ],
            "column_widths": {
                "A": 10, "B": 26, "C": 28, "D": 14, "E": 14, "F": 18, "G": 20,
                "H": 18, "I": 20, "J": 22, "K": 18, "L": 12, "M": 20, "N": 10,
            },
        }
    )
    playbooks.append(
        {
            "id": "policies-nat-rules",
            "title": "NAT Policies",
            "category": "Security & NAT",
            "sheet": "NAT Rules",
            "summary": (
                "Bulk create, update or delete source / destination NAT rules "
                "(dynamic-ip-and-port, dynamic-ip, static-ip)."
            ),
            "apply": policies.apply_nat_rules,
            "columns": _columns(
                "Action", "Name", "Description", "From", "Source", "Destination",
                "Service", "To", "NAT Type", "Source Translation",
                "Translated Interface", "Source Translated Address",
                "Destination Translated Address", "Destination Translated Port",
                "Disabled",
            ),
            "examples": [
                {
                    "Action": "create", "Name": _SAMPLE + "-snat",
                    "From": "trust", "To": "untrust", "Source": _sample_domains(),
                    "Destination": "any", "Service": "any", "NAT Type": "source",
                    "Source Translation": "dynamic-ip-and-port",
                    "Translated Interface": "ethernet1/1",
                }
            ],
            "column_widths": {
                "A": 10, "B": 26, "C": 28, "D": 14, "E": 26, "F": 26, "G": 14,
                "H": 14, "I": 16, "J": 20, "K": 20, "L": 26, "M": 26, "N": 22, "O": 10,
            },
        }
    )

    return playbooks


PLAYBOOKS = _build_playbooks()

CATEGORIES = ["Objects", "Network", "Security & NAT"]


def list_playbooks():
    """Public catalog payload for the workspace playbook panel."""
    result = []
    for playbook in PLAYBOOKS:
        result.append(
            {
                "id": playbook["id"],
                "title": playbook["title"],
                "category": playbook["category"],
                "sheet": playbook["sheet"],
                "summary": playbook["summary"],
            }
        )
    return result


def find_playbook(playbook_id):
    for playbook in PLAYBOOKS:
        if playbook["id"] == playbook_id:
            return playbook
    return None
