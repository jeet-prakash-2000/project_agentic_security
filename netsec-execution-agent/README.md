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
playbooks/              YAML playbook catalogue (one .yaml per playbook; the
                        NN- filename prefix sets the catalogue order)
run_playbook.py         CLI runner (python -m netsec_execution.run_playbook)
services/
  common.py             shared helpers (list parsing, env access)
  objects.py            address objects, groups, services, service groups, tags
  zones.py              zones (embedded in policies module helpers)
  vr.py                 virtual routers and static routes
  policies.py           security pre-rules and NAT rules
  network.py            layer3 interfaces
  loader.py             reads + validates the YAML playbooks, resolves handlers
  catalog.py            public catalogue API over the loaded YAML playbooks
  workbook.py           .xlsx parse / summarize / template build
  engine.py             per-row execution engine with error isolation
```

## Playbooks are YAML

Each playbook is a plain YAML file in `playbooks/` named after its `id` (e.g.
`objects-addresses.yaml`). It declares the workbook sheet it maps to, the
template columns, example rows, column widths, and the row-execution handler:

```yaml
id: objects-addresses
title: Address Objects
category: Objects
sheet: Addresses
summary: Bulk create, update or delete shared address objects.
handler: services.objects.apply_addresses
columns: [Action, Name, Address Type, Address Value, Description, Tags]
examples:
  - Action: create
    Name: sample-web
    Address Type: ip-netmask
    Address Value: 198.51.100.10/32
```

`catalog.py` no longer hard-codes playbooks: at import time
`services/loader.py` reads every file in `playbooks/`, validates the required
keys (`id`, `title`, `category`, `sheet`, `summary`, `handler`, `columns`) and
resolves each `handler` reference to the `services` function that executes a
single row. The engine, workbook builder and web service keep using the same
public API (`catalog.PLAYBOOKS`, `catalog.list_playbooks()`,
`catalog.find_playbook()`), so behaviour is unchanged.

The loader depends on `PyYAML` (`pip install pyyaml`); the workbook features
depend on `openpyxl` and the firewall client on `requests`.

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

### Command line

A runner reads an uploaded Excel workbook, matches its sheet to a YAML
playbook and executes every row (the same path the web bulk-upload uses):

```bash
# list the available YAML playbooks
python -m netsec_execution.run_playbook --list

# execute the playbook for the rows in the workbook (dry run by default)
python -m netsec_execution.run_playbook /tmp/workbook.xlsx objects-addresses

# JSON output; exit code 0 = all rows ok, 1 = row errors, 2 = usage/config
python -m netsec_execution.run_playbook /tmp/workbook.xlsx objects-addresses --json
```

## Safety model

* Every mutating call honours `client.dry_run`; nothing reaches the firewall
  until `NETSEC_FW_DRY_RUN=0`.
* In apply mode, `run_playbook` commits the candidate changes to the running
  configuration after the last row, so playbook runs actually take effect;
  dry-run runs never commit.
* The engine executes each row independently - one bad row never aborts the
  rest, and every outcome (create/update/delete/error) is returned per row.
* No credential is ever persisted or logged; the API key is held in memory.
