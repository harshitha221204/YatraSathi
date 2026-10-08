from flask import (

    Flask,

    render_template,

    request,

    redirect,

    url_for,

    session,

    jsonify

)

import json

import os

import sqlite3

import time

from urllib.parse import quote_plus, urlencode

from urllib.request import Request, urlopen



from google import genai

from dotenv import load_dotenv

from werkzeug.security import check_password_hash, generate_password_hash



from stories import stories

from places import places



from database import (

    get_db_connection,

    create_users_table,

    create_trips_table

)





# ============================================================

# LOAD ENVIRONMENT VARIABLES

# ============================================================



load_dotenv()





# ============================================================

# FLASK APP

# ============================================================



app = Flask(__name__)



app.secret_key = os.getenv(

    "FLASK_SECRET_KEY",

    "yatrasathi_secret_key"

)





# ============================================================

# DATABASE

# ============================================================



create_users_table()

create_trips_table()





# ============================================================

# GEMINI SETUP

# ============================================================



GEMINI_API_KEY = os.getenv(

    "GEMINI_API_KEY"

)



client = None





if GEMINI_API_KEY:



    try:



        client = genai.Client(

            api_key=GEMINI_API_KEY

        )



        print(

            "Gemini client configured successfully."

        )



    except Exception as e:



        print(

            "Gemini configuration error:"

        )



        print(e)



else:



    print(

        "WARNING: GEMINI_API_KEY not found."

    )





# ============================================================

# GEMINI MODELS

# ============================================================



GEMINI_MODELS = [



    os.getenv(

        "GEMINI_MODEL",

        "gemini-3.8-flash"

    ),



    # Stable fallbacks. Flash-Lite is useful when the main

    # model is temporarily busy or rate-limited.

    "gemini-3.6-flash",

    "gemini-3.5-flash-lite",

    "gemini-3.5-flash",

    "gemini-3.1-flash-lite"

]





# Remove duplicate model names



GEMINI_MODELS = list(

    dict.fromkeys(

        GEMINI_MODELS

    )

)





# ============================================================

# ASK GEMINI

# ============================================================



def ask_gemini(prompt):



    if client is None:



        raise RuntimeError(

            "Gemini API key is not configured."

        )





    last_error = None





    # Try available Gemini models



    for model_name in GEMINI_MODELS:





        # Retry each model once



        for attempt in range(2):



            try:



                print(

                    "Sending request to Gemini:",

                    model_name

                )





                interaction = (

                    client.interactions.create(



                        model=model_name,



                        input=prompt

                    )

                )





                reply = getattr(

                    interaction,

                    "output_text",

                    None

                )





                if not reply:



                    raise RuntimeError(

                        "Gemini returned an empty response."

                    )





                print(

                    "Gemini response received from:",

                    model_name

                )





                return reply.strip()





            except Exception as e:



                last_error = e





                error_text = (

                    str(e).lower()

                )





                print(

                    "Gemini model failed:",

                    model_name

                )



                print(

                    type(e).__name__

                )



                print(

                    str(e)

                )





                temporary_error = any(



                    text in error_text



                    for text in [



                        "503",



                        "unavailable",



                        "high demand",



                        "429",



                        "quota",



                        "resource_exhausted",



                        "deadline",



                        "timeout"

                    ]

                )





                # Retry once



                if (

                    temporary_error

                    and

                    attempt == 0

                ):



                    print(

                        "Temporary Gemini error. Retrying..."

                    )



                    time.sleep(2)



                    continue





                # Try next model



                break





    if last_error:



        raise last_error





    raise RuntimeError(

        "Gemini could not generate a response."

    )





# ============================================================

# DESTINATION ALIASES

# ============================================================



DESTINATION_ALIASES = {





    # Hampi



    "hampi": "Hampi",



    "ಹಂಪಿ": "Hampi",



    "हम्पी": "Hampi",





    # Mysuru



    "mysuru": "Mysuru",



    "mysore": "Mysuru",



    "ಮೈಸೂರು": "Mysuru",



    "मैसूर": "Mysuru",





    # Coorg



    "coorg": "Coorg",



    "kodagu": "Coorg",



    "ಕೊಡಗು": "Coorg",



    "कूर्ग": "Coorg",





    # Gokarna



    "gokarna": "Gokarna",



    "ಗೋಕರ್ಣ": "Gokarna",



    "गोकर्ण": "Gokarna",





    # Chikmagalur



    "chikmagalur": "Chikmagalur",



    "chikkamagaluru":

        "Chikmagalur",



    "ಚಿಕ್ಕಮಗಳೂರು":

        "Chikmagalur",



    "चिकमगलूर":

        "Chikmagalur",





    # Shivamogga



    "shivamogga":

        "Shivamogga",



    "shimoga":

        "Shivamogga",



    "ಶಿವಮೊಗ್ಗ":

        "Shivamogga",



    "शिवमोग्गा":

        "Shivamogga",





    # Udupi



    "udupi": "Udupi",



    "ಉಡುಪಿ": "Udupi",



    "उडुपी": "Udupi",





    # Badami



    "badami": "Badami",



    "ಬಾದಾಮಿ": "Badami",



    "बादामी": "Badami",





    # Bengaluru



    "bengaluru":

        "Bengaluru",



    "bangalore":

        "Bengaluru",



    "ಬೆಂಗಳೂರು":

        "Bengaluru",



    "बेंगलुरु":

        "Bengaluru",





    # Mangaluru



    "mangaluru":

        "Mangaluru",



    "mangalore":

        "Mangaluru",



    "ಮಂಗಳೂರು":

        "Mangaluru",



    "मंगलुरु":

        "Mangaluru"

}





# ============================================================

# FIND DESTINATION

# ============================================================



