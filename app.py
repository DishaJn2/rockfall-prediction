import streamlit as st
import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import requests
import googlemaps
import math

# ------------------ Load Model ------------------
@st.cache_resource
def load_model():
    model = joblib.load("models/rockfall_model.pkl")
    scaler = joblib.load("models/scaler.pkl")
    return model, scaler

model, scaler = load_model()

# ------------------ Load Cities CSV ------------------
@st.cache_data
def load_cities():
    try:
        city_data = pd.read_csv("data/indian_cities.csv")
        city_data["CityState"] = city_data["City"].astype(str) + " (" + city_data["State"].astype(str) + ")"
        return city_data
    except Exception as e:
        st.error(f"Error loading cities: {e}")
        return pd.DataFrame({"CityState": ["Delhi (Delhi)", "Mumbai (Maharashtra)"]})

city_data = load_cities()
city_list = sorted(city_data["CityState"].dropna().unique().tolist())

# ------------------ Weather API ------------------
def get_weather(city="Delhi"):
    API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"   # <-- apna OpenWeatherMap API key daalo
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={API_KEY}&units=metric"
    response = requests.get(url).json()
    if response.get("main"):
        return {
            "Temperature": response["main"]["temp"],
            "Humidity": response["main"]["humidity"],
            "Rainfall": response.get("rain", {}).get("1h", 0)
        }
    else:
        return None

# ------------------ Google Elevation API ------------------
API_KEY_GOOGLE = "AIzaSyCOFmuFUf_LzWiu4sv7twVJpwXJt0ElKMs"   # <-- apna Google API key daalo
gmaps = googlemaps.Client(key=API_KEY_GOOGLE)

def get_slope_from_location(city):
    try:
        geocode = gmaps.geocode(city)
        if not geocode:
            return None
        lat = geocode[0]['geometry']['location']['lat']
        lon = geocode[0]['geometry']['location']['lng']

        point1 = (lat, lon)
        point2 = (lat + 0.01, lon + 0.01)

        elevation1 = gmaps.elevation(point1)[0]['elevation']
        elevation2 = gmaps.elevation(point2)[0]['elevation']

        # Distance calculation
        R = 6371e3
        lat1, lon1, lat2, lon2 = map(math.radians, [lat, lon, lat+0.01, lon+0.01])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        distance = 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

        height_diff = elevation2 - elevation1
        slope_angle = math.degrees(math.atan(abs(height_diff)/distance))

        return round(slope_angle, 2)
    except Exception as e:
        return None

# ------------------ Page Config ------------------
st.set_page_config(page_title="Rockfall Prediction Dashboard", page_icon="⛰️", layout="wide")

