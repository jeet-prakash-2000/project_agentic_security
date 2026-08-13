(function () {
    "use strict";

    // ============================================================
    // DOM REFERENCES
    // ============================================================

    var sidebar = document.getElementById("wsSidebar");
    var insights = document.getElementById("wsInsights");
    var sidebarToggle = document.getElementById("sidebarToggle");
    var insightsToggle = document.getElementById("insightsToggle");
    var insightsClose = document.getElementById("insightsClose");
    var newChatBtn = document.getElementById("newChatBtn");
    var convSearch = document.getElementById("convSearch");
    var convList = document.getElementById("convList");
    var wsAgentSelect = document.getElementById("wsAgentSelect");

    var chatWindow = document.getElementById("chatWindow");
    var chatAgentTitle = document.getElementById("chatAgentTitle");
    var chatAgentSub = document.getElementById("chatAgentSub");
    var chatAgentAvatar = document.getElementById("chatAgentAvatar");
    var clearBtn = document.getElementById("clearChatBtn");
    var promptInput = document.getElementById("promptInput");
    var sendBtn = document.getElementById("sendBtn");
    var promptChips = document.getElementById("promptChips");
    var composerAgentBadge = document.getElementById("composerAgentBadge");

    var modal = document.getElementById("addAgentModal");
    var openBtn = document.getElementById("openAddAgentBtn");
    var closeBtn = document.getElementById("closeAddAgentBtn");
    var cancelBtn = document.getElementById("cancelAddAgentBtn");
    var form = document.getElementById("addAgentForm");

    var insightAvatar = document.getElementById("insightAvatar");
    var insightAgentName = document.getElementById("insightAgentName");
    var insightAgentModel = document.getElementById("insightAgentModel");
    var insightAgentStatus = document.getElementById("insightAgentStatus");
    var insightCompliance = document.getElementById("insightCompliance");
    var insightFindings = document.getElementById("insightFindings");
    var insightRuns = document.getElementById("insightRuns");
    var insightLastAssessment = document.getElementById("insightLastAssessment");
    var insightMessages = document.getElementById("insightMessages");
    var insightTokens = document.getElementById("insightTokens");
    var insightCost = document.getElementById("insightCost");
    var insightOutputs = document.getElementById("insightOutputs");

    // ============================================================
    // CONSTANTS — actions, prompts, tool metadata
    // ============================================================

    var STORE_KEY = "ltm_conversations";

    var ACTIONS = {
        assess: { label: "Run Assessment", tool: "assess", prompt: "Run a full compliance assessment of the firewall estate." },
        summary: { label: "Executive Summary", tool: "summary", prompt: "Generate an executive summary of the security posture." },
        excel: { label: "Generate Report", tool: "excel", prompt: "Generate the assessment workbook report." },
        findings: { label: "Show Findings", tool: "findings", prompt: "Review the compliance findings from the latest assessment." },
        config: { label: "Analyze Configuration", tool: null, prompt: "Analyze the current firewall configuration and highlight any misconfigurations." },
        recommend: { label: "Security Recommendations", tool: null, prompt: "Provide prioritized security recommendations to harden my firewall estate." }
    };

    var COMPOSER_CHIPS = ["assess", "summary", "excel", "findings", "recommend"];

    var SUGGESTIONS = [
        { label: "Run Compliance Assessment", action: "assess" },
        { label: "Generate Executive Summary", action: "summary" },
        { label: "Generate Firewall Report", action: "excel" },
        { label: "Review Compliance Findings", action: "findings" },
        { label: "Analyze Firewall Configuration", action: "config" },
        { label: "Security Recommendations", action: "recommend" }
    ];

    var TOOL_META = {
        assess: {
            name: "Compliance Assessment",
            link: { label: "View findings", href: "/findings" },
            icon: '<path d="M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6l7-3z"/>'
        },
        summary: {
            name: "Executive Summary",
            link: { label: "Open reports", href: "/reports" },
            icon: '<path d="M20 6L9 17l-5-5"/>'
        },
        excel: {
            name: "Report Generation",
            link: { label: "Download workbook", href: "/api/excel" },
            icon: '<path d="M6 2.5h8l4 4V21.5H6V2.5z"/><path d="M14 2.5v4h4"/>'
        },
        findings: {
            name: "Compliance Findings",
            link: { label: "View findings", href: "/findings" },
            icon: '<path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><path d="M12 9v4"/><circle cx="12" cy="17" r="1"/>'
        }
    };

    var COPY_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 012-2h10"/></svg>';
    var ARROW_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7M9 7h8v8"/></svg>';
    var DEFAULT_TOOL_ICON = '<path d="M12 3l1.9 4.6 4.6 1.9-4.6 1.9L12 16l-1.9-4.6L5.5 9.5l4.6-1.9L12 3z"/><path d="M18.5 15.5l.9 2.1 2.1.9-2.1.9-.9 2.1-.9-2.1-2.1-.9 2.1-.9.9-2.1z"/>';
    var LOGO_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.9 4.6 4.6 1.9-4.6 1.9L12 16l-1.9-4.6L5.5 9.5l4.6-1.9L12 3z"/></svg>';

    // ============================================================
    // STATE
    // ============================================================

    var state = {
        conversations: loadStore(),
        activeId: null,
        activeAgentId: null,
        activeAgent: null,
        agents: []
    };

    // ============================================================
    // STORAGE
    // ============================================================

    function loadStore() {
        try {
            var raw = localStorage.getItem(STORE_KEY);
            var data = raw ? JSON.parse(raw) : [];
            return Array.isArray(data) ? data : [];
        } catch (e) {
            return [];
        }
    }

    function saveStore() {
        try {
            localStorage.setItem(STORE_KEY, JSON.stringify(state.conversations));
        } catch (e) { /* storage unavailable */ }
    }

    function now() {
        return Math.floor(Date.now() / 1000);
    }

    function getActiveConv() {
        if (!state.activeId) return null;
        for (var i = 0; i < state.conversations.length; i++) {
            if (state.conversations[i].id === state.activeId) return state.conversations[i];
        }
        return null;
    }

    function getConv(id) {
        for (var i = 0; i < state.conversations.length; i++) {
            if (state.conversations[i].id === id) return state.conversations[i];
        }
        return null;
    }

    // ============================================================
    // CONVERSATION MANAGEMENT
    // ============================================================

    function createConversation() {
        var conv = {
            id: "conv-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8),
            title: "New chat",
            created: now(),
            updated: now(),
            agentId: state.activeAgentId || null,
            messages: []
        };
        state.conversations.unshift(conv);
        state.activeId = conv.id;
        saveStore();
        renderConversationList();
        renderActiveConversation();
        return conv;
    }

    function ensureConversation() {
        if (!state.activeId || !getConv(state.activeId)) return createConversation();
        return state.activeId;
    }

    function setActive(id) {
        state.activeId = id;
        renderActiveConversation();
        renderConversationList();
    }

    function maybeSetTitle(text) {
        var conv = getActiveConv();
        if (!conv) return;
        var userCount = conv.messages.filter(function (m) { return m.role === "user"; }).length;
        if (userCount === 1) {
            conv.title = text.length > 44 ? text.slice(0, 44) + "\u2026" : text;
            saveStore();
        }
    }

    // ============================================================
    // CONVERSATION LIST RENDERING
    // ============================================================

    function sameDay(a, b) {
        return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
    }

    function dateGroup(ts) {
        var d = new Date(ts * 1000);
        var today = new Date();
        var msgMidnight = new Date(d.getFullYear(), d.getMonth(), d.getDate());
        var todayMidnight = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        var diff = Math.round((todayMidnight - msgMidnight) / 86400000);
        if (diff <= 0) return "Today";
        if (diff === 1) return "Yesterday";
        if (diff < 7) return "Previous 7 Days";
        return "Older";
    }

    function convItemTime(ts) {
        var d = new Date(ts * 1000);
        if (sameDay(d, new Date())) {
            return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
        }
        return d.toLocaleDateString([], { month: "short", day: "numeric" });
    }

    function renderConversationList() {
        if (!convList) return;
        var q = (convSearch.value || "").trim().toLowerCase();

        var list = state.conversations.slice().sort(function (a, b) {
            return (b.updated || 0) - (a.updated || 0);
        });

        if (q) {
            list = list.filter(function (c) {
                return (c.title || "").toLowerCase().indexOf(q) !== -1;
            });
        }

        convList.innerHTML = "";

        if (!list.length) {
            var empty = document.createElement("div");
            empty.className = "ws-conv-empty";
            empty.textContent = q ? "No conversations found." : "No conversations yet. Start a new chat.";
            convList.appendChild(empty);
            return;
        }

        var groups = ["Today", "Yesterday", "Previous 7 Days", "Older"];
        var grouped = {};
        list.forEach(function (c) {
            var g = dateGroup(c.updated || c.created);
            if (!grouped[g]) grouped[g] = [];
            grouped[g].push(c);
        });

        groups.forEach(function (g) {
            var items = grouped[g];
            if (!items || !items.length) return;
            var label = document.createElement("div");
            label.className = "ws-conv-group-label";
            label.textContent = g;
            convList.appendChild(label);

            var groupEl = document.createElement("div");
            groupEl.className = "ws-conv-group";
            convList.appendChild(groupEl);

            items.forEach(function (c) {
                var item = document.createElement("button");
                item.className = "ws-conv-item" + (c.id === state.activeId ? " active" : "");
                item.setAttribute("data-conv-id", c.id);
                item.innerHTML =
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>' +
                    '<span class="ws-conv-item-title">' + escapeHtml(c.title || "New chat") + "</span>" +
                    '<span class="ws-conv-item-time">' + convItemTime(c.updated || c.created) + "</span>";
                item.addEventListener("click", function () { setActive(c.id); });
                groupEl.appendChild(item);
            });
        });
    }

    // ============================================================
    // MESSAGE RENDERING
    // ============================================================

    function scrollToBottom() {
        if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function buildRow(role) {
        var row = document.createElement("div");
        row.className = "ws-message" + (role === "user" ? " ws-message-user" : "");
        return row;
    }

    function metaRow(msg) {
        var row = document.createElement("div");
        row.className = "ws-msg-meta";
        var time = document.createElement("span");
        time.className = "ws-msg-time";
        time.textContent = msg.ts ? formatTime(msg.ts) : "";
        row.appendChild(time);
        if (msg.content) {
            var copy = document.createElement("button");
            copy.className = "ws-msg-copy";
            copy.innerHTML = COPY_ICON + " Copy";
            copy.addEventListener("click", function () { copyText(msg.content); });
            row.appendChild(copy);
        }
        return row;
    }

    function renderUserMessage(msg) {
        var row = buildRow("user");
        var avatar = document.createElement("div");
        avatar.className = "ws-msg-avatar";
        avatar.innerHTML = '<span class="ws-user-avatar">You</span>';
        var body = document.createElement("div");
        body.className = "ws-msg-body";
        var text = document.createElement("div");
        text.className = "ws-msg-text";
        var p = document.createElement("p");
        p.textContent = msg.content;
        text.appendChild(p);
        body.appendChild(text);
        body.appendChild(metaRow(msg));
        row.appendChild(avatar);
        row.appendChild(body);
        chatWindow.appendChild(row);
    }

    function toolCardHtml(name, bodyHtml, link, icon) {
        var h = '<div class="ws-tool-card">';
        h += '<div class="ws-tool-card-head">';
        h += '<span class="ws-tool-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + (icon || DEFAULT_TOOL_ICON) + "</svg></span>";
        h += '<span class="ws-tool-name">' + escapeHtml(name) + "</span>";
        h += '<span class="ws-tool-status"><span class="pulse-dot"></span>Completed</span>';
        h += "</div>";
        h += '<div class="ws-tool-card-body ws-msg-text">' + bodyHtml + "</div>";
        if (link) {
            h += '<div class="ws-tool-card-foot"><a class="ws-tool-link" href="' + link.href + '">' + escapeHtml(link.label) + " " + ARROW_ICON + "</a></div>";
        }
        h += "</div>";
        return h;
    }

    function assistantBodyHtml(msg) {
        if (msg.html) {
            return toolCardHtml(msg.cardTitle || "Firewall Data", msg.html, null);
        }
        if (msg.tool && TOOL_META[msg.tool]) {
            var meta = TOOL_META[msg.tool];
            return toolCardHtml(meta.name, formatAgentReply(msg.content), meta.link, meta.icon);
        }
        return '<div class="ws-msg-text">' + formatAgentReply(msg.content || "") + "</div>";
    }

    function renderAssistantMessage(msg) {
        var row = buildRow("assistant");
        var agentName = msg.agentName || (state.activeAgent ? state.activeAgent.name : "Firewall Auditor");
        var avatar = document.createElement("div");
        avatar.className = "ws-msg-avatar";
        avatar.innerHTML = '<span class="agent-avatar agent-avatar-blue">' + escapeHtml(avatarFor(agentName)) + "</span>";

        var body = document.createElement("div");
        body.className = "ws-msg-body";
        var agent = document.createElement("span");
        agent.className = "ws-msg-agent";
        agent.textContent = agentName;
        body.appendChild(agent);

        var rich = document.createElement("div");
        rich.innerHTML = assistantBodyHtml(msg);
        body.appendChild(rich);

        if (msg.usage && Object.keys(msg.usage).length) {
            var usage = document.createElement("div");
            usage.className = "ws-msg-usage";
            usage.textContent = usageText(msg.usage);
            body.appendChild(usage);
        }

        body.appendChild(metaRow(msg));

        row.appendChild(avatar);
        row.appendChild(body);
        chatWindow.appendChild(row);
    }

    function renderMessage(msg) {
        if (!chatWindow) return;
        if (msg.role === "user") renderUserMessage(msg);
        else renderAssistantMessage(msg);
        scrollToBottom();
    }

    function renderActiveConversation() {
        if (!chatWindow) return;
        chatWindow.innerHTML = "";
        var conv = getActiveConv();
        if (!conv || !conv.messages.length) {
            renderEmptyState();
            updateSessionMetrics();
            return;
        }
        conv.messages.forEach(renderMessage);
        updateSessionMetrics();
    }

    function appendAndStoreMessage(msg) {
        var conv = getActiveConv();
        if (!conv) return;
        conv.messages.push(msg);
        conv.updated = now();
        saveStore();
        renderMessage(msg);
        updateSessionMetrics();
    }

    function appendTyping(agentName) {
        var row = buildRow("assistant");
        row.dataset.typing = "true";
        var name = agentName || (state.activeAgent ? state.activeAgent.name : "Firewall Auditor");
        var avatar = document.createElement("div");
        avatar.className = "ws-msg-avatar";
        avatar.innerHTML = '<span class="agent-avatar agent-avatar-blue">' + escapeHtml(avatarFor(name)) + "</span>";
        var body = document.createElement("div");
        body.className = "ws-msg-body";
        body.innerHTML = '<span class="ws-msg-agent">' + escapeHtml(name) + '</span><div class="ws-typing"><span></span><span></span><span></span></div>';
        row.appendChild(avatar);
        row.appendChild(body);
        chatWindow.appendChild(row);
        scrollToBottom();
        return row;
    }

    function removeTyping(node) {
        if (node && node.parentNode) node.parentNode.removeChild(node);
    }

    function usageText(usage) {
        var parts = [];
        if (usage.total_tokens != null) parts.push(usage.total_tokens.toLocaleString("en-US") + " tokens");
        if (usage.input_tokens != null) parts.push(usage.input_tokens.toLocaleString("en-US") + " in");
        if (usage.output_tokens != null) parts.push(usage.output_tokens.toLocaleString("en-US") + " out");
        return parts.length ? parts.join(" \u00b7 ") : "Token usage tracked";
    }

    // ============================================================
    // EMPTY STATE
    // ============================================================

    function renderEmptyState() {
        if (!chatWindow) return;
        chatWindow.innerHTML = "";
        var wrap = document.createElement("div");
        wrap.className = "ws-empty";
        wrap.innerHTML =
            '<div class="ws-empty-mark">' + LOGO_ICON + "</div>" +
            "<h2>How can I help secure your environment today?</h2>" +
            "<p>Talk to your security copilot \u2014 run compliance assessments, review findings, and generate executive reports.</p>" +
            '<div class="ws-suggestions"></div>';
        chatWindow.appendChild(wrap);

        var sug = wrap.querySelector(".ws-suggestions");
        SUGGESTIONS.forEach(function (s) {
            var b = document.createElement("button");
            b.className = "ws-suggestion";
            b.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>' + escapeHtml(s.label);
            b.addEventListener("click", function () { runAction(s.action); });
            sug.appendChild(b);
        });
    }

    // ============================================================
    // PROMPT CHIPS
    // ============================================================

    function renderPromptChips() {
        if (!promptChips) return;
        promptChips.innerHTML = "";
        COMPOSER_CHIPS.forEach(function (id) {
            var a = ACTIONS[id];
            if (!a) return;
            var b = document.createElement("button");
            b.className = "ws-chip";
            b.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>' + escapeHtml(a.label);
            b.addEventListener("click", function () { runAction(id); });
            promptChips.appendChild(b);
        });
    }

    function runAction(action) {
        var a = ACTIONS[action];
        if (!a) return;
        sendPrompt(a.prompt, { tool: a.tool });
    }

    // ============================================================
    // CHAT / SEND
    // ============================================================

    function detectDataAction(lower) {
        if (lower.indexOf("inventory") !== -1 || lower.indexOf("device info") !== -1) return "inventory";
        if (lower.indexOf("health") !== -1 || lower.indexOf("cpu") !== -1 || lower.indexOf("memory") !== -1 || lower.indexOf("disk") !== -1 || lower.indexOf("session") !== -1) return "health";
        if (lower.indexOf("policy") !== -1 || lower.indexOf("rule") !== -1 || lower.indexOf("firewall rules") !== -1) return "policy";
        if (lower.indexOf("ha") !== -1 || lower.indexOf("high availability") !== -1) return "ha";
        if (lower.indexOf("service") !== -1 || lower.indexOf("security service") !== -1 || lower.indexOf("threat") !== -1 || lower.indexOf("wildfire") !== -1 || lower.indexOf("url filter") !== -1 || lower.indexOf("dns security") !== -1 || lower.indexOf("ssl decrypt") !== -1) return "services";
        if (lower.indexOf("routing") !== -1 || lower.indexOf("route") !== -1) return "routing";
        if (lower.indexOf("vpn") !== -1 || lower.indexOf("tunnel") !== -1) return "vpn";
        if (lower.indexOf("logging") !== -1 || lower.indexOf("log") !== -1 || lower.indexOf("siem") !== -1 || lower.indexOf("retention") !== -1) return "logging";
        if (lower.indexOf("admin") !== -1 || lower.indexOf("management") !== -1 || lower.indexOf("administration") !== -1 || lower.indexOf("ntp") !== -1 || lower.indexOf("snmp") !== -1) return "administration";
        if (lower.indexOf("zone protect") !== -1 || lower.indexOf("zone protection") !== -1 || lower.indexOf("dos") !== -1 || lower.indexOf("packet") !== -1) return "zone_protection";
        if (lower.indexOf("backup") !== -1 || lower.indexOf("recovery") !== -1) return "backup";
        return null;
    }

    function runDataAction(action) {
        var prompts = {
            inventory: "Show inventory details.", health: "Show health status.",
            policy: "Show policy configuration.", ha: "Show HA configuration.",
            services: "Show security services status.", routing: "Show routing configuration.",
            vpn: "Show VPN configuration.", logging: "Show logging configuration.",
            administration: "Show administration configuration.", zone_protection: "Show zone protection configuration.",
            backup: "Show backup configuration."
        };
        var endpoints = {
            inventory: "/api/firewall/inventory", health: "/api/firewall/health", policy: "/api/firewall/policy",
            ha: "/api/firewall/ha", services: "/api/firewall/services", routing: "/api/firewall/routing",
            vpn: "/api/firewall/vpn", logging: "/api/firewall/logging", administration: "/api/firewall/administration",
            zone_protection: "/api/firewall/zone-protection", backup: "/api/firewall/backup"
        };
        var titles = {
            inventory: "Firewall Inventory", health: "Health Status", policy: "Policy Configuration",
            ha: "HA Configuration", services: "Security Services", routing: "Routing Configuration",
            vpn: "VPN Configuration", logging: "Logging Configuration", administration: "Administration Configuration",
            zone_protection: "Zone Protection Configuration", backup: "Backup Configuration"
        };

        ensureConversation();
        appendAndStoreMessage({ role: "user", content: prompts[action], ts: now() });
        maybeSetTitle(prompts[action]);
        renderConversationList();

        var typing = appendTyping("Firewall Data");
        sendBtn.disabled = true;

        fetch(endpoints[action])
            .then(function (r) { return r.json(); })
            .then(function (data) {
                removeTyping(typing);
                if (data && data.error) throw new Error(data.error);
                var html = action === "policy" ? renderPolicyCard(data) : renderTableCard(titles[action], data);
                appendAndStoreMessage({ role: "assistant", content: "", html: html, cardTitle: titles[action], agentName: "Firewall Data", ts: now() });
                renderConversationList();
            })
            .catch(function () {
                removeTyping(typing);
                appendAndStoreMessage({ role: "assistant", content: "Unable to fetch data from the firewall function. Check connectivity.", agentName: "Firewall Data", ts: now() });
                renderConversationList();
            })
            .finally(function () { sendBtn.disabled = false; promptInput.focus(); });
    }

    function sendPrompt(prompt, opts) {
        opts = opts || {};
        var text = (prompt || "").trim();
        if (!text) return;

        var lower = text.toLowerCase();
        var dataAction = detectDataAction(lower);
        if (dataAction) { runDataAction(dataAction); return; }

        ensureConversation();
        appendAndStoreMessage({ role: "user", content: text, ts: now() });
        maybeSetTitle(text);
        renderConversationList();
        promptInput.value = "";
        autoResize();

        var typing = appendTyping();
        sendBtn.disabled = true;

        fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text, conversation_id: state.activeId, agent_id: state.activeAgentId })
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                removeTyping(typing);
                if (data && data.error) throw new Error(data.error);
                var reply = (data && data.reply) || buildAssistantReply(text);
                appendAndStoreMessage({ role: "assistant", content: reply, tool: opts.tool || null, usage: (data && data.usage) || null, agentName: (data && data.agent && data.agent.name) || null, ts: now() });
                renderConversationList();
                loadSessionInsights();
            })
            .catch(function (error) {
                removeTyping(typing);
                var fallback = buildAssistantReply(text);
                appendAndStoreMessage({ role: "assistant", content: fallback, tool: opts.tool || null, ts: now() });
                renderConversationList();
                if (error && error.message && error.message.indexOf("No connected agent") === -1) {
                    window.showToast("Agent unavailable \u2014 showing preview response.", "error");
                }
            })
            .finally(function () { sendBtn.disabled = false; promptInput.focus(); });
    }

    // ============================================================
    // AGENTS
    // ============================================================

    function avatarFor(name) {
        var parts = String(name || "").trim().split(/\s+/);
        return parts.map(function (p) { return p.charAt(0); }).join("").toUpperCase().slice(0, 2) || "AG";
    }

    function setActiveAgent(agent) {
        if (!agent) return;
        state.activeAgent = agent;
        state.activeAgentId = agent.id || null;

        if (chatAgentTitle) chatAgentTitle.textContent = agent.name || "Firewall Auditor";
        if (chatAgentSub) chatAgentSub.textContent = ((agent.model ? agent.model + " \u00b7 " : "") + (agent.type || "Copilot")).trim();
        if (chatAgentAvatar) chatAgentAvatar.textContent = avatarFor(agent.name);

        if (composerAgentBadge) {
            composerAgentBadge.innerHTML = '<span class="pulse-dot"></span>' + escapeHtml(agent.name || "Agent");
        }

        if (insightAvatar) insightAvatar.textContent = avatarFor(agent.name);
        if (insightAgentName) insightAgentName.textContent = agent.name || "Agent";
        if (insightAgentModel) insightAgentModel.textContent = agent.model || "gpt-5.1";
        if (insightAgentStatus) insightAgentStatus.classList.toggle("is-offline", !agent.connected);

        if (wsAgentSelect && agent.id && wsAgentSelect.value !== agent.id) {
            wsAgentSelect.value = agent.id;
        }
    }

    function populateAgentSelect() {
        if (!wsAgentSelect) return;
        wsAgentSelect.innerHTML = "";
        state.agents.forEach(function (a) {
            var opt = document.createElement("option");
            opt.value = a.id;
            opt.textContent = a.name;
            wsAgentSelect.appendChild(opt);
        });
        if (!state.agents.length) {
            var empty = document.createElement("option");
            empty.value = "";
            empty.textContent = "No agents configured";
            wsAgentSelect.appendChild(empty);
        }
    }

    function resolveInitialAgent() {
        var global = window.getGlobalAgent ? window.getGlobalAgent() : null;
        if (global) {
            for (var i = 0; i < state.agents.length; i++) {
                if (state.agents[i].id === global.id) return state.agents[i];
            }
        }
        var connected = state.agents.filter(function (a) { return a.connected; });
        if (connected[0]) return connected[0];
        return state.agents[0] || null;
    }

    function loadAgents() {
        fetch("/api/agents")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                state.agents = (data && data.agents) || [];
                populateAgentSelect();
                var agent = resolveInitialAgent();
                if (agent) setActiveAgent(agent);
            })
            .catch(function () {});
    }

    // ============================================================
    // INSIGHTS PANEL
    // ============================================================

    function fmtNum(n) {
        return Number(n).toLocaleString("en-US");
    }

    function relativeTime(ts) {
        if (!ts) return "";
        var diff = Math.floor(Date.now() / 1000) - ts;
        if (diff < 60) return "just now";
        if (diff < 3600) return Math.floor(diff / 60) + "m ago";
        if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
        return Math.floor(diff / 86400) + "d ago";
    }

    function updateSessionMetrics() {
        if (!insightMessages) return;
        var conv = getActiveConv();
        insightMessages.textContent = conv ? String(conv.messages.length) : "0";
    }

    function renderRecentOutputs(reports) {
        if (!insightOutputs) return;
        insightOutputs.innerHTML = "";
        if (!reports || !reports.length) {
            var empty = document.createElement("div");
            empty.className = "ws-insight-empty";
            empty.textContent = "No reports generated yet.";
            insightOutputs.appendChild(empty);
            return;
        }
        reports.forEach(function (r) {
            var el = document.createElement("div");
            el.className = "ws-output";
            var isExcel = (r.type || "").toLowerCase().indexOf("workbook") !== -1 || (r.type || "").toLowerCase().indexOf("excel") !== -1;
            var icon = isExcel
                ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2.5h8l4 4V21.5H6V2.5z"/><path d="M14 2.5v4h4"/></svg>'
                : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2.5h8l4 4V21.5H6V2.5z"/><path d="M9 12h6M9 16h6"/></svg>';
            var status = (r.status || "").toLowerCase();
            el.innerHTML =
                '<span class="ws-output-icon">' + icon + "</span>" +
                '<span class="ws-output-meta"><strong>' + escapeHtml(r.name || r.type || "Report") + "</strong><span>" + escapeHtml(r.type || "") + "</span></span>" +
                '<span class="ws-output-status ' + (status === "completed" ? "ok" : "fail") + '">' + escapeHtml(r.status || "") + "</span>";
            insightOutputs.appendChild(el);
        });
    }

    function loadSessionInsights() {
        fetch("/api/insights")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var totals = (data && data.totals) || {};
                if (insightTokens && totals.total_tokens != null) insightTokens.textContent = fmtNum(totals.total_tokens);
                if (insightCost && totals.cost != null) insightCost.textContent = "$" + Number(totals.cost).toFixed(2);
            })
            .catch(function () {});
    }

    function loadAssessmentInsights() {
        var controller = new AbortController();
        var timer = setTimeout(function () { controller.abort(); }, 20000);
        fetch("/api/dashboard", { signal: controller.signal })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                clearTimeout(timer);
                if (data && data.compliance) {
                    if (insightCompliance) {
                        insightCompliance.textContent = data.compliance.compliance_score + "%";
                        insightCompliance.className = "ws-metric-value " + (data.compliance.compliance_score >= 70 ? "is-good" : "is-bad");
                    }
                    if (insightFindings && data.findings) insightFindings.textContent = String(data.findings.open || 0);
                }
                if (insightRuns && data.assessments_run != null) insightRuns.textContent = String(data.assessments_run);
                if (insightLastAssessment && data.generated_at) {
                    insightLastAssessment.textContent = "Last assessment " + relativeTime(Math.floor(data.generated_at));
                }
            })
            .catch(function () { clearTimeout(timer); });
    }

    function loadRecentOutputs() {
        fetch("/api/reports")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                renderRecentOutputs((data && data.reports) || []);
            })
            .catch(function () {});
    }

    // ============================================================
    // ADD AGENT MODAL
    // ============================================================

    function openModal() {
        if (modal) modal.hidden = false;
        document.body.style.overflow = "hidden";
        setTimeout(function () { var f = document.getElementById("agentName"); if (f) f.focus(); }, 120);
    }

    function closeModal() {
        if (modal) modal.hidden = true;
        document.body.style.overflow = "";
    }

    function bindModal() {
        if (openBtn) openBtn.addEventListener("click", openModal);
        if (closeBtn) closeBtn.addEventListener("click", closeModal);
        if (cancelBtn) cancelBtn.addEventListener("click", closeModal);
        if (modal) modal.addEventListener("click", function (e) { if (e.target === modal) closeModal(); });
        document.addEventListener("keydown", function (e) { if (e.key === "Escape" && modal && !modal.hidden) closeModal(); });

        if (form) {
            form.addEventListener("submit", function (event) {
                event.preventDefault();
                var name = document.getElementById("agentName").value.trim();
                var type = document.getElementById("agentType").value;
                var endpoint = document.getElementById("agentEndpoint").value.trim();
                var model = document.getElementById("agentModel").value.trim() || "gpt-5.1";
                var key = document.getElementById("agentKey").value.trim();

                if (!name || !endpoint || !key) {
                    window.showToast("Agent name, endpoint, and API key are required.", "error");
                    return;
                }

                ensureConversation();
                appendAndStoreMessage({ role: "user", content: "Connect the " + name + " agent for " + type + ".", ts: now() });
                maybeSetTitle("Connect the " + name + " agent");
                renderConversationList();

                var typing = appendTyping();
                var connectBtn = form.querySelector('button[type="submit"]');
                if (connectBtn) connectBtn.disabled = true;

                fetch("/api/agents", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name: name, type: type, endpoint: endpoint, model: model, api_key: key })
                })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        removeTyping(typing);
                        if (data && data.error) throw new Error(data.error);
                        if (data.agent && data.agent.connected) setActiveAgent(data.agent);
                        appendAndStoreMessage({ role: "assistant", content: "Agent **" + name + "** has been connected successfully. It can now assess, monitor, and report on your " + type.toLowerCase() + " estate.", agentName: name, ts: now() });
                        renderConversationList();
                        loadAgents();
                        window.showToast(name + " connected successfully.", "success");
                    })
                    .catch(function (error) {
                        removeTyping(typing);
                        appendAndStoreMessage({ role: "assistant", content: "**Failed to connect " + name + ".** " + (error.message || "Backend unavailable."), agentName: name, ts: now() });
                        renderConversationList();
                        window.showToast("Connection failed.", "error");
                    })
                    .finally(function () { if (connectBtn) connectBtn.disabled = false; });

                form.reset();
                closeModal();
            });
        }
    }

    // ============================================================
    // HELPERS — text formatting
    // ============================================================

    function formatTime(ts) {
        var d = new Date(ts * 1000);
        return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    }

    function copyText(text) {
        if (!text) return;
        function done() { window.showToast("Copied to clipboard.", "success"); }
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(done).catch(function () { fallbackCopy(text); });
        } else {
            fallbackCopy(text);
        }
    }

    function fallbackCopy(text) {
        try {
            var ta = document.createElement("textarea");
            ta.value = text;
            ta.style.position = "fixed";
            ta.style.opacity = "0";
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            window.showToast("Copied to clipboard.", "success");
        } catch (e) { /* ignore */ }
    }

    function escapeHtml(value) {
        var div = document.createElement("div");
        div.textContent = value == null ? "" : String(value);
        return div.innerHTML;
    }

    function inlineFormat(raw) {
        var s = escapeHtml(raw);
        s = s.replace(/`([^`]+)`/g, function (m, code) { return '<code class="msg-code">' + code + "</code>"; });
        s = s.replace(/\*\*([^*]+)\*\*/g, function (m, bold) { return "<strong>" + bold + "</strong>"; });
        s = s.replace(/(^|[^*])\*([^*\n]+)\*/g, function (m, pre, em) { return pre + "<em>" + em + "</em>"; });
        return s;
    }

    function kvFormat(line) {
        var idx = line.indexOf(":");
        if (idx > 0) {
            var key = line.slice(0, idx).trim(), rest = line.slice(idx + 1).trim();
            if (key && rest && !/[`*]/.test(key)) return '<span class="msg-key">' + inlineFormat(key) + "</span> " + inlineFormat(rest);
        }
        return inlineFormat(line);
    }

    function renderTable(rows) {
        var html = '<div class="msg-table-wrap"><table class="msg-table">';
        for (var r = 0; r < rows.length; r++) {
            var row = rows[r];
            if (r === 1 && /^[\s:|\-]+$/.test(row)) continue;
            var cells = row.replace(/^\||\|$/g, "").split("|");
            var tag = r === 0 ? "th" : "td";
            html += "<tr>";
            for (var c = 0; c < cells.length; c++) html += "<" + tag + ">" + inlineFormat(cells[c].trim()) + "</" + tag + ">";
            html += "</tr>";
        }
        return html + "</table></div>";
    }

    function formatAgentReply(text) {
        if (!text) return "";
        var raw = String(text).replace(/\r\n/g, "\n").replace(/\r/g, "\n");
        var lines = raw.split("\n");
        var html = [], listStack = [], lastIndent = -1;

        function closeList() {
            while (listStack.length) { html.push("</" + listStack.pop() + ">"); }
            listStack = []; lastIndent = -1;
        }

        for (var i = 0, n = lines.length; i < n; i++) {
            var line = lines[i].replace(/\s+$/, ""), trimmed = line.trim();
            if (!trimmed) { closeList(); continue; }

            var heading = /^(#{1,6})\s+(.*)$/.exec(trimmed);
            if (heading) {
                closeList();
                var level = Math.min(heading[1].length + 2, 6);
                html.push("<h" + level + " class='msg-h msg-h-" + level + "'>" + inlineFormat(heading[2]) + "</h" + level + ">");
                continue;
            }

            if (trimmed.indexOf("|") === 0 && trimmed.indexOf("|", 1) !== -1) {
                closeList();
                var rows = [];
                while (i < n) {
                    var t = lines[i].trim();
                    if (t.indexOf("|") === 0 && t.lastIndexOf("|") > 0) { rows.push(t); i++; }
                    else { i--; break; }
                }
                html.push(renderTable(rows));
                continue;
            }

            var bullet = /^(\s*)[-*]\s+(.*)$/.exec(line);
            if (bullet) {
                var indent = bullet[1].replace(/\t/g, "  ").length;
                if (listStack.length === 0 || indent > lastIndent) { listStack.push("ul"); html.push("<ul class='msg-list'>"); }
                else if (indent < lastIndent) { while (listStack.length > 1 && indent < lastIndent) { html.push("</" + listStack.pop() + ">"); lastIndent = listStack.length === 1 ? 0 : lastIndent - 2; } }
                lastIndent = indent;
                html.push("<li>" + kvFormat(bullet[2]) + "</li>");
                continue;
            }

            var ordered = /^(\s*)\d+\.\s+(.*)$/.exec(line);
            if (ordered) {
                var oIndent = ordered[1].replace(/\t/g, "  ").length;
                if (listStack.length === 0 || listStack[listStack.length - 1] !== "ol") { listStack.push("ol"); html.push("<ol class='msg-list'>"); }
                lastIndent = oIndent;
                html.push("<li>" + kvFormat(ordered[2]) + "</li>");
                continue;
            }

            if (/^[-*_]{3,}$/.test(trimmed)) { html.push('<hr class="msg-hr">'); continue; }

            if (trimmed.length >= 4 && trimmed === trimmed.toUpperCase() && /^[A-Z0-9][A-Z0-9\s&\-/()]{2,}$/.test(trimmed)) {
                html.push('<div class="msg-section">' + escapeHtml(trimmed) + "</div>");
                continue;
            }
            html.push("<p>" + inlineFormat(trimmed) + "</p>");
        }
        closeList();
        return html.join("");
    }

    function renderTableCard(title, data) {
        var html = '<div class="msg-card"><strong>' + escapeHtml(title) + "</strong><br><br>";
        html += '<table style="width:100%;font-size:12px;">';
        for (var k in data) {
            if (data.hasOwnProperty(k)) {
                var val = data[k];
                var display = val === null ? "\u2014" : typeof val === "object" ? JSON.stringify(val).substring(0, 120) : String(val);
                html += '<tr><td style="padding:4px 8px;color:var(--text-3);font-weight:600">' + escapeHtml(k) + '</td><td style="padding:4px 8px;font-family:monospace">' + escapeHtml(display) + "</td></tr>";
            }
        }
        return html + "</table></div>";
    }

    function renderPolicyCard(data) {
        var rules = data.security_rules || [], zones = data.zones || [];
        var html = '<div class="msg-card"><strong>Policy Configuration</strong><br><br>';
        html += "<strong>Security Rules (" + rules.length + "):</strong><ul style=\"margin:6px 0;font-size:12px\">";
        rules.forEach(function (r) { html += "<li>" + escapeHtml(r.name || "Unnamed") + ' \u2014 <span style="color:var(--text-3)">' + escapeHtml(r.action || "?") + "</span></li>"; });
        html += "</ul>";
        html += "<strong>Zones (" + zones.length + "):</strong><ul style=\"margin:6px 0;font-size:12px\">";
        zones.forEach(function (z) { html += "<li>" + escapeHtml(z.name || z) + "</li>"; });
        return html + "</ul></div>";
    }

    function buildAssistantReply(prompt) {
        var lower = prompt.toLowerCase();
        if (lower.indexOf("hello") !== -1 || lower.indexOf("hi ") !== -1 || lower.indexOf("hey") !== -1)
            return "Hello. I'm the Firewall Auditor agent, connected to your Palo Alto firewall (vmpafw01, PAN-OS 10.2.10-h9). Ask me about your security posture, inventory, compliance status, or any firewall configuration.";
        if (lower.indexOf("thanks") !== -1 || lower.indexOf("thank you") !== -1)
            return "You're welcome. I'm here whenever you need to review your security posture.";
        return null;
    }

    // ============================================================
    // SIDEBAR / INSIGHTS TOGGLES
    // ============================================================

    function setSidebarOpen(open) {
        if (sidebar) sidebar.classList.toggle("open", open);
        if (sidebarToggle) sidebarToggle.classList.toggle("is-active", open);
    }

    function setInsightsOpen(open) {
        if (insights) insights.classList.toggle("open", open);
        if (insightsToggle) insightsToggle.classList.toggle("is-active", open);
    }

    // ============================================================
    // COMPOSER
    // ============================================================

    function autoResize() {
        if (!promptInput) return;
        promptInput.style.height = "auto";
        promptInput.style.height = Math.min(promptInput.scrollHeight, 160) + "px";
    }

    // ============================================================
    // WIRING
    // ============================================================

    if (newChatBtn) newChatBtn.addEventListener("click", function () { createConversation(); promptInput.focus(); });

    if (sidebarToggle) sidebarToggle.addEventListener("click", function () {
        setSidebarOpen(!sidebar.classList.contains("open"));
    });

    if (insightsToggle) insightsToggle.addEventListener("click", function () {
        setInsightsOpen(!insights.classList.contains("open"));
    });

    if (insightsClose) insightsClose.addEventListener("click", function () { setInsightsOpen(false); });

    if (convSearch) convSearch.addEventListener("input", renderConversationList);

    if (wsAgentSelect) {
        wsAgentSelect.addEventListener("change", function () {
            var id = wsAgentSelect.value;
            for (var i = 0; i < state.agents.length; i++) {
                if (state.agents[i].id === id) {
                    setActiveAgent(state.agents[i]);
                    if (window.setGlobalAgent) window.setGlobalAgent(state.agents[i]);
                    break;
                }
            }
        });
    }

    if (sendBtn) sendBtn.addEventListener("click", function () { sendPrompt(promptInput.value); });

    if (promptInput) {
        promptInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendPrompt(promptInput.value); }
        });
        promptInput.addEventListener("input", autoResize);
    }

    if (clearBtn) {
        clearBtn.addEventListener("click", function () {
            var conv = getActiveConv();
            if (conv) {
                conv.messages = [];
                conv.title = "New chat";
                conv.updated = now();
                saveStore();
            }
            renderActiveConversation();
            renderConversationList();
            window.showToast("Conversation cleared.", "success");
        });
    }

    document.querySelectorAll(".toggle-key").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var target = document.getElementById(btn.getAttribute("data-target"));
            if (!target) return;
            target.type = target.type === "password" ? "text" : "password";
        });
    });

    document.addEventListener("agent-changed", function (e) {
        var agent = e.detail;
        if (agent) setActiveAgent(agent);
    });

    // ============================================================
    // INIT
    // ============================================================

    bindModal();
    renderPromptChips();

    if (state.conversations.length) {
        state.activeId = state.conversations[0].id;
    }
    renderConversationList();
    renderActiveConversation();

    loadAgents();
    loadSessionInsights();
    loadAssessmentInsights();
    loadRecentOutputs();
})();