def find_destination(message):



    if not message:



        return None, None





    message_lower = (

        message.lower().strip()

    )





    # --------------------------------------------------------

    # CHECK ALL DESTINATIONS FROM places.py

    # --------------------------------------------------------



    # Longer names are checked first.



    sorted_places = sorted(



        places.keys(),



        key=len,



        reverse=True

    )





    for place_name in sorted_places:



        if (

            place_name.lower()

            in message_lower

        ):



            return (

                place_name,

                places[place_name]

            )





    # --------------------------------------------------------

    # CHECK ALIASES

    # --------------------------------------------------------



    sorted_aliases = sorted(



        DESTINATION_ALIASES.items(),



        key=lambda item: len(

            item[0]

        ),



        reverse=True

    )





    for alias, actual_name in sorted_aliases:



        if (

            alias.lower()

            in message_lower

        ):



            place_data = places.get(

                actual_name

            )





            if place_data:



                return (

                    actual_name,

                    place_data

                )





    return None, None





# ============================================================

# SAFE LIST TO TEXT

# ============================================================



def list_to_text(value):



    if not value:



        return "Not available"





    if isinstance(

        value,

        (list, tuple)

    ):



        return ", ".join(



            str(item)



            for item in value

        )





    return str(value)





# ============================================================

# CREATE DESTINATION CONTEXT

# ============================================================



def create_place_context(

    place_name,

    place_data

):





    if not place_data:



        return (

            "No matching destination was found "

            "in the YatraSathi database."

        )





    district = place_data.get(

        "district",

        "Not available"

    )





    category = place_data.get(

        "category",

        "Not available"

    )





    description = place_data.get(

        "description",

        "Not available"

    )





    best_time = place_data.get(

        "best_time",

        "Not available"

    )





    duration = place_data.get(

        "duration",

        "Not available"

    )





    entry_fee = place_data.get(

        "entry_fee",

        "Not available"

    )





    rating = place_data.get(

        "rating",

        "Not available"

    )





    estimated_budget = place_data.get(

        "budget",

        "Not available"

    )





    nearby_places = list_to_text(



        place_data.get(

            "nearby_places"

        )

    )





    things_to_do = list_to_text(



        place_data.get(

            "things_to_do"

        )

    )





    travel_tips = list_to_text(



        place_data.get(

            "travel_tips"

        )

    )





    why_visit = list_to_text(



        place_data.get(

            "why_visit"

        )

    )





    return f"""



YATRASATHI DESTINATION DATA



Destination:

{place_name}



District:

{district}



Category:

{category}



Description:

{description}



Best Time:

{best_time}



Suggested Duration:

{duration}



Entry Fee:

{entry_fee}



Rating:

{rating}



Estimated Budget:

{estimated_budget}



Nearby Places:

{nearby_places}



Things To Do:

{things_to_do}



Travel Tips:

{travel_tips}



Why Visit:

{why_visit}



""".strip()





# ============================================================

# WEATHER CODE

# ============================================================



def weather_code_to_text(code):





    weather_codes = {





        0: "Clear sky",



        1: "Mainly clear",



        2: "Partly cloudy",



        3: "Overcast",



        45: "Fog",



        48: "Rime fog",



        51: "Light drizzle",



        53: "Drizzle",



        55: "Heavy drizzle",



        56:

            "Light freezing drizzle",



        57:

            "Heavy freezing drizzle",



        61: "Light rain",



        63: "Rain",



        65: "Heavy rain",



        66:

            "Light freezing rain",



        67:

            "Heavy freezing rain",



        71: "Light snow",



        73: "Snow",



        75: "Heavy snow",



        77: "Snow grains",



        80:

            "Light rain showers",



        81:

            "Rain showers",



        82:

            "Heavy rain showers",



        85:

            "Light snow showers",



        86:

            "Heavy snow showers",



        95:

            "Thunderstorm",



        96:

            "Thunderstorm with light hail",



        99:

            "Thunderstorm with heavy hail"

    }





    try:



        return weather_codes.get(



            int(code),



            "Unknown"

        )





    except (

        TypeError,

        ValueError

    ):



        return "Unknown"





# ============================================================

# FETCH JSON

# ============================================================



def fetch_json(url):





    request_object = Request(



        url,



        headers={



            "User-Agent":

                "YatraSathi/1.0"

        }

    )





    with urlopen(

        request_object,

        timeout=10

    ) as response:





        data = response.read()





        return json.loads(

            data.decode("utf-8")

        )





# ============================================================

# GET LIVE WEATHER

# ============================================================



def get_live_weather(place_name):





    try:





        # ----------------------------------------------------

        # GEOCODING

        # ----------------------------------------------------



        geo_params = urlencode({



            "name":

                f"{place_name}, Karnataka",



            "count":

                1,



            "language":

                "en",



            "format":

                "json"

        })





        geo_url = (



            "https://geocoding-api.open-meteo.com/"

            "v1/search?"



            + geo_params

        )





        geo_data = fetch_json(

            geo_url

        )





        results = (

            geo_data.get("results")

            or []

        )





        # ----------------------------------------------------

        # SECOND SEARCH

        # ----------------------------------------------------



        if not results:





            geo_params = urlencode({



                "name":

                    place_name,



                "count":

                    5,



                "language":

                    "en",



                "format":

                    "json"

            })





            geo_url = (



                "https://geocoding-api.open-meteo.com/"

                "v1/search?"



                + geo_params

            )





            geo_data = fetch_json(

                geo_url

            )





            candidates = (

                geo_data.get("results")

                or []

            )





            # Prefer Karnataka



            karnataka_results = [



                item



                for item in candidates



                if str(

                    item.get(

                        "admin1",

                        ""

                    )

                ).lower()

                == "karnataka"

            ]





            results = (

                karnataka_results

                or

                candidates

            )





        if not results:



            return None





        location = results[0]





        latitude = location[

            "latitude"

        ]





        longitude = location[

            "longitude"

        ]





        # ----------------------------------------------------

        # WEATHER REQUEST

        # ----------------------------------------------------



        current_values = (



            "temperature_2m,"

            "apparent_temperature,"

            "relative_humidity_2m,"

            "precipitation,"

            "weather_code,"

            "wind_speed_10m"

        )





        weather_params = urlencode({



            "latitude":

                latitude,



            "longitude":

                longitude,



            "current":

                current_values,



            "timezone":

                "auto"

        })





        weather_url = (



            "https://api.open-meteo.com/"

            "v1/forecast?"



            + weather_params

        )





        weather_data = fetch_json(

            weather_url

        )





        current = (

            weather_data.get(

                "current"

            )

            or

            {}

        )





        if not current:



            return None





        return {





            "place":

                place_name,





            "temperature":

                current.get(

                    "temperature_2m",

                    "N/A"

                ),





            "feels_like":

                current.get(

                    "apparent_temperature",

                    "N/A"

                ),





            "humidity":

                current.get(

                    "relative_humidity_2m",

                    "N/A"

                ),





            "precipitation":

                current.get(

                    "precipitation",

                    "N/A"

                ),





            "wind_speed":

                current.get(

                    "wind_speed_10m",

                    "N/A"

                ),





            "condition":

                weather_code_to_text(



                    current.get(

                        "weather_code"

                    )

                ),





            "latitude":

                latitude,





            "longitude":

                longitude

        }





    except Exception as e:





        print(

            "WEATHER ERROR:"

        )





        print(

            type(e).__name__

        )





        print(

            str(e)

        )





        return None





