import streamlit as st
import requests


API_KEY = "7c3a4571fa791ee4395ee1ee676b4551"  

def get_weather(city, country_code=None):
    
    if country_code:
        query = f"{city},{country_code}"
    else:
        query = city

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": query,
        "appid": API_KEY,
        "units": "metric"  # Celsius
    }

    response = requests.get(url, params=params)
    data = response.json()

    # If city not found or other error
    if response.status_code != 200:
        return None, data.get("message", "Error fetching data")

    return data, None

# Streamlit UI
st.title("🌍VAYUCAST Global Weather App")
st.write("Get **real-time weather updates** from any city or country worldwide.")

# Input fields
city_name = st.text_input("Enter City Name", placeholder="e.g., Gorakhpur")
country_code = st.text_input("Enter Country Code (optional, e.g., IN for India, US for USA)", placeholder="e.g., IN")

if st.button("Get Weather"):
    if not city_name:
        st.error("⚠ Please enter a city name.")
    else:
        weather_data, error = get_weather(city_name, country_code)

        if error:
            st.error(f"❌ {error}")
        else:
            # Extract relevant data
            temperature = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            condition = weather_data['weather'][0]['description'].capitalize()
            humidity = weather_data['main']['humidity']
            wind_speed = weather_data['wind']['speed']
            visibility = weather_data.get('visibility', 'N/A')
            pressure = weather_data['main']['pressure']

            # Display results
            st.subheader(f"📍 Weather in {weather_data['name']}, {weather_data['sys']['country']}")
            st.metric("🌡 Temperature", f"{temperature} °C")
            st.metric("🌡 Feels Like", f"{feels_like} °C")
            st.metric("☁ Condition", condition)
            st.metric("💧 Humidity", f"{humidity}%")
            st.metric("🌬 Wind Speed", f"{wind_speed} km/h")
            st.metric("👁 Visibility", f"{visibility / 1000:.1f} km" if isinstance(visibility, int) else "N/A")
            st.metric("⚖ Pressure", f"{pressure} mb")

            # Show raw data toggle for debugging
            with st.expander("View Raw Data (For Debugging)"):
                st.json(weather_data)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using [Streamlit](https://streamlit.io/) and [OpenWeatherMap](https://openweathermap.org/) API")
