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
})();