# ============================================================

# HOME

# ============================================================



@app.route("/")

def home():





    return render_template(

        "home.html"

    )





# ============================================================

# PLANNER

# ============================================================



@app.route("/planner", methods=["GET", "POST"])

def planner():



    if request.method == "GET":

        return render_template(

            "planner.html",

            places=places

        )



    destination = request.form.get("destination")



    try:

        days = int(request.form.get("days"))

        travelers = int(request.form.get("travelers"))

        budget = int(request.form.get("budget"))

    except (TypeError, ValueError):

        return render_template(

            "planner.html",

            places=places,

            error="Please enter valid numbers for days, travelers and budget."

        )



    if days <= 0 or travelers <= 0 or budget <= 0:

        return render_template(

            "planner.html",

            places=places,

            error="Days, travelers and budget must be greater than zero."

        )



    interests = request.form.getlist("interests")

    style = request.form.get("style")



    place = places.get(destination)



    if not place:

        return render_template(

            "planner.html",

            places=places,

            error="Destination not found."

        )



    # --------------------------------------------------------

    # --------------------------------------------------------

    # LIVE WEATHER FOR THE SELECTED DESTINATION

    # --------------------------------------------------------



    weather = None



    try:

        weather = get_destination_weather(destination)

    except Exception as e:

        print("================================")

        print("PLANNER WEATHER ERROR")

        print(type(e).__name__)

        print(str(e))

        print("================================")



    # BUILD A USEFUL PLACE LIST

    # --------------------------------------------------------



    nearby = list(

        dict.fromkeys(

            place.get("nearby_places", [])

        )

    )



    filtered_places = []



    # Put interest-matching nearby places first.

    if interests:

        for location in nearby:

            location_lower = location.lower()



            for interest in interests:

                if interest.lower() in location_lower:

                    if location not in filtered_places:

                        filtered_places.append(location)

                    break



    # Always add the remaining nearby places so a single

    # interest match does not reduce the itinerary to one place.

    for location in nearby:

        if location not in filtered_places:

            filtered_places.append(location)



    # Add other YatraSathi destinations from the same district

    # when the selected destination does not have enough nearby places.

    current_district = str(

        place.get("district", "")

    ).strip().lower()



    if current_district:

        for other_name, other_data in places.items():

            other_district = str(

                other_data.get("district", "")

            ).strip().lower()



            if (

                other_district == current_district

                and other_name != destination

                and other_name not in filtered_places

            ):

                filtered_places.append(other_name)



    filtered_places = list(

        dict.fromkeys(filtered_places)

    )



    # --------------------------------------------------------

    # CREATE ITINERARY - UP TO 3 PLACES PER DAY

    # --------------------------------------------------------



    itinerary = []

    places_per_day = 3

    place_index = 0



    for day_number in range(1, days + 1):

        day_places = []



        for _ in range(places_per_day):

            if not filtered_places:

                break



            # Use unique places first. If the user requests more

            # days than the available data can fill, cycle safely.

            if place_index >= len(filtered_places):

                place_index = 0



            day_places.append(

                filtered_places[place_index]

            )

            place_index += 1



        itinerary.append({

            "day": day_number,

            "places": day_places

        })



    # --------------------------------------------------------

    # BUDGET BREAKDOWN

    # --------------------------------------------------------



    transport_cost = int(budget * 0.20)

    hotel_cost = int(budget * 0.30)

    food_cost = int(budget * 0.20)

    activity_cost = int(budget * 0.15)

    emergency_cost = int(budget * 0.10)



    used_budget = (

        transport_cost

        + hotel_cost

        + food_cost

        + activity_cost

        + emergency_cost

    )



    remaining_budget = budget - used_budget



    budget_breakdown = {

        "Transport": transport_cost,

        "Hotel": hotel_cost,

        "Food": food_cost,

        "Activities": activity_cost,

        "Emergency": emergency_cost,

        "Remaining": remaining_budget

    }



    # --------------------------------------------------------

    # SAVE TRIP

    # --------------------------------------------------------



    user_email = session.get("user_email")



    if user_email:

        conn = get_db_connection()



        conn.execute(

            """

            INSERT INTO trips

            (

                user_email,

                destination,

                days,

                travelers,

                budget,

                interests,

                style

            )

            VALUES (?, ?, ?, ?, ?, ?, ?)

            """,

            (

                user_email,

                destination,

                days,

                travelers,

                budget,

                ", ".join(interests),

                style

            )

        )



        conn.commit()

        conn.close()



    # --------------------------------------------------------

    # RESULT

    # --------------------------------------------------------



    return render_template(

        "planner.html",

        places=places,

        place=place,

        destination=destination,

        days=days,

        travelers=travelers,

        budget=budget,

        interests=interests,

        style=style,

        itinerary=itinerary,

        recommended_places=filtered_places,

        budget_breakdown=budget_breakdown,

        weather=weather

    )





