(function () {
    "use strict";

    var grid = document.getElementById("agentInsightsGrid");
    var overview = document.getElementById("insightsOverview");
    var recentBody = document.getElementById("recentBody");
    var recentCount = document.getElementById("recentCount");
    var refreshBtn = document.getElementById("refreshInsightsBtn");

    var costTotal = document.getElementById("costTotal");
    var costTokens = document.getElementById("costTokens");
    var costConvs = document.getElementById("costConvs");
    var costLatency = document.getElementById("costLatency");
    var costDrivers = document.getElementById("costDrivers");

    function fmtNumber(value) {
        if (value == null) return "-";
        return Number(value).toLocaleString("en-US");
    }

    function fmtTokens(value) {
        if (value == null) return "-";
        var n = Number(value);
        if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
        if (n >= 1000) return (n / 1000).toFixed(1) + "K";
        return String(n);
    }

    function fmtLatency(value) {
        if (value == null) return "-";
        if (value >= 1000) return (value / 1000).toFixed(2) + "s";
        return value + "ms";
    }

    function fmtCost(value) {
        if (value == null) return "-";
        var n = Number(value);
        if (n >= 1000) return "$" + (n / 1000).toFixed(2) + "K";
        if (n >= 1) return "$" + n.toFixed(2);
        return "$" + n.toFixed(4);
    }

    function fmtRelative(ts) {
        if (!ts) return "-";
        var diff = Math.floor(Date.now() / 1000 - ts);
        if (diff < 60) return "just now";
        if (diff < 3600) return Math.floor(diff / 60) + "m ago";
        if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
        return Math.floor(diff / 86400) + "d ago";
    }

    function escapeHtml(value) {
        var div = document.createElement("div");
        div.textContent = value == null ? "" : String(value);
        return div.innerHTML;
    }

    function avatarFor(name) {
        var parts = String(name || "").trim().split(/\s+/);
        var out = parts.map(function (p) { return p.charAt(0); }).join("").toUpperCase();
        return out.slice(0, 2) || "AG";
    }

    function renderOverview(totals) {
        if (!overview) return;
        var set = function (id, value) {
            var el = document.getElementById(id);
            if (el) el.textContent = value;
        };
        set("kpiAgents", "-");
        set("kpiConversations", fmtNumber(totals && totals.conversations));
        set("kpiTokens", fmtTokens(totals && totals.total_tokens));
        set("kpiLatency", fmtLatency(totals && totals.avg_latency_ms));
    }

    function renderCost(totals, agents) {
        if (!totals) return;

        if (costTotal) costTotal.textContent = fmtCost(totals.cost);
        if (costTokens) costTokens.textContent = fmtTokens(totals.total_tokens);
        if (costConvs) costConvs.textContent = fmtNumber(totals.conversations);
        if (costLatency) costLatency.textContent = fmtLatency(totals.avg_latency_ms);

        if (!costDrivers) return;

        var list = (agents || [])
            .filter(function (a) { return a.cost > 0; })
            .sort(function (a, b) { return b.cost - a.cost; })
            .slice(0, 5);

        if (!list.length) {
            costDrivers.innerHTML = '<p class="cost-driver-empty">No token usage recorded yet. Chat with an agent in the AI Workspace to start tracking.</p>';
            return;
        }

        var max = list[0].cost || 1;
        var html = "";
        list.forEach(function (a) {
            var pct = Math.max(4, Math.round((a.cost / max) * 100));
            html +=
                '<div class="cost-driver">' +
                '<div class="cost-driver-head">' +
                '<span class="cost-driver-name">' + escapeHtml(a.agent_name) + "</span>" +
                '<span class="cost-driver-value">' + fmtCost(a.cost) + " · " + fmtTokens(a.total_tokens) + " tokens</span>" +
                "</div>" +
                '<div class="cost-driver-track"><div class="cost-driver-fill" style="width:' + pct + '%"></div></div>' +
                "</div>";
        });
        costDrivers.innerHTML = html;
    }

    function renderAgentCard(agent) {
        var card = document.createElement("div");
        card.className = "agent-insight-card";

        var tokens = agent.total_tokens || 0;
        var input = agent.input_tokens || 0;
        var output = agent.output_tokens || 0;
        var cached = agent.cached_tokens || 0;
        var reasoning = agent.reasoning_tokens || 0;

        card.innerHTML =
            '<div class="agent-insight-head">' +
            '<span class="agent-avatar agent-avatar-blue">' + escapeHtml(avatarFor(agent.agent_name)) + "</span>" +
            "<div>" +
            "<h3>" + escapeHtml(agent.agent_name) + "</h3>" +
            "<p>" + escapeHtml(agent.agent_type || "Agent") + " · " + escapeHtml(agent.model || "-") + "</p>" +
            "</div>" +
            '<span class="agent-cost-badge">' + fmtCost(agent.cost) + "</span>" +
            "</div>" +

            '<div class="insight-token-grid">' +
            '<div class="insight-token insight-token-blue"><strong>' + fmtTokens(input) + "</strong><span>Input</span></div>" +
            '<div class="insight-token insight-token-green"><strong>' + fmtTokens(output) + "</strong><span>Output</span></div>" +
            '<div class="insight-token insight-token-purple"><strong>' + fmtTokens(tokens) + "</strong><span>Total</span></div>" +
            "</div>" +

            '<div class="insight-breakdown">' +
            '<span class="tag">Cached <strong>' + fmtNumber(cached) + "</strong></span>" +
            '<span class="tag">Reasoning <strong>' + fmtNumber(reasoning) + "</strong></span>" +
            '<span class="tag">Convos <strong>' + fmtNumber(agent.conversations) + "</strong></span>" +
            '<span class="tag">Turns <strong>' + fmtNumber(agent.turns) + "</strong></span>" +
            "</div>" +

            '<div class="insight-meta">' +
            '<div class="insight-meta-item"><span>Avg / turn</span><strong>' + fmtTokens(agent.avg_tokens_per_turn) + " tokens</strong></div>" +
            '<div class="insight-meta-item"><span>Avg latency</span><strong>' + fmtLatency(agent.avg_latency_ms) + "</strong></div>" +
            '<div class="insight-meta-item"><span>Last active</span><strong>' + fmtRelative(agent.last_active) + "</strong></div>" +
            "</div>";

        return card;
    }

    function renderAgents(agents) {
        if (!grid) return;
        grid.innerHTML = "";

        var list = agents || [];
        if (!list.length) {
            var empty = document.createElement("div");
            empty.className = "empty-state card";
            empty.innerHTML =
                '<div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6M10 22h4"/><path d="M12 2a7 7 0 00-4 12.7c.6.5 1 1.4 1 2.3h6c0-.9.4-1.8 1-2.3A7 7 0 0012 2z"/></svg></div>' +
                "<h3>No agent telemetry yet</h3>" +
                "<p>Chat with the Firewall Auditor in the AI Workspace to start collecting token and context insights.</p>" +
                '<a href="/workspace" class="btn btn-primary">Open AI Workspace</a>';
            grid.appendChild(empty);
            return;
        }

        list.forEach(function (agent) {
            grid.appendChild(renderAgentCard(agent));
        });
    }

    function renderRecent(conversations) {
        if (!recentBody) return;
        recentBody.innerHTML = "";

        var list = conversations || [];
        if (recentCount) recentCount.textContent = list.length + " recorded";

        if (!list.length) {
            var row = document.createElement("tr");
            row.innerHTML = '<td colspan="6" class="empty-cell">No conversations recorded yet.</td>';
            recentBody.appendChild(row);
            return;
        }

        list.forEach(function (conv) {
            var row = document.createElement("tr");
            row.innerHTML =
                "<td>" +
                '<span class="avatar-sm avatar-blue">' + escapeHtml(avatarFor(conv.agent_name)) + "</span> " +
                "<strong>" + escapeHtml(conv.agent_name) + "</strong>" +
                "</td>" +
                "<td>" + escapeHtml(conv.model || "-") + "</td>" +
                "<td>" + fmtNumber(conv.turn_count) + "</td>" +
                '<td class="text-right">' + fmtTokens(conv.last_tokens) + "</td>" +
                '<td class="text-right">' + fmtLatency(conv.last_latency_ms) + "</td>" +
                "<td>" + fmtRelative(conv.updated) + "</td>";
            recentBody.appendChild(row);
        });
    }

    function load() {
        fetch("/api/insights")
            .then(function (res) {
                return res.json();
            })
            .then(function (data) {
                if (!data) return;
                renderOverview(data.totals);
                renderAgents(data.agents);
                renderRecent(data.recent);
                renderCost(data.totals, data.agents);
            })
            .catch(function () {
                if (grid) grid.innerHTML = '<div class="empty-state card"><div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"/></svg></div><h3>Unable to load insights</h3><p>Backend unavailable.</p></div>';
            });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener("click", function () {
            load();
            window.showToast("Insights refreshed.", "success");
        });
    }

    load();
})();
