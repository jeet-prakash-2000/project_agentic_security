(function () {
    "use strict";

    document.querySelectorAll(".gen-card .btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var label = btn.textContent.trim();
            window.showToast("Starting " + label.toLowerCase() + " generation...");
        });
    });
})();