# ============================================================

# EXPLORE

# ============================================================



@app.route("/explore")

def explore():





    return render_template(



        "explore.html",



        places=places

    )





# ============================================================

# PLACE DETAILS

# ============================================================



@app.route(

    "/place/<place_name>"

)

def place_details(place_name):





    place = places.get(

        place_name

    )





    if not place:





        return (

            "Destination not found",

            404

        )





    return render_template(



        "place_details.html",



        name=place_name,



        place=place

    )





# ============================================================

# HOTELS

# ============================================================



@app.route(

    "/hotels/<place_name>"

)

def hotels_page(place_name):





    try:





        from hotels import hotels





        hotel_list = hotels.get(

            place_name,

            []

        )





    except ImportError:





        hotel_list = []





    maps_url = (

        "https://www.google.com/maps/search/?api=1&query="

        + quote_plus(f"hotels near {place_name}, Karnataka")

    )



    return render_template(

        "hotels.html",

        place_name=place_name,

        hotels=hotel_list,

        maps_url=maps_url

    )





# ============================================================

# RESTAURANTS

# ============================================================



@app.route(

    "/restaurants/<place_name>"

)

def restaurants_page(place_name):





    try:





        from restaurants import restaurants





        restaurant_list = (

            restaurants.get(

                place_name,

                []

            )

        )





    except ImportError:





        restaurant_list = []





    maps_url = (

        "https://www.google.com/maps/search/?api=1&query="

        + quote_plus(f"restaurants near {place_name}, Karnataka")

    )



    return render_template(

        "restaurants.html",

        place_name=place_name,

        restaurants=restaurant_list,

        maps_url=maps_url

    )





# ============================================================

# BUDGET PAGE

# ============================================================



@app.route("/budget")

def budget():





    return render_template(

        "budget.html"

    )





# ============================================================

# LOGIN

# ============================================================



@app.route(

    "/login",

    methods=["GET", "POST"]

)

def login():



    if request.method == "GET":

        return render_template("login.html")



    email = str(request.form.get("email", "")).strip().lower()

    password = str(request.form.get("password", ""))



    if not email or not password:

        return render_template(

            "login.html",

            error="Please enter your email and password."

        )



    # Admin login can be changed in .env without editing code.

    admin_email = os.getenv("ADMIN_EMAIL", "admin@gmail.com").strip().lower()

    admin_password = os.getenv("ADMIN_PASSWORD", "1234")



    if email == admin_email and password == admin_password:

        session["user_name"] = "Admin"

        session["user_email"] = email

        return redirect(url_for("home"))



    conn = get_db_connection()

    user = conn.execute(

        "SELECT * FROM users WHERE lower(email) = ?",

        (email,)

    ).fetchone()



    password_ok = False



    if user:

        stored_password = str(user["password"] or "")



        # New accounts use a secure password hash.

        try:

            password_ok = check_password_hash(

                stored_password,

                password

            )

        except (ValueError, TypeError):

            password_ok = False



        # Backward compatibility for accounts created by older

        # YatraSathi versions that stored plain-text passwords.

        if not password_ok and stored_password == password:

            password_ok = True

            conn.execute(

                "UPDATE users SET password = ? WHERE id = ?",

                (generate_password_hash(password), user["id"])

            )

            conn.commit()



    conn.close()



    if user and password_ok:

        session["user_name"] = user["name"]

        session["user_email"] = user["email"]

        return redirect(url_for("home"))



    return render_template(

        "login.html",

        error="Invalid email or password"

    )





# ============================================================

# LOGOUT

# ============================================================



@app.route("/logout")

def logout():





    session.clear()





    return redirect(

        url_for(

            "login"

        )

    )





# ============================================================

# REGISTER

# ============================================================



@app.route(

    "/register",

    methods=["GET", "POST"]

)

def register():



    if request.method == "GET":

        return render_template("register.html")



    name = str(request.form.get("name", "")).strip()

    email = str(request.form.get("email", "")).strip().lower()

    password = str(request.form.get("password", ""))



    if not name or not email or not password:

        return render_template(

            "register.html",

            error="Please complete all fields."

        )



    if len(password) < 6:

        return render_template(

            "register.html",

            error="Password must contain at least 6 characters."

        )



    conn = get_db_connection()



    try:

        conn.execute(

            """

            INSERT INTO users (name, email, password)

            VALUES (?, ?, ?)

            """,

            (name, email, generate_password_hash(password))

        )

        conn.commit()



    except sqlite3.IntegrityError:

        conn.close()

        return render_template(

            "register.html",

            error="Email already registered."

        )



    conn.close()

    return redirect(url_for("login"))





# ============================================================

# PROFILE

# ============================================================



@app.route("/profile")

def profile():





    return render_template(

        "profile.html"

    )





# ============================================================

# DASHBOARD

# ============================================================



@app.route("/dashboard")

def dashboard():





    return render_template(

        "user_dashboard.html"

    )





# ============================================================

# MY TRIPS

# ============================================================



@app.route("/my-trips")

def my_trips():





    user_email = session.get(

        "user_email"

    )





    if not user_email:





        return redirect(

            url_for(

                "login"

            )

        )





    conn = (

        get_db_connection()

    )





    trips = conn.execute(



        """



        SELECT *



        FROM trips



        WHERE user_email = ?



        ORDER BY id DESC



        """,



        (

            user_email,

        )

    ).fetchall()





    conn.close()





    return render_template(



        "my_trips.html",



        trips=trips

    )





# ============================================================

# DELETE TRIP

# ============================================================



@app.route(

    "/delete-trip/<int:trip_id>"

)

def delete_trip(trip_id):





    user_email = session.get(

        "user_email"

    )





    if not user_email:





        return redirect(

            url_for(

                "login"

            )

        )





    conn = (

        get_db_connection()

    )





    conn.execute(



        """



        DELETE FROM trips



        WHERE id = ?



        AND user_email = ?



        """,



        (

            trip_id,

            user_email

        )

    )





    conn.commit()





    conn.close()





    return redirect(

        url_for(

            "my_trips"

        )

    )





