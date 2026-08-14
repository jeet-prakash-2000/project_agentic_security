# LTM Security Platform — Final Project Structure

Agentic network & cloud security assessment platform. Three deployable units plus a web console:

| Unit | Technology | Purpose |
|------|------------|---------|
| `ui/` | Flask (Python 3.11) | Web console (AI Workspace, Security Ops, Telemetry Map, Reports) |
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
│
├── ui/                              # Flask web console
│   ├── app.py                       # Flask app, routes, auth (now bypassed)
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings.py              # App settings, SECRET_KEY, env-driven values
│   │   ├── storage.py               # JSON file <-> Azure Table storage abstraction
│   │   ├── keyvault.py              # Azure Key Vault access
│   │   ├── agents.json              # Agent registry (live API key — never committed)
│   │   ├── sessions.json            # Conversation history (runtime)
│   │   ├── users.json               # User accounts (scrypt-hashed passwords)
│   │   ├── insights.json            # Insight summaries (runtime)
│   │   ├── assessment_history.json  # Rolling posture snapshots
│   │   ├── assessment_stats.json    # Run counters / timestamps
│   │   ├── reports_history.json     # Generated report ledger
│   │   └── telemetry_*.json         # Telemetry metrics + history (runtime)
│   ├── gateway/
│   │   ├── agent_gateway.py         # Chat orchestration entry point
│   │   ├── foundry_client.py        # Azure AI Foundry (LLM) client
│   │   ├── session_manager.py       # Conversation persistence / scoping
│   │   └── tools.py                 # Agent tool registry
│   ├── services/
│   │   ├── assessment_service.py    # Posture aggregation (get_posture/get_full_assessment)
│   │   ├── agents_service.py        # Agent CRUD / connected-agent lookup
│   │   ├── chat_service.py          # Chat helpers
│   │   ├── dashboard_service.py     # Dashboard metrics
│   │   ├── app_insights.py          # App Insights telemetry
│   │   ├── firewall_data_service.py # Per-connector firewall calls
│   │   ├── function_client.py       # Azure Function HTTP client + live fallback
│   │   ├── insights_service.py      # Conversation/insight summarisation
│   │   ├── report_history_service.py# Report ledger
│   │   ├── sample_assessment.py     # Sample/fallback assessment data
│   │   ├── system_status_service.py # Live/sample status
│   │   ├── telemetry_map_service.py # Telemetry map graph + baselines
│   │   ├── timeutil.py              # IST/formatting helpers
│   │   └── users_service.py         # User create/authenticate (werkzeug)
│   ├── templates/
│   │   ├── base.html                # Shell: sidebar, topbar, toast, global agent
│   │   ├── login.html               # Auth screen (kept, not enforced)
│   │   ├── workspace.html           # AI Workspace (landing page)
│   │   ├── dashboard.html
│   │   ├── findings.html            # Security Operations Center
│   │   ├── telemetry_map.html
│   │   ├── insights.html
│   │   ├── reports.html
│   │   └── settings.html
│   └── static/
│       ├── css/                     # main.css + one per page
│       ├── js/                      # main.js + one per page (+finding_enrichment.js)
│       ├── images/logo.svg          # LTM monogram shield
│       ├── reports/                 # Generated PDF / XLSX artifacts
│       └── vendor/                  # cytoscape.js + webfonts
│
├── netsec-agent/                    # Palo Alto firewall auditor
│   └── functions/
│       ├── function_app.py          # HTTP-triggered endpoints
│       ├── host.json
│       ├── local.settings.json
│       ├── requirements.txt
│       ├── connectors/
│       │   ├── paloalto/            # XML/API collectors (inventory, HA, policy,
│       │   │                        #   routing, VPN, zones, backup, logging…)
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
│       └── openapi/firewall-auditor-openapi.json
│
└── cloudsec-agent/                  # Azure / M365 cloud security & IR
    └── functions/
        ├── function_app_cloudsec.py # IR tool endpoints
        ├── host.json
        ├── requirements.txt
        ├── incident_response_schema.json
        ├── connectors/
        │   ├── azure_config_cloudsec.py
        │   ├── compute_connector_cloudsec.py
        │   ├── defender_connector_cloudsec.py
        │   ├── network_connector_cloudsec.py
        │   ├── sentinel_connector_cloudsec.py
        │   └── utils/
        └── services/
            ├── incident_analysis_cloudsec.py
            ├── action_logger_cloudsec.py
            └── report_generator_cloudsec.py
```

---

## 2. Architecture

```
+-------------------------------------------------------+
|                     Browser (Client)                   |
|  Workspace | Security Ops | Telemetry Map | Insights  |
|  Dashboard | Reports | Settings                       |
+-------------------------+-----------------------------+
                          | HTTP (Flask, port 8003)
                          v
