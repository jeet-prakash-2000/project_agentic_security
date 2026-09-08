# LTM Security Platform — Project Structure

Agentic network & cloud security assessment platform. Three deployable units plus a web console:

| Unit | Technology | Purpose |
|------|------------|---------|
| `ui/` | Flask (Python 3.11) | Web console: landing page, dashboard, AI Workspace, Security Ops, Telemetry Map, Reports, Insights, Settings |
| `netsec-agent/` | Azure Functions (Python) | Palo Alto Networks firewall auditor (network security) |
| `cloudsec-agent/` | Azure Functions (Python) | Azure / Microsoft 365 cloud security & incident response |
| `.github/` | GitHub Actions | CI/CD build + deploy to Azure App Service |

---

## 1. Repository Layout

```
project_agentic_security/
├── .github/
│   └── workflows/
│       └── master_ltm-security-platform-ui.yml   # Build & deploy ui/ -> Azure Web App
├── .gitignore
├── PROJECT_STRUCTURE.md                          # This document
│
├── ui/                              # Flask web console
│   ├── app.py                       # Flask app, routes, demo auth (bypassed), startup validation
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings.py              # App settings, SECRET_KEY, env-driven values
│   │   ├── storage.py               # JSON / Azure Table / PostgreSQL storage abstraction
│   │   ├── keyvault.py              # Azure Key Vault secret resolution
│   │   ├── *.json                   # Runtime data (sessions, agents, insights, reports, telemetry…) — uncommitted
│   ├── database/                    # PostgreSQL persistence layer
│   │   ├── db.py                    # SQLAlchemy engine/session/Base + connection check
│   │   ├── models.py                # ORM models (users, agents, conversations, messages, findings…)
│   │   ├── storage_bridge.py        # JSON-document <-> relational conversion
│   │   ├── migrations/README.md     # Schema + migration guidance
│   │   └── repositories/
│   │       ├── base.py              # Shared repository CRUD
│   │       ├── users_repository.py
│   │       ├── agents_repository.py
│   │       ├── conversations_repository.py
│   │       ├── findings_repository.py
│   │       ├── reports_repository.py
│   │       ├── telemetry_repository.py
│   │       └── assessments_repository.py
│   ├── gateway/
│   │   ├── agent_gateway.py         # Chat orchestration entry point
│   │   ├── foundry_client.py        # Azure AI Foundry agent / responses client
│   │   ├── session_manager.py       # Conversation persistence / listing
│   │   └── tools.py                 # Agent tool registry
│   ├── services/
│   │   ├── assessment_service.py    # Posture, findings, history, live/sample assessment
│   │   ├── dashboard_service.py     # Dashboard metrics + recent findings + history
│   │   ├── agents_service.py        # Agent CRUD / connected-agent lookup
│   │   ├── users_service.py         # User create/authenticate (demo)
│   │   ├── insights_service.py      # Conversation/insight summarisation
│   │   ├── report_history_service.py# Report ledger
│   │   ├── telemetry_map_service.py # Telemetry map graph + metrics
│   │   ├── firewall_data_service.py # Per-connector firewall data (with assessment fallback)
│   │   ├── function_client.py       # Azure Function HTTP client + live fallback
│   │   ├── system_status_service.py # Live/sample status
│   │   ├── sample_assessment.py     # Sample/fallback assessment data
│   │   ├── app_insights.py          # App Insights telemetry
│   │   ├── chat_service.py
│   │   ├── netsec_service.py         # NetSec playbook bridge (env-config firewall)
│   │   ├── timeutil.py
│   │   └── dashboard_service.py
│   ├── scripts/
│   │   ├── migrate_json_to_postgres.py   # One-time JSON -> PostgreSQL migration
│   │   └── test_db_connection.py         # DB connectivity check
│   ├── static/
│   │   ├── css/                     # main.css, dashboard.css, findings.css, workspace.css, landing.css, login.css, …
│   │   ├── js/                      # main.js, dashboard.js, findings.js, workspace.js, finding_enrichment.js, netsec.js, …
│   │   ├── images/logo.svg          # LTM monogram shield
│   │   ├── reports/                 # Generated PDF / XLSX artifacts
│   │   └── vendor/                  # cytoscape.js + webfonts
│   ├── netsec_execution/            # NetSec Execution Agent engine (bulk firewall changes)
│   │   ├── connector/panos.py       # PAN-OS XML-API client (keygen + config ops, dry-run)
│   │   └── services/                # catalog/objects/zones/VR/routes/security/NAT/network/engine/workbook
│   └── templates/
│       ├── base.html                # Shell: collapsible sidebar, topbar, toast, global agent
│       ├── landing.html             # Public marketing page (login -> dashboard)
│       ├── login.html               # Demo login/register (any button -> dashboard)
│       ├── dashboard.html           # Security posture dashboard
│       ├── workspace.html           # AI Workspace (chat + conversation history)
│       ├── findings.html            # Security Operations Center
│       ├── telemetry_map.html
│       ├── insights.html
│       ├── reports.html
│       └── settings.html
│
├── netsec-agent/                    # Palo Alto firewall auditor (Azure Functions)
│   └── functions/
│       ├── function_app.py          # HTTP-triggered endpoints
│       ├── host.json / local.settings.json / requirements.txt
│       ├── connectors/
│       │   ├── paloalto/            # Collectors: inventory, health, HA, policy, security services,
│       │   │                        #   routing, VPN, logging, administration, zone protection, backup
│       │   │   └── paloalto_connector.py
│       │   └── utils/xml_parser.py
│       ├── compliance/
│       │   ├── compliance_engine.py # Baseline evaluation
│       │   └── findings_generator.py# Finding generation
│       ├── baseline/
│       │   ├── PaloAlto_Compliance_Baseline.txt
│       │   └── baseline_rules.json
│       ├── reports/
│       │   ├── report_generator.py
│       │   ├── executive_summary.py / _pdf.py
│       │   ├── risk_summary.py
│       │   └── excel_report.py
│       ├── openapi/firewall-auditor-openapi.json
│       └── applogs/                 # Azure runtime logs (tracked legacy, not source)
│
└── cloudsec-agent/                  # Azure / M365 cloud security & incident response
    ├── function_app.py              # IR tool endpoints (function_app.py at root)
    ├── host.json / requirements.txt / incident_response_schema.json
    ├── connectors/
    │   ├── auth.py
    │   ├── network_connector.py
    │   ├── sentinel_connector.py
    │   └── vm_connector.py
    └── services/
        ├── common.py
        ├── get_incidents_service.py / get_incident_service.py
        ├── generate_summary_service.py
        ├── get_vm_context_service.py / get_vm_instance_view_service.py
        └── start_vm_service.py / stop_vm_service.py / restart_vm_service.py /
            isolate_vm_service.py / reconnect_vm_service.py
```

