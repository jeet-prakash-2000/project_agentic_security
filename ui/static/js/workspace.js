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

    var insightMessages = document.getElementById("insightMessages");
    var insightTokens = document.getElementById("insightTokens");
    var insightCost = document.getElementById("insightCost");

    // ============================================================
    // CONSTANTS — actions, prompts, tool metadata
    // ============================================================

    var ACTIONS = {
        assess: { label: "Compliance Assessment", tool: "assess", prompt: "Run a full compliance assessment of the firewall estate." }
    };

    var COMPOSER_CHIPS = ["assess"];

    var SUGGESTIONS = [
        { label: "Run Compliance Assessment", action: "assess" }
    ];

    var ASSESSMENT_SECTIONS = [
        { id: "inventory", label: "Inventory", endpoint: "/api/firewall/inventory", domains: ["Software & Platform Currency", "Hardware & Capacity"] },
        { id: "health", label: "Health Status", endpoint: "/api/firewall/health", domains: ["Hardware & Capacity"] },
        { id: "ha", label: "HA Configuration", endpoint: "/api/firewall/ha", domains: ["High Availability"] },
        { id: "policy", label: "Security Policy", endpoint: "/api/firewall/policy", domains: ["Security Policy & Rule Base"] },
        { id: "segmentation", label: "Network Segmentation", endpoint: "/api/firewall/policy", domains: ["Network Segmentation & Zones"] },
        { id: "services", label: "Security Services", endpoint: "/api/firewall/services", domains: ["Threat Prevention", "SSL/TLS Decryption"] },
        { id: "routing", label: "Routing", endpoint: "/api/firewall/routing", domains: ["NAT & Routing"] },
        { id: "vpn", label: "VPN", endpoint: "/api/firewall/vpn", domains: ["VPN"] },
        { id: "logging", label: "Logging", endpoint: "/api/firewall/logging", domains: ["Logging & Monitoring"] },
        { id: "administration", label: "Administration", endpoint: "/api/firewall/administration", domains: ["Admin Access & Hardening"] },
        { id: "zone_protection", label: "Zone Protection", endpoint: "/api/firewall/zone-protection", domains: ["Zone Protection & DoS"] },
        { id: "backup", label: "Backup", endpoint: "/api/firewall/backup", domains: ["Backup & Change Management"] },
        { id: "report", label: "Report Generation", action: "report" },
        { id: "summary", label: "Executive Summary", action: "summary" }
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
            link: { label: "Download workbook", href: "/download-workbook" },
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
        conversations: [],
        messages: [],
        activeId: null,
        activeAgentId: null,
        activeAgent: null,
        agents: []
    };

    // ============================================================
    // STORAGE
    // ============================================================

    function now() {
        return Math.floor(Date.now() / 1000);
    }

    function newConvId() {
        return "conv-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
    }

    // ============================================================
    // CONVERSATION MANAGEMENT
    // ============================================================

    function createConversation() {
        state.activeId = null;
        state.messages = [];
        renderConversationList();
        renderActiveConversation();
        updateSessionMetrics();
        return null;
    }

    function ensureActiveId() {
        if (!state.activeId) {
            state.activeId = newConvId();
            state.conversations.unshift({ id: state.activeId, title: "New chat", created: now(), updated: now(), message_count: 0 });
            renderConversationList();
        }
        return state.activeId;
    }

    function setActive(id) {
        state.activeId = id;
        state.messages = [];
        renderConversationList();
        renderActiveConversation();
        updateSessionMetrics();
        if (id) {
            loadMessages(id);
            loadConversationInsights();
        }
    }

    function loadMessages(id) {
        fetch("/api/conversations/" + encodeURIComponent(id) + "/messages")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (state.activeId !== id) return;
                state.messages = (data && data.messages) || [];
                renderActiveConversation();
                updateSessionMetrics();
            })
            .catch(function () {});
    }

    function loadConversations() {
        return fetch("/api/conversations")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                state.conversations = (data && data.conversations) || [];
                renderConversationList();
                return state.conversations;
            })
            .catch(function () { return []; });
    }

    function persistMessages(messages) {
        if (!state.activeId) return;
        var payload = (messages || []).map(function (m) {
            return {
                role: m.role,
                content: m.content || "",
                ts: m.ts,
                html: m.html,
                cardTitle: m.cardTitle,
                tool: m.tool,
                usage: m.usage,
                agentName: m.agentName
            };
        });
        fetch("/api/conversations/" + encodeURIComponent(state.activeId) + "/messages", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ messages: payload })
        }).catch(function () {});
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
        if (!state.messages.length) {
            renderEmptyState();
            updateSessionMetrics();
            return;
        }
        state.messages.forEach(renderMessage);
        updateSessionMetrics();
    }

    function appendMessage(msg) {
        state.messages.push(msg);
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
        if (action === "assess") {
            showMcqCard();
            return;
        }
        var a = ACTIONS[action];
        if (!a) return;
        sendPrompt(a.prompt, { tool: a.tool });
    }

    // ============================================================
    // COMPLIANCE ASSESSMENT MCQ
    // ============================================================

    var assessmentCache = null;

    function loadAssessmentData() {
        if (assessmentCache) return Promise.resolve(assessmentCache);
        return fetch("/api/findings")
            .then(function (r) { return r.json(); })
            .then(function (data) { assessmentCache = data; return data; })
            .catch(function () { return null; });
    }

    function showMcqCard() {
        ensureActiveId();
        appendMessage({ role: "user", content: "Compliance Assessment", ts: now() });
        renderConversationList();

        var options = ASSESSMENT_SECTIONS.map(function (s) {
            return '<button class="mcq-option" type="button" data-section="' + s.id + '">' +
                '<span class="mcq-option-label">' + escapeHtml(s.label) + '</span>' +
                '<span class="mcq-option-arrow">' + ARROW_ICON + '</span>' +
                '</button>';
        }).join("");

        var html = '<div class="ws-mcq-card">' +
            '<div class="ws-mcq-head"><strong>Compliance Assessment</strong><span>Select a section to review</span></div>' +
            '<div class="ws-mcq-options">' + options + '</div>' +
            '</div>';

        appendMessage({ role: "assistant", content: "", html: html, cardTitle: "Compliance Assessment", agentName: "Firewall Auditor", ts: now() });
        renderConversationList();
    }

    function showSection(sectionId) {
        var section = null;
        for (var i = 0; i < ASSESSMENT_SECTIONS.length; i++) {
            if (ASSESSMENT_SECTIONS[i].id === sectionId) { section = ASSESSMENT_SECTIONS[i]; break; }
        }
        if (!section) return;

        if (section.action === "report") { generateReportFromMcq(); return; }
        if (section.action === "summary") { generateSummaryFromMcq(); return; }
        loadSectionData(section);
    }

    function generateReportFromMcq() {
        ensureActiveId();
        appendMessage({ role: "user", content: "Report Generation", ts: now() });
        renderConversationList();
        var typing = appendTyping();
        sendBtn.disabled = true;
        fetch("/api/excel")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                removeTyping(typing);
                if (data && data.error) throw new Error(data.error);
                appendMessage({ role: "assistant", content: "Assessment workbook generated and stored in Reports.", tool: "excel", ts: now() });
                loadConversations();
            })
            .catch(function () {
                removeTyping(typing);
                appendMessage({ role: "assistant", content: "Report generation failed.", ts: now() });
            })
            .finally(function () { sendBtn.disabled = false; promptInput.focus(); });
    }

    function generateSummaryFromMcq() {
        ensureActiveId();
        appendMessage({ role: "user", content: "Executive Summary", ts: now() });
        renderConversationList();
        var typing = appendTyping();
        sendBtn.disabled = true;
        fetch("/executive-summary")
            .then(function (r) { return r.ok; })
            .then(function (ok) {
                removeTyping(typing);
                if (!ok) throw new Error("failed");
                appendMessage({ role: "assistant", content: "Executive summary generated and stored in Reports.", tool: "summary", ts: now() });
                loadConversations();
            })
            .catch(function () {
                removeTyping(typing);
                appendMessage({ role: "assistant", content: "Executive summary generation failed.", ts: now() });
            })
            .finally(function () { sendBtn.disabled = false; promptInput.focus(); });
    }

    function loadSectionData(section) {
        ensureActiveId();
        appendMessage({ role: "user", content: section.label, ts: now() });
        renderConversationList();
        var typing = appendTyping("Firewall Auditor");
        sendBtn.disabled = true;

        var dataPromise = section.endpoint
            ? fetch(section.endpoint).then(function (r) { return r.json(); }).catch(function () { return null; })
            : Promise.resolve(null);
        var assessPromise = loadAssessmentData();

        Promise.all([dataPromise, assessPromise]).then(function (results) {
            removeTyping(typing);
            var sectionData = results[0];
            var assess = results[1];
            var html = buildSectionHtml(section, sectionData, assess);
            appendMessage({ role: "assistant", content: "", html: html, cardTitle: section.label, agentName: "Firewall Auditor", ts: now() });
            renderConversationList();
        }).finally(function () { sendBtn.disabled = false; promptInput.focus(); });
    }

    function controlDomain(cid) {
        if (typeof FINDING_ENRICHMENT !== "undefined" && FINDING_ENRICHMENT[cid]) {
            return FINDING_ENRICHMENT[cid].domain;
        }
        return null;
    }

    function computeSectionCompliance(assess, domains) {
        var total = 0, compliant = 0;
        var controls = (assess && assess.assessment) || [];
        controls.forEach(function (c) {
            var cid = (c.control || "").toUpperCase();
            var domain = controlDomain(cid);
            if (domain && domains.indexOf(domain) !== -1) {
                total++;
                if ((c.status || "").toUpperCase() === "COMPLIANT") compliant++;
            }
        });
        var pct = total ? Math.round(compliant / total * 100) : 0;
        return { total: total, compliant: compliant, pct: pct };
    }

    function collectRecommendations(assess, domains) {
        var recs = [];
        var seen = {};
        var findings = (assess && assess.findings) || [];
        findings.forEach(function (f) {
            var cid = (f.control || "").toUpperCase();
            var domain = controlDomain(cid);
            if (domain && domains.indexOf(domain) !== -1) {
                var r = f.remediation || (typeof FINDING_ENRICHMENT !== "undefined" && FINDING_ENRICHMENT[cid] ? FINDING_ENRICHMENT[cid].remediation : "") || "";
                if (r && !seen[r]) { seen[r] = true; recs.push(r); }
            }
        });
        return recs.slice(0, 5);
    }

    function buildSectionHtml(section, sectionData, assess) {
        var compliance = computeSectionCompliance(assess, section.domains);
        var recs = collectRecommendations(assess, section.domains);

        var tone = compliance.pct >= 80 ? "good" : (compliance.pct >= 50 ? "warn" : "bad");

        var html = '<div class="ws-section-card">';
        html += '<div class="ws-section-title">' + escapeHtml(section.label) + '</div>';
        html += '<div class="ws-section-compliance">' +
            '<span class="ws-comp-badge ' + tone + '">' + compliance.compliant + ' / ' + compliance.total + ' compliant</span>' +
            '<span class="ws-comp-pct">' + compliance.pct + '%</span>' +
            '</div>';

        if (recs.length) {
            html += '<div class="ws-section-recs"><strong>Recommendations</strong><ul>';
            recs.forEach(function (r) { html += '<li>' + escapeHtml(r) + '</li>'; });
            html += '</ul></div>';
        } else if (compliance.total) {
            html += '<div class="ws-section-recs"><strong>All compliant</strong> \u2014 no recommendations needed.</div>';
        }

        if (sectionData && typeof sectionData === "object") {
            html += '<div class="ws-section-data"><strong>Section Data</strong><div class="ws-section-kv">';
            for (var k in sectionData) {
                if (sectionData.hasOwnProperty(k)) {
                    var v = sectionData[k];
                    var display = v === null ? "\u2014" : typeof v === "object" ? JSON.stringify(v).substring(0, 140) : String(v);
                    html += '<div class="ws-kv-row"><span>' + escapeHtml(k) + '</span><span>' + escapeHtml(display) + '</span></div>';
                }
            }
            html += '</div></div>';
        }
        html += '</div>';
        return html;
    }

    // ============================================================
    // CHAT / SEND
    // ============================================================

    function sendPrompt(prompt, opts) {
        opts = opts || {};
        var text = (prompt || "").trim();
        if (!text) return;

        ensureActiveId();
        appendMessage({ role: "user", content: text, ts: now() });
        renderConversationList();
        promptInput.value = "";
        autoResize();

        var typing = appendTyping();
        sendBtn.disabled = true;

        var convId = state.activeId;
        fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text, conversation_id: convId, agent_id: state.activeAgentId, tool: opts.tool || null })
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                removeTyping(typing);
                if (data && data.error) throw new Error(data.error);
                if (data.conversation_id) state.activeId = data.conversation_id;
                var reply = (data && data.reply) || buildAssistantReply(text);
                appendMessage({ role: "assistant", content: reply, tool: opts.tool || null, usage: (data && data.usage) || null, agentName: (data && data.agent && data.agent.name) || null, ts: now() });
                loadConversations();
                loadConversationInsights();
            })
            .catch(function (error) {
                removeTyping(typing);
                var fallback = buildAssistantReply(text);
                appendMessage({ role: "assistant", content: fallback, tool: opts.tool || null, ts: now() });
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

    function updateSessionMetrics() {
        if (!insightMessages) return;
        insightMessages.textContent = String(state.messages.length);
    }

    function loadConversationInsights() {
        if (!state.activeId) {
            if (insightTokens) insightTokens.textContent = "—";
            if (insightCost) insightCost.textContent = "—";
            updateSessionMetrics();
            return;
        }
        fetch("/api/insights/conversation/" + encodeURIComponent(state.activeId))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var c = (data && data.conversation) || null;
                if (insightTokens) insightTokens.textContent = c ? fmtNum(c.total_tokens || 0) : "—";
                if (insightCost) insightCost.textContent = c ? "$" + Number(c.cost || 0).toFixed(2) : "—";
                updateSessionMetrics();
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

                ensureActiveId();
                var userMsg = { role: "user", content: "Connect the " + name + " agent for " + type + ".", ts: now() };
                appendMessage(userMsg);
                renderConversationList();

                var typing = appendTyping();
                var connectBtn = form.querySelector('button[type="submit"]');
                if (connectBtn) connectBtn.disabled = true;

                var finish = function (asstMsg) {
                    persistMessages([userMsg, asstMsg]);
                    loadConversations();
                };

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
                        var asstMsg = { role: "assistant", content: "Agent **" + name + "** has been connected successfully. It can now assess, monitor, and report on your " + type.toLowerCase() + " estate.", agentName: name, ts: now() };
                        appendMessage(asstMsg);
                        renderConversationList();
                        loadAgents();
                        finish(asstMsg);
                        window.showToast(name + " connected successfully.", "success");
                    })
                    .catch(function (error) {
                        removeTyping(typing);
                        var asstMsg = { role: "assistant", content: "**Failed to connect " + name + ".** " + (error.message || "Backend unavailable."), agentName: name, ts: now() };
                        appendMessage(asstMsg);
                        renderConversationList();
                        finish(asstMsg);
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

    if (chatWindow) {
        chatWindow.addEventListener("click", function (e) {
            var option = e.target.closest(".mcq-option");
            if (!option) return;
            var sectionId = option.getAttribute("data-section");
            if (sectionId) showSection(sectionId);
        });
    }

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
            if (!state.activeId) {
                window.showToast("Nothing to clear.", "success");
                return;
            }
            var id = state.activeId;
            fetch("/api/conversations/" + encodeURIComponent(id) + "/clear", { method: "POST" })
                .then(function (r) { return r.json(); })
                .then(function () {
                    state.messages = [];
                    renderActiveConversation();
                    loadConversations();
                    loadConversationInsights();
                    window.showToast("Conversation cleared.", "success");
                })
                .catch(function () {
                    window.showToast("Failed to clear conversation.", "error");
                });
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

    renderConversationList();
    renderActiveConversation();

    loadAgents();
    loadConversations().then(function () {
        loadConversationInsights();
    });
})();