st.markdown("<h1 style='text-align:center; color:#1E90FF;'>⛰️ AI-Powered Rockfall Prediction System</h1>", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Prediction", "Heatmap", "AI Assistant"])

# ------------------ Dashboard ------------------
if page == "Dashboard":
    st.header("📊 System Overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Risk Level", "Moderate", "⚠️")
    col2.metric("Active Alerts", "3", "🔴")
    col3.metric("System Status", "✅ Running")

    st.subheader("🌦️ Live Weather Data")
    city_state = st.selectbox("🌍 Select your Location:", city_list, index=0)
    selected_city = city_state.split(" (")[0]

    if st.button("Get Weather"):
        weather = get_weather(selected_city)
        if weather:
            col1, col2, col3 = st.columns(3)
            col1.metric("🌡️ Temp (°C)", weather["Temperature"])
            col2.metric("💧 Humidity (%)", weather["Humidity"])
            col3.metric("🌧️ Rainfall (mm)", weather["Rainfall"])
        else:
            st.error("⚠️ Weather data not available")

    st.subheader("📈 Risk Trend (Weekly)")
    x = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    y = [20, 35, 40, 55, 95, 80, 50]
    fig = px.line(x=x, y=y, markers=True, title="Weekly Risk Level (%)")
    st.plotly_chart(fig, use_container_width=True)

# ------------------ Prediction ------------------
elif page == "Prediction":
    st.header("⚡ Run Rockfall Prediction")

    city_state = st.selectbox("🌍 Select your Location:", city_list, index=0)
    selected_city = city_state.split(" (")[0]

    st.subheader("📡 Real-time Slope Data (Google Elevation API)")
    if st.button("Fetch Slope from Google API"):
        slope_angle = get_slope_from_location(selected_city)
        if slope_angle:
            st.success(f"⛰️ Auto-fetched Slope Angle: {slope_angle}°")
        else:
            st.error("❌ Could not fetch slope data, please use manual input.")
            slope_angle = st.slider("Slope Angle (°)", 10, 80, 40)
    else:
        slope_angle = st.slider("Slope Angle (°)", 10, 80, 40)

    cohesion = st.slider("Cohesion (kPa)", 5, 100, 50)
    friction_angle = st.slider("Internal Friction Angle (°)", 5, 45, 30)
    unit_weight = st.slider("Unit Weight (kN/m³)", 15, 30, 20)
    slope_height = st.slider("Slope Height (m)", 5, 60, 25)

    weather = get_weather(selected_city) or {"Temperature": 25, "Humidity": 50, "Rainfall": 10}

    features = np.array([[unit_weight, cohesion, friction_angle, slope_angle,
                          slope_height, weather["Rainfall"], weather["Temperature"]]])
    scaled = scaler.transform(features)
    prob = model.predict_proba(scaled)[0][1] * 100

    if prob < 30:
        st.success(f"✅ Safe | Risk: {prob:.2f}%")
    elif prob < 60:
        st.warning(f"⚠️ Moderate Risk | Risk: {prob:.2f}%")
    else:
        st.error(f"🚨 High Risk | Risk: {prob:.2f}%")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prob,
        title={'text': "Predicted Risk (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "green"},
                {'range': [30, 60], 'color': "yellow"},
                {'range': [60, 100], 'color': "red"},
            ],
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# ------------------ Heatmap ------------------
elif page == "Heatmap":
    st.header("🗺️ Mine Location Heatmap")
    df = pd.DataFrame({
        "lat": [28.6, 28.7, 28.8],
        "lon": [77.2, 77.3, 77.4],
        "risk": [20, 55, 85]
    })
    m = folium.Map(location=[28.6, 77.2], zoom_start=7)
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=10,
            popup=f"Risk: {row['risk']}%",
            color="red" if row["risk"] > 60 else "orange" if row["risk"] > 30 else "green",
            fill=True,
            fill_opacity=0.6
        ).add_to(m)
    st_folium(m, width=700, height=500)

# ------------------ AI Assistant ------------------
elif page == "AI Assistant":
    st.header("🤖 Rockfall Safety Assistant")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    user_input = st.chat_input("Ask about safety, weather, alerts...")
    if user_input:
        st.session_state["messages"].append(("user", user_input))
        if "safe" in user_input.lower():
            bot_reply = "✅ Slopes with <30% risk are safe."
        elif "moderate" in user_input.lower():
            bot_reply = "⚠️ 30–60% risk requires monitoring."
        elif "high" in user_input.lower():
            bot_reply = "🚨 Slopes with >60% risk are dangerous!"
        elif "weather" in user_input.lower():
            bot_reply = "🌦️ Live weather data is integrated into predictions."
        elif "alert" in user_input.lower():
            bot_reply = "🚨 Zone 5 has a high-risk alert right now."
        elif "system" in user_input.lower():
            bot_reply = "✅ System is operational and sensors are online."
        else:
            bot_reply = "🤖 I can answer about risk, weather, and alerts."
        st.session_state["messages"].append(("bot", bot_reply))

    for role, msg in st.session_state["messages"]:
        if role == "user":
            st.chat_message("user").markdown(msg)
        else:
            st.chat_message("assistant").markdown(msg)


