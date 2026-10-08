YatraSathi - Updated Project
============================

1. Open the YatraSathi_Updated folder in VS Code.

2. Open PowerShell/Terminal in this folder.

3. Install dependencies:
   python -m pip install -r requirements.txt

4. Check .env. It must contain:
   GEMINI_API_KEY=your_key
   GEMINI_MODEL=gemini-3.8-flash

   Optional:
   FLASK_SECRET_KEY=your_random_secret
   ADMIN_EMAIL=admin@gmail.com
   ADMIN_PASSWORD=1234

5. Start the website:
   python app.py

6. Open:
   http://127.0.0.1:5000/

Important tests
---------------
- Home page loads without JavaScript syntax errors.
- Live Weather button is the LAST navbar item and opens /weather.
- Weather: choose a destination -> Check Weather -> current + 5-day forecast.
- YatraSathi Assistant: orange route button above the chatbot button.
- Assistant -> Speak Page reads the page.
- Assistant -> Voice Command needs microphone permission and works best in Chrome/Edge.
- Assistant -> Ask AI opens the existing Gemini chatbot.
- Near Me -> allow Location permission -> map appears.
- Login -> Remember my email stores ONLY the email locally; browser password manager handles passwords.
- Place Details -> Hotels / Restaurants pages no longer fail when local hotel/restaurant datasets are absent.

Browser permissions
-------------------
Voice: allow Microphone permission.
Near Me: allow Location permission.
Geolocation works on localhost and on HTTPS deployments.

Gemini
------
The app tries the configured GEMINI_MODEL first and then stable fallback models.
If Google returns 503/high demand, YatraSathi retries and tries another model.
