import os
import threading

# Vault URL comes from environment so the code itself carries no secrets.
VAULT_URL = os.environ.get("AZURE_KEY_VAULT_URL", "").strip().rstrip("/")

_client = None
_client_error = None
_cache = {}
_cache_lock = threading.Lock()


def _load_client():
    global _client, _client_error

    if _client is not None or _client_error is not None:
        return _client

    if not VAULT_URL:
        _client_error = "AZURE_KEY_VAULT_URL is not configured."
        return None

    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
    except ImportError:
        _client_error = (
            "azure-identity / azure-keyvault-secrets are not installed."
        )
        return None

    try:
        _client = SecretClient(
            vault_url=VAULT_URL,
            credential=DefaultAzureCredential(),
        )
    except Exception as e:
        _client_error = str(e)
        _client = None

    return _client


def get_secret(name, default=None):
    env_value = os.environ.get(name.upper().replace("-", "_"))
    if env_value:
        return env_value

    with _cache_lock:
        if name in _cache:
            return _cache[name]

    client = _load_client()
    if client is None:
        return default

    try:
        value = client.get_secret(name).value
        with _cache_lock:
            _cache[name] = value
        return value
    except Exception:
        return default


def secret_available():
    return _load_client() is not None


def clear_cache():
    with _cache_lock:
        _cache.clear()
