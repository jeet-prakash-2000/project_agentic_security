(function () {
    "use strict";

    var nav = document.getElementById("ldNav");
    var menuBtn = document.getElementById("ldMenuBtn");
    var navLinks = document.getElementById("ldNavLinks");

    function onScroll() {
        if (nav) nav.classList.toggle("is-scrolled", (window.scrollY || 0) > 10);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    if (menuBtn && navLinks) {
        menuBtn.addEventListener("click", function () {
            var open = navLinks.classList.toggle("is-open");
            menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
        });
        navLinks.querySelectorAll("a").forEach(function (a) {
            a.addEventListener("click", function () {
                navLinks.classList.remove("is-open");
                if (menuBtn) menuBtn.setAttribute("aria-expanded", "false");
            });
        });
    }

    var tourTabs = document.querySelectorAll(".ld-tour-tab");
    var screens = document.querySelectorAll(".ld-screen");

    function showScreen(name) {
        tourTabs.forEach(function (tab) {
            var active = tab.getAttribute("data-screen") === name;
            tab.classList.toggle("is-active", active);
            tab.setAttribute("aria-selected", active ? "true" : "false");
        });
        screens.forEach(function (screen) {
            screen.classList.toggle("is-active", screen.getAttribute("data-screen") === name);
        });
    }

    tourTabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            showScreen(tab.getAttribute("data-screen"));
        });
    });

    var form = document.getElementById("ldDemoForm");
    if (!form) return;

    var errorBox = document.getElementById("ldDemoError");
    var submitBtn = document.getElementById("ldDemoSubmit");
    var successBox = document.getElementById("ldDemoSuccess");
    var formCard = document.getElementById("demoFormCard");

    function showError(message) {
        if (!errorBox) return;
        errorBox.textContent = message;
        errorBox.hidden = false;
    }

    function clearError() {
        if (errorBox) errorBox.hidden = true;
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        clearError();

        var payload = {
            name: (form.name.value || "").trim(),
            email: (form.email.value || "").trim(),
            company: (form.company.value || "").trim(),
            role: form.role.value || "",
            message: (form.message.value || "").trim()
        };

        if (!payload.name || !payload.email || !payload.message) {
            showError("Please fill in your name, email, and message.");
            return;
        }

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.classList.add("is-loading");
        }

        fetch("/request-demo", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Accept": "application/json" },
            body: JSON.stringify(payload)
        })
            .then(function (res) {
                return res.json().then(function (data) {
                    if (!res.ok) throw new Error(data.error || "Request failed. Please try again.");
                    return data;
                });
            })
            .then(function () {
                form.hidden = true;
                if (successBox) successBox.hidden = false;
                if (formCard) formCard.scrollIntoView({ behavior: "smooth", block: "center" });
            })
            .catch(function (err) {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.classList.remove("is-loading");
                }
                showError(err.message || "Something went wrong. Please try again.");
            });
    });
})();
