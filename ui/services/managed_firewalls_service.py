"""Managed firewall registry service (table ``managed_firewalls``).

Administrators register the firewalls the platform manages from
Settings > Firewall Inventory: device name (the firewall's logical name),
host name, host IP and host key. The host key is stored so agents can connect
and is always masked in API responses.
"""

import ipaddress
import threading
import time

from database.db import get_session
from database.repositories import ManagedFirewallsRepository

_lock = threading.Lock()


def _mask_key(value):
    if not value:
        return None
    return "••••••••" + (value[-4:] if len(value) > 4 else "")


def _public(entry):
    if not entry:
        return None
    return {
        "id": entry.id,
        "device_name": entry.device_name,
        "host_name": entry.host_name,
        "host_ip": entry.host_ip,
        "host_key": _mask_key(entry.host_key),
        "has_host_key": bool(entry.host_key),
        "created": entry.created,
    }


def _repo():
    return ManagedFirewallsRepository(get_session())


def list_firewalls():
    return [_public(entry) for entry in _repo().list_all()]


def add_firewall(device_name, host_name, host_ip, host_key):
    """Register a firewall inventory entry (administrator action)."""
    device_name = (device_name or "").strip()
    host_name = (host_name or "").strip()
    host_ip = (host_ip or "").strip()
    host_key = (host_key or "").strip()

    if not device_name or not host_name or not host_ip or not host_key:
        raise ValueError(
            "Device name, host name, host IP, and host key are required."
        )
    try:
        ipaddress.ip_address(host_ip)
    except ValueError:
        raise ValueError("Enter a valid host IP address.")

    with _lock:
        repo = _repo()
        if repo.by_device_name(device_name):
            raise ValueError(
                "A firewall with this device name already exists."
            )
        if repo.by_host_ip(host_ip):
            raise ValueError(
                "A firewall with this host IP already exists."
            )
        entry = repo.create(
            {
                "device_name": device_name,
                "host_name": host_name,
                "host_ip": host_ip,
                "host_key": host_key,
                "created": time.time(),
            }
        )

    return _public(entry)


def remove_firewall(firewall_id):
    """Remove a firewall inventory entry (administrator action)."""
    with _lock:
        deleted = _repo().delete_id(firewall_id)
    if deleted is None:
        raise ValueError("Firewall inventory entry not found.")
    return deleted
