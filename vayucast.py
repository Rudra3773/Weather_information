# ============================================================
#                 🌍 VAYUCAST – ADVANCED WEATHER APP
#  Real-time + Live Location + Past 5 Days + 14-Day Forecast
#  Rain Probability + Dynamic Weather Background + AQI
#  Secure Login/Registration + Dark Mode + Free Open-Meteo
# ============================================================

import streamlit as st
import requests
import sqlite3
import os
import hashlib
import binascii
import pandas as pd
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import re
import textwrap

# Browser geolocation component
try:
    from streamlit_geolocation import streamlit_geolocation
    GEOLOCATION_AVAILABLE = True
except ImportError:
    GEOLOCATION_AVAILABLE = False


# ============================================================
#                         PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="VAYUCAST – Advanced Weather App",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🌙",
)


# ============================================================
#                  WEATHER UI / DYNAMIC BACKGROUND
# ============================================================

BASE_CSS = """
<style>
    .stApp {
        background: #0E1117;
        color: white;
        transition: background 0.8s ease-in-out;
    }

    [data-testid="stSidebar"] {
        background: rgba(22, 26, 35, 0.96);
    }

    .weather-hero {
        position: relative;
        overflow: hidden;
        border-radius: 24px;
        padding: 28px;
        margin: 10px 0 24px 0;
        min-height: 220px;
        display: flex;
        align-items: center;
        box-shadow: 0 12px 40px rgba(0,0,0,0.25);
        isolation: isolate;
    }

    .weather-hero-content {
        position: relative;
        z-index: 3;
        width: 100%;
    }

    .weather-animation {
        position: absolute;
        inset: 0;
        z-index: 1;
        pointer-events: none;
    }

    .weather-animation span {
        position: absolute;
        user-select: none;
    }

    .sun {
        font-size: 90px;
        right: 7%;
        top: 20px;
        animation: floatSun 4s ease-in-out infinite;
    }

    .cloud {
        font-size: 72px;
        opacity: 0.75;
        animation: driftCloud 12s linear infinite;
    }

    .cloud.c1 { left: 8%; top: 18px; }
    .cloud.c2 { left: 42%; top: 95px; animation-duration: 17s; }
    .cloud.c3 { right: 8%; top: 110px; animation-duration: 20s; }

    .rain-drop {
        font-size: 28px;
        animation: rainFall 1.1s linear infinite;
    }

    .rain-drop.r1 { left: 12%; animation-delay: 0.0s; }
    .rain-drop.r2 { left: 27%; animation-delay: 0.25s; }
    .rain-drop.r3 { left: 43%; animation-delay: 0.45s; }
    .rain-drop.r4 { left: 58%; animation-delay: 0.1s; }
    .rain-drop.r5 { left: 74%; animation-delay: 0.65s; }
    .rain-drop.r6 { left: 88%; animation-delay: 0.35s; }

    .snow-flake {
        font-size: 26px;
        animation: snowFall 5s linear infinite;
    }

    .snow-flake.s1 { left: 12%; animation-delay: 0s; }
    .snow-flake.s2 { left: 32%; animation-delay: 1.2s; }
    .snow-flake.s3 { left: 52%; animation-delay: 2.0s; }
    .snow-flake.s4 { left: 72%; animation-delay: 0.8s; }
    .snow-flake.s5 { left: 90%; animation-delay: 2.8s; }

    .lightning {
        font-size: 70px;
        right: 12%;
        top: 35px;
        animation: flash 1.8s infinite;
    }

    .stars {
        font-size: 22px;
        letter-spacing: 22px;
        right: 5%;
        top: 20px;
        opacity: 0.9;
    }

    @keyframes floatSun {
        0%, 100% { transform: translateY(0) scale(1); }
        50% { transform: translateY(-8px) scale(1.04); }
    }

    @keyframes driftCloud {
        0% { transform: translateX(-15px); }
        50% { transform: translateX(25px); }
        100% { transform: translateX(-15px); }
    }

    @keyframes rainFall {
        0% { transform: translateY(-120px); opacity: 0; }
        20% { opacity: 1; }
        100% { transform: translateY(280px); opacity: 0; }
    }

    @keyframes snowFall {
        0% { transform: translateY(-80px) translateX(0); opacity: 0; }
        15% { opacity: 1; }
        100% { transform: translateY(290px) translateX(45px); opacity: 0; }
    }

    @keyframes flash {
        0%, 88%, 100% { opacity: 0.15; }
        90% { opacity: 1; }
        93% { opacity: 0.25; }
        96% { opacity: 0.9; }
    }

    .metric-card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 16px;
        padding: 18px;
        text-align: center;
        height: 100%;
    }

    .metric-value {
        font-size: 30px;
        font-weight: 700;
        margin-top: 5px;
    }

    .rain-box {
        background: rgba(42, 120, 255, 0.13);
        border: 1px solid rgba(80, 160, 255, 0.25);
        border-radius: 16px;
        padding: 18px;
        margin: 12px 0;
    }

    .forecast-card {
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 18px;
        margin: 12px 0;
    }

    .forecast-title {
        font-size: 19px;
        font-weight: 700;
    }

    .muted {
        opacity: 0.78;
        font-size: 14px;
    }

    .location-pill {
        display: inline-block;
        background: rgba(255,255,255,0.10);
        padding: 7px 12px;
        border-radius: 999px;
        margin-top: 6px;
    }
</style>
"""

