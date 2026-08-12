import time
import requests
from config import settings


def _call_function(endpoint, cache_key=None):
    cache = _call_function._cache if hasattr(_call_function, "_cache") else {}
    _call_function._cache = cache

    force = cache_key is None
    now = time.time()

    if not force and cache_key in cache:
        entry = cache[cache_key]
        if now - entry["ts"] < 30:
            return entry["data"]

    url = f"{settings.BASE_URL}/{endpoint}"
    try:
        resp = requests.get(
            url,
            params={"code": settings.FUNCTION_KEY},
            timeout=settings.LIVE_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            if cache_key:
                _call_function._cache[cache_key] = {"data": data, "ts": now}
            return data
    except Exception:
        pass
    return None


def get_inventory():
    return _call_function("get_inventory", "inventory")


def get_health_status():
    return _call_function("get_health_status", "health")


def get_ha_configuration():
    return _call_function("get_ha_configuration", "ha")


def get_policy_configuration():
    return _call_function("get_policy_configuration", "policy")


def get_security_services():
    return _call_function("get_security_services", "services")


def get_routing_configuration():
    return _call_function("get_routing_configuration", "routing")


def get_vpn_configuration():
    return _call_function("get_vpn_configuration", "vpn")


def get_logging_configuration():
    return _call_function("get_logging_configuration", "logging")


def get_administration_configuration():
    return _call_function("get_administration_configuration", "admin")


def get_zone_protection_configuration():
    return _call_function("get_zone_protection_configuration", "zone_protection")


def get_backup_configuration():
    return _call_function("get_backup_configuration", "backup")


def get_full_status():
    return {
        "inventory": get_inventory(),
        "health_status": get_health_status(),
        "ha_configuration": get_ha_configuration(),
        "policy_configuration": get_policy_configuration(),
        "security_services": get_security_services(),
        "routing_configuration": get_routing_configuration(),
        "vpn_configuration": get_vpn_configuration(),
        "logging_configuration": get_logging_configuration(),
        "administration_configuration": get_administration_configuration(),
        "zone_protection_configuration": get_zone_protection_configuration(),
        "backup_configuration": get_backup_configuration(),
    }