+-------------------------------------------------------+
|                 Flask Web Console (ui/)                |
|  +-----------+  +------------+  +------------------+   |
|  | gateway/  |  | services/  |  | config/          |   |
|  | agent chat|  | assessment |  | storage (JSON/   |   |
|  | sessions  |  | dashboard  |  | Azure Table)     |   |
|  | tools     |  | telemetry  |  | settings/keyvault|   |
|  | foundry   |  | insights   |  +------------------+   |
|  +-----+-----+  +-----+------+                        |
+--------+---------------+-------------------------------+
         |               |
         |               v
         |      +-------------------+
         |      | Azure AI Foundry  |
         |      | (LLM chat backend)|
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
+--------+----------------------------------------------+
|   Azure Functions — cloudsec-agent (Azure/M365 IR)     |
|   GetSentinelIncident / GetVMContext / RunSecurityScan |
|   IsolateAzureVM / BlockMaliciousIP / PatchVM / etc.   |
|   RunFullIncidentResponse / GenerateIncidentSummary    |
+-------------------------------------------------------+
```

---

## 3. Flask Web Console (`ui/`)

Entry point `ui/app.py` (run with `python3 app.py`, port `8003`).

### Page routes

| Route | Template | Purpose |
|-------|----------|---------|
| `/` | redirect | Redirects to `/workspace` |
| `/workspace` | `workspace.html` | AI Workspace (chat + conversation history) — landing page |
| `/dashboard` | `dashboard.html` | Overview dashboard |
| `/findings` | `findings.html` | Security Operations Center console |
| `/run-assessment` | `findings.html` | Force a fresh assessment then render findings |
| `/telemetry-map` | `telemetry_map.html` | Telemetry graph |
| `/insights` | `insights.html` | Agent insights |
| `/reports` | `reports.html` | Report history |
| `/executive-summary` | PDF | Executive summary PDF |
| `/generate-excel` | — | Generate Excel workbook |
| `/download-workbook` | file | Download generated workbook |
| `/settings` | `settings.html` | Settings |
| `/login` / `/signup` / `/logout` | `login.html` | Auth (present; enforcement removed) |

### API routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/findings` | GET | Posture + findings (`get_posture`) |
| `/api/compliance` | GET | Full compliance assessment |
| `/api/firewall/*` | GET | Per-connector firewall data (inventory, health, ha, policy, services, status, routing, vpn, logging, administration, zone-protection, backup) |
| `/api/summary` | GET | Aggregated summary |
| `/api/excel` | GET | Generate Excel report |
| `/api/agents` | GET/POST | List / add agents |
| `/api/chat` | POST | AI chat (single turn) |
| `/api/tools` | GET | Tool registry |
| `/api/conversations` | GET | List all conversations (no user scoping) |
| `/api/conversations/<id>/messages` | GET/POST | Read / persist messages |
| `/api/conversations/<id>/clear` | POST | Clear a conversation |
| `/api/me` | GET | Current user profile |
| `/api/insights` | GET | Insight summary |
| `/api/insights/conversation/<id>` | GET | Per-conversation summary |
| `/api/dashboard` | GET | Dashboard data |
| `/api/reports` | GET | Report history |
| `/api/system-status` | GET | Live/sample status |
| `/api/telemetry-map` | GET | Telemetry graph |
| `/api/telemetry-map/history` | GET | Telemetry history |

### Storage (`config/storage.py`)

Documents map to local JSON files under `config/` and are transparently mirrored to
Azure Table Storage when `AZURE_STORAGE_*` environment variables are present
(base64-chunked entities). If Azure is unconfigured, JSON files are the source of truth.

| Document | File | Notes |
|----------|------|-------|
| `agents` | `agents.json` | Live API key kept out of git |
| `sessions` | `sessions.json` | Conversation history |
| `users` | `users.json` | scrypt-hashed passwords |
| `insights` | `insights.json` | Summaries |
| `reports_history` | `reports_history.json` | Report ledger |
| `assessment_history` | `assessment_history.json` | Posture snapshots |
| `assessment_stats` | `assessment_stats.json` | Run counters |
| `telemetry_history` / `telemetry_metrics` | `telemetry_*.json` | Telemetry |

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
(`function_app_cloudsec.py`), all POST triggers:

- Detection: `GetSentinelIncident`, `GetIncidentEntities`, `GetVMContext`,
  `GetDefenderAlertDetails`, `GetSecurityRecommendations`, `CollectVMEvidence`,
  `BuildIncidentTimeline`, `AnalyzeRisk`
- Response: `IsolateAzureVM`, `StopAzureVM`, `BlockMaliciousIP`, `RunSecurityScan`,
  `RemovePersistence`, `PatchVM`, `RestoreVMConnectivity`, `ValidateVMHealth`
- Reporting: `GenerateIncidentSummary`, `GenerateTechnicalReport`,
  `GenerateExecutiveReport`, `CloseIncident`
- Orchestration: `RunFullIncidentResponse`

Connectors: Sentinel, Defender, Compute, Network, Azure config. Services: incident
analysis, action logger, report generator.

---

## 6. Deployment

- **UI**: GitHub Actions workflow (`.github/workflows/master_ltm-security-platform-ui.yml`)
  builds `ui/` with Python 3.11 and deploys to Azure Web App `ltm-security-platform-ui`
  on every push to `master`.
- **Function apps**: `netsec-agent/` and `cloudsec-agent/` deploy as Azure Functions
  (zip-deploy), configured via `local.settings.json` / app settings.
```
