"""Managed firewall registry service (table ``managed_firewalls``).

Administrators register the firewalls the platform manages from
Settings > Firewall Inventory: device name (the firewall's logical name),
host name, host IP and host key. Host keys are stored so agents can connect
and are always masked in API responses.

Live/down status is determined by a short TCP reachability probe of each
registered host IP (management HTTPS 443, then SSH 22). Results are cached in
memory for a short TTL and persisted on the row (``status``/``last_checked``)
so every state is also stored in the database.
"""

import concurrent.futures
import ipaddress
import socket
import threading
import time

from database.db import get_session
from database.repositories import ManagedFirewallsRepository

_lock = threading.Lock()

# Seconds before the stored probe result is considered stale and re-probed.
PROBE_TTL = 60

# Fallback hosts seeded on bootstrap so existing platform firewalls appear in
# the inventory automatically (host key is empty until one is registered).
DEFAULT_FIREWALLS = [
    {
        "device_name": "vmpafw01",
        "host_name": "20.44.53.215",
        "host_ip": "20.44.53.215",
        "host_key": "",
    }
]

# In-memory probe cache: host_ip -> (checked_at, live).
_probe_cache = {}


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
        "clone_of": entry.clone_of,
        "status": entry.status or "down",
        "last_checked": entry.last_checked,
        "created": entry.created,
    }


def _repo():
    return ManagedFirewallsRepository(get_session())


# --------------------------------------------------
# Reachability probe
# --------------------------------------------------

def _port_open(host_ip, port, timeout):
    try:
        with socket.create_connection((host_ip, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def _probe_host(host_ip):
    host_ip = (host_ip or "").strip()
    if not host_ip:
        return False
    cached = _probe_cache.get(host_ip)
    if cached and time.time() - cached[0] < PROBE_TTL:
        return cached[1]
    live = _port_open(host_ip, 443, 1.5) or _port_open(host_ip, 22, 1.5)
    _probe_cache[host_ip] = (time.time(), live)
    return live


def _probe_many(host_ips):
    """Probe unique host IPs concurrently and return ``{ip: live}``."""
    unique = list(dict.fromkeys(host_ips or []))
    if not unique:
        return {}
    results = {}
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(8, len(unique))
    ) as pool:
        for ip, live in zip(unique, pool.map(_probe_host, unique)):
            results[ip] = live
    return results


def _needs_probe(entry, now):
    if not (entry.host_ip or "").strip():
        return False
    if entry.last_checked is None:
        return True
    return now - entry.last_checked >= PROBE_TTL


# --------------------------------------------------
# List / create / clone / remove
# --------------------------------------------------

def list_firewalls():
    """Return every registered firewall, probing stale statuses first."""
    repo = _repo()
    entries = repo.list_all()
    now = time.time()
    stale = [entry for entry in entries if _needs_probe(entry, now)]
    if stale:
        live_by_ip = _probe_many([entry.host_ip for entry in stale])
        for entry in stale:
            entry.status = "live" if live_by_ip.get(entry.host_ip) else "down"
            entry.last_checked = now
        repo.session.commit()
    return [_public(entry) for entry in entries]


def _persist_probe(entry):
    live = _probe_host(entry.host_ip)
    entry.status = "live" if live else "down"
    entry.last_checked = time.time()
    return entry


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
        entry = repo.create(
            {
                "device_name": device_name,
                "host_name": host_name,
                "host_ip": host_ip,
                "host_key": host_key,
                "status": "down",
                "last_checked": None,
                "created": time.time(),
            }
        )
        _persist_probe(entry)
        repo.session.commit()

    return _public(entry)


def clone_firewall(source_id, clone_device_name):
    """Clone a registered firewall under a new device name.

    The clone copies the source host name/IP/key and is recorded as a clone
    of the source device (``clone_of``) so the original appears alongside it.
    """
    clone_device_name = (clone_device_name or "").strip()
    if not clone_device_name:
        raise ValueError("A name is required for the clone.")
    if len(clone_device_name) > 64:
        raise ValueError("Device name must be 64 characters or fewer.")

    with _lock:
        repo = _repo()
        source = repo.get(source_id)
        if source is None:
            raise ValueError("Firewall inventory entry not found.")
        if repo.by_device_name(clone_device_name):
            raise ValueError(
                "A firewall with this device name already exists."
            )
        entry = repo.create(
            {
                "device_name": clone_device_name,
                "host_name": source.host_name,
                "host_ip": source.host_ip,
                "host_key": source.host_key or "",
                "clone_of": source.device_name,
                "status": "down",
                "last_checked": None,
                "created": time.time(),
            }
        )
        _persist_probe(entry)
        repo.session.commit()

    return _public(entry)


def remove_firewall(firewall_id):
    """Remove a firewall inventory entry (administrator action)."""
    with _lock:
        deleted = _repo().delete_id(firewall_id)
    if deleted is None:
        raise ValueError("Firewall inventory entry not found.")
    return deleted


def ensure_defaults():
    """Seed the default platform firewalls when they are not registered yet.

    Called from startup bootstrap; idempotent.
    """
    repo = _repo()
    seeded = 0
    for spec in DEFAULT_FIREWALLS:
        if repo.by_device_name(spec["device_name"]):
            continue
        entry = repo.create(
            {
                "device_name": spec["device_name"],
                "host_name": spec["host_name"],
                "host_ip": spec["host_ip"],
                "host_key": spec["host_key"],
                "status": "down",
                "last_checked": None,
                "created": time.time(),
            }
        )
        _persist_probe(entry)
        repo.session.commit()
        seeded += 1
    return seeded
