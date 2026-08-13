"""Storage abstraction for JSON-backed persistence.

By default services persist to local JSON files under ``config/``. When Azure
Table Storage is configured, the same JSON documents are stored as entities in
Azure Tables instead, so the rest of the application (Flask routes, services,
and their data structures) is unaffected.

Configuration (environment variables, checked in priority order):

* ``AZURE_STORAGE_CONNECTION_STRING`` - full connection string (preferred)
* ``AZURE_STORAGE_ACCOUNT_NAME`` + ``AZURE_STORAGE_ACCOUNT_KEY`` - account key auth
* ``AZURE_STORAGE_ACCOUNT_NAME`` only - managed identity via ``DefaultAzureCredential``
* ``AZURE_STORAGE_TABLE_PREFIX`` - optional prefix applied to every table name

If none of the Azure settings are present, local JSON files are used.
"""

import base64
import json
import os
import threading

CONFIG_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")
)

# Map of logical document name -> local JSON filename.
DOCUMENTS = {
    "agents": "agents.json",
    "sessions": "sessions.json",
    "insights": "insights.json",
    "reports_history": "reports_history.json",
    "telemetry_history": "telemetry_history.json",
    "telemetry_metrics": "telemetry_metrics.json",
    "assessment_stats": "assessment_stats.json",
    "users": "users.json",
}

# Azure Table limits: string properties are measured in UTF-16 (2 bytes/char),
# so a single string property is effectively capped at 32K characters. Each
# document is base64-encoded and split into chunks stored across multiple
# entities (partition key "doc", row keys "chunk-000000", "chunk-000001", ...).
CHUNK_CHARS = 30 * 1024
PARTITION_KEY = "doc"

_service_client = None
_service_error = None
_table_clients = {}
_lock = threading.Lock()


def _env(name):
    return (os.environ.get(name) or "").strip()


def connection_string():
    return _env("AZURE_STORAGE_CONNECTION_STRING") or None


def account_name():
    return _env("AZURE_STORAGE_ACCOUNT_NAME") or None


def account_key():
    return _env("AZURE_STORAGE_ACCOUNT_KEY") or None


def table_prefix():
    return _env("AZURE_STORAGE_TABLE_PREFIX") or ""


def enabled():
    return bool(connection_string() or account_name())


def backend():
    return "azure-table" if enabled() else "json"


def _table_name(document_name):
    # Azure Table names must be 3-63 alphanumeric characters (no underscores).
    name = document_name.replace("_", "")
    return (table_prefix() + name)[:63]


def _get_service_client():
    global _service_client, _service_error

    if _service_client is not None or _service_error is not None:
        return _service_client

    if not enabled():
        _service_error = "Azure Storage is not configured."
        return None

    try:
        from azure.data.tables import TableServiceClient
    except ImportError:
        _service_error = "azure-data-tables is not installed."
        return None

    conn = connection_string()
    if conn:
        try:
            _service_client = TableServiceClient.from_connection_string(conn)
            return _service_client
        except Exception as exc:
            _service_error = str(exc)
            return None

    name = account_name()
    endpoint = "https://{0}.table.core.windows.net".format(name)

    key = account_key()
    if key:
        try:
            from azure.core.credentials import AzureNamedKeyCredential

            _service_client = TableServiceClient(
                endpoint=endpoint,
                credential=AzureNamedKeyCredential(name, key),
            )
            return _service_client
        except Exception as exc:
            _service_error = str(exc)
            return None

    try:
        from azure.identity import DefaultAzureCredential

        _service_client = TableServiceClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential(),
        )
        return _service_client
    except Exception as exc:
        _service_error = str(exc)
        return None


def _get_table_client(document_name):
    with _lock:
        client = _table_clients.get(document_name)
        if client is not None:
            return client

    service = _get_service_client()
    if service is None:
        return None

    try:
        table_name = _table_name(document_name)
        client = service.create_table_if_not_exists(table_name)
        with _lock:
            _table_clients[document_name] = client
        return client
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Payload chunking (byte-safe via base64)
# ---------------------------------------------------------------------------

def _chunk_payload(payload):
    encoded = base64.b64encode(payload).decode("ascii")
    return [encoded[i:i + CHUNK_CHARS] for i in range(0, len(encoded), CHUNK_CHARS)]


def _join_chunks(chunks):
    encoded = "".join(chunks)
    return base64.b64decode(encoded.encode("ascii"))


# ---------------------------------------------------------------------------
# File backend
# ---------------------------------------------------------------------------

def _file_path(document_name):
    return os.path.join(CONFIG_DIR, DOCUMENTS[document_name])


def _file_load(document_name, default):
    path = _file_path(document_name)
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return default


def _file_save(document_name, data):
    path = _file_path(document_name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


# ---------------------------------------------------------------------------
# Table backend
# ---------------------------------------------------------------------------

def _table_load(document_name):
    client = _get_table_client(document_name)
    if client is None:
        return None

    entities = list(
        client.query_entities(
            "PartitionKey eq '{0}'".format(PARTITION_KEY),
            select=["RowKey", "data"],
        )
    )
    chunks = sorted(
        (e for e in entities if e.get("data")),
        key=lambda e: e["RowKey"],
    )
    if not chunks:
        return None

    payload = _join_chunks([e["data"] for e in chunks])
    return json.loads(payload.decode("utf-8"))


def _table_save(document_name, data):
    client = _get_table_client(document_name)
    if client is None:
        return

    payload = json.dumps(data).encode("utf-8")
    chunks = _chunk_payload(payload)

    # Remove stale chunk entities before rewriting the document.
    existing = list(
        client.query_entities(
            "PartitionKey eq '{0}'".format(PARTITION_KEY),
            select=["RowKey"],
        )
    )
    for entity in existing:
        try:
            client.delete_entity(PARTITION_KEY, entity["RowKey"])
        except Exception:
            pass

    for index, chunk in enumerate(chunks):
        client.upsert_entity(
            {
                "PartitionKey": PARTITION_KEY,
                "RowKey": "chunk-{0:06d}".format(index),
                "data": chunk,
            }
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_document(document_name, default):
    if document_name not in DOCUMENTS:
        return default

    if enabled():
        try:
            data = _table_load(document_name)
            if data is not None:
                return data
        except Exception:
            pass

    # Fall back to the local file (also seeds on first run after enabling
    # Azure Storage: the next save will write the table).
    data = _file_load(document_name, default)
    if enabled() and data is not None and data != default:
        try:
            _table_save(document_name, data)
        except Exception:
            pass
    return data


def save_document(document_name, data):
    if document_name not in DOCUMENTS:
        return

    _file_save(document_name, data)

    if enabled():
        try:
            _table_save(document_name, data)
        except Exception:
            pass
