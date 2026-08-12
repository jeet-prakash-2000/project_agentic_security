(function () {
    "use strict";

    var modal = document.getElementById("addAgentModal");
    var openBtn = document.getElementById("openAddAgentBtn");
    var addTile = document.getElementById("addAgentTile");
    var closeBtn = document.getElementById("closeAddAgentBtn");
    var cancelBtn = document.getElementById("cancelAddAgentBtn");
    var form = document.getElementById("addAgentForm");
    var chatWindow = document.getElementById("chatWindow");
    var promptInput = document.getElementById("promptInput");
    var sendBtn = document.getElementById("sendBtn");
    var clearBtn = document.getElementById("clearChatBtn");
    var agentGrid = document.getElementById("agentGrid");
    var chatAgentTitle = document.getElementById("chatAgentTitle");
    var chatAgentSub = document.getElementById("chatAgentSub");

    var chatHistory = [];
    var activeAgentId = null;

    function newConversationId() {
        var existing = localStorage.getItem("ltmConversationId");
        if (existing) return existing;
        var id = "conv-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
        localStorage.setItem("ltmConversationId", id);
        return id;
    }

    var conversationId = newConversationId();

    function openModal() {
        if (modal) modal.hidden = false;
        document.body.style.overflow = "hidden";
        setTimeout(function () { var f = document.getElementById("agentName"); if (f) f.focus(); }, 120);
    }

    function closeModal() {
        if (modal) modal.hidden = true;
        document.body.style.overflow = "";
    }

    if (openBtn) openBtn.addEventListener("click", openModal);
    if (addTile) addTile.addEventListener("click", openModal);
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
            var llmEndpoint = document.getElementById("agentLlmEndpoint").value.trim();
            var model = document.getElementById("agentModel").value.trim() || "gpt-5.1";
            var key = document.getElementById("agentKey").value.trim();

            if (!name || !endpoint || !key) {
                window.showToast("Agent name, endpoint, and API key are required.", "error");
                return;
            }

            appendMessage("user", "Connect the " + name + " agent for " + type + ".", null);
            var typing = appendTyping();
            var connectBtn = form.querySelector('button[type="submit"]');
            if (connectBtn) connectBtn.disabled = true;

            fetch("/api/agents", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: name, type: type, endpoint: endpoint, llm_endpoint: llmEndpoint, model: model, api_key: key })
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    removeTyping(typing);
                    if (data && data.error) throw new Error(data.error);
                    if (data.agent && data.agent.connected) setChatAgent(data.agent);
                    appendMessage("assistant", null, "Agent <strong>" + escapeHtml(name) + "</strong> has been connected successfully. It can now assess, monitor, and report on your " + escapeHtml(type.toLowerCase()) + " estate.");
                    loadAgents();
                    window.showToast(name + " connected successfully.", "success");
                })
                .catch(function (error) {
                    removeTyping(typing);
                    appendMessage("assistant", null, "<strong>Failed to connect " + escapeHtml(name) + ".</strong><br>" + escapeHtml(error.message || "Backend unavailable."));
                    window.showToast("Connection failed.", "error");
                })
                .finally(function () { if (connectBtn) connectBtn.disabled = false; });

            form.reset();
            closeModal();
        });
    }

    function setChatAgent(agent) {
        activeAgentId = agent.id || null;
        if (chatAgentTitle) chatAgentTitle.textContent = agent.name || "Firewall Auditor";
        if (chatAgentSub) chatAgentSub.textContent = (agent.model ? agent.model + " · " : "") + "Copilot session";
    }

    function avatarFor(name) {
        var parts = String(name || "").trim().split(/\s+/);
        return parts.map(function (p) { return p.charAt(0); }).join("").toUpperCase().slice(0, 2) || "AG";
    }

    function loadAgents() {
        if (!agentGrid) return;
        fetch("/api/agents")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var agents = (data && data.agents) || [];
                agentGrid.querySelectorAll(".agent-card[data-agent-id]").forEach(function (n) { n.parentNode.removeChild(n); });

                agents.forEach(function (agent) {
                    if (agent.id === "firewall-audit-agent" && !agent.connected) return;
                    var card = document.createElement("div");
                    card.className = "agent-card";
                    card.setAttribute("data-agent-id", agent.id);
                    var statusClass = agent.connected ? "status-on" : "status-warn";
                    var statusLabel = agent.connected ? "Connected" : "Connecting";

                    card.innerHTML =
                        '<div class="agent-card-top">' +
                        '<span class="agent-avatar agent-avatar-blue">' + escapeHtml(avatarFor(agent.name)) + "</span>" +
                        '<span class="status-chip ' + statusClass + '"><span class="pulse-dot"></span> ' + statusLabel + "</span>" +
                        "</div>" +
                        "<h4>" + escapeHtml(agent.name) + "</h4>" +
                        "<p>" + escapeHtml(agent.type || "Agent") + " copilot" + (agent.model ? " · " + escapeHtml(agent.model) : "") + " connected to your AI workspace.</p>" +
                        '<div class="agent-card-foot">' +
                        '<span class="tag">' + escapeHtml(agent.type || "Agent") + "</span>" +
                        '<span class="tag">' + escapeHtml(agent.model || "gpt-5.1") + "</span>" +
                        "</div>";

                    var addTile = document.getElementById("addAgentTile");
                    if (addTile) { agentGrid.insertBefore(card, addTile); }
                    else { agentGrid.appendChild(card); }
                });

                var connected = agents.filter(function (a) { return a.connected; });
                if (connected[0]) setChatAgent(connected[0]);
            })
            .catch(function () {});
    }

    function escapeHtml(value) {
        var div = document.createElement("div");
        div.textContent = value == null ? "" : String(value);
        return div.innerHTML;
    }

    function appendMessage(role, text, html, agentName) {
        if (!chatWindow) return null;
        var msg = document.createElement("div");
        msg.className = "message " + (role === "user" ? "message-user" : "message-assistant");
        var avatar = document.createElement("span");
        avatar.className = "msg-avatar agent-avatar " + (role === "user" ? "agent-avatar-purple" : "agent-avatar-blue");
        avatar.textContent = role === "user" ? "You" : "FA";
        var bubble = document.createElement("div");
        bubble.className = "msg-bubble";

        if (role === "assistant") {
            var agent = document.createElement("span");
            agent.className = "msg-agent";
            agent.textContent = agentName || "Firewall Auditor";
            bubble.appendChild(agent);
        }

        if (html) {
            var rich = document.createElement("div");
            rich.className = "msg-rich";
            rich.innerHTML = html;
            bubble.appendChild(rich);
        } else {
            var p = document.createElement("p");
            p.textContent = text || (role === "user" ? "No prompt" : "Processing complete.");
            bubble.appendChild(p);
        }
        msg.appendChild(avatar);
        msg.appendChild(bubble);
        chatWindow.appendChild(msg);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        return msg;
    }

    function appendUsageMeta(data) {
        if (!chatWindow) return;
        var meta = document.createElement("div");
        meta.className = "msg-usage";
        var usage = data.usage || {}, parts = [];
        if (usage.total_tokens != null) parts.push(usage.total_tokens.toLocaleString("en-US") + " tokens total");
        if (usage.input_tokens != null) parts.push(usage.input_tokens.toLocaleString("en-US") + " in");
        if (usage.output_tokens != null) parts.push(usage.output_tokens.toLocaleString("en-US") + " out");
        if (usage.input_tokens_details && usage.input_tokens_details.cached_tokens) parts.push(usage.input_tokens_details.cached_tokens.toLocaleString("en-US") + " cached");
        if (usage.output_tokens_details && usage.output_tokens_details.reasoning_tokens) parts.push(usage.output_tokens_details.reasoning_tokens.toLocaleString("en-US") + " reasoning");
        if (data.latency_ms != null) parts.push(data.latency_ms >= 1000 ? (data.latency_ms / 1000).toFixed(2) + "s" : data.latency_ms + "ms");
        meta.textContent = parts.length ? parts.join(" · ") : "Token usage tracked";
        chatWindow.appendChild(meta);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function appendTyping() {
        var msg = document.createElement("div");
        msg.className = "message message-assistant";
        msg.dataset.typing = "true";
        var avatar = document.createElement("span");
        avatar.className = "msg-avatar agent-avatar agent-avatar-blue";
        avatar.textContent = "FA";
        var bubble = document.createElement("div");
        bubble.className = "msg-bubble typing-bubble";
        bubble.innerHTML = "<span></span><span></span><span></span>";
        msg.appendChild(avatar);
        msg.appendChild(bubble);
        chatWindow.appendChild(msg);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        return msg;
    }

    function removeTyping(node) { if (node && node.parentNode) node.parentNode.removeChild(node); }

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
        if (!text) return escapeHtml("");
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
        var html = '<div class="msg-card"><strong>' + escapeHtml(title) + '</strong><br><br>';
        html += '<table style="width:100%;font-size:12px;">';
        for (var k in data) {
            if (data.hasOwnProperty(k)) {
                var val = data[k];
                var display = val === null ? "\u2014" : typeof val === "object" ? JSON.stringify(val).substring(0, 120) : String(val);
                html += '<tr><td style="padding:4px 8px;color:var(--text-3);font-weight:600">' + escapeHtml(k) + '</td><td style="padding:4px 8px;font-family:monospace">' + escapeHtml(display) + '</td></tr>';
            }
        }
        return html + '</table></div>';
    }

    function renderPolicyCard(data) {
        var rules = data.security_rules || [], zones = data.zones || [];
        var html = '<div class="msg-card"><strong>Policy Configuration</strong><br><br>';
        html += '<strong>Security Rules (' + rules.length + '):</strong><ul style="margin:6px 0;font-size:12px">';
        rules.forEach(function (r) { html += '<li>' + escapeHtml(r.name || 'Unnamed') + ' \u2014 <span style="color:var(--text-3)">' + escapeHtml(r.action || '?') + '</span></li>'; });
        html += '</ul>';
        html += '<strong>Zones (' + zones.length + '):</strong><ul style="margin:6px 0;font-size:12px">';
        zones.forEach(function (z) { html += '<li>' + escapeHtml(z.name || z) + '</li>'; });
        return html + '</ul></div>';
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

        appendMessage("user", prompts[action], null);
        chatHistory.push({ role: "user", content: prompts[action] });
        var typing = appendTyping();
        sendBtn.disabled = true;

        fetch(endpoints[action])
            .then(function (r) { return r.json(); })
            .then(function (data) {
                removeTyping(typing);
                if (data && data.error) throw new Error(data.error);
                var html = action === "policy" ? renderPolicyCard(data) : renderTableCard(titles[action], data);
                appendMessage("assistant", null, html, "Firewall Data");
            })
            .catch(function () {
                removeTyping(typing);
                appendMessage("assistant", null, "Unable to fetch data from the firewall function. Check connectivity.", "Firewall Data");
            })
            .finally(function () { sendBtn.disabled = false; promptInput.focus(); });
    }

    function buildAssistantReply(prompt) {
        var lower = prompt.toLowerCase();
        if (lower.indexOf("hello") !== -1 || lower.indexOf("hi ") !== -1 || lower.indexOf("hey") !== -1)
            return "Hello. I'm the Firewall Auditor agent, connected to your Palo Alto firewall (vmpafw01, PAN-OS 10.2.10-h9). Ask me about your security posture, inventory, compliance status, or any firewall configuration.";
        if (lower.indexOf("thanks") !== -1 || lower.indexOf("thank you") !== -1)
            return "You're welcome. I'm here whenever you need to review your security posture.";
        return null;
    }

    function sendPrompt(prompt) {
        var text = (prompt || "").trim();
        if (!text) return;

        var lower = text.toLowerCase();
        var dataAction = null;
        if (lower.indexOf("inventory") !== -1 || lower.indexOf("device info") !== -1) dataAction = "inventory";
        else if (lower.indexOf("health") !== -1 || lower.indexOf("cpu") !== -1 || lower.indexOf("memory") !== -1 || lower.indexOf("disk") !== -1 || lower.indexOf("session") !== -1) dataAction = "health";
        else if (lower.indexOf("policy") !== -1 || lower.indexOf("rule") !== -1 || lower.indexOf("firewall rules") !== -1) dataAction = "policy";
        else if (lower.indexOf("ha") !== -1 || lower.indexOf("high availability") !== -1) dataAction = "ha";
        else if (lower.indexOf("service") !== -1 || lower.indexOf("security service") !== -1 || lower.indexOf("threat") !== -1 || lower.indexOf("wildfire") !== -1 || lower.indexOf("url filter") !== -1 || lower.indexOf("dns security") !== -1 || lower.indexOf("ssl decrypt") !== -1) dataAction = "services";
        else if (lower.indexOf("routing") !== -1 || lower.indexOf("route") !== -1) dataAction = "routing";
        else if (lower.indexOf("vpn") !== -1 || lower.indexOf("tunnel") !== -1) dataAction = "vpn";
        else if (lower.indexOf("logging") !== -1 || lower.indexOf("log") !== -1 || lower.indexOf("siem") !== -1 || lower.indexOf("retention") !== -1) dataAction = "logging";
        else if (lower.indexOf("admin") !== -1 || lower.indexOf("management") !== -1 || lower.indexOf("administration") !== -1 || lower.indexOf("ntp") !== -1 || lower.indexOf("snmp") !== -1) dataAction = "administration";
        else if (lower.indexOf("zone protect") !== -1 || lower.indexOf("zone protection") !== -1 || lower.indexOf("dos") !== -1 || lower.indexOf("packet") !== -1) dataAction = "zone_protection";
        else if (lower.indexOf("backup") !== -1 || lower.indexOf("recovery") !== -1) dataAction = "backup";

        if (dataAction) { runDataAction(dataAction); return; }

        appendMessage("user", text, null);
        chatHistory.push({ role: "user", content: text });
        promptInput.value = "";
        autoResize();

        var typing = appendTyping();
        sendBtn.disabled = true;
        fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text, conversation_id: conversationId, agent_id: activeAgentId })
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                removeTyping(typing);
                if (data && data.error) throw new Error(data.error);
                if (data && data.conversation_id) { conversationId = data.conversation_id; localStorage.setItem("ltmConversationId", data.conversation_id); }
                var reply = (data && data.reply) || buildAssistantReply(text);
                appendMessage("assistant", null, formatAgentReply(reply), "Firewall Auditor");
                if (data && data.usage) appendUsageMeta(data);
                chatHistory.push({ role: "assistant", content: reply });
            })
            .catch(function (error) {
                removeTyping(typing);
                var fallback = buildAssistantReply(text);
                appendMessage("assistant", null, formatAgentReply(fallback), "Firewall Auditor");
                chatHistory.push({ role: "assistant", content: fallback });
                if (error && error.message && error.message.indexOf("No connected agent") === -1) window.showToast("Agent unavailable — showing preview response.", "error");
            })
            .finally(function () { sendBtn.disabled = false; promptInput.focus(); });
    }

    if (sendBtn) sendBtn.addEventListener("click", function () { sendPrompt(promptInput.value); });

    if (promptInput) {
        promptInput.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendPrompt(promptInput.value); } });
        promptInput.addEventListener("input", autoResize);
    }

    function autoResize() {
        if (!promptInput) return;
        promptInput.style.height = "auto";
        promptInput.style.height = Math.min(promptInput.scrollHeight, 140) + "px";
    }

    document.querySelectorAll("[data-action]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var act = btn.getAttribute("data-action");
            var prompts = { assess: "Run a full compliance assessment of the firewall estate.", summary: "Generate an executive summary of the security posture.", excel: "Generate the assessment workbook report." };
            sendPrompt(prompts[act] || act);
        });
    });

    if (clearBtn) {
        clearBtn.addEventListener("click", function () {
            if (!chatWindow) return;
            chatHistory = [];
            chatWindow.innerHTML = "";
            var welcome = document.createElement("div");
            welcome.className = "message message-assistant";
            welcome.innerHTML = '<span class="msg-avatar agent-avatar agent-avatar-blue">FA</span>' +
                '<div class="msg-bubble">' +
                '<span class="msg-agent">Firewall Auditor</span>' +
                "<p>Hello. I'm your firewall security and compliance auditor for vmpafw01 (PAN-OS 10.2.10-h9). I can run assessments, review policies/VPNs/logging/HA, generate executive summaries, and produce downloadable reports. What would you like to do?</p>" +
                "</div>";
            chatWindow.appendChild(welcome);
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

    loadAgents();
})();
