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