> Note: `netsec_execution/` inside the UI is the deployed copy of the
> standalone `netsec-execution-agent/` module (see its README). The two are
> kept in sync before commit.

---

## 2. Architecture

```
+-------------------------------------------------------+
|                     Browser (Client)                   |
|  Landing -> Login -> Dashboard -> Workspace -> SOC     |
+-------------------------+-----------------------------+
                          | HTTP (Flask, port 8003)
                          v
+-------------------------------------------------------+
|                 Flask Web Console (ui/)                |
|  +-----------+  +------------+  +------------------+   |
|  | gateway/  |  | services/  |  | config/storage   |   |
|  | agent chat|  | assessment |  | JSON / Azure     |   |
|  | sessions  |  | dashboard  |  | Table / Postgres |   |
|  | tools     |  | telemetry  |  +------------------+   |
|  | foundry   |  | insights   |  | database/ (PG)   |   |
|  +-----+-----+  +-----+------+  +------------------+   |
+--------+---------------+-------------------------------+
         |               |
         |               v
         |      +-------------------+
         |      | Azure AI Foundry  |
         |      | (LLM agent)       |
         |      +-------------------+
         |
         | HTTP (function key auth)
         v
+--------+----------------------------------------------+
|   Azure Functions — netsec-agent (Palo Alto auditor)   |
|   get_inventory / get_health_status / get_ha_config    |
|   get_policy / security_services / routing / vpn /     |
|   logging / administration / zone_protection / backup  |
|   run_full_assessment / run_compliance_assessment      |
|   executive_summary / generate_excel_report            |
+-------------------------------------------------------+
|   Azure Functions — cloudsec-agent (Azure/M365 IR)     |
|   GetSentinelIncident / GetVMContext / RunSecurityScan |
|   IsolateAzureVM / BlockMaliciousIP / PatchVM / etc.   |
+-------------------------------------------------------+
```

---

## 3. Flask Web Console (`ui/`)

Entry point `ui/app.py` (run with `python3 app.py`, port `8003`).

### Page routes