st.markdown(textwrap.dedent(BASE_CSS).strip(), unsafe_allow_html=True)


# ============================================================
#                 PASSWORD HASHING (SECURE)
# ============================================================

def hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200_000,
    )
    return binascii.hexlify(salt).decode(), binascii.hexlify(dk).decode()


def verify_password(
    stored_salt_hex: str,
    stored_hash_hex: str,
    provided_password: str,
) -> bool:
    try:
        salt = binascii.unhexlify(stored_salt_hex)
        _, h2 = hash_password(provided_password, salt)
        return h2 == stored_hash_hex
    except (ValueError, binascii.Error):
        return False


# ============================================================
#                         DATABASE
# ============================================================

DB_PATH = "users.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT,
            salt TEXT,
            pwdhash TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def create_user(username, email, password):
    salt, pwdhash = hash_password(password)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO users (username, email, salt, pwdhash)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, salt, pwdhash),
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError as e:
        return False, str(e)
    finally:
        conn.close()


def authenticate_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT salt, pwdhash FROM users WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return False

    return verify_password(row[0], row[1], password)


# ============================================================
#                     OPEN-METEO APIs
# ============================================================

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


ICON_MAP = {
    0: "☀️ Clear Sky",
    1: "🌤️ Mainly Clear",
    2: "⛅ Partly Cloudy",
    3: "☁️ Overcast",
    45: "🌫️ Fog",
    48: "🌫️ Depositing Rime Fog",
    51: "🌦️ Light Drizzle",
    53: "🌦️ Moderate Drizzle",
    55: "🌧️ Dense Drizzle",
    56: "🌧️ Freezing Drizzle",
    57: "🌧️ Dense Freezing Drizzle",
    61: "🌧️ Slight Rain",
    63: "🌧️ Moderate Rain",
    65: "🌧️ Heavy Rain",
    66: "🌧️ Freezing Rain",
    67: "🌧️ Heavy Freezing Rain",
    71: "❄️ Slight Snow",
    73: "❄️ Moderate Snow",
    75: "❄️ Heavy Snow",
    77: "🌨️ Snow Grains",
    80: "🌦️ Slight Rain Showers",
    81: "🌧️ Moderate Rain Showers",
    82: "🌧️ Violent Rain Showers",
    85: "🌨️ Slight Snow Showers",
    86: "❄️ Heavy Snow Showers",
    95: "⛈️ Thunderstorm",
    96: "⛈️ Thunderstorm + Hail",
    99: "⛈️ Severe Thunderstorm + Hail",
}


def weather_icon(code):
    try:
        return ICON_MAP.get(int(code), "🌍 Unknown")
    except (TypeError, ValueError):
        return "🌍 Unknown"


