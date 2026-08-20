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


def _assessment_section(key):
    """Fall back to the latest assessment snapshot when the live function
    is unreachable (e.g. the function key is not configured in the current
    environment). The assessment payload already carries every firewall
    configuration section.
    """
    try:
        from services import assessment_service

        assessment = assessment_service.get_full_assessment()
        if isinstance(assessment, dict):
            data = assessment.get(key)
            if data is not None:
                return data
    except Exception:
        pass
    return {"status": "No data collected for this section"}


def _get_or_fallback(endpoint, cache_key, section_key):
    data = _call_function(endpoint, cache_key)
    if data is None:
        data = _assessment_section(section_key)
    return data


def get_inventory():
    return _get_or_fallback("get_inventory", "inventory", "inventory")


def get_health_status():
    return _get_or_fallback("get_health_status", "health", "health_status")


def get_ha_configuration():
    return _get_or_fallback("get_ha_configuration", "ha", "ha_configuration")


def get_policy_configuration():
    return _get_or_fallback(
        "get_policy_configuration", "policy", "policy_configuration"
    )


def get_security_services():
    return _get_or_fallback(
        "get_security_services", "services", "security_services"
    )


def get_routing_configuration():
    return _get_or_fallback(
        "get_routing_configuration", "routing", "routing_configuration"
    )


def get_vpn_configuration():
    return _get_or_fallback("get_vpn_configuration", "vpn", "vpn_configuration")


def get_logging_configuration():
    return _get_or_fallback(
        "get_logging_configuration", "logging", "logging_configuration"
    )


def get_administration_configuration():
    return _get_or_fallback(
        "get_administration_configuration",
        "admin",
        "administration_configuration",
    )


def get_zone_protection_configuration():
    return _get_or_fallback(
        "get_zone_protection_configuration",
        "zone_protection",
        "zone_protection_configuration",
    )


def get_backup_configuration():
    return _get_or_fallback(
        "get_backup_configuration", "backup", "backup_configuration"
    )


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
