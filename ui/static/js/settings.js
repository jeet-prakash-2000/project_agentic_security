(function () {
    "use strict";

    document.querySelectorAll("[data-save]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var label = btn.textContent.trim();
            window.showToast(label + " saved successfully.", "success");
        });
    });

    document.querySelectorAll(".toggle-key").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var target = document.getElementById(btn.getAttribute("data-target"));
            if (!target) return;
            target.type = target.type === "password" ? "text" : "password";
        });
    });

    // ---- User accounts & approvals (administrators only) ----

    var usersBody = document.getElementById("usersBody");
    if (!usersBody) return;

    var pendingChip = document.getElementById("pendingCountChip");

    function chipClass(status) {
        if (status === "pending") return "status-chip status-warn";
        if (status === "rejected" || status === "disabled") return "status-chip status-idle";
        return "status-chip status-on";
    }

    function renderUsers(users) {
        var pending = 0;
        var rows = users.map(function (user) {
            if (user.status === "pending") pending += 1;
            var role = (user.role || "").toLowerCase();
            var selfAdmin = (user.status === "approved") && (
                user.role === "Admin" || user.role === "Administrator"
            );
            var actions = "";
            if (user.status === "pending") {
                actions =
                    '<button class="btn btn-sm btn-primary" data-action="approve" data-id="' + user.id + '">Approve</button>' +
                    '<button class="btn btn-sm btn-danger" data-action="reject" data-id="' + user.id + '">Reject</button>';
            } else if (selfAdmin) {
                actions = '<span class="users-none">Administrator</span>';
            } else if (role !== "admin" && role !== "administrator") {
                actions =
                    '<button class="btn btn-sm btn-ghost" data-action="approve" data-id="' + user.id + '">Re-enable</button>';
            }
            return (
                "<tr>" +
                "<td>" + escapeHtml(user.name || "") + "</td>" +
                "<td>" + escapeHtml(user.email || "") + "</td>" +
                "<td>" + escapeHtml(user.role || "") + "</td>" +
                "<td><span class=\"" + chipClass(user.status) + "\">" + escapeHtml(capitalize(user.status || "approved")) + "</span></td>" +
                "<td class=\"users-actions\">" + actions + "</td>" +
                "</tr>"
            );
        }).join("");

        usersBody.innerHTML = rows ||
            '<tr><td colspan="5" class="users-empty">No accounts yet.</td></tr>';

        if (pendingChip) pendingChip.textContent = "Pending " + pending;
    }

    function capitalize(value) {
        return value.charAt(0).toUpperCase() + value.slice(1);
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function loadUsers() {
        fetch("/api/admin/users", { headers: { "Accept": "application/json" } })
            .then(function (res) { return res.ok ? res.json() : Promise.reject(new Error("Failed to load accounts")); })
            .then(function (data) { renderUsers(data.users || []); })
            .catch(function (err) {
                usersBody.innerHTML = '<tr><td colspan="5" class="users-empty">' + escapeHtml(err.message) + '</td></tr>';
            });
    }

    function postJson(url, payload) {
        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Accept": "application/json" },
            body: JSON.stringify(payload || {})
        }).then(function (res) {
            return res.json().then(function (data) {
                if (!res.ok) throw new Error(data.error || "Request failed");
                return data;
            });
        });
    }

    usersBody.addEventListener("click", function (event) {
        var button = event.target.closest("[data-action]");
        if (!button) return;
        var action = button.getAttribute("data-action");
        var userId = button.getAttribute("data-id");
        var verb = action === "approve" ? "approve" : "reject";
        postJson("/api/admin/users/" + encodeURIComponent(userId) + "/" + verb)
            .then(function () {
                window.showToast("Account " + verb + "d.", "success");
                loadUsers();
            })
            .catch(function (err) {
                window.showToast(err.message, "error");
            });
    });

    var inviteBtn = document.getElementById("inviteBtn");
    if (inviteBtn) {
        inviteBtn.addEventListener("click", function () {
            var name = (document.getElementById("inviteName").value || "").trim();
            var email = (document.getElementById("inviteEmail").value || "").trim();
            var password = document.getElementById("invitePassword").value || "";
            var role = document.getElementById("inviteRole").value || "Security Analyst";

            if (!name || !email || !password) {
                window.showToast("Name, email, and password are required.", "error");
                return;
            }
            postJson("/api/admin/users", { name: name, email: email, password: password, role: role })
                .then(function () {
                    window.showToast("Account created and approved.", "success");
                    document.getElementById("inviteName").value = "";
                    document.getElementById("inviteEmail").value = "";
                    document.getElementById("invitePassword").value = "";
                    loadUsers();
                })
                .catch(function (err) {
                    window.showToast(err.message, "error");
                });
        });
    }

    loadUsers();
})();

