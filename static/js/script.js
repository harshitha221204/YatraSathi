/* ==========================================================
   YatraSathi shared JavaScript
   Safe on pages even when optional elements/libraries are absent.
========================================================== */

(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        // AOS is optional. Only initialize it when the library exists.
        if (window.AOS && typeof window.AOS.init === "function") {
            window.AOS.init({ duration: 900, once: true });
        }

        // Optional animated counters.
        const counters = document.querySelectorAll(".counter[data-target]");
        counters.forEach(function (counter) {
            const target = Number(counter.dataset.target || 0);
            if (!Number.isFinite(target)) return;

            let value = 0;
            const step = Math.max(1, Math.ceil(target / 80));

            function update() {
                value = Math.min(target, value + step);
                counter.textContent = value + (counter.dataset.suffix || "");
                if (value < target) requestAnimationFrame(update);
            }

            update();
        });

        // Optional scroll reveal.
        const reveals = document.querySelectorAll(".fade-up");
        if (reveals.length && "IntersectionObserver" in window) {
            const observer = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("show");
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.12 });
            reveals.forEach(function (item) { observer.observe(item); });
        }

        // Home search: carry the selected filters to the Explore page.
        const homeSearch = document.getElementById("homeExploreSearch");
        if (homeSearch) {
            homeSearch.addEventListener("click", function (event) {
                event.preventDefault();
                const search = document.getElementById("destinationSearch");
                const district = document.getElementById("districtFilter");
                const category = document.getElementById("categoryFilter");
                const url = new URL(homeSearch.href, window.location.origin);

                if (search && search.value.trim()) url.searchParams.set("q", search.value.trim());
                if (district && district.value) url.searchParams.set("district", district.value);
                if (category && category.value) url.searchParams.set("category", category.value);

                window.location.href = url.toString();
            });
        }

        // Optional loader.
        const loader = document.querySelector(".loader");
        if (loader) loader.style.display = "none";

        // Optional custom navbar scroll state.
        const customNavbar = document.querySelector(".custom-navbar");
        if (customNavbar) {
            function updateNavbar() {
                customNavbar.classList.toggle("scrolled", window.scrollY > 50);
            }
            updateNavbar();
            window.addEventListener("scroll", updateNavbar, { passive: true });
        }

        // Optional scroll-to-top button.
        const topBtn = document.getElementById("topBtn");
        if (topBtn) {
            function updateTopButton() {
                topBtn.style.display = window.scrollY > 300 ? "block" : "none";
            }
            updateTopButton();
            window.addEventListener("scroll", updateTopButton, { passive: true });
        }
    });

    // Kept global for any existing onclick="topFunction()" usage.
    window.topFunction = function () {
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    window.toggleDarkMode = function () {
        document.body.classList.toggle("dark-mode");
    };
})();
