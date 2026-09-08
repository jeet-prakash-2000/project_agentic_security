/* NetSec Execution Agent panel - playbook-driven firewall changes.
 * Activated by workspace.js whenever the NetSec-Execution-Agent is selected.
 * Talks to the /api/netsec/* endpoints (see app.py + netsec_service.py). */
(function () {
    "use strict";

    var NETSEC_AGENT_ID = "netsec-execution-agent";
    var els = {};
    var state = { info: null, uploaded: null };
    var bound = false;

    function q(id) { return document.getElementById(id); }

    function grab() {
        els.panel = q("wsNetsecPanel");
        els.badge = q("netsecBadge");
        els.connAlert = q("netsecConnAlert");
        els.modeAlert = q("netsecModeAlert");
        els.downloadBtn = q("netsecDownloadBtn");
        els.file = q("netsecFile");
        els.uploadBtn = q("netsecUploadBtn");
        els.summaryBox = q("netsecWorkbookSummary");
        els.playbookSelect = q("netsecPlaybookSelect");
        els.runBtn = q("netsecRunBtn");
        els.runNote = q("netsecRunNote");
        els.results = q("netsecRunResults");
    }

    function esc(value) {
        return String(value == null ? "" : value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function badge(stateName, label) {
        if (!els.badge) return;
        els.badge.setAttribute("data-state", stateName);
        els.badge.textContent = label;
    }

    function setAlert(node, html) {
        if (!node) return;
        if (html) { node.innerHTML = html; node.hidden = false; }
        else { node.innerHTML = ""; node.hidden = true; }
    }

    function toast(msg, kind) {
        if (window.showToast) window.showToast(msg, kind || "error");
    }

    /* ------------------------------------------------------------ */

    function loadInfo() {
        badge("unknown", "Checking connection\u2026");
        fetch("/api/netsec/info")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data && data.error) { setAlert(els.connAlert, esc(data.error)); badge("down", "Unavailable"); return; }
                state.info = data;
                renderConnection(data);
                renderPlaybooks(data);
                loadWorkbook();
            })
            .catch(function () {
                badge("down", "Unavailable");
                setAlert(els.connAlert, "Could not reach the NetSec service. Try again.");
            });
    }

    function renderConnection(info) {
        if (info.configured) {
            badge("ok", "Connected \u00b7 " + (info.host || ""));
            setAlert(els.connAlert, "");
            if (info.dry_run) {
                setAlert(els.modeAlert, "<strong>Dry-run mode is ON.</strong> Running a playbook previews every change without sending anything to the firewall. To apply changes, deploy with <code>NETSEC_FW_DRY_RUN=0</code>.");
            } else {
                setAlert(els.modeAlert, "<strong>Apply mode is ON</strong> (<code>NETSEC_FW_DRY_RUN=0</code>) - running a playbook writes changes to the firewall candidate configuration.");
            }
        } else {
            badge("down", "Not connected");
            setAlert(els.connAlert, "<strong>Firewall not configured.</strong> The platform is missing <code>" + (info.missing || []).map(esc).join("</code>, <code>") + "</code>. Set these environment variables on the App Service, then reload this page.");
            setAlert(els.modeAlert, "");
        }
        renderRunNote();
    }

    function renderPlaybooks(info) {
        if (!els.playbookSelect) return;
        els.playbookSelect.innerHTML = "";
        if (!info.playbooks || !info.playbooks.length) {
            var none = document.createElement("option");
            none.textContent = "No playbooks available";
            els.playbookSelect.appendChild(none);
            return;
        }
        var groups = {};
        info.playbooks.forEach(function (pb) {
            (groups[pb.category || "Playbooks"] = groups[pb.category || "Playbooks"] || []).push(pb);
        });
        Object.keys(groups).forEach(function (category) {
            var og = document.createElement("optgroup");
            og.label = category;
            groups[category].forEach(function (pb) {
                var opt = document.createElement("option");
                opt.value = pb.id;
                opt.textContent = pb.title + " (" + pb.sheet + ")";
                og.appendChild(opt);
            });
            els.playbookSelect.appendChild(og);
        });
        els.playbookSelect.addEventListener("change", function () { renderRunNote(); });
    }

    function renderRunNote() {
        if (!els.runNote) return;
        var info = state.info;
        var pb = selectedPlaybook();
        var parts = [];
        if (info && info.dry_run) parts.push("DRY RUN - nothing will be written to the firewall.");
        if (pb && pb.sheet) parts.push("Executes sheet \u201c" + pb.sheet + "\u201d.");
        if (pb && pb.summary) parts.push(pb.summary);
        els.runNote.textContent = parts.join(" ");
        if (els.runBtn) els.runBtn.disabled = !(state.uploaded && selectedPlaybook());
    }

    function selectedPlaybook() {
        if (!els.playbookSelect || !state.info) return null;
        var id = els.playbookSelect.value;
        if (!id) return null;
        for (var i = 0; i < state.info.playbooks.length; i++) {
            if (state.info.playbooks[i].id === id) return state.info.playbooks[i];
        }
        return null;
    }

    /* ------------------------------------------------------------ */

    function loadWorkbook() {
        fetch("/api/netsec/workbook")
            .then(function (r) { return r.status === 404 ? null : r.json(); })
            .then(function (data) {
                if (data && data.summary) { state.uploaded = data.summary; renderWorkbookSummary(data.summary); }
                else { state.uploaded = null; renderWorkbookSummary(null); }
                renderRunNote();
            })
            .catch(function () { state.uploaded = null; renderWorkbookSummary(null); });
    }

    function renderWorkbookSummary(summary) {
        if (!els.summaryBox) return;
        if (!summary || !summary.sheets || !summary.sheets.length) {
            els.summaryBox.innerHTML = "";
            return;
        }
        var html = '<div class="netsec-wb-summary"><span class="netsec-wb-total">' +
            esc(summary.total_rows) + " data row" + (summary.total_rows === 1 ? "" : "s") +
            " loaded from " + esc(summary.sheets.length) + " sheet" + (summary.sheets.length === 1 ? "" : "s") +
            '</span><ul class="netsec-wb-sheets">';
        summary.sheets.forEach(function (sheet) {
            html += "<li><span class=\"netsec-wb-sheet\">" + esc(sheet.sheet) + "</span>" +
                "<span class=\"netsec-wb-count\">" + esc(sheet.rows) + " row" + (sheet.rows === 1 ? "" : "s") + "</span></li>";
        });
        html += "</ul></div>";
        els.summaryBox.innerHTML = html;
    }

    /* ------------------------------------------------------------ */

    function downloadTemplate() {
        if (!els.downloadBtn) return;
        els.downloadBtn.disabled = true;
        var original = els.downloadBtn.textContent;
        els.downloadBtn.textContent = "Preparing\u2026";
        fetch("/api/netsec/workbook/template")
            .then(function (r) {
                if (!r.ok) throw new Error("HTTP " + r.status);
                return r.blob();
            })
            .then(function (blob) {
                var url = URL.createObjectURL(blob);
                var a = document.createElement("a");
                a.href = url;
                a.download = "netsec-playbook-template.xlsx";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
                toast("Template downloaded - open it in Excel.", "success");
            })
            .catch(function () { toast("Could not download the template."); })
            .finally(function () {
                els.downloadBtn.disabled = false;
                els.downloadBtn.textContent = original;
            });
    }

    function uploadWorkbook() {
        var file = els.file && els.file.files && els.file.files[0];
        if (!file) { toast("Choose a workbook file first."); return; }
        if (els.uploadBtn) { els.uploadBtn.disabled = true; els.uploadBtn.textContent = "Uploading\u2026"; }
        var fd = new FormData();
        fd.append("file", file);
        fetch("/api/netsec/workbook", { method: "POST", body: fd })
            .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
            .then(function (res) {
                if (!res.ok) throw new Error(res.data.error || "Upload failed");
                state.uploaded = res.data.summary;
                renderWorkbookSummary(res.data.summary);
                renderRunNote();
                toast("Workbook uploaded.", "success");
            })
            .catch(function (err) { toast(err.message || "Upload failed."); })
            .finally(function () {
                if (els.uploadBtn) { els.uploadBtn.disabled = false; els.uploadBtn.textContent = "Upload workbook"; }
            });
    }

    /* ------------------------------------------------------------ */

    function runPlaybook() {
        var pb = selectedPlaybook();
        if (!pb) return;
        if (els.runBtn) { els.runBtn.disabled = true; els.runBtn.textContent = "Running\u2026"; }
        if (els.results) els.results.innerHTML = '<div class="netsec-loading">Executing ' + esc(pb.title) + "\u2026</div>";

        fetch("/api/netsec/playbooks/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ playbook_id: pb.id })
        })
            .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
            .then(function (res) {
                if (!res.ok) throw new Error(res.data.error || "Run failed");
                renderRunResults(res.data);
            })
            .catch(function (err) {
                if (els.results) els.results.innerHTML = "";
                toast(err.message || "Playbook run failed.");
            })
            .finally(function () {
                if (els.runBtn) { els.runBtn.textContent = "Run playbook"; renderRunNote(); }
            });
    }

    function renderRunResults(data) {
        if (!els.results) return;
        var c = data.counts || {};
        var dry = !!data.dry_run;
        var cards = [];
        var badgeClass = dry ? "netsec-ok" : (c.errors ? "netsec-partial" : "netsec-ok");
        cards.push(
            '<div class="netsec-result-card">',
            '<div class="netsec-result-head"><span class="netsec-result-title">' + esc(data.playbook_title || data.playbook_id) + "</span>",
            '<span class="netsec-pill ' + badgeClass + '">' + (dry ? "Dry-run" : "Applied") + "</span></div>",
            '<div class="netsec-result-counts">',
            countChip(c.created, "created", dry), countChip(c.updated, "updated", dry),
            countChip(c.deleted, "deleted", dry), countChip(c.errors, "errors", true),
            "</div>",
            "<p class=\"netsec-result-summary\">" + esc(data.summary || "") + "</p>",
            (data.host ? '<p class="netsec-result-meta">Firewall: ' + esc(data.host) + "</p>" : ""),
            "</div>"
        );
        var rows = data.rows || [];
        if (rows.length) {
            var thead = "<tr><th>Row</th><th>Op</th><th>Object</th><th>Detail</th></tr>";
            var body = rows.map(function (row) {
                var op = row.op === "error" ? "error" : (row.dry_run ? "dry-run" : row.op);
                var name = row.error ? "Error" : (row.kind ? row.kind : "");
                var detail = row.error || row.detail || "";
                return "<tr><td>" + esc(row.row) + "</td>" +
                    "<td><span class=\"netsec-op netsec-op-" + op + "\">" + esc(op) + "</span></td>" +
                    "<td>" + esc(name) + (row.name ? " <code>" + esc(row.name) + "</code>" : "") + "</td>" +
                    "<td class=\"netsec-cell-detail\">" + esc(detail) + "</td></tr>";
            }).join("");
            cards.push('<div class="netsec-results-table"><table><thead>' + thead + "</thead><tbody>" + body + "</tbody></table></div>");
        }
        els.results.innerHTML = cards.join("");
    }

    function countChip(n, label, emphasise) {
        n = n || 0;
        return '<span class="netsec-count' + (emphasise && n ? " netsec-count-warn" : "") + '">' + n + " " + label + "</span>";
    }

    /* ------------------------------------------------------------ */

    function activate() {
        grab();
        if (!els.panel) return;
        state = { info: null, uploaded: null };
        loadInfo();
        if (!bound) {
            bound = true;
            els.downloadBtn.addEventListener("click", downloadTemplate);
            els.uploadBtn.addEventListener("click", uploadWorkbook);
            if (els.file) els.file.addEventListener("change", function () {
                els.uploadBtn.disabled = !(els.file.files && els.file.files[0]);
            });
            els.runBtn.addEventListener("click", runPlaybook);
        }
    }

    function isNetsecId(id) {
        return id === NETSEC_AGENT_ID;
    }

    function isNetsecAgent(agent) {
        if (!agent) return false;
        var text = String(agent.id || "") + " " + String(agent.name || "") + " " + String(agent.type || "");
        return isNetsecId(agent.id) || /netsec/i.test(text);
    }

    window.NetsecPanel = {
        agentId: NETSEC_AGENT_ID,
        isNetsecAgent: isNetsecAgent,
        activate: activate
    };
})();