# ============================================================

# STORY PAGE

# ============================================================



@app.route("/story")

def story():





    return render_template(



        "story.html",



        stories=stories

    )





# ============================================================

# GENERATE STORY

# ============================================================



@app.route(

    "/generate-story",

    methods=["POST"]

)

def generate_story():





    data = (

        request.get_json(

            silent=True

        )

        or

        {}

    )





    destination = str(



        data.get(

            "destination",

            ""

        )



    ).strip()





    language = str(



        data.get(

            "language",

            "en"

        )



    ).strip().lower()





    if not destination:





        return jsonify({



            "story":

                "Please select a destination."



        }), 400





    if client is None:





        return jsonify({



            "story":

                "Gemini AI is not configured. "

                "Please check GEMINI_API_KEY."



        }), 500





    languages = {





        "en":

            "English",





        "hi":

            "Hindi",





        "kn":

            "Kannada"

    }





    language_name = languages.get(



        language,



        "English"

    )





    destination_data = (

        places.get(

            destination

        )

    )





    place_information = ""





    if destination_data:





        place_information = (

            create_place_context(



                destination,



                destination_data

            )

        )





    prompt = f"""



You are YatraSathi AI.



You are a Karnataka tourism storyteller.



Create an interesting travel story about:



{destination}





YatraSathi destination information:



{place_information}





Write completely in:



{language_name}





Include when information is known:



- Historical background



- Important places



- Local culture



- Interesting facts



- Traditional stories



- Why tourists visit



- A memorable ending





Rules:



- Focus on Karnataka.



- Use simple language.



- Make the story interesting for students and tourists.



- Do not invent precise historical facts.



- Use clear paragraphs.



- Do not use excessive emojis.



"""





    try:





        story_text = (

            ask_gemini(

                prompt

            )

        )





        return jsonify({



            "story":

                story_text



        }), 200





    except Exception as e:





        print(

            "================================"

        )





        print(

            "GEMINI STORY ERROR"

        )





        print(

            type(e).__name__

        )





        print(

            str(e)

        )





        print(

            "================================"

        )





        return jsonify({



            "story":



                "Sorry, YatraSathi AI "

                "is temporarily unavailable. "

                "Please try again."



        }), 503





# ============================================================

# AI CHATBOT

# ============================================================



@app.route(

    "/chat",

    methods=["POST"]

)