def weather_group(code):
    """Map WMO weather codes to a small set of UI background groups."""
    try:
        code = int(code)
    except (TypeError, ValueError):
        return "unknown"

    if code == 0:
        return "sunny"
    if code in (1, 2):
        return "partly_cloudy"
    if code in (3, 45, 48):
        return "cloudy"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (95, 96, 99):
        return "storm"
    return "cloudy"


def normalize_city_name(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"\b(city|town|district)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def city_match_score(query: str, result: dict) -> float:
    q = normalize_city_name(query)

    candidates = [
        result.get("name", ""),
        result.get("ascii", ""),
    ]

    scores = []
    for candidate in candidates:
        c = normalize_city_name(candidate)
        if not c:
            continue
        if q == c:
            scores.append(1.0)
        else:
            scores.append(SequenceMatcher(None, q, c).ratio())

    for candidate in candidates:
        c = normalize_city_name(candidate)
        if q and q in c:
            scores.append(0.82)

    return max(scores, default=0.0)


def geocode_city(city_name, country_code=None):
    """
    Validate the city instead of blindly accepting Open-Meteo's
    fuzzy first result. This prevents typos from silently becoming
    a completely different city.
    """
    city_name = (city_name or "").strip()
    country_code = (country_code or "").strip().upper()

    if len(city_name) < 2:
        return None

    params = {
        "name": city_name,
        "count": 10,
        "language": "en",
        "format": "json",
    }

    if country_code:
        params["countryCode"] = country_code

    try:
        response = requests.get(GEOCODE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    results = data.get("results", [])
    if not results:
        return None

    if country_code:
        results = [
            item
            for item in results
            if str(item.get("country_code", "")).upper() == country_code
        ]

    if not results:
        return None

    ranked = sorted(
        results,
        key=lambda item: city_match_score(city_name, item),
        reverse=True,
    )

    best = ranked[0]
    score = city_match_score(city_name, best)

    if score < 0.70:
        return None

    return best


def reverse_geocode(lat, lon):
    """Optional human-readable location for browser GPS coordinates."""
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "zoom": 10,
        "addressdetails": 1,
    }
    headers = {
        "User-Agent": "VayuCast/1.0 (weather application)"
    }

    try:
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        address = data.get("address", {})

        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("county")
        )
        state = address.get("state")
        country = address.get("country")

        parts = [p for p in [city, state, country] if p]
        return ", ".join(parts) if parts else None
    except (requests.RequestException, ValueError):
        return None


# ============================================================
#                         WEATHER DATA
# ============================================================

