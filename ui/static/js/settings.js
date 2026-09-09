(function () {
    "use strict";

    // ---- User accounts (administrators manage; members view name + role) ----

    var usersBody = document.getElementById("usersBody");
    if (!usersBody) return;

    var selfCard = document.getElementById("userAccountsCard");
    var isUsersAdmin = selfCard
        ? selfCard.getAttribute("data-is-admin") === "true"
        : false;
    var selfUserId = selfCard ? (selfCard.getAttribute("data-self-user") || "") : "";
    var pendingChip = document.getElementById("pendingCountChip");

    function chipClass(status) {
        if (status === "pending") return "status-chip status-warn";
        if (status === "rejected" || status === "disabled") return "status-chip status-idle";
        return "status-chip status-on";
    }

    function chipLabel(status) {
        if (status === "disabled") return "Removed";
        return capitalize(status || "approved");
    }

    function renderUsers(users) {
        var pending = 0;
        var rows = users.map(function (user) {
            if (isUsersAdmin) {
                if (user.status === "pending") pending += 1;
                var actions = "";
                if (user.status === "pending") {
                    actions =
                        '<button class="btn btn-sm btn-primary" data-action="approve" data-id="' + user.id + '">Approve</button>' +
                        '<button class="btn btn-sm btn-danger" data-action="reject" data-id="' + user.id + '">Reject</button>';
                } else if (selfUserId && user.id === selfUserId) {
                    actions = '<span class="users-none">This is you</span>';
                } else {
                    actions =
                        '<button class="btn btn-sm btn-danger" data-action="remove" data-id="' + user.id + '">Remove</button>';
                }
                return (
                    "<tr>" +
                    "<td>" + escapeHtml(user.name || "") + "</td>" +
                    "<td>" + escapeHtml(user.email || "") + "</td>" +
                    "<td>" + escapeHtml(user.role || "") + "</td>" +
                    "<td><span class=\"" + chipClass(user.status) + "\">" + escapeHtml(chipLabel(user.status)) + "</span></td>" +
                    "<td class=\"users-actions\">" + actions + "</td>" +
                    "</tr>"
                );
            }
            return (
                "<tr>" +
                "<td>" + escapeHtml(user.name || "") + "</td>" +
                "<td>" + escapeHtml(user.role || "") + "</td>" +
                "</tr>"
            );
        }).join("");

        usersBody.innerHTML = rows ||
            '<tr><td colspan="' + (isUsersAdmin ? 5 : 2) + '" class="users-empty">No accounts yet.</td></tr>';

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
                usersBody.innerHTML = '<tr><td colspan="' + (isUsersAdmin ? 5 : 2) + '" class="users-empty">' + escapeHtml(err.message) + '</td></tr>';
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

    if (isUsersAdmin) {
        usersBody.addEventListener("click", function (event) {
            var button = event.target.closest("[data-action]");
            if (!button) return;
            var action = button.getAttribute("data-action");
            var userId = button.getAttribute("data-id");
            var row = button.closest("tr");
            var userName = row ? row.cells[0].textContent.trim() : "account";

            if (action === "remove") {
                if (!window.confirm(
                    "Remove \"" + userName + "\"? They will no longer be able to sign in. " +
                    "The account and its data are retained in the database but hidden from the platform."
                )) return;
                postJson("/api/admin/users/" + encodeURIComponent(userId) + "/remove")
                    .then(function () {
                        window.showToast("Account removed. Sign-in is disabled.", "success");
                        loadUsers();
                    })
                    .catch(function (err) {
                        window.showToast(err.message, "error");
                    });
                return;
            }

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
    }

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

// ---- Firewall inventory (administrators manage; members view read-only) ----

(function () {
    "use strict";

    var body = document.getElementById("fwInventoryBody");
    if (!body) return;

    var card = document.getElementById("fwInventoryCard");
    var isFwAdmin = card
        ? card.getAttribute("data-is-admin") === "true"
        : false;
    var countChip = document.getElementById("fwCountChip");

    function escapeHtml(value) {
        return String(value == null ? "" : value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function statusHtml(status) {
        var live = status === "live";
        var cls = live ? "live" : "down";
        var label = live ? "Live" : "Down";
        return '<span class="fw-status"><span class="status-dot ' + cls + '"></span>' + label + "</span>";
    }

    function deviceHtml(fw) {
        var name = '<span class="fw-device">' + escapeHtml(fw.device_name || "") + "</span>";
        if (fw.clone_of) {
            name += '<span class="fw-clone-tag">clone of ' + escapeHtml(fw.clone_of) + "</span>";
        }
        return name;
    }

    function renderFirewalls(firewalls) {
        var rows = firewalls.map(function (fw) {
            var cells =
                "<td>" + deviceHtml(fw) + "</td>" +
                "<td class=\"fw-ip\">" + escapeHtml(fw.host_ip || "—") + "</td>" +
                "<td>" + statusHtml(fw.status) + "</td>";
            if (isFwAdmin) {
                var cloneButton = fw.clone_of
                    ? ""
                    : '<button class="btn btn-sm btn-ghost" data-action="clone" data-id="' + fw.id + '">Clone</button>';
                cells +=
                    "<td class=\"users-actions\">" +
                    cloneButton +
                    '<button class="btn btn-sm btn-danger" data-action="remove" data-id="' + fw.id + '">Remove</button>' +
                    "</td>";
            }
            return "<tr data-id=\"" + fw.id + "\">" + cells + "</tr>";
        }).join("");

        body.innerHTML = rows ||
            '<tr><td colspan="' + (isFwAdmin ? 4 : 3) + '" class="users-empty">No firewalls registered yet.</td></tr>';

        if (countChip) countChip.textContent = "Total " + firewalls.length;
    }

    function removeCloneRows() {
        var rows = body.querySelectorAll("tr.fw-clone-row");
        for (var i = 0; i < rows.length; i += 1) rows[i].remove();
    }

    function beginClone(fw, anchorRow) {
        removeCloneRows();
        var tr = document.createElement("tr");
        tr.className = "fw-clone-row";
        tr.setAttribute("data-source-id", fw.id);
        tr.innerHTML =
            '<td colspan="4">' +
            '<div class="fw-clone-form">' +
            '<span class="fw-clone-form-label">Clone of <strong>' + escapeHtml(fw.device_name || "") + "</strong></span>" +
            '<input type="text" class="fw-clone-input" placeholder="Enter a device name for the clone" autocomplete="off" value="' + escapeHtml(fw.device_name + "-clone") + '">' +
            '<button type="button" class="btn btn-sm btn-primary" data-clone-confirm>Clone</button>' +
            '<button type="button" class="btn btn-sm btn-ghost" data-clone-cancel>Cancel</button>' +
            "</div>" +
            "</td>";

        var confirmBtn = tr.querySelector("[data-clone-confirm]");
        var cancelBtn = tr.querySelector("[data-clone-cancel]");
        var input = tr.querySelector(".fw-clone-input");

        confirmBtn.addEventListener("click", function () {
            var name = (input.value || "").trim();
            if (!name) {
                window.showToast("A device name is required to clone.", "error");
                input.focus();
                return;
            }
            confirmBtn.disabled = true;
            postJson("/api/admin/firewalls/" + encodeURIComponent(fw.id) + "/clone", { device_name: name })
                .then(function () {
                    window.showToast("Firewall cloned as " + name + ".", "success");
                    removeCloneRows();
                    loadFirewalls();
                })
                .catch(function (err) {
                    confirmBtn.disabled = false;
                    window.showToast(err.message, "error");
                    input.focus();
                });
        });

        cancelBtn.addEventListener("click", function () {
            removeCloneRows();
        });

        input.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                confirmBtn.click();
            } else if (event.key === "Escape") {
                event.preventDefault();
                removeCloneRows();
            }
        });

        if (anchorRow && anchorRow.nextSibling) {
            anchorRow.parentNode.insertBefore(tr, anchorRow.nextSibling);
        } else {
            body.appendChild(tr);
        }
        input.focus();
        input.select();
    }

    function loadFirewalls() {
        fetch("/api/admin/firewalls", { headers: { "Accept": "application/json" } })
            .then(function (res) { return res.ok ? res.json() : Promise.reject(new Error("Failed to load firewall inventory")); })
            .then(function (data) { renderFirewalls(data.firewalls || []); })
            .catch(function (err) {
                body.innerHTML = '<tr><td colspan="' + (isFwAdmin ? 4 : 3) + '" class="users-empty">' + escapeHtml(err.message) + '</td></tr>';
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

    if (isFwAdmin) {
        body.addEventListener("click", function (event) {
            var button = event.target.closest("[data-action]");
            if (!button) return;
            var action = button.getAttribute("data-action");
            var id = button.getAttribute("data-id");
            var anchorRow = button.closest("tr");
            var deviceName = anchorRow && anchorRow.querySelector(".fw-device")
                ? anchorRow.querySelector(".fw-device").textContent.trim()
                : "";

            if (action === "clone") {
                var firewalls = Array.prototype.map.call(
                    body.querySelectorAll("tr[data-id]"),
                    function (tr) {
                        return {
                            id: tr.getAttribute("data-id"),
                            device_name: tr.querySelector(".fw-device") ? tr.querySelector(".fw-device").textContent.trim() : ""
                        };
                    }
                );
                var fw = null;
                for (var i = 0; i < firewalls.length; i += 1) {
                    if (firewalls[i].id === id) { fw = firewalls[i]; break; }
                }
                if (!fw) return;
                beginClone(fw, anchorRow);
                return;
            }

            if (action === "remove") {
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
            }
        });
    }

    loadFirewalls();
})();
