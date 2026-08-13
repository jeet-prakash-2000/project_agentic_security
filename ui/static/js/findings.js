(function () {
    "use strict";

    var root = document.getElementById("findingsRoot");
    var searchInput = document.getElementById("findingsSearch");
    var sortSelect = document.getElementById("sortSelect");
    var viewSelect = document.getElementById("viewSelect");

    var CATEGORY_ORDER = [
        "Software & Platform",
        "Capacity & Performance",
        "Security Services",
        "Network Configuration",
        "Administration & Management"
    ];

    var PRESET_VIEWS = [
        { id: "all", name: "All Findings", filters: { severity: "all", status: "all", domain: "all", search: "", sort: "severity" } },
        { id: "critical", name: "Critical Only", filters: { severity: "critical", status: "all", domain: "all", search: "", sort: "severity" } },
        { id: "high", name: "High Risk", filters: { severity: "high", status: "all", domain: "all", search: "", sort: "severity" } },
        { id: "operational", name: "Operational Risks", filters: { severity: "all", status: "non-compliant", domain: "all", search: "", sort: "risk" } },
        { id: "gaps", name: "Compliance Gaps", filters: { severity: "all", status: "non-compliant", domain: "all", search: "", sort: "domain" } },
        { id: "patching", name: "Patch Related", filters: { severity: "all", status: "non-compliant", domain: "Software & Platform", search: "", sort: "severity" } }
    ];

    var STORAGE_FILTERS = "findings.filters.v1";
    var STORAGE_VIEWS = "findings.views.v1";
    var STORAGE_REVIEWED = "findings.reviewed.v1";

    var state = {
        data: null,
        records: [],
        filters: { severity: "all", status: "all", domain: "all", search: "", sort: "severity" },
        customViews: [],
        reviewed: {},
        collapsed: {}
    };

    function escapeHtml(v) {
        var d = document.createElement("div");
        d.textContent = v == null ? "" : String(v);
        return d.innerHTML;
    }

    function categoryFor(domain) {
        if (typeof FINDING_ENRICHMENT_CATEGORIES !== "undefined" && FINDING_ENRICHMENT_CATEGORIES[domain]) {
            return FINDING_ENRICHMENT_CATEGORIES[domain];
        }
        return "Administration & Management";
    }

    function enrich(result, finding, meta, ctx) {
        var cid = (result.control || "").toUpperCase();
        var e = (typeof FINDING_ENRICHMENT !== "undefined" && FINDING_ENRICHMENT[cid]) ? FINDING_ENRICHMENT[cid] : null;
        var domain = (e && e.domain) || "General";
        var risk = (result.risk || "LOW").toUpperCase();
        var status = (result.status || "NON_COMPLIANT").toUpperCase();
        var compliant = status === "COMPLIANT";

        var rec = {
            control: cid,
            metric: result.metric || "",
            observed: result.observed,
            expected: result.expected,
            operator: result.operator || "",
            status: status,
            risk: compliant ? "COMPLIANT" : risk,
            _compliant: compliant,
            _domain: domain,
            _category: categoryFor(domain),
            _check: (e && e.check) || (finding && finding.finding) || "Control " + cid,
            _method: (e && e.method) || "",
            _gap: (e && e.gap) || "",
            _impact: (e && e.impact) || "",
            _risk_score: compliant ? 0 : (e && e.risk_score) || defaultRiskScore(risk),
            _evidence: (e && e.evidence) || [],
            _finding: (finding && finding.finding) || "",
            _remediation: (finding && finding.remediation) || (e && e.remediation) || "",
            _detected: ctx.detected,
            _firewall: ctx.firewall.hostname,
            _model: ctx.firewall.model,
            _version: ctx.firewall.version
        };
        return rec;
    }

    function defaultRiskScore(risk) {
        return risk === "CRITICAL" ? 95 : risk === "HIGH" ? 72 : risk === "MEDIUM" ? 45 : 20;
    }

    var SEV_ORDER = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, COMPLIANT: 4 };

    function sortRecords(records) {
        var sort = state.filters.sort;
        var copy = records.slice();
        copy.sort(function (a, b) {
            if (sort === "severity") {
                return (SEV_ORDER[a.risk] != null ? SEV_ORDER[a.risk] : 9) - (SEV_ORDER[b.risk] != null ? SEV_ORDER[b.risk] : 9)
                    || (a.control || "").localeCompare(b.control || "");
            }
            if (sort === "risk") {
                return (b._risk_score - a._risk_score) || (a.control || "").localeCompare(b.control || "");
            }
            if (sort === "recent" || sort === "oldest") {
                var at = a._detected || "", bt = b._detected || "";
                var cmp = at < bt ? -1 : at > bt ? 1 : 0;
                return sort === "recent" ? -cmp : cmp;
            }
            if (sort === "domain") {
                return (a._category || "").localeCompare(b._category || "") || (a._domain || "").localeCompare(b._domain || "") || (a.control || "").localeCompare(b.control || "");
            }
            if (sort === "firewall") {
                return (a._firewall || "").localeCompare(b._firewall || "") || (SEV_ORDER[a.risk] || 9) - (SEV_ORDER[b.risk] || 9);
            }
            return 0;
        });
        return copy;
    }

    function matchesFilters(rec) {
        var f = state.filters;
        var risk = rec.risk.toLowerCase();
        if (f.severity !== "all" && risk !== f.severity) return false;
        if (f.status !== "all") {
            if (f.status === "non-compliant" && rec._compliant) return false;
            if (f.status === "compliant" && !rec._compliant) return false;
        }
        if (f.domain !== "all" && rec._category !== f.domain) return false;
        if (f.search) {
            var q = f.search.toLowerCase();
            var hay = [rec.control, rec._check, rec._finding, rec._gap, rec._impact, rec._domain, rec._category, rec._firewall, rec.metric, rec._remediation, (rec._evidence || []).join(" ")].join(" ").toLowerCase();
            var terms = q.split(/\s+/);
            for (var i = 0; i < terms.length; i++) {
                if (hay.indexOf(terms[i]) === -1) return false;
            }
        }
        return true;
    }

    function getVisible() {
        return sortRecords(state.records.filter(matchesFilters));
    }

    // ============================================================
    // POSTURE KPIs
    // ============================================================

    function renderPosture(posture, firewall) {
        var pct = posture.compliance_pct || 0;
        var scoreValue = document.getElementById("scoreValue");
        var gaugeFill = document.getElementById("gaugeFill");
        var scoreTrend = document.getElementById("scoreTrend");
        var postureSource = document.getElementById("postureSource");

        if (scoreValue) scoreValue.textContent = pct;
        if (gaugeFill) {
            var CIRC = 326.7;
            gaugeFill.style.strokeDashoffset = (CIRC - (CIRC * pct / 100)).toFixed(1);
            gaugeFill.className = "gauge-fill" + (pct >= 75 ? " is-good" : pct >= 50 ? "" : " is-warn");
        }
        if (postureSource) postureSource.textContent = posture._source === "live" ? "Live" : "Sample";

        if (scoreTrend) {
            var trend = posture.trend_pct || 0;
            var cls = trend > 0 ? "up" : trend < 0 ? "down" : "flat";
            var arrow = trend > 0 ? "\u25B2" : trend < 0 ? "\u25BC" : "\u25AC";
            var sign = trend > 0 ? "+" : "";
            scoreTrend.innerHTML = '<span class="score-trend-value ' + cls + '">' + arrow + ' ' + sign + trend + '%</span>' +
                '<span class="score-trend-label">vs previous assessment</span>';
        }

        setText("kpiCompliant", posture.compliant);
        setText("kpiTotal", posture.total_controls);
        setText("kpiCompliantLabel", posture.compliant);
        setText("kpiNonCompliant", posture.non_compliant);

        var bar = document.getElementById("barCompliant");
        if (bar) bar.style.width = pct + "%";

        renderSeverityStack(posture);

        if (document.getElementById("kpiLastAssessed")) {
            document.getElementById("kpiLastAssessed").textContent = formatTs(posture.collected_at || posture.last_assessment_ts);
        }
        setText("kpiFirewall", firewall.hostname + (firewall.model ? " \u00b7 " + firewall.model : "") + (firewall.version ? " \u00b7 " + firewall.version : ""));
        setText("kpiAssessmentsRun", posture.assessments_run + " assessments run");
    }

    function setText(id, value) {
        var el = document.getElementById(id);
        if (el) el.textContent = value == null ? "\u2014" : String(value);
    }

    function renderSeverityStack(posture) {
        var el = document.getElementById("sevStack");
        if (!el) return;
        var sev = posture.severity || {};
        var change = posture.severity_change || {};
        var max = Math.max(1, sev.critical || 0, sev.high || 0, sev.medium || 0, sev.low || 0);
        var keys = [
            { key: "critical", name: "Critical", color: "#ef4444" },
            { key: "high", name: "High", color: "#f97316" },
            { key: "medium", name: "Medium", color: "#f59e0b" },
            { key: "low", name: "Low", color: "#22c55e" }
        ];
        var html = "";
        keys.forEach(function (k) {
            var count = sev[k.key] || 0;
            var delta = change[k.key] || 0;
            var dcls = delta > 0 ? "up" : delta < 0 ? "down" : "flat";
            var dtext = delta > 0 ? "+" + delta : delta < 0 ? String(delta) : "\u00b70";
            html += '<div class="sev-row">' +
                '<span class="sev-name">' + k.name + '</span>' +
                '<span class="sev-track"><span class="sev-track-fill" style="width:' + (count / max * 100) + '%;background:' + k.color + '"></span></span>' +
                '<span class="sev-num">' + count + ' <span class="sev-delta ' + dcls + '">' + dtext + '</span></span>' +
                '</div>';
        });
        el.innerHTML = html;
    }

    // ============================================================
    // SIDE RAIL — trend / timeline / domains
    // ============================================================

    function renderTrend(history, posture) {
        var el = document.getElementById("trendChart");
        if (!el) return;
        var snapshots = (history || []).slice(-14);
        if (!snapshots.length) { el.innerHTML = '<p class="trend-summary">No history yet.</p>'; return; }
        var max = 100;
        var html = '<div class="trend-bars">';
        snapshots.forEach(function (s, i) {
            var h = Math.max(4, (s.compliance_pct / max) * 100);
            html += '<div class="trend-bar' + (i === snapshots.length - 1 ? ' last' : '') + '" style="height:' + h + '%" title="' + s.compliance_pct + '%"></div>';
        });
        html += '</div><div class="trend-labels">';
        snapshots.forEach(function (s, i) {
            if (i === 0 || i === snapshots.length - 1 || i === Math.floor(snapshots.length / 2)) {
                html += '<span class="trend-label">' + formatShortTs(s.ts) + '</span>';
            } else {
                html += '<span class="trend-label"></span>';
            }
        });
        html += '</div>';
        var trend = posture.trend_pct || 0;
        var dir = trend > 0 ? "improved" : trend < 0 ? "declined" : "held steady";
        html += '<p class="trend-summary">Compliance ' + dir + ' by ' + Math.abs(trend) + '% since the previous assessment.</p>';
        el.innerHTML = html;
    }

    function renderTimeline(posture, firewall, data) {
        var el = document.getElementById("assessmentTimeline");
        if (!el) return;
        var collected = posture.collected_at || posture.last_assessment_ts;
        var items = [
            { label: "Assessment Started", detail: "Compliance assessment initiated", ts: posture.last_assessment_ts, dot: "warn" },
            { label: "Data Collected", detail: firewall.hostname + " \u00b7 PAN-OS " + firewall.version, ts: collected, dot: "" },
            { label: "Findings Generated", detail: posture.non_compliant + " findings across " + CATEGORY_ORDER.length + " domains", ts: collected, dot: "" },
            { label: "Controls Evaluated", detail: posture.compliant + " of " + posture.total_controls + " compliant", ts: collected, dot: "ok" }
        ];
        var html = "";
        items.forEach(function (it) {
            html += '<div class="timeline-item">' +
                '<span class="timeline-dot ' + it.dot + '"></span>' +
                '<div class="timeline-label">' + escapeHtml(it.label) + '</div>' +
                '<div class="timeline-detail">' + escapeHtml(it.detail) + '</div>' +
                '<div class="timeline-ts">' + escapeHtml(formatTs(it.ts)) + '</div>' +
                '</div>';
        });
        el.innerHTML = html;
    }

    function renderDomainList(records) {
        var el = document.getElementById("domainList");
        if (!el) return;
        var counts = {};
        records.forEach(function (r) { if (!r._compliant) counts[r._category] = (counts[r._category] || 0) + 1; });
        var max = 1;
        CATEGORY_ORDER.forEach(function (c) { max = Math.max(max, counts[c] || 0); });
        var html = "";
        CATEGORY_ORDER.forEach(function (c) {
            var n = counts[c] || 0;
            if (!n) return;
            html += '<div class="domain-row">' +
                '<div class="domain-row-head"><span class="domain-row-name">' + escapeHtml(c) + '</span><span class="domain-row-count">' + n + '</span></div>' +
                '<div class="domain-row-bar"><div class="domain-row-bar-fill" style="width:' + (n / max * 100) + '%"></div></div>' +
                '</div>';
        });
        el.innerHTML = html || '<p class="trend-summary">No non-compliant findings.</p>';
    }

    // ============================================================
    // FINDING CARDS
    // ============================================================

    function formatVal(v) {
        if (typeof v === "boolean") return v ? "Enabled" : "Disabled";
        if (Array.isArray(v)) return v.join(", ");
        if (v === null || v === undefined) return "\u2014";
        return String(v);
    }

    function formatExpected(v, op) {
        if (op === "not_empty") return "Not Empty";
        if (op === "supported_version") return Array.isArray(v) ? "in (" + v.join(", ") + ")" : "in (" + String(v) + ")";
        return formatVal(v);
    }

    var OPERATOR_SYMBOLS = {
        "==": "=", "!=": "\u2260", "<": "<", "<=": "\u2264", ">": ">", ">=": "\u2265",
        "supported_version": "\u2208", "not_empty": "\u2260"
    };

    var ICONS = {
        rem: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
        impact: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>',
        evidence: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 21l-4.3-4.3"/><circle cx="11" cy="11" r="7"/></svg>',
        verify: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="9"/></svg>',
        chevron: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>'
    };

    function findingCardHtml(rec) {
        var sev = (rec.risk || "low").toLowerCase();
        var cid = escapeHtml(rec.control);
        var title = escapeHtml(rec._check || "Untitled");
        var domain = escapeHtml(rec._domain);
        var category = escapeHtml(rec._category);
        var score = rec._risk_score || 0;
        var detected = escapeHtml(rec._detected || "\u2014");
        var fw = escapeHtml(rec._firewall);
        var statusKey = rec.status;
        var statusClass = rec._compliant ? "compliant" : "non-compliant";
        var isReviewed = !!state.reviewed[rec.control];

        var metricName = escapeHtml(rec.metric || "\u2014");
        var observedVal = escapeHtml(formatVal(rec.observed));
        var expectedVal = escapeHtml(formatExpected(rec.expected, rec.operator));
        var opSym = OPERATOR_SYMBOLS[rec.operator] || "?";
        var opLabel = escapeHtml(rec.operator || "");

        var summary = rec._compliant
            ? "Observed value '" + formatVal(rec.observed) + "' meets the expected baseline."
            : (rec._gap || rec._finding || "Finding requires attention.");

        var html = '<div class="finding-card" data-control="' + cid + '" role="button" tabindex="0" aria-expanded="false">' +
            '<span class="finding-card-accent ' + sev + '"></span>' +
            '<div class="finding-card-inner">' +
            '<div class="finding-card-head">' +
            '<div class="finding-card-top">' +
            '<span class="finding-card-id">' + cid + '</span>' +
            '<span class="sev-badge sev-' + sev + '">' + escapeHtml(rec.risk) + '</span>' +
            '<span class="status-badge ' + statusClass + '">' + statusKey + '</span>' +
            '</div>' +
            '<div class="finding-card-title">' + title + '</div>' +
            '<div class="finding-summary">' + escapeHtml(summary) + '</div>' +
            '<div class="finding-card-meta">' +
            '<div class="meta-item"><span class="meta-label">Domain</span><span class="meta-value">' + domain + '</span></div>' +
            '<div class="meta-item"><span class="meta-label">Category</span><span class="meta-value">' + category + '</span></div>' +
            '<div class="meta-item"><span class="meta-label">Risk Score</span><span class="meta-value mono"><span class="risk-chip"><span class="risk-meter"><span class="risk-meter-fill ' + sev + '" style="width:' + score + '%"></span></span>' + score + '/100</span></span></div>' +
            '<div class="meta-item"><span class="meta-label">Detected</span><span class="meta-value mono">' + detected + '</span></div>' +
            '<div class="meta-item"><span class="meta-label">Firewall</span><span class="meta-value mono">' + fw + '</span></div>' +
            (isReviewed ? '<div class="meta-item"><span class="meta-label">Review</span><span class="meta-value compliant">Reviewed</span></div>' : '') +
            '</div>' +
            '</div>' +
            '<span class="finding-chevron">' + ICONS.chevron + '</span>' +
            '<div class="finding-body">' +
            findingBodyHtml(rec) +
            actionsHtml(rec, isReviewed) +
            '</div>' +
            '</div>' +
            '</div>';
        return html;
    }

    function findingBodyHtml(rec) {
        var html = "";
        if (!rec._compliant) {
            html += '<div class="finding-section">' +
                '<div class="finding-section-title">' + ICONS.impact + ' What failed</div>' +
                '<div class="cmp-values">' +
                '<div class="cmp-block cmp-observed"><span class="cmp-block-label">Observed</span><span class="cmp-block-val">' + escapeHtml(formatVal(rec.observed)) + '</span></div>' +
                '<div class="cmp-op"><span class="cmp-op-sym">' + escapeHtml(OPERATOR_SYMBOLS[rec.operator] || "?") + '</span><span class="cmp-op-label">' + escapeHtml(rec.operator || "") + '</span></div>' +
                '<div class="cmp-block cmp-expected"><span class="cmp-block-label">Expected</span><span class="cmp-block-val">' + escapeHtml(formatExpected(rec.expected, rec.operator)) + '</span></div>' +
                '</div></div>';

            if (rec._gap) {
                html += '<div class="finding-section"><div class="finding-section-title">' + ICONS.impact + ' Potential Impact</div><p>' + escapeHtml(rec._gap) + '</p></div>';
            }
            if (rec._impact) {
                html += '<div class="finding-section"><div class="finding-section-title">' + ICONS.impact + ' Business Impact</div><p>' + escapeHtml(rec._impact) + '</p></div>';
            }
            if (rec._remediation) {
                html += '<div class="finding-section"><div class="remediation-callout"><div class="finding-section-title">' + ICONS.rem + ' Remediation</div><p>' + escapeHtml(rec._remediation) + '</p></div></div>';
            }
        } else {
            html += '<div class="finding-section">' +
                '<div class="finding-section-title">' + ICONS.verify + ' Compliance Check</div>' +
                '<div class="cmp-values">' +
                '<div class="cmp-block cmp-observed"><span class="cmp-block-label">Observed</span><span class="cmp-block-val">' + escapeHtml(formatVal(rec.observed)) + '</span></div>' +
                '<div class="cmp-op"><span class="cmp-op-sym">' + escapeHtml(OPERATOR_SYMBOLS[rec.operator] || "?") + '</span><span class="cmp-op-label">' + escapeHtml(rec.operator || "") + '</span></div>' +
                '<div class="cmp-block cmp-expected"><span class="cmp-block-label">Expected</span><span class="cmp-block-val">' + escapeHtml(formatExpected(rec.expected, rec.operator)) + '</span></div>' +
                '</div></div>';
        }

        html += evidenceHtml(rec);

        if (rec._method) {
            html += '<div class="finding-section"><div class="verification-box"><div class="finding-section-title">' + ICONS.verify + ' Verification Method</div><p>' + escapeHtml(rec._method) + '</p></div></div>';
        }
        return html;
    }

    function evidenceHtml(rec) {
        var srcs = rec._evidence || [];
        var expected = formatExpected(rec.expected, rec.operator);
        var items = '<div class="evidence-item">' +
            '<div class="evidence-row">' +
            '<span class="evidence-obs">' + escapeHtml(formatVal(rec.observed)) + '</span>' +
            '<span class="evidence-arrow">\u2192 expected</span>' +
            '<span class="evidence-exp">' + escapeHtml(expected) + '</span>' +
            '</div>' +
            '<div class="evidence-meta">' +
            '<span><span class="em-label">Metric</span> ' + escapeHtml(rec.metric || "\u2014") + '</span>' +
            '<span><span class="em-label">Detected</span> ' + escapeHtml(rec._detected || "\u2014") + '</span>' +
            '<span><span class="em-label">Device</span> ' + escapeHtml(rec._firewall) + '</span>' +
            '</div></div>';
        var html = '<div class="finding-section"><div class="finding-section-title">' + ICONS.evidence + ' Technical Evidence</div>' +
            '<div class="evidence-list">' + items;
        srcs.forEach(function (s) {
            html += '<span class="evidence-src">' + escapeHtml(s) + '</span>';
        });
        html += '</div></div>';
        return html;
    }

    function actionsHtml(rec, isReviewed) {
        var html = '<div class="finding-actions">' +
            '<button class="action-btn ai" data-act="explain" type="button">Explain</button>' +
            '<button class="action-btn ai" data-act="fixplan" type="button">Fix Plan</button>' +
            '<button class="action-btn ai" data-act="risk" type="button">Risk</button>' +
            '<button class="action-btn ai" data-act="summarize" type="button">Summarize</button>' +
            '<button class="action-btn" data-act="device" type="button">View Device</button>' +
            '<button class="action-btn" data-act="export" type="button">Export</button>' +
            '<button class="action-btn" data-act="report" type="button">Report</button>' +
            '<button class="action-btn" data-act="share" type="button">Share</button>' +
            '<button class="action-btn ' + (isReviewed ? 'is-reviewed' : '') + '" data-act="review" type="button">' + (isReviewed ? 'Reviewed' : 'Mark Reviewed') + '</button>' +
            '</div>';
        return html;
    }

    function renderGroups(records) {
        if (!root) return;
        var countEl = document.getElementById("findingsCount");
        if (countEl) countEl.textContent = records.length + " finding" + (records.length === 1 ? "" : "s");

        if (!records.length) {
            root.innerHTML = '<div class="empty-state card"><h3>No findings match filters</h3><p>Adjust filters or run a fresh assessment.</p></div>';
            return;
        }

        var groups = {};
        CATEGORY_ORDER.forEach(function (c) { groups[c] = []; });
        records.forEach(function (r) {
            var c = r._category || "Administration & Management";
            if (!groups[c]) groups[c] = [];
            groups[c].push(r);
        });

        var html = "";
        Object.keys(groups).forEach(function (category) {
            var list = groups[category];
            if (!list.length) return;
            var isCollapsed = !!state.collapsed[category];
            var badges = { critical: 0, high: 0, medium: 0, low: 0 };
            list.forEach(function (r) {
                var k = r.risk.toLowerCase();
                if (badges[k] != null) badges[k]++;
            });
            var badgeHtml = "";
            ["critical", "high", "medium", "low"].forEach(function (k) {
                if (badges[k]) badgeHtml += '<span class="group-badge ' + k + '">' + badges[k] + ' ' + k + '</span>';
            });
            html += '<section class="group-section' + (isCollapsed ? ' is-collapsed' : '') + '" data-category="' + escapeHtml(category) + '">' +
                '<div class="group-head" role="button" tabindex="0">' +
                '<span class="group-toggle">' + ICONS.chevron + '</span>' +
                '<span class="group-name">' + escapeHtml(category) + '</span>' +
                '<span class="group-count">' + list.length + '</span>' +
                '<span class="group-badges">' + badgeHtml + '</span>' +
                '</div>' +
                '<div class="group-body">' +
                list.map(findingCardHtml).join("") +
                '</div>' +
                '</section>';
        });
        root.innerHTML = html;
    }

    // ============================================================
    // RENDER ALL
    // ============================================================

    function renderAll() {
        var visible = getVisible();
        renderGroups(visible);
        renderDomainList(state.records);
    }

    function applyFilters() {
        saveFilters();
        syncFilterChips();
        renderAll();
    }

    // ============================================================
    // FILTER CHIPS & DOMAIN CHIPS
    // ============================================================

    function renderDomainChips() {
        var el = document.getElementById("domainChips");
        if (!el) return;
        var chips = '<button class="chip chip-domain is-active" data-value="all">All</button>';
        CATEGORY_ORDER.forEach(function (c) {
            chips += '<button class="chip chip-domain" data-value="' + escapeHtml(c) + '">' + escapeHtml(c) + '</button>';
        });
        el.innerHTML = chips;
    }

    function syncFilterChips() {
        syncChipGroup("severityChips", state.filters.severity);
        syncChipGroup("statusChips", state.filters.status);
        syncChipGroup("domainChips", state.filters.domain);
    }

    function syncChipGroup(id, value) {
        var el = document.getElementById(id);
        if (!el) return;
        el.querySelectorAll(".chip").forEach(function (c) {
            c.classList.toggle("is-active", c.getAttribute("data-value") === value);
        });
    }

    function bindChips(id, key) {
        var el = document.getElementById(id);
        if (!el) return;
        el.addEventListener("click", function (e) {
            var chip = e.target.closest(".chip");
            if (!chip) return;
            state.filters[key] = chip.getAttribute("data-value") || "all";
            applyFilters();
        });
    }

    // ============================================================
    // SAVED VIEWS
    // ============================================================

    function loadSavedViews() {
        try {
            state.customViews = JSON.parse(localStorage.getItem(STORAGE_VIEWS) || "[]") || [];
        } catch (e) { state.customViews = []; }
    }

    function populateViewSelect() {
        if (!viewSelect) return;
        var html = "";
        PRESET_VIEWS.forEach(function (v) { html += '<option value="' + v.id + '">' + escapeHtml(v.name) + '</option>'; });
        state.customViews.forEach(function (v) { html += '<option value="custom:' + v.name + '">' + escapeHtml(v.name) + '</option>'; });
        viewSelect.innerHTML = html;
    }

    function applyView(view) {
        state.filters = Object.assign({}, view.filters);
        if (sortSelect) sortSelect.value = state.filters.sort;
        if (searchInput) searchInput.value = state.filters.search || "";
        applyFilters();
    }

    function findPresetView() {
        return PRESET_VIEWS.find(function (v) {
            return v.filters.severity === state.filters.severity &&
                v.filters.status === state.filters.status &&
                v.filters.domain === state.filters.domain &&
                v.filters.search === state.filters.search;
        });
    }

    function syncViewSelect() {
        if (!viewSelect) return;
        var preset = findPresetView();
        if (preset) { viewSelect.value = preset.id; return; }
        var custom = state.customViews.find(function (v) {
            return v.filters.severity === state.filters.severity &&
                v.filters.status === state.filters.status &&
                v.filters.domain === state.filters.domain &&
                v.filters.search === state.filters.search;
        });
        if (custom) { viewSelect.value = "custom:" + custom.name; return; }
        viewSelect.value = "all";
    }

    function saveView() {
        var name = window.prompt("Name this view:");
        if (!name || !name.trim()) return;
        name = name.trim();
        state.customViews = state.customViews.filter(function (v) { return v.name !== name; });
        state.customViews.push({ name: name, filters: Object.assign({}, state.filters) });
        localStorage.setItem(STORAGE_VIEWS, JSON.stringify(state.customViews));
        populateViewSelect();
        viewSelect.value = "custom:" + name;
        if (window.showToast) window.showToast("View saved as \u201c" + name + "\u201d.", "success");
    }

    // ============================================================
    // PERSISTENCE
    // ============================================================

    function loadFilters() {
        try {
            var saved = JSON.parse(localStorage.getItem(STORAGE_FILTERS) || "null");
            if (saved && typeof saved === "object") state.filters = Object.assign({}, state.filters, saved);
        } catch (e) { /* ignore */ }
        try {
            state.reviewed = JSON.parse(localStorage.getItem(STORAGE_REVIEWED) || "{}") || {};
        } catch (e) { state.reviewed = {}; }
    }

    function saveFilters() {
        try { localStorage.setItem(STORAGE_FILTERS, JSON.stringify(state.filters)); } catch (e) { /* ignore */ }
    }

    function saveReviewed() {
        try { localStorage.setItem(STORAGE_REVIEWED, JSON.stringify(state.reviewed)); } catch (e) { /* ignore */ }
    }

    // ============================================================
    // AI COPILOT
    // ============================================================

    var copilot = { panel: document.getElementById("copilotPanel"), backdrop: document.getElementById("copilotBackdrop"), body: document.getElementById("copilotBody"), current: null };

    function openCopilot(rec) {
        copilot.current = rec;
        document.getElementById("copilotFindingRef").textContent = rec.control + " \u00b7 " + rec._domain;
        copilot.body.innerHTML = '<p class="copilot-placeholder">Select an action to get AI assistance for this finding.</p>';
        copilot.panel.classList.add("open");
        copilot.backdrop.classList.add("show");
        resetCopilotChips();
    }

    function closeCopilot() {
        copilot.panel.classList.remove("open");
        copilot.backdrop.classList.remove("show");
    }

    function resetCopilotChips() {
        var chips = document.querySelectorAll("#copilotActions .copilot-chip");
        chips.forEach(function (c) { c.classList.remove("is-active"); });
    }

    var ACTION_LABELS = { explain: "Explain Finding", fixplan: "Generate Fix Plan", risk: "Show Risk Analysis", summarize: "Summarize Finding" };

    function runCopilot(action) {
        if (!copilot.current) return;
        var chips = document.querySelectorAll("#copilotActions .copilot-chip");
        chips.forEach(function (c) { c.classList.toggle("is-active", c.getAttribute("data-action") === action); });

        copilot.body.innerHTML = '<div class="copilot-loading"><span class="spin"></span> Thinking\u2026</div>';
        var rec = copilot.current;
        var prompt = buildPrompt(action, rec);

        fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: prompt })
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data && data.error) throw new Error(data.error);
                var reply = (data && data.reply) || "";
                if (reply) { renderCopilotAnswer(reply); return; }
                renderCopilotAnswer(buildLocalAnswer(action, rec));
            })
            .catch(function () {
                renderCopilotAnswer(buildLocalAnswer(action, rec));
            });
    }

    function buildPrompt(action, rec) {
        var context = [
            "Finding " + rec.control + " (" + rec._domain + ", " + rec._category + ")",
            "Check: " + rec._check,
            "Severity: " + rec.risk + ", Risk Score: " + rec._risk_score + "/100",
            "Metric: " + rec.metric,
            "Observed: " + JSON.stringify(rec.observed),
            "Expected: " + JSON.stringify(rec.expected) + " (operator " + rec.operator + ")",
            "Gap: " + rec._gap,
            "Impact: " + rec._impact,
            "Remediation: " + rec._remediation,
            "Firewall: " + rec._firewall + " (" + rec._model + ", " + rec._version + ")"
        ].join("\n");

        var instruction = {
            explain: "Explain this firewall security finding in plain, concise language for a network engineer. Include what is wrong, why it matters, and the single most important first step.",
            fixplan: "Produce a concrete, ordered fix plan (numbered steps) to remediate this finding. Include verification steps and rollback considerations.",
            risk: "Provide a focused risk analysis of this finding: likelihood, business impact, and a recommended risk response (accept/mitigate/transfer/avoid).",
            summarize: "Summarize this finding in 2-3 crisp bullet points suitable for an executive dashboard."
        }[action] || "";

        return instruction + "\n\nFINDING CONTEXT:\n" + context;
    }

    function renderCopilotAnswer(text) {
        var body = copilot.body;
        var html = '<div class="copilot-answer">';
        html += text.split(/\n{2,}/).map(function (para) {
            return '<p>' + escapeHtml(para).replace(/\n/g, "<br>") + '</p>';
        }).join("");
        html += '</div>';
        body.innerHTML = html;
    }

    function buildLocalAnswer(action, rec) {
        if (action === "explain") {
            return "Finding " + rec.control + " \u2014 " + rec._check + "\n\n" +
                "What is wrong: " + (rec._gap || "The control does not meet its baseline.") + "\n\n" +
                "Why it matters: " + (rec._impact || "This exposes the environment to risk.") + "\n\n" +
                "First step: " + (rec._remediation || "Review the control and apply the recommended remediation.");
        }
        if (action === "fixplan") {
            var steps = [
                "1. Acknowledge and scope \u2014 confirm " + rec.control + " applies to " + rec._firewall + " and capture a change ticket.",
                "2. Assess current state \u2014 " + (rec._method || "collect the current configuration and metric."),
                "3. Apply remediation \u2014 " + (rec._remediation || "align the configuration with the baseline."),
                "4. Verify \u2014 re-run the check and confirm " + rec.metric + " now satisfies " + formatExpected(rec.expected, rec.operator) + ".",
                "5. Document and close \u2014 attach evidence and schedule the next re-assessment."
            ];
            return "Fix plan for " + rec.control + "\n\n" + steps.join("\n");
        }
        if (action === "risk") {
            return "Risk analysis \u2014 " + rec.control + "\n\n" +
                "Severity: " + rec.risk + " (risk score " + rec._risk_score + "/100)\n" +
                "Likelihood: " + (rec._risk_score >= 80 ? "High" : rec._risk_score >= 55 ? "Moderate" : "Low") + "\n" +
                "Business impact: " + (rec._impact || "See finding impact.") + "\n" +
                "Recommended response: " + (rec._risk_score >= 80 ? "Mitigate immediately" : "Mitigate on a planned cycle") + ".";
        }
        return "Summary \u2014 " + rec.control + "\n\n" +
            "\u2022 " + rec._check + "\n" +
            "\u2022 Severity " + rec.risk + ", risk score " + rec._risk_score + "/100\n" +
            "\u2022 " + (rec._remediation || "No remediation guidance available.");
    }

    // ============================================================
    // OPERATIONAL ACTIONS
    // ============================================================

    function handleOperationalAction(act, rec) {
        if (act === "device") {
            if (window.showToast) window.showToast("Firewall: " + rec._firewall + " \u00b7 " + rec._model + " \u00b7 PAN-OS " + rec._version, "info");
        } else if (act === "export") {
            downloadJson(rec.control + "_finding.json", buildExportPayload(rec));
            if (window.showToast) window.showToast("Exported " + rec.control + ".", "success");
        } else if (act === "report") {
            generateReport();
        } else if (act === "share") {
            shareFinding(rec);
        } else if (act === "review") {
            toggleReview(rec);
        }
    }

    function buildExportPayload(rec) {
        return {
            control: rec.control,
            status: rec.status,
            severity: rec.risk,
            risk_score: rec._risk_score,
            domain: rec._domain,
            category: rec._category,
            check: rec._check,
            metric: rec.metric,
            observed: rec.observed,
            expected: rec.expected,
            operator: rec.operator,
            gap: rec._gap,
            impact: rec._impact,
            remediation: rec._remediation,
            verification_method: rec._method,
            evidence: rec._evidence,
            firewall: { hostname: rec._firewall, model: rec._model, version: rec._version },
            detected_at: rec._detected
        };
    }

    function downloadJson(filename, obj) {
        var blob = new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" });
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function generateReport() {
        fetch("/api/excel")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data && data.error) throw new Error(data.error);
                if (window.showToast) window.showToast("Workbook generated. Download from Reports.", "success");
                if (data && data.download_url) {
                    var a = document.createElement("a");
                    a.href = data.download_url;
                    a.download = "";
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                }
            })
            .catch(function () { if (window.showToast) window.showToast("Report generation failed.", "error"); });
    }

    function shareFinding(rec) {
        var text = rec.control + " " + rec._check + " \u2014 Severity " + rec.risk + " (" + rec._risk_score + "/100) on " + rec._firewall + ". Remediation: " + rec._remediation;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function () {
                if (window.showToast) window.showToast("Finding copied to clipboard.", "success");
            });
        } else {
            window.prompt("Copy this finding:", text);
        }
    }

    function toggleReview(rec) {
        if (state.reviewed[rec.control]) {
            delete state.reviewed[rec.control];
        } else {
            state.reviewed[rec.control] = true;
        }
        saveReviewed();
        renderAll();
    }

    // ============================================================
    // EVENT BINDING
    // ============================================================

    function bindEvents() {
        root.addEventListener("click", function (e) {
            var groupHead = e.target.closest(".group-head");
            if (groupHead) {
                var section = groupHead.closest(".group-section");
                var category = section.getAttribute("data-category");
                state.collapsed[category] = !section.classList.contains("is-collapsed");
                section.classList.toggle("is-collapsed");
                return;
            }

            var actionBtn = e.target.closest(".action-btn");
            if (actionBtn) {
                e.stopPropagation();
                var card = actionBtn.closest(".finding-card");
                var cid = card.getAttribute("data-control");
                var rec = findRecord(cid);
                if (!rec) return;
                var act = actionBtn.getAttribute("data-act");
                if (actionBtn.classList.contains("ai")) {
                    openCopilot(rec);
                    runCopilot(act);
                } else {
                    handleOperationalAction(act, rec);
                }
                return;
            }

            var card = e.target.closest(".finding-card");
            if (card) {
                var wasActive = card.classList.contains("is-active");
                card.classList.toggle("is-active");
                card.setAttribute("aria-expanded", String(!wasActive));
            }
        });

        root.addEventListener("keydown", function (e) {
            if ((e.key === "Enter" || e.key === " ") && e.target.classList.contains("finding-card")) {
                e.preventDefault();
                e.target.classList.toggle("is-active");
            }
            if ((e.key === "Enter" || e.key === " ") && e.target.classList.contains("group-head")) {
                e.preventDefault();
                e.target.closest(".group-section").classList.toggle("is-collapsed");
            }
        });

        if (searchInput) {
            var t;
            searchInput.addEventListener("input", function () {
                clearTimeout(t);
                t = setTimeout(function () {
                    state.filters.search = searchInput.value.trim();
                    applyFilters();
                }, 220);
            });
        }

        if (sortSelect) {
            sortSelect.addEventListener("change", function () {
                state.filters.sort = sortSelect.value;
                applyFilters();
            });
        }

        if (viewSelect) {
            viewSelect.addEventListener("change", function () {
                var val = viewSelect.value;
                if (val.startsWith("custom:")) {
                    var name = val.slice(7);
                    var v = state.customViews.find(function (x) { return x.name === name; });
                    if (v) applyView(v);
                } else {
                    var preset = PRESET_VIEWS.find(function (x) { return x.id === val; });
                    if (preset) applyView(preset);
                }
            });
        }

        document.getElementById("btnSaveView").addEventListener("click", saveView);
        document.getElementById("btnResetFilters").addEventListener("click", function () {
            state.filters = { severity: "all", status: "all", domain: "all", search: "", sort: "severity" };
            if (sortSelect) sortSelect.value = "severity";
            if (searchInput) searchInput.value = "";
            if (viewSelect) viewSelect.value = "all";
            applyFilters();
        });
        document.getElementById("btnExpandAll").addEventListener("click", function () {
            state.collapsed = {};
            document.querySelectorAll(".group-section").forEach(function (s) { s.classList.remove("is-collapsed"); });
        });
        document.getElementById("btnCollapseAll").addEventListener("click", function () {
            CATEGORY_ORDER.forEach(function (c) { state.collapsed[c] = true; });
            document.querySelectorAll(".group-section").forEach(function (s) { s.classList.add("is-collapsed"); });
        });
        document.getElementById("btnExportReport").addEventListener("click", generateReport);

        document.getElementById("copilotClose").addEventListener("click", closeCopilot);
        document.getElementById("copilotBackdrop").addEventListener("click", closeCopilot);
        document.getElementById("copilotActions").addEventListener("click", function (e) {
            var chip = e.target.closest(".copilot-chip");
            if (!chip) return;
            runCopilot(chip.getAttribute("data-action"));
        });
    }

    function findRecord(cid) {
        return state.records.find(function (r) { return r.control === cid; });
    }

    // ============================================================
    // TIME FORMATTING
    // ============================================================

    function formatTs(ts) {
        if (!ts) return "\u2014";
        var d = parseDate(ts);
        if (!d) return String(ts).slice(0, 16);
        return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
    }

    function formatShortTs(ts) {
        var d = parseDate(ts);
        if (!d) return "";
        return d.toLocaleString(undefined, { month: "short", day: "numeric" });
    }

    function parseDate(ts) {
        if (typeof ts === "number") return new Date(ts * 1000);
        var d = new Date(ts);
        return isNaN(d.getTime()) ? null : d;
    }

    // ============================================================
    // LOAD
    // ============================================================

    function load() {
        fetch("/api/findings")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data || data.error) {
                    if (root) root.innerHTML = '<div class="empty-state card"><h4>No findings available</h4><p>Run an assessment from the AI Workspace to populate findings.</p></div>';
                    return;
                }
                state.data = data;
                var ctx = {
                    detected: data._collected_at ? String(data._collected_at).slice(0, 10) : new Date().toISOString().slice(0, 10),
                    firewall: data.firewall || { hostname: "edge-fw-01", model: "", version: "" }
                };
                var findingMap = {};
                (data.findings || []).forEach(function (f) { findingMap[(f.control || "").toUpperCase()] = f; });
                state.records = (data.assessment || []).map(function (r) {
                    return enrich(r, findingMap[(r.control || "").toUpperCase()], null, ctx);
                });

                renderPosture(data.posture, data.firewall);
                renderTrend(data.history, data.posture);
                renderTimeline(data.posture, data.firewall, data);
                renderDomainChips();
                populateViewSelect();
                if (sortSelect) sortSelect.value = state.filters.sort;
                if (searchInput) searchInput.value = state.filters.search || "";
                syncViewSelect();
                renderAll();
            })
            .catch(function () {
                if (root) root.innerHTML = '<div class="empty-state card"><h4>Unable to load findings</h4></div>';
            });
    }

    loadFilters();
    loadSavedViews();
    bindChips("severityChips", "severity");
    bindChips("statusChips", "status");
    bindChips("domainChips", "domain");
    bindEvents();
    load();
})();