def get_current_weather(lat, lon, tz="auto"):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,relative_humidity_2m,precipitation,"
            "rain,showers,wind_speed_10m,weather_code,cloud_cover,is_day"
        ),
        "hourly": "precipitation_probability,precipitation,rain,showers",
        "forecast_days": 2,
        "timezone": tz,
    }

    try:
        response = requests.get(FORECAST_URL, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return {}


def get_14_days(lat, lon, tz="auto"):
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": (
            "temperature_2m_max,temperature_2m_min,precipitation_sum,"
            "rain_sum,showers_sum,precipitation_probability_max,"
            "precipitation_hours,weather_code,sunrise,sunset"
        ),
        "forecast_days": 14,
        "timezone": tz,
    }

    try:
        response = requests.get(FORECAST_URL, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return {}


def get_past_5_days(lat, lon, tz="auto"):
    end = datetime.utcnow().date()
    start = end - timedelta(days=6)

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": (end - timedelta(days=1)).isoformat(),
        "hourly": "temperature_2m,precipitation",
        "timezone": tz,
    }

    try:
        response = requests.get(ARCHIVE_URL, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return {}


def get_aqi(lat, lon, tz="auto"):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "us_aqi",
        "timezone": tz,
    }

    try:
        response = requests.get(AIR_QUALITY_URL, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return {}


def get_current_rain_probability(current_data):
    """Match current local time to the hourly precipitation probability."""
    try:
        current_time = current_data["current"]["time"]
        hourly_times = current_data["hourly"]["time"]
        probabilities = current_data["hourly"]["precipitation_probability"]

        current_dt = pd.to_datetime(current_time)
        parsed = pd.to_datetime(hourly_times)

        exact_matches = [
            i for i, t in enumerate(parsed) if t == current_dt
        ]
        if exact_matches:
            return probabilities[exact_matches[0]]

        nearest_idx = min(
            range(len(parsed)),
            key=lambda i: abs(parsed[i] - current_dt),
        )
        return probabilities[nearest_idx]
    except (KeyError, TypeError, ValueError, IndexError):
        return None


# ============================================================
#                    DYNAMIC WEATHER BACKGROUND
# ============================================================

def apply_weather_background(code, is_day=1):
    group = weather_group(code)

    if not is_day:
        background = (
            "radial-gradient(circle at 75% 20%, rgba(85,100,170,0.25), transparent 28%),"
            "linear-gradient(135deg, #07111f 0%, #101827 50%, #03050a 100%)"
        )
    elif group == "sunny":
        background = (
            "radial-gradient(circle at 78% 18%, rgba(255,211,80,0.38), transparent 18%),"
            "linear-gradient(135deg, #1477c9 0%, #56b8e8 50%, #dff6ff 100%)"
        )
    elif group == "partly_cloudy":
        background = (
            "linear-gradient(135deg, #4a86b8 0%, #6ca9c8 45%, #a9c9d6 100%)"
        )
    elif group == "cloudy":
        background = (
            "linear-gradient(135deg, #34495e 0%, #607487 50%, #8595a0 100%)"
        )
    elif group == "rain":
        background = (
            "linear-gradient(135deg, #162638 0%, #30475e 48%, #15202b 100%)"
        )
    elif group == "storm":
        background = (
            "linear-gradient(135deg, #090d18 0%, #25283a 48%, #11131d 100%)"
        )
    elif group == "snow":
        background = (
            "linear-gradient(135deg, #5e7787 0%, #a9c3cf 50%, #e7f4f8 100%)"
        )
    else:
        background = "#0E1117"

    st.markdown(
        f"""
        <style>
            .stApp {{
                background: {background} !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    if not is_day:
        animation = """
        <div class="weather-animation">
            <span class="stars">✦ ✧ ✦ ✧ ✦</span>
        </div>
        """
    elif group == "sunny":
        animation = """
        <div class="weather-animation">
            <span class="sun">☀️</span>
        </div>
        """
    elif group == "partly_cloudy":
        animation = """
        <div class="weather-animation">
            <span class="sun">🌤️</span>
            <span class="cloud c1">☁️</span>
            <span class="cloud c2">☁️</span>
        </div>
        """
    elif group == "cloudy":
        animation = """
        <div class="weather-animation">
            <span class="cloud c1">☁️</span>
            <span class="cloud c2">☁️</span>
            <span class="cloud c3">☁️</span>
        </div>
        """
    elif group == "rain":
        animation = """
        <div class="weather-animation">
            <span class="cloud c1">☁️</span>
            <span class="cloud c2">☁️</span>
            <span class="cloud c3">☁️</span>
            <span class="rain-drop r1">💧</span>
            <span class="rain-drop r2">💧</span>
            <span class="rain-drop r3">💧</span>
            <span class="rain-drop r4">💧</span>
            <span class="rain-drop r5">💧</span>
            <span class="rain-drop r6">💧</span>
        </div>
        """
    elif group == "storm":
        animation = """
        <div class="weather-animation">
            <span class="cloud c1">☁️</span>
            <span class="cloud c2">☁️</span>
            <span class="cloud c3">☁️</span>
            <span class="lightning">⚡</span>
        </div>
        """
    elif group == "snow":
        animation = """
        <div class="weather-animation">
            <span class="cloud c1">☁️</span>
            <span class="cloud c2">☁️</span>
            <span class="snow-flake s1">❄️</span>
            <span class="snow-flake s2">❄️</span>
            <span class="snow-flake s3">❄️</span>
            <span class="snow-flake s4">❄️</span>
            <span class="snow-flake s5">❄️</span>
        </div>
        """
    else:
        animation = ""

    return animation


def rain_label(probability):
    if probability is None:
        return "Rain probability unavailable"
    if probability >= 70:
        return "🌧️ High chance of rain"
    if probability >= 40:
        return "🌦️ Moderate chance of rain"
    if probability >= 20:
        return "🌤️ Low chance of rain"
    return "☀️ Very low chance of rain"


# ============================================================
#                    SESSION STATE HELPERS
# ============================================================

init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "weather_location" not in st.session_state:
    st.session_state.weather_location = None

if "weather_source" not in st.session_state:
    st.session_state.weather_source = None


# ============================================================
#                         LOGIN UI
# ============================================================

st.title("🌙 VAYUCAST – Advanced Global Weather App")

with st.sidebar:
    st.header("User Authentication")

    if not st.session_state.logged_in:
        mode = st.radio("Select Option", ["Login", "Register"])

        if mode == "Register":
            u = st.text_input("Username")
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")

            if st.button("Sign Up"):
                valid = (
                    len(u) >= 3
                    and len(p) >= 8
                    and re.match(r"[^@]+@[^@]+\.[^@]+", e)
                )

                if not valid:
                    st.error("Please enter valid details.")
                else:
                    ok, msg = create_user(u, e, p)
                    if ok:
                        st.success("Account created successfully!")
                    else:
                        st.error(f"Error: {msg}")

        else:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")

            if st.button("Login"):
                if authenticate_user(u, p):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid login details!")

    else:
        st.success("Logged In ✔")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.weather_location = None
            st.session_state.weather_source = None
            st.rerun()


# ============================================================
#                     MAIN WEATHER SECTION
# ============================================================

if not st.session_state.logged_in:
    st.warning("Login to continue.")
    st.stop()

st.subheader("🌍 Search City Weather")

col_search, col_country = st.columns([3, 1])

with col_search:
    city = st.text_input(
        "City Name",
        placeholder="e.g. Gorakhpur, Lucknow, Delhi",
    )

with col_country:
    country = st.text_input(
        "Country Code",
        placeholder="IN",
        help="Optional ISO country code, e.g. IN, US, GB.",
    )

col1, col2 = st.columns([1, 1])

with col1:
    search_clicked = st.button(
        "🔎 Get Weather",
        use_container_width=True,
    )

with col2:
    location_clicked = st.button(
        "📍 Use My Live Location",
        use_container_width=True,
    )


# ============================================================
# LIVE DEVICE LOCATION
# ============================================================

if location_clicked:
    if not GEOLOCATION_AVAILABLE:
        st.error(
            "Live location module is not installed. "
            "Run: pip install streamlit-geolocation"
        )
    else:
        location = streamlit_geolocation()

        if not location:
            st.info(
                "Click the location button again and allow browser location permission."
            )
        elif "error" in location:
            error = location.get("error", {})
            code = error.get("code")
            message = error.get("message", "Unable to fetch location.")

            if code == 1:
                st.error(
                    "❌ Location permission denied. "
                    "Allow location access in your browser and try again."
                )
            else:
                st.error(f"❌ Location error: {message}")
        else:
            lat = location.get("latitude")
            lon = location.get("longitude")

            if lat is None or lon is None:
                st.warning("Location coordinates were not returned. Try again.")
            else:
                detected_name = reverse_geocode(lat, lon)

                st.session_state.weather_location = {
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "timezone": "auto",
                    "name": detected_name or "Current Device Location",
                    "country": "",
                }
                st.session_state.weather_source = "live"
                st.success(
                    "📍 Live location detected"
                    + (f": {detected_name}" if detected_name else "")
                )
                st.rerun()


# ============================================================
# CITY SEARCH
# ============================================================

if search_clicked:
    if not city.strip():
        st.warning("Please enter a city name.")
    elif country.strip() and not re.fullmatch(r"[A-Za-z]{2}", country.strip()):
        st.error("❌ Invalid country code. Use a 2-letter code such as IN or US.")
    else:
        with st.spinner("🔎 Validating city and fetching location..."):
            geo = geocode_city(city, country)

        if not geo:
            st.error(
                f"❌ Invalid city name: '{city}'. "
                "Please enter a valid city and check the spelling."
            )
            st.session_state.weather_location = None
            st.session_state.weather_source = None
        else:
            st.session_state.weather_location = {
                "latitude": geo["latitude"],
                "longitude": geo["longitude"],
                "timezone": geo.get("timezone", "auto"),
                "name": geo.get("name", city.title()),
                "country": geo.get("country", ""),
            }
            st.session_state.weather_source = "search"
            st.rerun()


# ============================================================
# FETCH WEATHER FOR SELECTED LOCATION
# ============================================================

location = st.session_state.weather_location

if location:
    lat = location["latitude"]
    lon = location["longitude"]
    tz = location.get("timezone", "auto")

    with st.spinner("🌦️ Loading live weather data..."):
        current = get_current_weather(lat, lon, tz)
        forecast = get_14_days(lat, lon, tz)
        past = get_past_5_days(lat, lon, tz)
        aqi = get_aqi(lat, lon, tz)

    if "current" not in current:
        st.error("❌ Weather service could not return current conditions.")
        st.stop()

    c = current["current"]
    weather_code = c.get("weather_code", 0)
    is_day = c.get("is_day", 1)

    animation_html = textwrap.dedent(
        apply_weather_background(weather_code, is_day)
    ).strip()

    if st.session_state.weather_source == "live":
        location_name = location["name"]
        location_line = f"{location_name} · {lat:.4f}, {lon:.4f}"
        source_label = "📍 LIVE DEVICE LOCATION"
    else:
        location_name = f"{location['name']}, {location['country']}"
        location_line = location_name
        source_label = "🔎 CITY SEARCH"

    # IMPORTANT: keep every HTML line flush-left. Streamlit Markdown
    # interprets indented HTML as a code block.
    hero_html = f"""<div class="weather-hero">
{animation_html}
<div class="weather-hero-content">
<div class="muted">{source_label}</div>
<h1 style="margin: 4px 0 4px 0;">{weather_icon(weather_code)}</h1>
<h2 style="margin: 0;">{location_name}</h2>
<div class="location-pill">{location_line}</div>
</div>
</div>"""

    st.markdown(hero_html.strip(), unsafe_allow_html=True)

    # ========================================================
    # REAL-TIME WEATHER
    # ========================================================

    st.subheader("🔵 Real-Time Weather")

    temp = c.get("temperature_2m", 0)
    humidity = c.get("relative_humidity_2m", 0)
    precipitation = c.get("precipitation", 0)
    rain_now = c.get("rain", 0)
    showers_now = c.get("showers", 0)
    wind = c.get("wind_speed_10m", 0)
    cloud_cover = c.get("cloud_cover", 0)

    current_rain_probability = get_current_rain_probability(current)

    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.metric("🌡️ Temperature", f"{temp:.1f} °C")

    with m2:
        st.metric("💧 Humidity", f"{humidity:.0f} %")

    with m3:
        st.metric("🌧️ Precipitation", f"{precipitation:.1f} mm")

    with m4:
        st.metric("💨 Wind", f"{wind:.1f} km/h")

    with m5:
        st.metric("☁️ Cloud Cover", f"{cloud_cover:.0f} %")

    # ========================================================
    # CURRENT RAIN PREDICTION
    # ========================================================

    st.subheader("🌧️ Rain Prediction — Current Conditions")

    r1, r2, r3 = st.columns(3)

    with r1:
        if current_rain_probability is None:
            st.metric("Rain Probability", "N/A")
        else:
            st.metric("Rain Probability", f"{current_rain_probability:.0f}%")

    with r2:
        st.metric("Rain Now", f"{rain_now:.1f} mm")

    with r3:
        st.metric("Showers Now", f"{showers_now:.1f} mm")

    rain_status_html = f"""<div class="rain-box">
<strong>{rain_label(current_rain_probability)}</strong>
<div class="muted" style="margin-top:6px;">
Current condition: {weather_icon(weather_code)}
</div>
</div>"""

    st.markdown(rain_status_html.strip(), unsafe_allow_html=True)

    # ========================================================
    # AQI
    # ========================================================

    st.subheader("🟣 Air Quality Index (AQI)")

    try:
        aqi_values = aqi.get("hourly", {}).get("us_aqi", [])
        aqi_val = aqi_values[0] if aqi_values else None

        if aqi_val is None:
            st.info("AQI data unavailable for this location.")
        else:
            st.metric("US AQI", aqi_val)
    except (TypeError, IndexError):
        st.info("AQI data unavailable for this location.")

    # ========================================================
    # PAST 5 DAYS
    # ========================================================

    st.subheader("🟡 Past 5 Days — Temperature & Precipitation")

    if "hourly" in past:
        try:
            df_past = pd.DataFrame({
                "time": pd.to_datetime(past["hourly"]["time"]),
                "temperature": past["hourly"]["temperature_2m"],
                "precipitation": past["hourly"]["precipitation"],
            }).set_index("time")

            st.line_chart(
                df_past[["temperature", "precipitation"]],
                use_container_width=True,
            )
        except (KeyError, ValueError, TypeError):
            st.info("Historical weather chart is temporarily unavailable.")
    else:
        st.info("Historical weather data is unavailable.")

    # ========================================================
    # 14-DAY FORECAST + RAIN PREDICTION
    # ========================================================

    st.subheader("🔴 Next14-Day Forecast and Rain Prediction")

    daily = forecast.get("daily", {})

    required_keys = [
        "time",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "rain_sum",
        "showers_sum",
        "precipitation_probability_max",
        "precipitation_hours",
        "weather_code",
    ]

    if not all(key in daily for key in required_keys):
        st.error("14-day forecast data is incomplete.")
    else:
        df_fore = pd.DataFrame({
            "date": daily["time"],
            "temp_max": daily["temperature_2m_max"],
            "temp_min": daily["temperature_2m_min"],
            "precipitation": daily["precipitation_sum"],
            "rain": daily["rain_sum"],
            "showers": daily["showers_sum"],
            "rain_probability": daily["precipitation_probability_max"],
            "precipitation_hours": daily["precipitation_hours"],
            "weather": daily["weather_code"],
        })

        for i in range(len(df_fore)):
            code = df_fore.loc[i, "weather"]
            probability = df_fore.loc[i, "rain_probability"]
            precipitation_total = df_fore.loc[i, "precipitation"]
            rain_total = df_fore.loc[i, "rain"]
            shower_total = df_fore.loc[i, "showers"]
            hours = df_fore.loc[i, "precipitation_hours"]

            forecast_html = textwrap.dedent(
                f"""
                <div class="forecast-card">
                    <div class="forecast-title">
                        📅 {df_fore.loc[i, 'date']} &nbsp; {weather_icon(code)}
                    </div>
                    <div style="margin-top:10px;">
                        🌡️ <strong>{df_fore.loc[i, 'temp_min']:.1f}°C — {df_fore.loc[i, 'temp_max']:.1f}°C</strong>
                    </div>
                    <div style="margin-top:8px;">
                        🌧️ Rain Probability: <strong>{probability:.0f}%</strong>
                    </div>
                    <div style="margin-top:6px;">
                        💧 Expected Precipitation: <strong>{precipitation_total:.1f} mm</strong>
                    </div>
                    <div style="margin-top:6px;">
                        🌧️ Rain: <strong>{rain_total:.1f} mm</strong>
                        &nbsp; | &nbsp;
                        🌦️ Showers: <strong>{shower_total:.1f} mm</strong>
                    </div>
                    <div class="muted" style="margin-top:6px;">
                        ⏱️ Expected precipitation hours: {hours:.1f} h
                        &nbsp; | &nbsp;
                        {rain_label(probability)}
                    </div>
                </div>
                """
            ).strip()

            st.markdown(forecast_html, unsafe_allow_html=True)

st.markdown("---")
st.caption(
    "Powered by Open-Meteo Free Weather API • "
    "Browser location is used only when you choose Live Location."
)