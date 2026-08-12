# LTM Security Platform — Project Structure & Architecture

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Directory Map](#directory-map)
3. [Component Deep Dive](#component-deep-dive)
   - [Azure Functions Backend (`functions/`)](#azure-functions-backend-functionss)
   - [Flask Frontend (`ui/`)](#flask-frontend-ui)
4. [Data Flow](#data-flow)
5. [Page Routing](#page-routing)
6. [Design Patterns](#design-patterns)
7. [Configuration & Persistence](#configuration--persistence)

---

## Architecture Overview

```
+----------------------------------------------------+
|                  Browser (Client)                   |
|  Dashboard | Workspace | Telemetry Map | Insights  |
|  Findings  | Reports   | Settings                   |
+---------+------------------------------------------+
          |
          | HTTP (port 8003)
          v
+---------+------------------------------------------+
|             Flask Frontend (ui/app.py)              |
|  +-----------+ +-------------+ +----------------+  |
|  |  gateway/ | |  services/  | |   config/      |  |
|  |  (agent   | | (assessment | | (settings,     |  |
|  |   chat,   | |  dashboard, | |  keyvault,     |  |
|  |   session | |  insights,  | |  agents.json,  |  |
|  |   manager,| |  telemetry, | |  sessions.json)|  |
|  |   tools,  | |  system     | |                |  |
|  |   foundry) | |  status)   | |                |  |
|  +-----+-----+ +------+------+ +----------------+  |
+--------+---------------+----------------------------+
         |               |
         |               v
         |   +-----------+-----------+
         |   | Azure AI Foundry      |
         |   | (LLM chat backend)    |
         |   +-----------------------+
         |
         | HTTP (function key auth)
         v
+--------+-------------------------------------------+
|       Azure Functions Backend (function_app.py)     |
|  +-------------+ +-------------+ +--------------+  |
|  | connectors/ | | compliance/ | |  reports/    |  |
|  | (paloalto   | | (engine +   | | (summary,    |  |
|  |  collector  | |  findings)  | |  excel,      |  |
|  |  modules)   | |             | |  risk)       |  |
|  +------+------+ +------+------+ +------+-------+  |
+---------+----------------+----------------+--------+
          |                |                |
          v                v                v
    +---------+     +-----------+     +---------+
    | Palo    |     | Baseline  |     | .xlsx   |
    | Alto    |     | Rules     |     | Reports |
    | Firewall|     | (44 rules)|     |         |
    +---------+     +-----------+     +---------+
```

The platform is split into two independently deployable components:

| Component | Location | Runtime | Port | Purpose |
|-----------|----------|---------|------|---------|
| **Functions** | `functions/` | Azure Functions (Python 3.11) | — | Connects to Palo Alto firewalls, collects config & health data, evaluates compliance, generates reports |
| **UI** | `ui/` | Flask dev server (Python 3.11) | 8003 | Web dashboard, AI chat, telemetry visualization, agent management |

---

## Directory Map

```
netsec-agent/
|
+-- test_inventory.py              Quick test: connects to firewall at 10.1.0.5
|                                   and prints device inventory
|
+-- functions/                     === AZURE FUNCTIONS BACKEND ===
|   +-- function_app.py            Main entry: 15 HTTP endpoints
|   +-- host.json                  Azure Functions host config (v2)
|   +-- local.settings.json        Local dev settings (storage emulator)
|   +-- requirements.txt           deps: azure-functions, requests,
|   |                               pan-os-python, openpyxl, azure-*
|   +-- test_excel.py              Test script for ExcelReport generation
|   +-- PaloAlto_Assessment.xlsx   Sample assessment workbook output
|   +-- functionapp.zip            Deployable package (~518 KB)
|   +-- webapp_logs.zip            Web app logs archive (~247 KB)
|   |
|   +-- baseline/
|   |   +-- baseline_rules.json    44 compliance rules (PA-01 to PA-67)
|   |   +-- PaloAlto_Compliance_Baseline.txt
|   |                               Human-readable compliance doc (67+ controls)
|   |
|   +-- compliance/
|   |   +-- compliance_engine.py   Evaluates assessment data against rules
|   |   +-- findings_generator.py  Converts non-compliant results into
|   |                               detailed findings with remediation
|   |
|   +-- connectors/
|   |   +-- utils/
|   |   |   +-- xml_parser.py      XML parsing utility (get_text, get_int,
|   |   |                            get_float, get_elements, to_dict...)
|   |   |
|   |   +-- paloalto/             === 11 Collector Modules ===
|   |       +-- paloalto_connector.py  Facade orchestrating all collectors
|   |       +-- inventory.py           Device info (hostname, model, version)
|   |       +-- health_status.py       CPU, memory, disk, session utilization
|   |       +-- ha_configuration.py    HA state, peer status, sync monitoring
|   |       +-- policy_configuration.py Security rules, NAT, zones, App-ID %
|   |       +-- security_services.py   Threat/AV/AS/DNS/WildFire/URL/SSL
|   |       +-- routing_configuration.py Virtual routers, BGP, OSPF
|   |       +-- vpn_configuration.py   GlobalProtect, IKE, IPsec, MFA
|   |       +-- logging_configuration.py Syslog, SIEM, SNMP, profiles
|   |       +-- administration_configuration.py Admins, IPs, HTTPS, NTP
|   |       +-- zone_protection_configuration.py Zone/DoS profiles
|   |       +-- backup_configuration.py Scheduled backup jobs
|   |
|   +-- reports/
|   |   +-- report_generator.py    Thin wrapper delegating to summaries
|   |   +-- executive_summary.py   Management-level summary text
|   |   +-- excel_report.py        Multi-sheet Excel workbook (openpyxl)
|   |   +-- risk_summary.py        CRITICAL/HIGH/MEDIUM/LOW risk level
|   |
|   +-- openapi/
|   |   +-- firewall-auditor-openapi.json  OpenAPI 3.0.1 spec (15 endpoints)
|   |
|   +-- applogs/                   Azure deployment logs (runtime artifacts,
|       |                           not application code)
|       +-- LogFiles/StartupLogs/  Container startup success logs
|       +-- LogFiles/Application/  Function host debug logs
|       +-- LogFiles/kudu/trace/   Kudu deployment engine traces (~50 files)
|       +-- deployments/           Per-deployment status.xml + log.log
|
+-- ui/                            === FLASK FRONTEND ===
    +-- app.py                     Flask app: routes + REST APIs, port 8003
    +-- requirements.txt           deps: flask, requests, azure-*
    |
    +-- config/
    |   +-- settings.py            Platform settings (function URL, key,
    |   |                            live mode, cache TTL, app insights)
    |   +-- keyvault.py            Azure Key Vault secret client with
    |   |                            in-memory cache + env var fallback
    |   +-- agents.json            Persisted agent registrations
    |   +-- sessions.json          Chat conversation history
    |   +-- insights.json          Token usage, latency, cost per turn
    |   +-- assessment_stats.json  Assessment run counter + last run time
    |   +-- reports_history.json   Report generation history (demo seeded)
    |   +-- telemetry_metrics.json Per-agent request/error metrics
    |   +-- telemetry_history.json Time-series map snapshots for slider
    |
    +-- gateway/                   === Agent Chat Orchestration ===
    |   +-- agent_gateway.py       Routes chat to foundry_client, persists
    |   |                            sessions, records telemetry & insights
    |   +-- session_manager.py     Conversation CRUD with thread-safe locking
    |   +-- tools.py               Tool registry: run_compliance_assessment,
    |   |                            run_full_assessment, executive_summary,
    |   |                            generate_excel_report
    |   +-- foundry_client.py      Azure AI Foundry chat client
    |                              (OpenAI Responses API format)
    |
    +-- services/                  === Business Logic Services ===
    |   +-- assessment_service.py  Assessment orchestrator: live Azure call
    |   |                            first, sample fallback, 120s cache
    |   +-- sample_assessment.py   Static demo data (hostname "edge-fw-01",
    |   |                            model PA-3220)
    |   +-- agents_service.py      Agent CRUD: add, list, get, remove,
    |   |                            set-connected, key masking
    |   +-- function_client.py     HTTP client for Azure Function endpoints
    |   +-- firewall_service.py    Thin delegation to function_client
    |   +-- dashboard_service.py   Aggregates compliance stats, agent health,
    |   |                            findings, cost, token, top cost drivers
    |   +-- chat_service.py        Delegates chat to gateway (single + multi)
    |   +-- insights_service.py    Per-conversation token/latency/cost
    |   |                            tracking; pricing: $1.25/$10 per M
    |   +-- report_history_service.py Report history with demo seed, 50 max
    |   +-- system_status_service.py  Probes 8 components (agent, functions,
    |   |                            firewall, foundry, model, keyvault,
    |   |                            appinsights, gateway); 30s cache;
    |   |                            returns overall/source/components
    |   +-- telemetry_map_service.py Builds node/edge ontology graph for
    |   |                            Cytoscape.js; history snapshots;
    |   |                            health scores; status lookup
    |   +-- app_insights.py        Azure App Insights telemetry sender
    |   +-- empty files: foundry_client.py, report_client.py
    |
    +-- templates/                 === Jinja2 HTML Templates ===
    |   +-- base.html              Sidebar nav (7 pages), top bar with
    |   |                            live badge + user chip, empty/loading/
    |   |                            skeleton states
    |   +-- dashboard.html         KPI cards, compliance ring, agent health
    |   +-- workspace.html         Chat UI, agent grid, add-agent modal,
    |   |                            quick action pills
    |   +-- findings.html          Agent Operations Center: search, risk/
    |   |                            status/impact filters, findings cards
    |   +-- reports.html           Report generation cards, recent reports
    |   |                            table, result display
    |   +-- insights.html          Agent KPI overview, per-agent cards,
    |   |                            cost observability, conversations table
    |   +-- telemetry_map.html     Cytoscape.js canvas, agent selector,
    |   |                            node detail panel, legend, KPI bar,
    |   |                            status/group filter chips, history
    |   |                            slider, zoom controls, source chip
    |   +-- settings.html          Azure Function, Foundry, Agent, API Keys,
    |   |                            Security config forms
    |
    +-- static/
        +-- images/
        |   +-- logo.svg           Red hexagon "LTM" brand logo
        |
        +-- vendor/
        |   +-- cytoscape.min.js   Cytoscape.js graph library
        |   +-- fonts/
        |       +-- inter.woff2        Inter variable font (400-800)
        |       +-- grotesk.woff2      Space Grotesk variable font (400-700)
        |       +-- inter-latin.css    Inter @font-face declarations
        |       +-- grotesk-latin.css  Space Grotesk @font-face declarations
        |       +-- inter-urls.txt     Original Inter download URLs
        |       +-- grotesk-urls.txt   Original Space Grotesk download URLs
        |
        +-- js/
        |   +-- main.js            Shared: sidebar toggle, responsive resize,
        |   |                        toast notifications, system status
        |   |                        polling (/api/system-status),
        |   |                        live badge updates
        |   +-- dashboard.js       Fetches /api/dashboard, animated KPI
        |   |                        counters, security posture ring,
        |   |                        agent health cards
        |   +-- workspace.js       Agent CRUD via /api/agents, chat via
        |   |                        /api/chat, quick actions, message
        |   |                        rendering, localStorage persistence
        |   +-- findings.js        Fetches /api/compliance, findings list
        |   |                        with filtering + collapsible cards
        |   +-- reports.js         Report history table from /api/reports,
        |   |                        download/view actions
        |   +-- insights.js        /api/insights, agent cards, cost KPI
        |   +-- settings.js        Save/test connection form handlers
        |   +-- telemetry_map.js   Cytoscape.js graph rendering, node/edge
        |                            visualization, detail panel, history
        |                            slider, zoom controls, group/status
        |                            filters, system source chip
        |
        +-- css/
        |   +-- main.css           Global design system (1423 lines): CSS
        |   |                        custom properties, fonts, hexagon
        |   |                        motifs, sidebar, top bar, content
        |   |                        layout, toasts, KPIs, forms, modals,
        |   |                        skeletons, system-status indicators,
        |   |                        responsive breakpoints
        |   +-- dashboard.css      Hero section, KPI grid, quick actions,
        |   |                        agent health cards, ring chart
        |   +-- workspace.css      Agent grid, chat section, message bubbles,
        |   |                        quick action pills, add-agent modal
        |   +-- findings.css       Toolbar, filters, findings cards,
        |   |                        summary chips, collapsible toggles
        |   +-- reports.css        Generation cards, report table, results
        |   +-- insights.css       Agent cards, cost observability grid,
        |   |                        conversation table
        |   +-- settings.css       Settings cards, toggle rows, form layouts
        |   +-- telemetry_map.css  Cytoscape canvas, detail panel, legend
        |                            (operational/stopped/faulted/changed),
        |                            KPI bar, history slider, zoom controls,
        |                            map-source chip
        |
        +-- reports/
            +-- PaloAlto_Assessment.xlsx  Exported assessment workbook
                                          (served as static download)
```

---

## Component Deep Dive

### Azure Functions Backend (`functions/`)

**Entry point:** `function_app.py` — exposed as a Blueprint with 15 HTTP-triggered endpoints:

| Endpoint | Method | Function |
|----------|--------|----------|
| `/get_inventory` | GET | Device info (hostname, model, serial, version) |
| `/get_health_status` | GET | CPU, memory, disk, session utilization |
| `/get_ha_configuration` | GET | HA state, peer status, sync monitoring |
| `/get_policy_configuration` | GET | Security rules, NAT, zones, App-ID analysis |
| `/get_security_services` | GET | Threat/AV/AS/DNS/WildFire/URL/SSL config |
| `/get_routing_configuration` | GET | Virtual routers, static routes, BGP/OSPF |
| `/get_vpn_configuration` | GET | GlobalProtect, IKE, IPsec, MFA |
| `/get_logging_configuration` | GET | Syslog, SIEM, SNMP, profiles |
| `/get_administration_configuration` | GET | Admins, management IPs, HTTPS/SSH, NTP |
| `/get_zone_protection` | GET | Zone protection, DoS profiles |
| `/get_backup_configuration` | GET | Scheduled backup jobs |
| `/run_full_assessment` | POST | Runs all 11 collectors, returns full JSON |
| `/run_compliance_assessment` | POST | Full assessment → compliance evaluation → findings |
| `/get_executive_summary` | POST | Management-level summary text |
| `/generate_excel_report` | POST | Multi-sheet .xlsx workbook |

**Connector architecture:** `PaloAltoConnector` in `paloalto_connector.py` is a Facade that wraps 11 individual collector modules. Each collector:
1. Connects to the firewall via `pan-os-python` SDK
2. Runs XML API commands (`show system info`, `show session info`, etc.)
3. Parses responses with `XmlParser` utility
4. Returns structured Python dicts

`function_app.py` instantiates the connector once per request and delegates to the appropriate collector.

**Compliance pipeline:**
```
Assessment JSON → ComplianceEngine.evaluate() → 44-rule baseline → 
COMPLIANT / NON_COMPLIANT / NOT_ASSESSED statuses → 
FindingsGenerator.generate() → remediation-guidance-augmented findings
```

**Reports pipeline:**
```
Assessment JSON → ExecutiveSummary.generate() → text summary
Assessment JSON → ExcelReport.generate() → 7-sheet .xlsx workbook
Findings JSON   → RiskSummary.calculate() → CRITICAL/HIGH/MEDIUM/LOW
```

---

### Flask Frontend (`ui/`)

**Entry point:** `app.py` — Flask application serving on port 8003 with 26 routes:

**Page routes (HTML):**
| Route | Template | Description |
|-------|----------|-------------|
| `/` | redirect → `/workspace` | Root redirect |
| `/dashboard` | `dashboard.html` | Security posture overview |
| `/workspace` | `workspace.html` | AI chat interface |
| `/findings` | `findings.html` | Agent Operations Center |
| `/reports` | `reports.html` | Report generation center |
| `/insights` | `insights.html` | Agent usage analytics |
| `/telemetry-map` | `telemetry_map.html` | Graph visualization |
| `/settings` | `settings.html` | Configuration forms |

**API routes (JSON):**
| Route | Method | Service Used | Returns |
|-------|--------|-------------|---------|
| `/api/compliance` | GET | `assessment_service` | Compliance results + findings |
| `/api/summary` | GET | `assessment_service` | Executive summary text |
| `/api/excel` | GET | `assessment_service` | .xlsx file download |
| `/api/agents` | GET/POST/DELETE | `agents_service` | Agent CRUD |
| `/api/chat` | POST | `chat_service` | LLM chat response |
| `/api/tools` | GET | `tools.py` | Available tool list |
| `/api/conversations` | GET | `session_manager` | Conversation list |
| `/api/conversations/<id>` | GET | `session_manager` | Conversation details |
| `/api/insights` | GET | `insights_service` | Usage analytics |
| `/api/dashboard` | GET | `dashboard_service` | Aggregated KPIs |
| `/api/reports` | GET | `report_history_service` | Report history |
| `/api/system-status` | GET | `system_status_service` | 8-component health |
| `/api/telemetry-map` | GET | `telemetry_map_service` | Node/edge graph |
| `/api/telemetry-map/history` | GET | `telemetry_map_service` | Time-series snapshots |

**Chat orchestration flow:**
```
Browser → POST /api/chat → ChatService → AgentGateway
  ├── SessionManager — load/save conversation state
  ├── FoundryClient — POST to Azure AI Foundry endpoint
  ├── InsightsService — record token usage, latency, cost
  └── AppInsights — send telemetry events
→ JSON response back to browser
```

**Assessment flow:**
```
Browser → GET /api/compliance → AssessmentService
  ├── Try: FunctionClient.get() → Azure Functions /run_compliance_assessment
  ├── Catch: fallback to SampleAssessment static data
  └── Cache for 120 seconds
→ JSON response with compliance results + findings
```

**System status probe:**
```
Browser → GET /api/system-status → SystemStatusService
  ├── Agent: check /api/agents for connected agent
  ├── Functions: GET {URL}/get_inventory (6s timeout)
  │   ├── 200 OK → functions=operational, firewall=operational
  │   ├── 5xx → functions=operational, firewall=degraded
  │   └── exception → functions=offline
  ├── Foundry: check FOUNDRY_ENDPOINT config
  ├── Model: check LLM_MODEL config
  ├── Key Vault: check VAULT_URL config
  ├── AppInsights: check APPINSIGHTS_CONNECTION_STRING
  └── Gateway: always operational if server running
→ Returns: overall (operational/degraded/offline),
          source (live/sample),
          components list with statuses
```

---

## Data Flow

### 1. Firewall Assessment (Real-Time)
```
Browser                Flask UI              Azure Functions           Palo Alto FW
  |                      |                        |                        |
  |--GET /api/compliance->|                        |                        |
  |                      |--POST /run_compliance->|                        |
  |                      |                        |--XML API commands----->|
  |                      |                        |<--device config/data---|
  |                      |                        |--run 44 rules--------->|
  |                      |                        |--generate findings---->|
  |                      |<--JSON results----------|                        |
  |<--JSON response-------|                        |                        |
```

### 2. AI Chat (Agent Gateway)
```
Browser                Flask UI            Gateway           Azure AI Foundry
  |                      |                   |                     |
  |--POST /api/chat----->|                   |                     |
  |                      |--delegate-------->|                     |
  |                      |                   |--load session------>|
  |                      |                   |--POST chat--------->|
  |                      |                   |<--LLM response------|
  |                      |                   |--save session------>|
  |                      |                   |--record insights--->|
  |                      |                   |--send telemetry--->|
  |                      |<--response---------|                     |
  |<--JSON response-------|                   |                     |
```

### 3. Telemetry Map Construction
```
Browser                Flask UI              TelemetryMapService
  |                      |                        |
  |--GET /api/telemetry->|                        |
  |                      |--build_map()----------->|
  |                      |                        |--query metrics.json
  |                      |                        |--resolve system status
  |                      |                        |--build node/edge graph
  |                      |                        |--compute health scores
  |                      |                        |--save history snapshot
  |                      |<--JSON graph------------|
  |<--JSON response-------|                        |
  |                      |                        |
  |--render Cytoscape.js->|                        |
```

---

## Page Routing

All pages share `base.html` as the parent template, which provides:
- **Sidebar:** 7 navigation links (Dashboard, AI Workspace, Telemetry Map, Agent Insights, Agent Ops Center, Reports, Settings)
- **Top bar:** Live/Sample badge, user chip
- **System status:** Dynamic dot + label (green/yellow/red) in sidebar footer
- **Shared JS:** `main.js` loads system status, handles toasts, sidebar toggle

Each page loads its own page-specific JS and CSS:
| Page | Template | JS File | CSS File |
|------|----------|---------|----------|
| Dashboard | `dashboard.html` | `dashboard.js` | `dashboard.css` |
| Workspace | `workspace.html` | `workspace.js` | `workspace.css` |
| Findings | `findings.html` | `findings.js` | `findings.css` |
| Reports | `reports.html` | `reports.js` | `reports.css` |
| Insights | `insights.html` | `insights.js` | `insights.css` |
| Telemetry Map | `telemetry_map.html` | `telemetry_map.js` | `telemetry_map.css` |
| Settings | `settings.html` | `settings.js` | `settings.css` |

---

## Design Patterns

| Pattern | Where Used | Description |
|---------|-----------|-------------|
| **Facade** | `paloalto_connector.py` | Single entry point wrapping 11 collector modules |
| **Strategy** | `assessment_service.py` | Live → sample fallback; `system_status_service.py` probe with 6s timeout |
| **Gateway** | `gateway/agent_gateway.py` | Centralized chat routing with session, insight, telemetry hooks |
| **Repository** | `config/*.json` files | JSON file-backed persistence with thread-safe file locking |
| **Cache-Aside** | `assessment_service.py` (120s), `system_status_service.py` (30s), `keyvault.py` (in-memory) | Avoid redundant API calls |
| **Observer** | `insights_service.py` → `app_insights.py` | Cost/token events broadcast to Azure telemetry |
| **Singleton** | `config/settings.py` | Single `Settings` instance across app |
| **Template Method** | `base.html` extending to 7 page templates | Shared layout with per-page content blocks |

---

## Configuration & Persistence

All data is stored in `ui/config/` as JSON files:

| File | Schema | Purpose |
|------|--------|---------|
| `agents.json` | `{name, type, endpoint, model, api_key, connected}` | Agent registrations |
| `sessions.json` | `{id, agent_id, messages[], created_at}` | Chat history |
| `insights.json` | `{conversation_id, tokens_in, tokens_out, latency_ms, cost}` | Usage tracking |
| `assessment_stats.json` | `{total_runs, last_run}` | Assessment run counter |
| `reports_history.json` | `{id, type, filename, created_at, findings_count}` | Report records |
| `telemetry_metrics.json` | `{request_count, error_count, avg_latency_ms}` | Per-agent metrics |
| `telemetry_history.json` | `[{timestamp, nodes[], edges[]}]` | Map time series |

Key Vault secrets (if provisioned) are fetched via `config/keyvault.py` with a fallback to environment variables: `FUNCTION_KEY`, `FOUNDRY_KEY`, `FOUNDRY_ENDPOINT`.
