(function () {
    "use strict";

    var sourceBadge = document.getElementById("dataSourceBadge");
    var refreshBtn = document.getElementById("refreshBtn");

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

    function setKpi(id, value, animate) {
        var el = document.getElementById(id);
        if (!el) return;
        if (animate && typeof value === "number") { animateCount(el, value); }
        else { el.textContent = value == null ? "-" : String(value); }
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

        var points = snapshots.map(function (s, i) { return [x(i), y(s.compliance_pct)]; });
        var linePath = "M" + points.map(function (p) { return p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" L");
        var areaPath = linePath + " L" + points[points.length - 1][0].toFixed(1) + " " + (H - PAD_BOTTOM) + " L" + points[0][0].toFixed(1) + " " + (H - PAD_BOTTOM) + " Z";

        var html = '<svg class="trend-line-svg" viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none" role="img" aria-label="Compliance score over time">';
        html += '<defs><linearGradient id="trendAreaFill" x1="0" y1="0" x2="0" y2="1">' +
            '<stop offset="0%" stop-color="#E4002B" stop-opacity="0.18"/>' +
            '<stop offset="100%" stop-color="#E4002B" stop-opacity="0"/>' +
            '</linearGradient></defs>';

        for (var g = 0; g <= 4; g++) {
            var gv = g * 25;
            var gy = y(gv);
            html += '<line x1="' + PAD_LEFT + '" y1="' + gy.toFixed(1) + '" x2="' + (W - PAD_RIGHT) + '" y2="' + gy.toFixed(1) + '" class="trend-grid"/>';
            html += '<text x="' + (PAD_LEFT - 8) + '" y="' + (gy + 3).toFixed(1) + '" class="trend-axis-label" text-anchor="end">' + gv + '</text>';
        }

        html += '<path d="' + areaPath + '" fill="url(#trendAreaFill)"/>';
        html += '<path d="' + linePath + '" class="trend-line" fill="none" vector-effect="non-scaling-stroke"/>';

        points.forEach(function (p, i) {
            var s = snapshots[i];
            var latest = i === n - 1;
            var label = formatShortTs(s.ts) + " \u00b7 " + s.compliance_pct + "%";
            html += '<circle cx="' + p[0].toFixed(1) + '" cy="' + p[1].toFixed(1) + '" r="' + (latest ? 4 : 2.6) + '" class="trend-dot' + (latest ? ' latest' : '') + '" vector-effect="non-scaling-stroke"><title>' + escapeHtml(label) + '</title></circle>';
        });

        html += '</svg>';

        html += '<div class="trend-labels">';
        snapshots.forEach(function (s, i) {
            if (i === 0 || i === n - 1 || i === Math.floor((n - 1) / 2)) {
                html += '<span class="trend-label">' + escapeHtml(formatShortTs(s.ts)) + '</span>';
            } else {
                html += '<span class="trend-label"></span>';
            }
        });
        html += '</div>';

        var latest = snapshots[n - 1];
        var prev = n > 1 ? snapshots[n - 2] : null;
        var change = prev ? Math.round((latest.compliance_pct - prev.compliance_pct) * 10) / 10 : null;
        var dir = change == null ? "\u2014" : (change > 0 ? "Improving" : change < 0 ? "Declining" : "Stable");
        var dirCls = change == null ? "" : (change > 0 ? "good" : change < 0 ? "bad" : "flat");
        var changeText = change == null ? "\u2014" : (change > 0 ? "+" : "") + change + "%";

        html += '<div class="trend-analysis">' +
            '<div class="trend-metric"><span class="trend-metric-label">Current Score</span><span class="trend-metric-value">' + latest.compliance_pct + '%</span></div>' +
            '<div class="trend-metric"><span class="trend-metric-label">Change</span><span class="trend-metric-value ' + dirCls + '">' + changeText + '</span></div>' +
            '<div class="trend-metric"><span class="trend-metric-label">Trend</span><span class="trend-metric-value ' + dirCls + '">' + dir + '</span></div>' +
            '</div>';

        el.innerHTML = html;
    }

    function applyNetsecData(data) {
        var c = data.compliance || {};

        var values = document.querySelectorAll(".kpi-grid .kpi-value[data-count]");
        var keys = ["total_controls", "compliant", "non_compliant", "not_assessed"];
        var targets = keys.map(function (k) {
            var v = c[k]; return v == null ? "-" : Number(v);
        });
        values.forEach(function (el, i) {
            if (typeof targets[i] === "number") animateCount(el, targets[i]);
            else el.textContent = "-";
        });
        setSource(c.source);

        setKpi("kpiComplianceScore", c.compliance_score == null ? "-" : c.compliance_score + "%", false);
        renderComplianceTrend(data.history || []);
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
