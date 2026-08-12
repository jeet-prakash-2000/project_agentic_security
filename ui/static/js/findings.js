(function () {
    "use strict";

    var container = document.getElementById("findingsRoot");
    var summaryBin = document.getElementById("summaryChips");
    var searchInput = document.getElementById("findingsSearch");

    var activeFilters = { severity: "all", status: "all", search: "" };
    var currentFindings = [];
    var currentData = null;

    function escapeHtml(v) {
        var d = document.createElement("div");
        d.textContent = v == null ? "" : String(v);
        return d.innerHTML;
    }

    function enrich(f) {
        var cid = (f.control || "").toUpperCase();
        var meta = (typeof FINDING_ENRICHMENT !== "undefined" && FINDING_ENRICHMENT[cid]) ? FINDING_ENRICHMENT[cid] : {
            domain: "General",
            risk_score: f.risk === "CRITICAL" ? 95 : f.risk === "HIGH" ? 72 : f.risk === "MEDIUM" ? 45 : 20,
            gap: f.finding || "",
            impact: "See finding details for business impact analysis.",
            evidence: ["Assessment data collected from live firewall connector"]
        };
        f._domain = meta.domain;
        f._risk_score = meta.risk_score;
        f._check = meta.check || f.finding || "";
        f._gap = meta.gap;
        f._impact = meta.impact;
        f._evidence = meta.evidence || [];
        f._affected_rules = meta.affected_rules || [];
        f._remediation = meta.remediation || f.remediation || "";
        f._verification = meta.method || "";
        f._detected = (currentData && currentData._collected_at) ? currentData._collected_at.slice(0, 10) : new Date().toISOString().slice(0, 10);
        f._firewall = (currentData && currentData.inventory && currentData.inventory.hostname) || "vmpafw01";
        return f;
    }

    function severitySort(a, b) {
        var order = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
        var va = order[a.risk] != null ? order[a.risk] : 9;
        var vb = order[b.risk] != null ? order[b.risk] : 9;
        return va - vb || (a.control || "").localeCompare(b.control || "");
    }

    function applyFilters() {
        var filtered = currentFindings.filter(function (f) {
            if (activeFilters.severity !== "all" && (f.risk || "").toLowerCase() !== activeFilters.severity) return false;
            if (activeFilters.status !== "all") {
                var s = (f.status || "").toLowerCase();
                if (activeFilters.status === "non-compliant" && s !== "non_compliant") return false;
                if (activeFilters.status === "compliant" && s !== "compliant") return false;
            }
            if (activeFilters.search) {
                var q = activeFilters.search.toLowerCase();
                var hay = ((f.control || "") + " " + (f.finding || "") + " " + (f._domain || "") + " " + (f._gap || "")).toLowerCase();
                if (hay.indexOf(q) === -1) return false;
            }
            return true;
        });
        renderCards(filtered);
        updateSummary(filtered);
    }

    function updateSummary(findings) {
        if (!summaryBin) return;
        var crit = 0, hi = 0, med = 0, lo = 0;
        findings.forEach(function (f) { var r = (f.risk || "").toLowerCase(); if (r === "critical") crit++; else if (r === "high") hi++; else if (r === "medium") med++; else lo++; });
        var items = [
            { id: "summaryOpenCount", el: null, val: findings.length },
            { id: "summaryCritCount", el: null, val: crit },
            { id: "summaryHiCount", el: null, val: hi },
            { id: "summaryMedCount", el: null, val: med },
            { id: "summaryLoCount", el: null, val: lo }
        ];
        items.forEach(function (it) { it.el = document.getElementById(it.id); if (it.el) it.el.textContent = it.val; });
    }

    function formatVal(v) {
        if (typeof v === "boolean") return v ? "Enabled" : "Disabled";
        if (v === null || v === undefined) return "\u2014";
        return String(v);
    }

    function formatExpected(v, op) {
        if (op === "not_empty") return "Not Empty";
        if (op === "supported_version") {
            if (Array.isArray(v)) return "in (" + v.join(", ") + ")";
            return "in (" + String(v) + ")";
        }
        return String(v != null ? v : "\u2014");
    }

    var OPERATOR_SYMBOLS = {
        "==": "=",
        "!=": "\u2260",
        "<": "<",
        "<=": "\u2264",
        ">": ">",
        ">=": "\u2265",
        "supported_version": "\u2208",
        "not_empty": "\u2260"
    };

    function renderCards(findings) {
        if (!container) return;
        if (!findings.length) {
            container.innerHTML = '<div class="empty-state card"><h3>No findings match filters</h3></div>';
            return;
        }

        var html = "";
        findings.forEach(function (f) {
            var sev = (f.risk || "low").toLowerCase();
            var cid = escapeHtml(f.control || "\u2014");
            var title = escapeHtml(f._check || f.finding || "Untitled");
            var domain = escapeHtml(f._domain || "General");
            var score = f._risk_score || 50;
            var detected = escapeHtml(f._detected || "\u2014");
            var fw = escapeHtml(f._firewall || "\u2014");
            var statusKey = (f.status || "").toUpperCase();
            var statusClass = statusKey === "COMPLIANT" ? "compliant" : "non-compliant";

            var metricName = escapeHtml(f.metric || "\u2014");
            var observedVal = escapeHtml(formatVal(f.observed));
            var expectedVal = escapeHtml(formatExpected(f.expected, f.operator));
            var opSym = OPERATOR_SYMBOLS[f.operator] || "?";
            var opLabel = escapeHtml(f.operator || "");

            var gap = escapeHtml(f._gap || "");
            var impact = escapeHtml(f._impact || "");
            var remediation = escapeHtml(f._remediation || "");

            var rules = f._affected_rules || [];

            html +=
                '<div class="finding-card">' +
                '<div class="finding-card-head">' +
                '<div class="finding-card-top">' +
                '<span class="finding-card-id">' + cid + '</span>' +
                '<span class="sev-badge sev-' + sev + '">' + escapeHtml(f.risk || "LOW") + '</span>' +
                '</div>' +
                '<div class="finding-card-title">' + title + '</div>' +
                '<div class="finding-card-meta">' +
                '<div class="meta-item"><span class="meta-label">Status</span><span class="meta-value ' + statusClass + '">' + statusKey + '</span></div>' +
                '<div class="meta-item"><span class="meta-label">Domain</span><span class="meta-value">' + domain + '</span></div>' +
                '<div class="meta-item"><span class="meta-label">Risk Score</span><span class="meta-value mono">' + score + '/100</span></div>' +
                '<div class="meta-item"><span class="meta-label">Detected</span><span class="meta-value mono">' + detected + '</span></div>' +
                '<div class="meta-item"><span class="meta-label">Firewall</span><span class="meta-value mono">' + fw + '</span></div>' +
                '</div>' +
                '</div>' +
                '<div class="cmp-check">' +
                '<div class="cmp-metric"><span class="cmp-label">Metric</span><span class="cmp-name">' + metricName + '</span></div>' +
                '<div class="cmp-values">' +
                '<div class="cmp-block cmp-observed"><span class="cmp-block-label">Observed</span><span class="cmp-block-val">' + observedVal + '</span></div>' +
                '<div class="cmp-op"><span class="cmp-op-sym">' + opSym + '</span><span class="cmp-op-label">' + opLabel + '</span></div>' +
                '<div class="cmp-block cmp-expected"><span class="cmp-block-label">Expected</span><span class="cmp-block-val">' + expectedVal + '</span></div>' +
                '</div>' +
                '</div>' +
                (gap ? '<div class="finding-gap"><div class="finding-gap-row"><span class="finding-gap-label">Gap</span><p>' + gap + '</p></div></div>' : '') +
                (impact ? '<div class="finding-impact"><div class="finding-impact-row"><span class="finding-impact-label">Impact</span><p>' + impact + '</p></div></div>' : '') +
                (remediation ? '<div class="finding-rem"><span class="cmp-block-label">Remediation</span><p>' + remediation + '</p></div>' : '');
            if (rules.length) {
                html += '<div class="finding-detail-section"><h5>Affected Rules</h5><div class="affected-list">';
                rules.forEach(function (r) { html += '<span class="affected-tag">' + escapeHtml(r) + '</span>'; });
                html += '</div></div>';
            }
            html += '</div>';
        });
        container.innerHTML = html;
    }

    if (container) {
        container.addEventListener("click", function (e) {
            var card = e.target.closest(".finding-card");
            if (!card) return;
            var wasActive = card.classList.contains("is-active");
            container.querySelectorAll(".finding-card.is-active").forEach(function (c) { c.classList.remove("is-active"); });
            if (!wasActive) card.classList.add("is-active");
        });
    }

    function setupFilterChips() {
        var sevContainer = document.getElementById("severityChips");
        var statusContainer = document.getElementById("statusChips");

        if (sevContainer) {
            sevContainer.addEventListener("click", function (e) {
                var chip = e.target.closest(".chip");
                if (!chip) return;
                sevContainer.querySelectorAll(".chip").forEach(function (c) { c.classList.remove("is-active"); });
                chip.classList.add("is-active");
                activeFilters.severity = chip.getAttribute("data-value") || "all";
                applyFilters();
            });
        }

        if (statusContainer) {
            statusContainer.addEventListener("click", function (e) {
                var chip = e.target.closest(".chip");
                if (!chip) return;
                statusContainer.querySelectorAll(".chip").forEach(function (c) { c.classList.remove("is-active"); });
                chip.classList.add("is-active");
                activeFilters.status = chip.getAttribute("data-value") || "all";
                applyFilters();
            });
        }
    }

    if (searchInput) {
        var debounceTimer;
        searchInput.addEventListener("input", function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function () {
                activeFilters.search = searchInput.value.trim();
                applyFilters();
            }, 250);
        });
    }

    function renderNetsecFindings(data) {
        if (!data || data.error) {
            if (container) container.innerHTML = '<div class="empty-state card"><h4>No findings available</h4><p>Run an assessment from the AI Workspace to populate findings.</p></div>';
            return;
        }
        currentData = data;
        var findings = (data.findings || []).map(enrich).sort(severitySort);
        currentFindings = findings;
        applyFilters();
        setupFilterChips();
    }

    function load() {
        fetch("/api/compliance")
            .then(function (r) { return r.json(); })
            .then(function (data) { renderNetsecFindings(data); })
            .catch(function () { if (container) container.innerHTML = '<div class="empty-state card"><h4>Unable to load findings</h4></div>'; });
    }

    load();
})();