def chat():





    try:





        # ----------------------------------------------------

        # GET DATA

        # ----------------------------------------------------



        data = (

            request.get_json(

                silent=True

            )

            or

            {}

        )





        message = str(



            data.get(

                "message",

                ""

            )



        ).strip()





        language = str(



            data.get(

                "language",

                "en"

            )



        ).strip().lower()





        # ----------------------------------------------------

        # CHECK MESSAGE

        # ----------------------------------------------------



        if not message:





            return jsonify({



                "reply":

                    "Please enter a message."



            }), 400





        # ----------------------------------------------------

        # CHECK GEMINI

        # ----------------------------------------------------



        if client is None:





            return jsonify({



                "reply":



                    "YatraSathi AI is not configured. "

                    "Please check GEMINI_API_KEY "

                    "in your .env file."



            }), 500





        # ----------------------------------------------------

        # LANGUAGE

        # ----------------------------------------------------



        languages = {





            "en":

                "English",





            "hi":

                "Hindi",





            "kn":

                "Kannada"

        }





        language_name = (

            languages.get(

                language,

                "English"

            )

        )





        print(

            "=============================="

        )





        print(

            "CHAT MESSAGE:",

            message

        )





        print(

            "LANGUAGE:",

            language_name

        )





        print(

            "=============================="

        )





        # ----------------------------------------------------

        # FIND DESTINATION

        # ----------------------------------------------------



        place_name, place_data = (

            find_destination(

                message

            )

        )





        message_lower = (

            message.lower()

        )





        # ====================================================

        # MAP REQUEST

        # ====================================================



        map_keywords = [





            "map",



            "maps",



            "location",



            "directions",



            "direction",



            "route",





            # Kannada



            "ಮ್ಯಾಪ್",



            "ಸ್ಥಳ",



            "ನಕ್ಷೆ",



            "ದಾರಿ",





            # Hindi



            "मानचित्र",



            "मैप",



            "लोकेशन",



            "स्थान",



            "रास्ता"

        ]





        is_map_request = any(



            keyword.lower()

            in message_lower



            for keyword

            in map_keywords

        )





        # ----------------------------------------------------

        # MAP REQUEST

        # ----------------------------------------------------



        if is_map_request:





            if not place_name:





                map_not_found = {





                    "en":



                        "Please tell me which Karnataka "

                        "destination you want to see on the map. "

                        "For example: Show Hampi on map.",





                    "kn":



                        "ನೀವು ನಕ್ಷೆಯಲ್ಲಿ ನೋಡಲು ಬಯಸುವ "

                        "ಕರ್ನಾಟಕದ ಸ್ಥಳದ ಹೆಸರನ್ನು ತಿಳಿಸಿ. "

                        "ಉದಾಹರಣೆ: ಹಂಪಿ ಮ್ಯಾಪ್ ತೋರಿಸಿ.",





                    "hi":



                        "कृपया उस कर्नाटक पर्यटन स्थल का "

                        "नाम बताइए जिसे आप मैप पर देखना चाहते हैं। "

                        "उदाहरण: हम्पी का मैप दिखाओ।"

                }





                return jsonify({



                    "reply":

                        map_not_found.get(



                            language,



                            map_not_found[

                                "en"

                            ]

                        )



                }), 200





            map_query = quote_plus(



                f"{place_name}, Karnataka"

            )





            map_url = (



                "https://www.google.com/"

                "maps/search/"

                "?api=1&query="



                + map_query

            )





            map_messages = {





                "en":



                    f"Here is {place_name} "

                    f"on Google Maps.",





                "kn":



                    f"{place_name} ಸ್ಥಳವನ್ನು "

                    f"Google Maps ನಲ್ಲಿ ಇಲ್ಲಿ ನೋಡಬಹುದು.",





                "hi":



                    f"{place_name} का स्थान "

                    f"Google Maps पर यहाँ देख सकते हैं।"

            }





            reply = (

                map_messages.get(



                    language,



                    map_messages[

                        "en"

                    ]

                )

            )





            return jsonify({





                "reply":

                    reply,





                "map_url":

                    map_url,





                "place_name":

                    place_name





            }), 200





        # ====================================================

        # WEATHER REQUEST

        # ====================================================



        weather_keywords = [





            "weather",



            "temperature",



            "climate",



            "rain",



            "raining",





            # Kannada



            "ಹವಾಮಾನ",



            "ತಾಪಮಾನ",



            "ಮಳೆ",





            # Hindi



            "मौसम",



            "तापमान",



            "बारिश"

        ]





        is_weather_request = any(



            keyword.lower()

            in message_lower



            for keyword

            in weather_keywords

        )





        # ----------------------------------------------------

        # WEATHER REQUEST

        # ----------------------------------------------------



        if is_weather_request:





            if not place_name:





                weather_not_found = {





                    "en":



                        "Please tell me the Karnataka destination. "

                        "For example: Weather in Hampi.",





                    "kn":



                        "ದಯವಿಟ್ಟು ಕರ್ನಾಟಕದ ಸ್ಥಳದ ಹೆಸರನ್ನು ತಿಳಿಸಿ. "

                        "ಉದಾಹರಣೆ: ಹಂಪಿಯ ಹವಾಮಾನ.",





                    "hi":



                        "कृपया कर्नाटक के स्थान का नाम बताइए। "

                        "उदाहरण: हम्पी का मौसम।"

                }





                return jsonify({



                    "reply":



                        weather_not_found.get(



                            language,



                            weather_not_found[

                                "en"

                            ]

                        )



                }), 200





            weather = (

                get_live_weather(

                    place_name

                )

            )





            if weather:





                # --------------------------------------------

                # KANNADA

                # --------------------------------------------



                if language == "kn":





                    weather_reply = f"""



🌦️ {place_name} ಪ್ರಸ್ತುತ ಹವಾಮಾನ



🌡️ ತಾಪಮಾನ: {weather["temperature"]}°C



🤗 ಅನುಭವಿಸುವ ತಾಪಮಾನ: {weather["feels_like"]}°C



💧 ಆರ್ದ್ರತೆ: {weather["humidity"]}%



🌧️ ಮಳೆ: {weather["precipitation"]} mm



💨 ಗಾಳಿಯ ವೇಗ: {weather["wind_speed"]} km/h



☁️ ಸ್ಥಿತಿ: {weather["condition"]}



ಹವಾಮಾನ ಬದಲಾಗಬಹುದು.

ಪ್ರಯಾಣಕ್ಕೆ ಮೊದಲು ಇತ್ತೀಚಿನ ಮಾಹಿತಿಯನ್ನು ಪರಿಶೀಲಿಸಿ.



""".strip()





                # --------------------------------------------

                # HINDI

                # --------------------------------------------



                elif language == "hi":





                    weather_reply = f"""



🌦️ {place_name} का वर्तमान मौसम



🌡️ तापमान: {weather["temperature"]}°C



🤗 महसूस होने वाला तापमान: {weather["feels_like"]}°C



💧 नमी: {weather["humidity"]}%



🌧️ वर्षा: {weather["precipitation"]} mm



💨 हवा की गति: {weather["wind_speed"]} km/h



☁️ स्थिति: {weather["condition"]}



मौसम बदल सकता है।

यात्रा से पहले नवीनतम जानकारी जाँच लें।



""".strip()





                # --------------------------------------------

                # ENGLISH

                # --------------------------------------------



                else:





                    weather_reply = f"""



🌦️ Current Weather in {place_name}



🌡️ Temperature: {weather["temperature"]}°C



🤗 Feels Like: {weather["feels_like"]}°C



💧 Humidity: {weather["humidity"]}%



🌧️ Precipitation: {weather["precipitation"]} mm



💨 Wind Speed: {weather["wind_speed"]} km/h



☁️ Condition: {weather["condition"]}



Weather can change, so check again before travelling.



""".strip()





                return jsonify({





                    "reply":

                        weather_reply,





                    "weather":

                        weather





                }), 200





            # Weather API failed



            weather_failed = {





                "en":



                    f"Sorry, I could not get live weather "

                    f"for {place_name} right now.",





                "kn":



                    f"ಕ್ಷಮಿಸಿ, ಈಗ {place_name} ಸ್ಥಳದ "

                    f"ನೇರ ಹವಾಮಾನ ಮಾಹಿತಿಯನ್ನು ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.",





                "hi":



                    f"क्षमा करें, अभी {place_name} का "

                    f"लाइव मौसम प्राप्त नहीं हो सका।"

            }





            return jsonify({



                "reply":



                    weather_failed.get(



                        language,



                        weather_failed[

                            "en"

                        ]

                    )



            }), 200





        # ====================================================

        # DESTINATION CONTEXT

        # ====================================================



        if place_data:





            print(

                "DESTINATION FOUND:",

                place_name

            )





            place_context = (

                create_place_context(



                    place_name,



                    place_data

                )

            )





        else:





            print(

                "No destination detected "

                "from places.py"

            )





            place_context = """



No specific destination from the

YatraSathi database was detected.



Answer the user's general Karnataka

tourism question using your tourism

knowledge.



If current or live information is required

and you do not have it, clearly mention

that it may need verification.



"""





        # ====================================================

        # GEMINI PROMPT

        # ====================================================



        prompt = f"""



You are YatraSathi AI.



You are a friendly and helpful

Karnataka tourism assistant.





==================================================

LANGUAGE

==================================================



The user selected:



{language_name}





Reply completely in {language_name}.





If the selected language is Kannada:



Write naturally using Kannada script.





If the selected language is Hindi:



Write naturally using Devanagari script.





If the selected language is English:



Use simple English.





Destination names, hotel names and

restaurant names may remain in their

commonly used form.





==================================================

YATRASATHI DESTINATION DATA

==================================================



{place_context}





==================================================

YOU CAN HELP WITH

==================================================



You can help users with:



- Karnataka tourist destinations



- Nearby tourist places



- Travel planning



- Day-by-day itineraries



- Budget planning



- Hotels



- Restaurants



- Local food



- Temples



- Heritage places



- Beaches



- Waterfalls



- Hill stations



- Wildlife



- Photography



- Best time to visit



- Things to do



- Travel tips



- Karnataka tourism stories





==================================================

IMPORTANT RULES

==================================================



1. When YatraSathi destination data is

available, use that information first.



2. Do not contradict factual information

provided by the YatraSathi database.



3. If the user asks for nearby places,

use Nearby Places from the database.



4. If the user asks about things to do,

use Things To Do.



5. If the user asks about the best time

to visit, use Best Time.



6. If the user asks about entry fees,

use Entry Fee.



7. If the user asks for travel tips,

use Travel Tips.



8. If the user asks why they should visit,

use Why Visit.



9. If the user asks for an itinerary,

create a simple and clear day-by-day

itinerary.



10. If the user asks about budget,

provide an approximate breakdown for:



- Transport



- Hotel



- Food



- Activities



- Emergency expenses



- Total estimated cost



Clearly mention that actual travel

prices can change.



11. If the user asks for a tourism story,

make it interesting and easy to understand.



12. Do not invent precise historical facts

when you are uncertain.



13. Focus mainly on Karnataka tourism.



14. Keep answers simple and useful.



15. Do not make answers unnecessarily long.





==================================================

USER QUESTION

==================================================



{message}





Answer now in {language_name}.



"""





        # ====================================================

        # CALL GEMINI

        # ====================================================



        reply = (

            ask_gemini(

                prompt

            )

        )





        print(

            "CHAT SUCCESS"

        )





        # ====================================================

        # RETURN RESPONSE

        # ====================================================



        return jsonify({



            "reply":

                reply



        }), 200





    # ========================================================

    # ERROR HANDLING

    # ========================================================



    except Exception as e:





        print(

            "=============================="

        )





        print(

            "CHAT ERROR"

        )





        print(

            type(e).__name__

        )





        print(

            str(e)

        )





        print(

            "=============================="

        )





        error_text = (

            str(e).lower()

        )





        # ----------------------------------------------------

        # GEMINI BUSY

        # ----------------------------------------------------



        if any(



            text in error_text



            for text in [



                "503",



                "unavailable",



                "high demand"

            ]

        ):





            return jsonify({



                "reply":



                    "YatraSathi AI is busy right now. "

                    "Please try again shortly."



            }), 503





        # ----------------------------------------------------

        # QUOTA

        # ----------------------------------------------------



        if any(



            text in error_text



            for text in [



                "429",



                "quota",



                "resource_exhausted"

            ]

        ):





            return jsonify({



                "reply":



                    "The AI request limit has been "

                    "reached. Please try again later."



            }), 429





        # ----------------------------------------------------

        # API KEY

        # ----------------------------------------------------



        if any(



            text in error_text



            for text in [



                "api key",



                "api_key",



                "401",



                "403"

            ]

        ):





            return jsonify({



                "reply":



                    "YatraSathi AI has an API "

                    "configuration problem. "

                    "Please check your GEMINI_API_KEY."



            }), 500





        # ----------------------------------------------------

        # OTHER ERROR

        # ----------------------------------------------------



        return jsonify({



            "reply":



                "Sorry, YatraSathi AI could not "

                "answer your question. "

                "Please try again."



        }), 500



