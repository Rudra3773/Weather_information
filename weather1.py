import requests

def get_weather(city_name, api_key):
    url = "https://api.openweathermap.org/data/2.5/weather"
    
    params = {
        'q': city_name,
        'appid': api_key,
        'units': 'metric'  # For Celsius
    }

    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code == 200:
        print(f"\n📍 Weather in {data['name']}, {data['sys']['country']}")
        print(f"🌡️ Temperature: {data['main']['temp']}°C")
        print(f"☁️ Condition: {data['weather'][0]['description'].capitalize()}")
        print(f"💧 Humidity: {data['main']['humidity']}%")
        print(f"🌬️ Wind Speed: {data['wind']['speed']} km/h \n")
       
    else:
        print("❌ Error: City not found or API issue.\n")

# --------- Main App Loop ---------
if __name__ == "__main__":
    api_key = "7c3a4571fa791ee4395ee1ee676b4551"  # Replace with your actual API key
    
    while True:
        city = input("🔍 Enter city name (or type 'exit' to quit): ")
        if city.lower() == 'exit':
            print("👋 Exiting weather app.")
            break
        get_weather(city, api_key)
