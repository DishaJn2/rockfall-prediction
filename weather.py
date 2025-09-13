import streamlit as st
import requests
import time
import plotly.express as px

# ---------- CONFIG ----------
API_KEY = "e485fe9a0dfd4f27ee76b7de15d0acac"  # apna OpenWeather API key daalo
cities = ["Delhi", "Mumbai", "Bengaluru", "Chennai", "Kolkata", "Hyderabad", "Pune", "Jaipur"]

# ---------- FUNCTION ----------
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url).json()
    if response.get("main"):
        return {
            "City": city,
            "Temperature (°C)": response["main"]["temp"],
            "Humidity (%)": response["main"]["humidity"],
            "Rainfall (mm)": response.get("rain", {}).get("1h", 0),
            "Weather": response["weather"][0]["description"].title()
        }
    else:
        return {"Error": response.get("message", "Unable to fetch weather data")}

# ---------- UI ----------
st.set_page_config(page_title="🌍 Live Weather Report", layout="wide")
st.title("🌍 Live Weather Report Dashboard")

# Dropdown for cities
city = st.selectbox("Select City", cities)

# Live update interval
interval = st.slider("⏱ Refresh Interval (seconds)", 10, 300, 30)

placeholder = st.empty()

while True:
    with placeholder.container():
        data = get_weather(city)
        if "Error" not in data:
            col1, col2, col3 = st.columns(3)
            col1.metric("🌡️ Temperature (°C)", data["Temperature (°C)"])
            col2.metric("💧 Humidity (%)", data["Humidity (%)"])
            col3.metric("🌧️ Rainfall (mm)", data["Rainfall (mm)"])

            st.info(f"**Condition:** {data['Weather']} in {data['City']}")

        else:
            st.error("⚠️ Weather data not available")

    time.sleep(interval)

