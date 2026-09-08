# NetSec Execution Agent

Playbook-driven bulk configuration of Palo Alto Networks firewalls over the
PAN-OS XML API. The agent turns an Excel workbook into hundreds of safe,
per-row firewall changes (objects, zones, VRs, routes, security/NAT policies,
interfaces) with full dry-run preview support.

This package is the standalone source of the `netsec_execution` module that
ships inside the AI Workspace UI at `ui/netsec_execution`. When the UI is
deployed, it exposes the NetSec Execution Agent in the workspace with a
download -> fill -> upload -> run playbook panel.

## Layout

```
connector/panos.py      PAN-OS XML-API client (keygen + config get/set/delete)
services/
  common.py             shared helpers (list parsing, env access)
  objects.py            address objects, groups, services, service groups, tags
  zones.py              zones (embedded in policies module helpers)
  vr.py                 virtual routers and static routes
  policies.py           security pre-rules and NAT rules
  network.py            layer3 interfaces
  catalog.py            playbook catalogue (11 playbooks, template columns)
  workbook.py           .xlsx parse / summarize / template build
  engine.py             per-row execution engine with error isolation
```

## Environment variables

Every value is read from the environment at call time (never from code):

| Variable | Meaning | Default |
| --- | --- | --- |
| `NETSEC_FW_HOST` | firewall host or IP | - |
| `NETSEC_FW_USERNAME` | admin username (used for `keygen`) | - |
| `NETSEC_FW_PASSWORD` | admin password (used for `keygen`) | - |
| `NETSEC_FW_API_KEY` | optional pre-generated API key (skips `keygen`) | - |
| `NETSEC_FW_PORT` | HTTPS port | `443` |
| `NETSEC_FW_VERIFY_TLS` | disable cert checks when unset | `0` |
| `NETSEC_FW_DRY_RUN` | `1` previews changes, `0` applies them | `1` |
| `NETSEC_FW_TIMEOUT` | per-request timeout (s) | `30` |

## Usage

```bash
export NETSEC_FW_HOST=fw.example.net
export NETSEC_FW_USERNAME=fwadmin
export NETSEC_FW_PASSWORD='secret'
export NETSEC_FW_DRY_RUN=1          # preview first
```

```python
from netsec_execution.connector.panos import PanosClient
from netsec_execution.services import catalog, engine, workbook

client = PanosClient()                       # reads NETSEC_FW_*
playbook = catalog.find_playbook("objects-addresses")

# 1. generate a template workbook
workbook.build_template("/tmp/workbook.xlsx", catalog.PLAYBOOKS)

# 2. user fills it in, then:
result = engine.run_playbook(client, "objects-addresses",
                             workbook_path="/tmp/workbook.xlsx")
print(result["counts"])                      # rows/created/updated/deleted/errors
```

## Safety model

* Every mutating call honours `client.dry_run`; nothing reaches the firewall
  until `NETSEC_FW_DRY_RUN=0`.
* The engine executes each row independently - one bad row never aborts the
  rest, and every outcome (create/update/delete/error) is returned per row.
* No credential is ever persisted or logged; the API key is held in memory.
