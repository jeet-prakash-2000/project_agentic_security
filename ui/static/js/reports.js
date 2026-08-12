(function () {
    "use strict";

    document.querySelectorAll(".gen-card .btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var label = btn.textContent.trim();
            window.showToast("Starting " + label.toLowerCase() + " generation...");
        });
    });

    document.querySelectorAll(".retry-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var row = btn.closest("tr");
            if (!row) return;
            var status = row.querySelector(".status-chip");
            if (!status) return;
            status.className = "status-chip status-warn";
            status.textContent = "Retrying";
            setTimeout(function () {
                status.className = "status-chip status-on";
                status.textContent = "Completed";
            }, 2600);
        });
    });
})();
