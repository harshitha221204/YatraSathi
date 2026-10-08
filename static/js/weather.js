const destination =
    document.getElementById("destination");

const weatherButton =
    document.getElementById("weatherButton");

const weatherResult =
    document.getElementById("weatherResult");

const loading =
    document.getElementById("loading");

const errorMessage =
    document.getElementById("errorMessage");


weatherButton.addEventListener(
    "click",
    loadWeather
);


async function loadWeather() {

    const place =
        destination.value;


    errorMessage.textContent = "";


    if (!place) {

        errorMessage.textContent =
            "Please select a destination.";

        return;
    }


    weatherResult.classList.add(
        "hidden"
    );


    loading.classList.remove(
        "hidden"
    );


    weatherButton.disabled = true;


    try {

        const response = await fetch(
            `/api/weather/${encodeURIComponent(place)}`
        );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Unable to get weather."
            );
        }


        showWeather(
            data.weather
        );

    }

    catch (error) {

        console.error(
            "Weather error:",
            error
        );


        errorMessage.textContent =
            error.message ||
            "Unable to load live weather.";

    }

    finally {

        loading.classList.add(
            "hidden"
        );


        weatherButton.disabled = false;

    }

}



function showWeather(weather) {

    document.getElementById(
        "placeName"
    ).textContent =
        weather.place;


    document.getElementById(
        "weatherIcon"
    ).textContent =
        weather.icon;


    document.getElementById(
        "temperature"
    ).textContent =
        weather.temperature ?? "--";


    document.getElementById(
        "condition"
    ).textContent =
        weather.condition;


    document.getElementById(
        "feelsLike"
    ).textContent =
        weather.feels_like ?? "--";


    document.getElementById(
        "humidity"
    ).textContent =
        `${weather.humidity ?? "--"}%`;


    document.getElementById(
        "precipitation"
    ).textContent =
        `${weather.precipitation ?? "--"} mm`;


    document.getElementById(
        "windSpeed"
    ).textContent =
        `${weather.wind_speed ?? "--"} km/h`;


    document.getElementById(
        "updatedTime"
    ).textContent =
        weather.updated
        ? `Updated: ${formatDateTime(weather.updated)}`
        : "Updated now";


    createForecast(
        weather.forecast || []
    );


    weatherResult.classList.remove(
        "hidden"
    );


    weatherResult.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}



function createForecast(forecast) {

    const container =
        document.getElementById(
            "forecastContainer"
        );


    container.innerHTML = "";


    forecast.forEach(
        (day, index) => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "forecast-card";


            const dayName =
                index === 0
                ? "Today"
                : formatDay(
                    day.date
                );


            card.innerHTML = `

                <p class="day">
                    ${dayName}
                </p>

                <div class="forecast-icon">
                    ${day.icon}
                </div>

                <p class="forecast-condition">
                    ${day.condition}
                </p>

                <p class="forecast-temp">

                    ${Math.round(day.max)}°C

                    <span class="forecast-min">
                        /
                        ${Math.round(day.min)}°C
                    </span>

                </p>

                <p class="rain-chance">
                    💧 ${day.rain_chance ?? 0}% rain
                </p>
            `;


            container.appendChild(
                card
            );

        }
    );

}



function formatDay(dateString) {

    const date =
        new Date(
            `${dateString}T00:00:00`
        );


    return date.toLocaleDateString(
        "en-IN",
        {
            weekday: "short"
        }
    );

}



function formatDateTime(dateString) {

    const date =
        new Date(
            dateString
        );


    return date.toLocaleString(
        "en-IN",
        {
            dateStyle: "medium",
            timeStyle: "short"
        }
    );

}