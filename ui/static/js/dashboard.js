(function () {
    "use strict";

    var sourceBadge = document.getElementById("dataSourceBadge");
    var refreshBtn = document.getElementById("refreshBtn");

    var CATEGORY_ORDER = [
        "Software & Platform",
        "Capacity & Performance",
        "Security Services",
        "Networking",
        "VPN & Remote Access",
        "Administration",
        "Logging & Monitoring"
    ];

    function setSource(source) {
        if (!sourceBadge) return;
        var label = source === "live" ? "Live Data" : "Sample Data";
        sourceBadge.innerHTML = '<span class="pulse-dot"></span> ' + label;
        sourceBadge.style.borderColor = source === "live" ? "rgba(34, 197, 94, 0.5)" : "rgba(245, 158, 11, 0.5)";
        sourceBadge.style.color = source === "live" ? "#059669" : "#B45309";
    }

    function escapeHtml(value) {
        var d = document.createElement("div");
        d.textContent = value == null ? "" : String(value);
        return d.innerHTML;
    }

    function parseDate(ts) {
        if (typeof ts === "number") return new Date(ts * 1000);
        var d = new Date(ts);
        return isNaN(d.getTime()) ? null : d;
    }

    function formatShortTs(ts) {
        var d = parseDate(ts);
        if (!d) return "";
        return d.toLocaleString(undefined, { month: "short", day: "numeric" });
    }

    // ============================================================
    // COMPLIANCE PIE (square, hover/click per segment)
    // ============================================================

    function polar(cx, cy, r, angleDeg) {
        var rad = (angleDeg - 90) * Math.PI / 180;
        return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
    }

    function donutSegmentPath(cx, cy, outerR, innerR, start, end) {
        var s = polar(cx, cy, outerR, start);
        var e = polar(cx, cy, outerR, end);
        var is = polar(cx, cy, innerR, end);
        var ie = polar(cx, cy, innerR, start);
        var large = (end - start) > 180 ? 1 : 0;
        return "M" + s.x.toFixed(1) + " " + s.y.toFixed(1) +
            " A" + outerR + " " + outerR + " 0 " + large + " 1 " + e.x.toFixed(1) + " " + e.y.toFixed(1) +
            " L" + is.x.toFixed(1) + " " + is.y.toFixed(1) +
            " A" + innerR + " " + innerR + " 0 " + large + " 0 " + ie.x.toFixed(1) + " " + ie.y.toFixed(1) + " Z";
    }

    function renderCompliancePie(c) {
        var svg = document.getElementById("compliancePie");
        if (!svg) return;
        var compliant = Number(c.compliant) || 0;
        var nonCompliant = Number(c.non_compliant) || 0;
        var notAssessed = Number(c.not_assessed) || 0;
        var total = compliant + nonCompliant + notAssessed;
        var pct = total ? Math.round(compliant / total * 100) : 0;

        var percentEl = document.getElementById("donutPercent");
        var statusEl = document.getElementById("donutStatus");
        function statusText(v) {
            return v >= 80 ? "Healthy Posture" : v >= 50 ? "At Risk" : "Critical Posture";
        }
        if (percentEl) percentEl.textContent = pct + "%";
        if (statusEl) statusEl.textContent = statusText(pct);

        var cx = 100, cy = 100, outerR = 92, innerR = 62;
        var segments = [
            { value: compliant, color: "#16A34A", label: "Compliant", status: "compliant" },
            { value: nonCompliant, color: "#DC2626", label: "Non-Compliant", status: "non-compliant" },
            { value: notAssessed, color: "#F59E0B", label: "Not Assessed", status: "not-assessed" }
        ];
        var totalSeg = Math.max(total, 1);
        var angle = 0;
        var html = "";
        segments.forEach(function (s) {
            if (s.value <= 0) return;
            var sweep = s.value / totalSeg * 360;
            html += '<path class="donut-seg" d="' + donutSegmentPath(cx, cy, outerR, innerR, angle, angle + sweep) + '" fill="' + s.color + '" ' +
                'data-status="' + s.status + '" data-label="' + s.label + '" data-value="' + s.value + '">' +
                "<title>" + s.label + ": " + s.value + "</title></path>";
            angle += sweep;
        });
        if (html === "") {
            html = '<circle class="donut-empty" cx="100" cy="100" r="92" fill="#F1F5F9"/>';
        }
        svg.innerHTML = html;

        svg.querySelectorAll(".donut-seg").forEach(function (seg) {
            seg.addEventListener("mouseover", function () {
                if (percentEl) percentEl.textContent = seg.getAttribute("data-value");
                if (statusEl) statusEl.textContent = seg.getAttribute("data-label");
            });
            seg.addEventListener("mouseout", function () {
                if (percentEl) percentEl.textContent = pct + "%";
                if (statusEl) statusEl.textContent = statusText(pct);
            });
            seg.addEventListener("click", function () {
                window.location.href = "/findings?status=" + encodeURIComponent(seg.getAttribute("data-status"));
            });
        });

        var pills = document.getElementById("donutPills");
        if (pills) {
            var defs = [
                { label: "Compliant", count: compliant, color: "#16A34A", status: "compliant" },
                { label: "Non-Compliant", count: nonCompliant, color: "#DC2626", status: "non-compliant" },
                { label: "Not Assessed", count: notAssessed, color: "#F59E0B", status: "not-assessed" }
            ];
            var pillHtml = "";
            defs.forEach(function (d) {
                var pctV = total ? Math.round(d.count / total * 100) : 0;
                pillHtml += '<button class="donut-pill" data-status="' + d.status + '" type="button">' +
                    '<i class="donut-dot" style="background:' + d.color + '"></i>' +
                    "<span>" + d.label + "</span>" +
                    "<strong>" + d.count + "</strong>" +
                    "<em>" + pctV + "%</em>" +
                    "</button>";
            });
            pills.innerHTML = pillHtml;
            pills.querySelectorAll(".donut-pill").forEach(function (pill) {
                pill.addEventListener("click", function () {
                    window.location.href = "/findings?status=" + encodeURIComponent(pill.getAttribute("data-status"));
                });
            });
        }
    }

    // ============================================================
    // FINDINGS BY SEVERITY (colored squares)
    // ============================================================

    function renderSeverityGrid(f) {
        var el = document.getElementById("severityGrid");
        if (!el) return;
        var sev = [
            { label: "Critical", color: "#DC2626", count: f.critical || 0, status: "critical" },
            { label: "High", color: "#F97316", count: f.high || 0, status: "high" },
            { label: "Medium", color: "#F59E0B", count: f.medium || 0, status: "medium" },
            { label: "Low", color: "#22C55E", count: f.low || 0, status: "low" }
        ];
        var html = "";
        sev.forEach(function (s) {
            html += '<a class="sev-tile" href="/findings?severity=' + s.status + '" title="' + s.label + ': ' + s.count + ' findings">' +
                '<span class="sev-tile-color" style="background:' + s.color + '"></span>' +
                '<span class="sev-tile-count">' + s.count + "</span>" +
                '<span class="sev-tile-label">' + s.label + "</span>" +
                "</a>";
        });
        el.innerHTML = html;
    }

    // ============================================================
    // RECENT FINDINGS
    // ============================================================

    function renderRecentFindings(recent) {
        var el = document.getElementById("recentFindings");
        if (!el) return;
        if (!recent.length) { el.innerHTML = '<p class="empty-inline">No findings.</p>'; return; }
        var html = "";
        recent.forEach(function (f) {
            var risk = (f.risk || "LOW").toLowerCase();
            var cls = risk === "critical" ? "bad" : risk === "high" ? "warn" : risk === "medium" ? "flat" : "good";
            html += '<div class="recent-finding">' +
                '<span class="recent-finding-control">' + escapeHtml(f.control || "") + "</span>" +
                '<span class="recent-finding-title">' + escapeHtml(f.title || "") + "</span>" +
                '<span class="recent-finding-risk ' + cls + '">' + escapeHtml(f.risk || "LOW") + "</span>" +
                "</div>";
        });
        el.innerHTML = html;
    }

    // ============================================================
    // TOP RISK DOMAINS (vertical bar graph, 7 categories)
    // ============================================================

    function categoryForControl(control) {
        var cid = (control || "").toUpperCase();
        var domain = (typeof FINDING_ENRICHMENT !== "undefined" && FINDING_ENRICHMENT[cid]) ? FINDING_ENRICHMENT[cid].domain : null;
        if (!domain) return null;
        return (typeof FINDING_ENRICHMENT_CATEGORIES !== "undefined" && FINDING_ENRICHMENT_CATEGORIES[domain]) || domain;
    }

    function renderVerticalBars(findingsList) {
        var el = document.getElementById("verticalBars");
        if (!el) return;
        var counts = {};
        (findingsList || []).forEach(function (f) {
            var cat = categoryForControl(f.control);
            if (cat) counts[cat] = (counts[cat] || 0) + 1;
        });
        var max = 1;
        CATEGORY_ORDER.forEach(function (c) { max = Math.max(max, counts[c] || 0); });

        var html = '<div class="vertical-bars-axis">';
        CATEGORY_ORDER.forEach(function (cat) {
            var n = counts[cat] || 0;
            var h = max ? Math.round(n / max * 100) : 0;
            html += '<a class="vbar" href="/findings?domain=' + encodeURIComponent(cat) + '" title="' + escapeHtml(cat) + ": " + n + '">' +
                '<span class="vbar-count">' + n + "</span>" +
                '<span class="vbar-track"><span class="vbar-fill" style="height:' + h + '%"></span></span>' +
                '<span class="vbar-label">' + escapeHtml(shortLabel(cat)) + "</span>" +
                "</a>";
        });
        html += "</div>";
        el.innerHTML = html;
    }

    function shortLabel(cat) {
        return cat.replace(" & Remote Access", "").replace(" & Platform", "").replace(" & Performance", "").replace(" & Monitoring", "").replace(" &", "");
    }

    // ============================================================
    // COMPLIANCE TREND
    // ============================================================

    function renderTrendStats(history) {
        var el = document.getElementById("trendStats");
        if (!el) return;
        var snapshots = (history || []).filter(function (s) {
            return s && typeof s.compliance_pct === "number";
        });
        if (!snapshots.length) return;
        var latest = snapshots[snapshots.length - 1];
        var prev = snapshots.length > 1 ? snapshots[snapshots.length - 2] : null;
        var current = latest.compliance_pct;
        var prevScore = prev ? prev.compliance_pct : null;
        var improvement = prevScore != null ? Math.round((current - prevScore) * 10) / 10 : null;
        var impCls = improvement == null ? "" : improvement > 0 ? "good" : improvement < 0 ? "bad" : "flat";
        var impText = improvement == null ? "\u2014" : (improvement > 0 ? "+" : "") + improvement + "%";

        el.innerHTML =
            '<span class="trend-stat"><span>Current Score</span><strong>' + current + "%</strong></span>" +
            '<span class="trend-stat"><span>Previous Scan</span><strong>' + (prevScore != null ? prevScore + "%" : "\u2014") + "</strong></span>" +
            '<span class="trend-stat"><span>Improvement</span><strong class="' + impCls + '">' + impText + "</strong></span>";
    }

    function renderComplianceTrend(history) {
        var el = document.getElementById("trendChart");
        if (!el) return;

        var snapshots = (history || []).filter(function (s) {
            return s && typeof s.compliance_pct === "number";
        });
        if (!snapshots.length) {
            el.innerHTML = '<p class="trend-summary">No history yet. Run an assessment to start tracking compliance.</p>';
            return;
        }
        if (snapshots.length > 12) snapshots = snapshots.slice(-12);

        var W = 900, H = 160;
        var PAD_LEFT = 36, PAD_RIGHT = 12, PAD_TOP = 12, PAD_BOTTOM = 22;
        var min = 0, max = 100;
        var n = snapshots.length;

        function x(i) {
            if (n === 1) return PAD_LEFT + (W - PAD_LEFT - PAD_RIGHT) / 2;
            return PAD_LEFT + (i / (n - 1)) * (W - PAD_LEFT - PAD_RIGHT);
        }
        function y(v) {
            return PAD_TOP + (1 - (v - min) / (max - min)) * (H - PAD_TOP - PAD_BOTTOM);
        }

        var avg = snapshots.reduce(function (s, a) { return s + a.compliance_pct; }, 0) / n;
        var points = snapshots.map(function (s, i) { return [x(i), y(s.compliance_pct)]; });
        var linePath = "M" + points.map(function (p) { return p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" L");
        var areaPath = linePath + " L" + points[points.length - 1][0].toFixed(1) + " " + (H - PAD_BOTTOM) + " L" + points[0][0].toFixed(1) + " " + (H - PAD_BOTTOM) + " Z";
        var avgY = y(avg);

        var html = '<svg class="trend-line-svg" viewBox="0 0 ' + W + " " + H + '" preserveAspectRatio="none" role="img" aria-label="Compliance score over time">';
        html += '<defs><linearGradient id="trendAreaFill" x1="0" y1="0" x2="0" y2="1">' +
            '<stop offset="0%" stop-color="#E4002B" stop-opacity="0.18"/>' +
            '<stop offset="100%" stop-color="#E4002B" stop-opacity="0"/>' +
            "</linearGradient></defs>";

        for (var g = 0; g <= 4; g++) {
            var gv = g * 25;
            var gy = y(gv);
            html += '<line x1="' + PAD_LEFT + '" y1="' + gy.toFixed(1) + '" x2="' + (W - PAD_RIGHT) + '" y2="' + gy.toFixed(1) + '" class="trend-grid"/>';
            html += '<text x="' + (PAD_LEFT - 8) + '" y="' + (gy + 3).toFixed(1) + '" class="trend-axis-label" text-anchor="end">' + gv + "</text>";
        }

        html += '<path d="' + areaPath + '" fill="url(#trendAreaFill)"/>';
        html += '<line x1="' + PAD_LEFT + '" y1="' + avgY.toFixed(1) + '" x2="' + (W - PAD_RIGHT) + '" y2="' + avgY.toFixed(1) + '" class="trend-avg" vector-effect="non-scaling-stroke"/>';
        html += '<path d="' + linePath + '" class="trend-line" fill="none" vector-effect="non-scaling-stroke"/>';

        points.forEach(function (p, i) {
            var s = snapshots[i];
            var latest = i === n - 1;
            var label = formatShortTs(s.ts) + " \u00b7 " + s.compliance_pct + "%";
            html += '<circle cx="' + p[0].toFixed(1) + '" cy="' + p[1].toFixed(1) + '" r="' + (latest ? 4 : 2.6) + '" class="trend-dot' + (latest ? " latest" : "") + '" vector-effect="non-scaling-stroke"><title>' + escapeHtml(label) + "</title></circle>";
        });

        html += "</svg>";
        html += '<div class="trend-labels">';
        snapshots.forEach(function (s, i) {
            if (i === 0 || i === n - 1 || i === Math.floor((n - 1) / 2)) {
                html += '<span class="trend-label">' + escapeHtml(formatShortTs(s.ts)) + "</span>";
            } else {
                html += '<span class="trend-label"></span>';
            }
        });
        html += "</div>";

        el.innerHTML = html;
    }

    // ============================================================
    // MAIN
    // ============================================================

    function applyNetsecData(data) {
        var c = data.compliance || {};
        setSource(c.source);
        renderCompliancePie(c);
        renderSeverityGrid(data.findings || {});
        renderRecentFindings(data.recent_findings || []);
        renderVerticalBars(data.findings_list || []);
        renderTrendStats(data.history || []);
        renderComplianceTrend(data.history || []);
    }

    function load() {
        fetch("/api/dashboard")
            .then(function (r) { return r.json(); })
            .then(function (data) { applyNetsecData(data); })
            .catch(function () { window.showToast("Dashboard data unavailable.", "error"); });
    }

    if (window.showToast) {
        window.showToast("Welcome back, Jeet \u2014 reviewing your security posture.", "success", 5000);
    }

    if (refreshBtn) {
        refreshBtn.addEventListener("click", function () {
            window.showToast("Refreshing dashboard data...");
            load();
        });
    }

    load();
})();