| Route | Template | Purpose |
|-------|----------|---------|
| `/` | `landing.html` | Public landing / marketing page |
| `/login` | `login.html` | Demo login/register (any button -> dashboard) |
| `/logout` | redirect | Clears session -> `/` |
| `/dashboard` | `dashboard.html` | Security posture dashboard |
| `/workspace` | `workspace.html` | AI Workspace (chat + conversation history) |
| `/findings` | `findings.html` | Security Operations Center |
| `/run-assessment` | `findings.html` | Force a fresh assessment then render findings |
| `/telemetry-map` | `telemetry_map.html` | Telemetry graph |
| `/insights` | `insights.html` | Agent insights |
| `/reports` | `reports.html` | Report history |
| `/executive-summary` | PDF | Executive summary PDF (stores report history) |
| `/generate-excel` | `reports.html` | Generate Excel workbook (stores report history) |
| `/download-workbook` | file | Download generated workbook (stores report history) |
| `/settings` | `settings.html` | Settings |

### API routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/findings` | GET | Posture + findings (44 controls, 38 findings) |
| `/api/compliance` | GET | Full compliance assessment |
| `/api/firewall/*` | GET | Per-connector firewall data (inventory, health, ha, policy, services, status, routing, vpn, logging, administration, zone-protection, backup) |
| `/api/summary` | GET | Aggregated summary |
| `/api/excel` | GET | Generate Excel report (stores report history) |
| `/api/agents` | GET/POST | List / add agents |
| `/api/chat` | POST | AI chat (single turn) |
| `/api/tools` | GET | Tool registry |
| `/api/conversations` | GET | List all conversations |
| `/api/conversations/<id>/messages` | GET/POST | Read / persist messages |
| `/api/conversations/<id>/clear` | POST | Clear a conversation |
| `/api/me` | GET | Current user profile |
| `/api/insights` | GET | Insight summary |
| `/api/insights/conversation/<id>` | GET | Per-conversation summary |
| `/api/dashboard` | GET | Dashboard metrics + history + recent findings |
| `/api/reports` | GET | Report history |
| `/api/system-status` | GET | Live/sample status |
| `/api/telemetry-map` | GET | Telemetry graph |
| `/api/telemetry-map/history` | GET | Telemetry history |
| `/api/netsec/info` | GET | NetSec panel: connection status + playbook catalogue |
| `/api/netsec/workbook/template` | GET | Download fill-in playbook `.xlsx` template |
| `/api/netsec/workbook` | GET/POST | Read / store the user's playbook workbook |
| `/api/netsec/playbooks/run` | POST | Execute a playbook against the firewall (per-row) |

### Storage (`config/storage.py` + `database/`)

Documents map to local JSON files under `config/` and are transparently mirrored to
Azure Table Storage when `AZURE_STORAGE_*` is set, or PostgreSQL when `DATABASE_URL`
is set (PostgreSQL is the preferred primary source). JSON files remain as backup.

| Document | JSON file | PostgreSQL table(s) |
|----------|-----------|---------------------|
| `agents` | `agents.json` | `agents` |
| `sessions` | `sessions.json` | `conversations` + `messages` |
| `users` | `users.json` | `users` |
| `insights` | `insights.json` | `insights` |
| `reports_history` | `reports_history.json` | `reports_history` |
| `assessment_history` | `assessment_history.json` | `assessment_history` |
| `assessment_stats` | `assessment_stats.json` | `assessment_stats` |
| `telemetry_metrics` | `telemetry_metrics.json` | `telemetry_metrics` |
| `telemetry_history` | `telemetry_history.json` | `telemetry_history` |
| — | (derived) | `findings` |

---

## 4. Azure Functions — `netsec-agent/`

Palo Alto Networks firewall auditor. HTTP triggers in `function_app.py`:

- `get_inventory`, `get_health_status`, `get_ha_configuration`
- `get_policy_configuration`, `get_security_services`, `get_routing_configuration`
- `get_vpn_configuration`, `get_logging_configuration`, `get_administration_configuration`
- `get_zone_protection_configuration`, `get_backup_configuration`
- `run_full_assessment`, `run_compliance_assessment`
- `executive_summary`, `generate_excel_report`

Supporting modules: `connectors/paloalto/*` (device collectors), `compliance/*`
(baseline evaluation + finding generation), `baseline/*` (rules), `reports/*`
(summary / risk / Excel / PDF).

---

## 5. Azure Functions — `cloudsec-agent/`

Azure / Microsoft 365 cloud security and incident response toolset
(`function_app.py`), all POST triggers:

- Detection: `GetSentinelIncidents`, `GetSentinelIncident`, `GenerateIncidentSummary`
- Compute: `GetVMContext`, `GetVMInstanceView`
- Response: `StartVM`, `StopVM`, `RestartVM`, `IsolateAzureVM`, `RestoreVMConnectivity`

---

## 6. Deployment

### 6.1 UI — Azure Web App (`ui/`)

Deployed via GitHub Actions (`.github/workflows/master_ltm-security-platform-ui.yml`):

- **Trigger**: `push` to `master` or `workflow_dispatch`.
- **Build job**: checkout -> setup-python 3.11 -> venv `antenv` -> `pip install -r ui/requirements.txt`
  -> bundle `netsec-agent/functions/{compliance,reports,baseline}` into `ui/netsec_functions/`
  -> upload `ui/` artifact.
- **Deploy job**: `azure/webapps-deploy@v3` -> `ltm-security-platform-ui` (Production)
  using the publish-profile secret.
- **Live URL**: `https://ltm-security-platform-ui-c8fff7f9ghb0e6hg.southindia-01.azurewebsites.net`
- **Local run**: `cd ui && python3 app.py` (port `8003`).

### 6.2 Azure Functions — `netsec-agent/` & `cloudsec-agent/`

Deployed as Azure Function Apps (zip-deploy). Function-key auth is used by the UI
(`services/function_client.py`) for live firewall calls; when keys are absent the UI
degrades to sample data or the assessment snapshot.

### 6.5 NetSec Execution Agent (`ui/netsec_execution` + `netsec-execution-agent/`)

The NetSec Execution Agent appears in the AI Workspace as a third copilot
(`NetSec-Execution-Agent`, `config/agents.json` -> `agents` table on boot via
`services/bootstrap.py`). Selecting it opens the playbook panel
(download -> fill -> upload -> run). Playbook runs talk **directly** to the
firewall XML API from the web app; credentials are environment-only and are
never stored in the database.

| Variable | Purpose | Default |
|----------|---------|---------|
| `NETSEC_FW_HOST` | firewall host/IP targeted by playbooks | — |
| `NETSEC_FW_USERNAME` / `NETSEC_FW_PASSWORD` | admin credentials for `keygen` | — |
| `NETSEC_FW_API_KEY` | optional pre-generated API key (skips `keygen`) | — |
| `NETSEC_FW_DRY_RUN` | `1` previews every change, `0` applies them | `1` |
| `NETSEC_WORKBOOK_DIR` | where uploaded workbooks are stored | `/tmp/netsec_uploads` |
| `NETSEC_MAX_ROWS` | max data rows executed per run | `500` |
| `FOUNDRY_API_KEY_NETSEC_EXECUTION_AGENT` | Foundry key for Agent Health probe of this agent | shared `FOUNDRY_API_KEY` |

The Agent Health card probes every registered agent, so without a Foundry key
for the netsec agent it reports `down` (`No API key configured`) even though
playbooks still run against `NETSEC_FW_*`; set
`FOUNDRY_API_KEY_NETSEC_EXECUTION_AGENT` to the firewall project key to show it
live.

### 6.3 Configuration & Secret Resolution

`ui/config/settings.py` loads values through `ui/config/keyvault.py`, which resolves a
secret in this order: env var -> in-memory cache -> Azure Key Vault (`DefaultAzureCredential`)
-> baked-in default.

| Setting | Secret / env | Default |
|---------|--------------|---------|
| `SECRET_KEY` | `SECRET_KEY` | dev-only placeholder |
| `BASE_URL` | `firewall-function-url` | netsec-agent function URL |
| `FUNCTION_KEY` | `FIREWALL_FUNCTION_KEY` | placeholder |
| `FULL_ASSESSMENT_KEY` | `FIREWALL_FULL_ASSESSMENT_KEY` | placeholder |
| `EXCEL_KEY` | `FIREWALL_EXCEL_KEY` | placeholder |
| `EXECUTIVE_SUMMARY_KEY` | `FIREWALL_EXECUTIVE_SUMMARY_KEY` | placeholder |
| `APP_INSIGHTS_CONNECTION_STRING` | `app-insights-connection-string` | baked-in instrumentation key |
| `DATABASE_URL` | `DATABASE_URL` | none (JSON fallback) |

### 6.4 Credentials & Secrets (never committed)

- GitHub Actions publish-profile secret.
- Azure Key Vault `netsec-agent-project-key` — function keys, AI Foundry keys, storage keys.
- `ui/config/agents.json` — live agent API key (left out of git).
