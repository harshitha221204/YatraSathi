/* ==========================================
        YatraSathi Explore Page
========================================== */

document.addEventListener("DOMContentLoaded", function () {

    const searchInput = document.getElementById("searchInput");
    const categoryFilter = document.getElementById("categoryFilter");
    const districtFilter = document.getElementById("districtFilter");

    const cards = document.querySelectorAll(".destination-card");

    function filterPlaces() {

        const searchValue = searchInput.value.toLowerCase();
        const categoryValue = categoryFilter.value;
        const districtValue = districtFilter.value;

        cards.forEach(card => {

            const placeName = card.querySelector("h4").textContent.toLowerCase();
            const category = card.getAttribute("data-category");
            const district = card.getAttribute("data-district");

            const searchMatch = placeName.includes(searchValue);

            const categoryMatch =
                categoryValue === "All" || category === categoryValue;

            const districtMatch =
                districtValue === "All" || district === districtValue;

            if (searchMatch && categoryMatch && districtMatch) {

                card.parentElement.style.display = "block";

            } else {

                card.parentElement.style.display = "none";

            }

        });

    }

    searchInput.addEventListener("keyup", filterPlaces);

    categoryFilter.addEventListener("change", filterPlaces);

    districtFilter.addEventListener("change", filterPlaces);

});