# ============================================================

# NEAR ME / CURRENT LOCATION

# ============================================================



@app.route("/near-me")

def near_me():

    return render_template("near_me.html")





# ============================================================

# LIVE WEATHER

# ============================================================



def weather_description(code):



    weather_codes = {

        0: ("Clear Sky", "☀️"),

        1: ("Mainly Clear", "🌤️"),

        2: ("Partly Cloudy", "⛅"),

        3: ("Cloudy", "☁️"),

        45: ("Fog", "🌫️"),

        48: ("Fog", "🌫️"),

        51: ("Light Drizzle", "🌦️"),

        53: ("Drizzle", "🌦️"),

        55: ("Heavy Drizzle", "🌧️"),

        61: ("Light Rain", "🌦️"),

        63: ("Rain", "🌧️"),

        65: ("Heavy Rain", "🌧️"),

        71: ("Light Snow", "🌨️"),

        73: ("Snow", "🌨️"),

        75: ("Heavy Snow", "❄️"),

        80: ("Light Showers", "🌦️"),

        81: ("Rain Showers", "🌧️"),

        82: ("Heavy Showers", "⛈️"),

        95: ("Thunderstorm", "⛈️"),

        96: ("Thunderstorm", "⛈️"),

        99: ("Heavy Thunderstorm", "⛈️")

    }



    try:

        return weather_codes.get(

            int(code),

            ("Unknown", "🌤️")

        )



    except (TypeError, ValueError):

        return ("Unknown", "🌤️")





# ============================================================

# FETCH JSON

# ============================================================



def weather_fetch_json(url):



    req = Request(

        url,

        headers={

            "User-Agent": "YatraSathi/1.0"

        }

    )



    with urlopen(

        req,

        timeout=10

    ) as response:



        return json.loads(

            response.read().decode("utf-8")

        )





# ============================================================

# FIND DESTINATION COORDINATES

# ============================================================



