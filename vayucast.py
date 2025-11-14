# ============================================================
#               🌍 VAYUCAST – ADVANCED WEATHER APP
#  Real-time + Past 5 Days + 14-Day Forecast + AQI + Icons
#   Secure Login/Registration + Dark Mode + Free Open-Meteo
# ============================================================

import streamlit as st
import requests
import sqlite3
import os
import hashlib
import binascii
import pandas as pd
from datetime import datetime, timedelta
import re

# ============================================================
#                      STREAMLIT DARK THEME
# ============================================================
st.set_page_config(
    page_title="VAYUCAST – Advanced Weather App",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🌙",
)

# Inject Dark Mode Style
st.markdown("""
    <style>
        body { background-color: #0E1117; color: white; }
        .stApp { background-color: #0E1117; }
        .css-1v0mbdj { background-color: #161A23 !important; }
        .css-1kyxreq { color: white !important; }
        .css-10trblm { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# ============================================================
#                 PASSWORD HASHING (SECURE)
# ============================================================

def hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
    return binascii.hexlify(salt).decode(), binascii.hexlify(dk).decode()

def verify_password(stored_salt_hex: str, stored_hash_hex: str, provided_password: str) -> bool:
    salt = binascii.unhexlify(stored_salt_hex)
    _, h2 = hash_password(provided_password, salt)
    return h2 == stored_hash_hex

# ============================================================
#                        DATABASE SETUP
# ============================================================

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT,
        salt TEXT,
        pwdhash TEXT
    )
    """)
    conn.commit()
    conn.close()

def create_user(username, email, password):
    salt, pwdhash = hash_password(password)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, email, salt, pwdhash) VALUES (?, ?, ?, ?)",
                    (username, email, salt, pwdhash))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError as e:
        return False, str(e)
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT salt, pwdhash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return verify_password(row[0], row[1], password)

# ============================================================
#                OPEN-METEO WEATHER API HELPERS
# ============================================================

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Weather icons mapping
ICON_MAP = {
    0: "☀️ Clear Sky",
    1: "🌤 Partly Cloudy",
    2: "⛅ Cloudy",
    3: "☁️ Overcast",
    45: "🌫 Fog",
    48: "🌫 Freezing Fog",
    51: "🌦 Light Drizzle",
    61: "🌧 Moderate Rain",
    71: "❄️ Snowfall",
    95: "⛈ Thunderstorm",
}

def weather_icon(code):
    return ICON_MAP.get(code, "🌍")

# ------- Geocoding --------
def geocode_city(city_name, country_code=None):
    params = {"name": city_name, "count": 1}
    if country_code:
        params["country"] = country_code
    r = requests.get(GEOCODE_URL, params=params)
    data = r.json()
    if "results" not in data:
        return None
    return data["results"][0]

# -------- Real-Time Weather ---------
def get_current_weather(lat, lon, tz="auto"):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relativehumidity_2m,precipitation,wind_speed_10m,weather_code",
        "timezone": tz,
    }
    r = requests.get(FORECAST_URL, params=params)
    return r.json()

# -------- 14-DAY FORECAST ---------
def get_14_days(lat, lon, tz="auto"):
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
        "forecast_days": 14,
        "timezone": tz,
    }
    r = requests.get(FORECAST_URL, params=params)
    return r.json()

# -------- Past 5 Days --------
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
    r = requests.get(ARCHIVE_URL, params=params)
    return r.json()

# -------- AQI --------
def get_aqi(lat, lon):
    params = {"latitude": lat, "longitude": lon, "hourly": "us_aqi"}
    r = requests.get(AIR_QUALITY_URL, params=params)
    return r.json()

# ============================================================
#                    STREAMLIT LOGIN UI
# ============================================================

init_db()

st.title("🌙 VAYUCAST – Advanced Global Weather App")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

with st.sidebar:
    st.header("User Authentication")

    if not st.session_state.logged_in:
        mode = st.radio("Select Option", ["Login", "Register"])

        if mode == "Register":
            u = st.text_input("Username")
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")

            if st.button("Sign Up"):
                valid = len(u) >= 3 and len(p) >= 8 and re.match(r"[^@]+@[^@]+\.[^@]+", e)
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
                    st.success("Logged in successfully!")
                else:
                    st.error("Invalid login details!")

    else:
        st.success("Logged In ✔")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.experimental_rerun()

# ============================================================
#                     MAIN WEATHER SECTION
# ============================================================

if not st.session_state.logged_in:
    st.warning("Login to continue.")
    st.stop()

st.subheader("🌍 Search City Weather")

city = st.text_input("City Name")
country = st.text_input("Country Code (optional, e.g., IN)")

if st.button("Get Weather"):
    geo = geocode_city(city, country)

    if not geo:
        st.error("City not found!")
    else:
        lat = geo["latitude"]
        lon = geo["longitude"]
        tz = geo["timezone"]

        st.markdown(f"### 📍 {geo['name']}, {geo['country']}")

        # ========== Real-Time Weather ==========
        st.subheader("🔵 Real-Time Weather")

        current = get_current_weather(lat, lon, tz)
        c = current["current"]

        st.metric("Temperature", f"{c['temperature_2m']} °C")
        st.metric("Humidity", f"{c['relativehumidity_2m']} %")
        st.metric("Rain", f"{c['precipitation']} mm")
        st.metric("Wind", f"{c['wind_speed_10m']} km/h")
        st.write("Weather:", weather_icon(c["weather_code"]))

        # ========== AQI ==========
        st.subheader("🟣 Air Quality Index (AQI)")

        aqi = get_aqi(lat, lon)
        aqi_val = aqi["hourly"]["us_aqi"][0]
        st.metric("AQI", aqi_val)

        # ========== Past 5 Days ==========
        st.subheader("🟡 Past 5 Days (Hourly)")
        past = get_past_5_days(lat, lon, tz)
        if "hourly" in past:
            df_past = pd.DataFrame({
                "time": pd.to_datetime(past["hourly"]["time"]),
                "temperature": past["hourly"]["temperature_2m"],
            }).set_index("time")
            st.line_chart(df_past)

        # ========== 14-Day Forecast ==========
        st.subheader("🔴 14-Day Forecast")
        forecast = get_14_days(lat, lon, tz)

        df_fore = pd.DataFrame({
            "date": forecast["daily"]["time"],
            "temp_max": forecast["daily"]["temperature_2m_max"],
            "temp_min": forecast["daily"]["temperature_2m_min"],
            "weather": forecast["daily"]["weather_code"],
        })

        # Show forecast cards
        for i in range(14):
            st.write(f"📅 {df_fore['date'][i]} — {weather_icon(df_fore['weather'][i])}")
            st.write(f"🌡 {df_fore['temp_min'][i]}°C — {df_fore['temp_max'][i]}°C")
            st.write("---")

st.markdown("---")
st.caption("Powered by Open-Meteo Free Weather API")