// ---- Firewall inventory (administrators only) ----

(function () {
    "use strict";

    var body = document.getElementById("fwInventoryBody");
    if (!body) return;

    var countChip = document.getElementById("fwCountChip");

    function escapeHtml(value) {
        return String(value == null ? "" : value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function formatDate(ts) {
        if (!ts) return "—";
        try {
            return new Date(ts * 1000).toISOString().slice(0, 10);
        } catch (err) {
            return "—";
        }
    }

    function renderFirewalls(firewalls) {
        var rows = firewalls.map(function (fw) {
            var key = fw.host_key
                ? '<span class="fw-key-masked">' + escapeHtml(fw.host_key) + "</span>"
                : '<span class="users-none">—</span>';
            return (
                "<tr>" +
                "<td class=\"fw-device\">" + escapeHtml(fw.device_name || "") + "</td>" +
                "<td>" + escapeHtml(fw.host_name || "") + "</td>" +
                "<td>" + escapeHtml(fw.host_ip || "") + "</td>" +
                "<td>" + key + "</td>" +
                "<td>" + formatDate(fw.created) + "</td>" +
                "<td class=\"users-actions\"><button class=\"btn btn-sm btn-danger\" data-action=\"remove\" data-id=\"" + fw.id + "\">Remove</button></td>" +
                "</tr>"
            );
        }).join("");

        body.innerHTML = rows ||
            '<tr><td colspan="6" class="users-empty">No firewalls registered yet.</td></tr>';

        if (countChip) countChip.textContent = "Total " + firewalls.length;
    }

    function loadFirewalls() {
        fetch("/api/admin/firewalls", { headers: { "Accept": "application/json" } })
            .then(function (res) { return res.ok ? res.json() : Promise.reject(new Error("Failed to load firewall inventory")); })
            .then(function (data) { renderFirewalls(data.firewalls || []); })
            .catch(function (err) {
                body.innerHTML = '<tr><td colspan="6" class="users-empty">' + escapeHtml(err.message) + '</td></tr>';
            });
    }

    function postJson(url, payload) {
        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Accept": "application/json" },
            body: JSON.stringify(payload || {})
        }).then(function (res) {
            return res.json().then(function (data) {
                if (!res.ok) throw new Error(data.error || "Request failed");
                return data;
            });
        });
    }

    var addBtn = document.getElementById("fwAddBtn");
    if (addBtn) {
        addBtn.addEventListener("click", function () {
            var deviceName = (document.getElementById("fwDeviceName").value || "").trim();
            var hostName = (document.getElementById("fwHostName").value || "").trim();
            var hostIp = (document.getElementById("fwHostIp").value || "").trim();
            var hostKey = document.getElementById("fwHostKey").value || "";

            if (!deviceName || !hostName || !hostIp || !hostKey) {
                window.showToast("Device name, host name, host IP, and host key are required.", "error");
                return;
            }
            postJson("/api/admin/firewalls", {
                device_name: deviceName,
                host_name: hostName,
                host_ip: hostIp,
                host_key: hostKey
            }).then(function () {
                window.showToast("Firewall added to the inventory.", "success");
                document.getElementById("fwDeviceName").value = "";
                document.getElementById("fwHostName").value = "";
                document.getElementById("fwHostIp").value = "";
                document.getElementById("fwHostKey").value = "";
                loadFirewalls();
            }).catch(function (err) {
                window.showToast(err.message, "error");
            });
        });
    }

    body.addEventListener("click", function (event) {
        var button = event.target.closest("[data-action]");
        if (!button || button.getAttribute("data-action") !== "remove") return;
        var id = button.getAttribute("data-id");
        var deviceName = button.closest("tr").cells[0].textContent.trim();

        if (!window.confirm("Remove \"" + deviceName + "\" from the firewall inventory?")) return;

        fetch("/api/admin/firewalls/" + encodeURIComponent(id), { method: "DELETE" })
            .then(function (res) {
                return res.json().then(function (data) {
                    if (!res.ok) throw new Error(data.error || "Request failed");
                    return data;
                });
            })
            .then(function () {
                window.showToast("Firewall removed from the inventory.", "success");
                loadFirewalls();
            })
            .catch(function (err) {
                window.showToast(err.message, "error");
            });
    });

    loadFirewalls();
})();
