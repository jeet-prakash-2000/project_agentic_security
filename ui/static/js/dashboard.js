(function () {
    "use strict";

    var RING_LENGTH = 314.159;

    var sourceBadge = document.getElementById("dataSourceBadge");
    var refreshBtn = document.getElementById("refreshBtn");
    var ringFg = document.getElementById("ringFg");
    var ringPercent = document.getElementById("ringPercent");
    var agentHealthGrid = document.getElementById("agentHealthGrid");
    var kpiGrid = document.getElementById("kpiRow");
    var kpiGridAlt = document.getElementById("kpiRowAlt");

    function animateCount(el, target) {
        var start = null;
        var duration = 900;
        function step(timestamp) {
            if (!start) start = timestamp;
            var progress = Math.min((timestamp - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(target * eased);
            if (progress < 1) window.requestAnimationFrame(step);
        }
        window.requestAnimationFrame(step);
    }

    function setSource(source) {
        if (!sourceBadge) return;
        var label = source === "live" ? "Live Data" : "Sample Data";
        sourceBadge.innerHTML = '<span class="pulse-dot"></span> ' + label;
        sourceBadge.style.borderColor = source === "live" ? "rgba(34, 197, 94, 0.5)" : "rgba(245, 158, 11, 0.5)";
        sourceBadge.style.color = source === "live" ? "#059669" : "#B45309";
    }

    function updateRing(compliant, total) {
        var pct = total > 0 ? Math.round((compliant / total) * 100) : 0;
        if (ringPercent) ringPercent.textContent = pct + "%";
        if (ringFg) {
            ringFg.style.transition = "stroke-dashoffset 1.2s ease";
            ringFg.style.strokeDashoffset = RING_LENGTH - (RING_LENGTH * pct) / 100;
        }
    }

    function setKpi(id, value, animate) {
        var el = document.getElementById(id);
        if (!el) return;
        if (animate && typeof value === "number") { animateCount(el, value); }
        else { el.textContent = value == null ? "-" : String(value); }
    }

    function fmtToken(value) { if (value == null) return "-"; var n=Number(value); return n>=1e6?(n/1e6).toFixed(1)+"M":n>=1e3?(n/1e3).toFixed(1)+"K":String(n); }
    function fmtCost(value) { if (value == null) return "-"; var n=Number(value); return n>=1000?"$"+(n/1000).toFixed(2)+"K":n>=1?"$"+n.toFixed(2):"$"+n.toFixed(4); }
    function fmtRelative(ts) { if (!ts) return "-"; var d=Math.floor(Date.now()/1000-ts); return d<60?"just now":d<3600?Math.floor(d/60)+"m ago":d<86400?Math.floor(d/3600)+"h ago":Math.floor(d/86400)+"d ago"; }
    function fmtPercent(value) { return value==null?"-":value+"%"; }
    function escapeHtml(value) { var d=document.createElement("div"); d.textContent=value==null?"":String(value); return d.innerHTML; }
    function avatarFor(name) { var p=String(name||"").trim().split(/\s+/); return p.map(function(x){return x.charAt(0)}).join("").toUpperCase().slice(0,2)||"AG"; }
    function statusClass(status) { var k=String(status||"").toLowerCase(); if(k==="healthy")return"status-on"; if(k==="faulted")return"status-fail"; return"status-warn"; }
    function healthColor(s) { if(s==null)return"#8A94A3"; if(s>=70)return"#22c55e"; if(s>=40)return"#f59e0b"; return"#ef4444"; }
    function fmtNumber(value) { if(value==null)return"-"; return Number(value).toLocaleString("en-US"); }
    function fmtLatency(value) { if(value==null)return"-"; return value>=1000?(value/1000).toFixed(2)+"s":value+"ms"; }

    function renderAgentHealth(agents) {
        if (!agentHealthGrid) return;
        var list = agents || [];
        agentHealthGrid.innerHTML = "";
        if (!list.length) {
            agentHealthGrid.innerHTML = '<p class="agent-health-empty">No agents connected. Add one in the AI Workspace.</p>';
            return;
        }
        list.forEach(function (agent) {
            var card = document.createElement("div");
            card.className = "agent-health-card";
            var h = agent.health_score == null ? "-" : agent.health_score + "%";
            var sr = agent.success_rate == null ? "-" : agent.success_rate + "%";
            card.innerHTML =
                '<div class="agent-health-head">' +
                '<span class="agent-avatar agent-avatar-blue">' + escapeHtml(avatarFor(agent.name)) + "</span>" +
                "<div><h4>" + escapeHtml(agent.name) + "</h4><p>" + escapeHtml(agent.type||"Agent") + " &middot; " + escapeHtml(agent.model||"-") + "</p></div>" +
                '<span class="status-chip ' + statusClass(agent.status) + '"><span class="pulse-dot"></span> ' + escapeHtml(agent.status) + "</span>" +
                "</div>" +
                '<div class="agent-health-stats">' +
                '<div class="agent-health-stat"><span>Health</span><strong style="color:' + healthColor(agent.health_score) + '">' + h + "</strong></div>" +
                '<div class="agent-health-stat"><span>Tools</span><strong>' + fmtNumber(agent.tools) + "</strong></div>" +
                '<div class="agent-health-stat"><span>Success Rate</span><strong>' + sr + "</strong></div>" +
                '<div class="agent-health-stat"><span>Last Assessment</span><strong>' + fmtRelative(agent.last_assessment_ts) + "</strong></div>" +
                '<div class="agent-health-stat"><span>Latency</span><strong>' + fmtLatency(agent.avg_latency_ms) + "</strong></div>" +
                '<div class="agent-health-stat"><span>Est. Cost</span><strong>' + fmtCost(agent.cost) + "</strong></div>" +
                "</div>";
            agentHealthGrid.appendChild(card);
        });
    }

    function applyNetsecData(data) {
        var c = data.compliance || {};
        var f = data.findings || {};
        var cost = data.cost || {};

        var values = document.querySelectorAll(".kpi-grid .kpi-value[data-count]");
        var keys = ["total_controls", "compliant", "non_compliant", "not_assessed"];
        var targets = keys.map(function (k) {
            var v = c[k]; return v == null ? "-" : Number(v);
        });
        values.forEach(function (el, i) {
            if (typeof targets[i] === "number") animateCount(el, targets[i]);
            else el.textContent = "-";
        });
        updateRing(Number(c.compliant)||0, Number(c.total_controls)||0);
        setSource(c.source);

        setKpi("kpiComplianceScore", c.compliance_score==null?"-":c.compliance_score+"%", false);
        setKpi("kpiCritical", f.critical==null?"-":Number(f.critical), true);
        setKpi("kpiAssessments", data.assessments_run==null?"-":Number(data.assessments_run), true);
        setKpi("kpiTokens", fmtToken(cost.total_tokens), false);
        setKpi("kpiCost", fmtCost(cost.total_cost), false);
        setKpi("kpiAgentHealth", fmtPercent(data.avg_health), false);
    }

    function load() {
        fetch("/api/dashboard")
            .then(function (r) { return r.json(); })
            .then(function (data) { applyNetsecData(data); })
            .catch(function () { window.showToast("Dashboard data unavailable.", "error"); });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener("click", function () {
            window.showToast("Refreshing dashboard data...");
            load();
        });
    }

    load();
})();
