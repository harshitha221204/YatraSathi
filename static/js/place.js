/* ==========================================
   AOS ANIMATION
========================================== */

AOS.init({
    duration: 1000,
    once: true
});

/* ==========================================
   WEATHER API
========================================== */

// Replace with your OpenWeather API Key
const apiKey = "YOUR_API_KEY";

// Get city name from HTML
const cityElement = document.getElementById("weather-city");

if (cityElement) {

    const city = cityElement.textContent.trim();

    const url =
        `https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric`;

    fetch(url)

        .then(response => response.json())

        .then(data => {

            document.getElementById("temperature").innerHTML =
                `🌡 ${Math.round(data.main.temp)}°C`;

            document.getElementById("weather-condition").innerHTML =
                `☁ ${data.weather[0].main}`;

            document.getElementById("humidity").innerHTML =
                `💧 Humidity : ${data.main.humidity}%`;

            document.getElementById("wind").innerHTML =
                `🌬 Wind : ${data.wind.speed} km/h`;

        })

        .catch(error => {

            document.getElementById("temperature").innerHTML =
                "Weather unavailable";

            document.getElementById("weather-condition").innerHTML = "";

            document.getElementById("humidity").innerHTML = "";

            document.getElementById("wind").innerHTML = "";

            console.log(error);

        });

}

/* ==========================================
   SMOOTH SCROLL
========================================== */

document.querySelectorAll('a[href^="#"]').forEach(anchor => {

    anchor.addEventListener("click", function(e) {

        e.preventDefault();

        const target = document.querySelector(this.getAttribute("href"));

        if (target) {

            target.scrollIntoView({

                behavior: "smooth"

            });

        }

    });

});