def find_weather_coordinates(place_name):



    # --------------------------------------------------------

    # FIRST CHECK IF LATITUDE/LONGITUDE EXIST IN places.py

    # --------------------------------------------------------



    place_data = places.get(

        place_name,

        {}

    )



    latitude = place_data.get("latitude")

    longitude = place_data.get("longitude")



    if latitude is not None and longitude is not None:



        return {

            "latitude": latitude,

            "longitude": longitude,

            "location_name": place_name

        }





    # --------------------------------------------------------

    # SEARCH PLACE NAME

    # --------------------------------------------------------



    params = urlencode({

        "name": f"{place_name}, Karnataka",

        "count": 5,

        "language": "en",

        "format": "json",

        "countryCode": "IN"

    })



    url = (

        "https://geocoding-api.open-meteo.com/"

        "v1/search?"

        + params

    )



    data = weather_fetch_json(url)



    results = data.get(

        "results",

        []

    )





    # --------------------------------------------------------

    # PREFER KARNATAKA RESULT

    # --------------------------------------------------------



    for result in results:



        admin1 = str(

            result.get(

                "admin1",

                ""

            )

        ).lower()



        if admin1 == "karnataka":



            return {

                "latitude":

                    result["latitude"],



                "longitude":

                    result["longitude"],



                "location_name":

                    result.get(

                        "name",

                        place_name

                    )

            }





    # --------------------------------------------------------

    # USE FIRST RESULT

    # --------------------------------------------------------



    if results:



        result = results[0]



        return {

            "latitude":

                result["latitude"],



            "longitude":

                result["longitude"],



            "location_name":

                result.get(

                    "name",

                    place_name

                )

        }





    # --------------------------------------------------------

    # FALLBACK TO DISTRICT

    # --------------------------------------------------------



    district = place_data.get(

        "district"

    )



    if district:



        params = urlencode({

            "name": f"{district}, Karnataka",

            "count": 5,

            "language": "en",

            "format": "json",

            "countryCode": "IN"

        })



        url = (

            "https://geocoding-api.open-meteo.com/"

            "v1/search?"

            + params

        )



        data = weather_fetch_json(url)



        results = data.get(

            "results",

            []

        )



        if results:



            result = results[0]



            return {

                "latitude":

                    result["latitude"],



                "longitude":

                    result["longitude"],



                "location_name":

                    place_name

            }





    return None





# ============================================================

# GET WEATHER

# ============================================================



def get_destination_weather(place_name):



    coordinates = (

        find_weather_coordinates(

            place_name

        )

    )



    if not coordinates:

        return None





    latitude = coordinates[

        "latitude"

    ]



    longitude = coordinates[

        "longitude"

    ]





    # --------------------------------------------------------

    # WEATHER API

    # --------------------------------------------------------



    params = urlencode({



        "latitude":

            latitude,



        "longitude":

            longitude,



        "current":

            (

                "temperature_2m,"

                "relative_humidity_2m,"

                "apparent_temperature,"

                "precipitation,"

                "weather_code,"

                "wind_speed_10m,"

                "is_day"

            ),



        "daily":

            (

                "weather_code,"

                "temperature_2m_max,"

                "temperature_2m_min,"

                "precipitation_probability_max"

            ),



        "timezone":

            "Asia/Kolkata",



        "forecast_days":

            5

    })





    url = (

        "https://api.open-meteo.com/"

        "v1/forecast?"

        + params

    )





    data = weather_fetch_json(

        url

    )





    current = data.get(

        "current",

        {}

    )





    daily = data.get(

        "daily",

        {}

    )





    # --------------------------------------------------------

    # CURRENT WEATHER

    # --------------------------------------------------------



    condition, icon = (

        weather_description(

            current.get(

                "weather_code"

            )

        )

    )





    # --------------------------------------------------------

    # 5 DAY FORECAST

    # --------------------------------------------------------



    forecast = []





    dates = daily.get(

        "time",

        []

    )



    max_temps = daily.get(

        "temperature_2m_max",

        []

    )



    min_temps = daily.get(

        "temperature_2m_min",

        []

    )



    codes = daily.get(

        "weather_code",

        []

    )



    rain_chances = daily.get(

        "precipitation_probability_max",

        []

    )





    for index in range(

        min(

            5,

            len(dates)

        )

    ):



        forecast_condition, forecast_icon = (

            weather_description(

                codes[index]

            )

        )





        forecast.append({



            "date":

                dates[index],



            "max":

                max_temps[index],



            "min":

                min_temps[index],



            "condition":

                forecast_condition,



            "icon":

                forecast_icon,



            "rain_chance":

                rain_chances[index]

        })





    # --------------------------------------------------------

    # FINAL DATA

    # --------------------------------------------------------



    return {



        "place":

            place_name,



        "latitude":

            latitude,



        "longitude":

            longitude,



        "temperature":

            current.get(

                "temperature_2m"

            ),



        "feels_like":

            current.get(

                "apparent_temperature"

            ),



        "humidity":

            current.get(

                "relative_humidity_2m"

            ),



        "precipitation":

            current.get(

                "precipitation"

            ),



        "wind_speed":

            current.get(

                "wind_speed_10m"

            ),



        "condition":

            condition,



        "icon":

            icon,



        "is_day":

            current.get(

                "is_day"

            ),



        "updated":

            current.get(

                "time"

            ),



        "forecast":

            forecast

    }





# ============================================================

# WEATHER PAGE

# ============================================================



@app.route("/weather")

def weather_page():



    return render_template(

        "weather.html",

        places=places

    )





# ============================================================

# WEATHER API

# ============================================================



@app.route(

    "/api/weather/<path:place_name>"

)

def weather_api(place_name):



    try:



        # Security / validation:

        # only allow destinations in places.py



        if place_name not in places:



            return jsonify({

                "success": False,

                "error":

                    "Destination not found."

            }), 404





        weather = (

            get_destination_weather(

                place_name

            )

        )





        if not weather:



            return jsonify({

                "success": False,

                "error":

                    "Weather information is not available for this destination."

            }), 404





        return jsonify({

            "success": True,

            "weather": weather

        }), 200





    except Exception as e:



        print("==========================")

        print("WEATHER ERROR")

        print(type(e).__name__)

        print(str(e))

        print("==========================")





        return jsonify({

            "success": False,

            "error":

                "Unable to load live weather. Please try again."

        }), 500







# ============================================================

# RUN APPLICATION

# ============================================================



if __name__ == "__main__":





    app.run(

        debug=True

    )