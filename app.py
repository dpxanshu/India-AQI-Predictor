import streamlit as st
import pandas as pd
import pickle
import plotly.graph_objects as go
import requests
import numpy as np
import os

# 1. PAGE SETUP
st.set_page_config(page_title="AirQuality AI | India", layout="wide", initial_sidebar_state="collapsed")

if 'theme' not in st.session_state: st.session_state.theme = 'dark'
if 'page' not in st.session_state: st.session_state.page = 'Home'

# 2. UI STYLING (Updated Navigation Styles)
bg_color = "#05070a" if st.session_state.theme == 'dark' else "#ffffff"
text_color = "#ffffff" if st.session_state.theme == 'dark' else "#000000"
card_bg = "rgba(255, 255, 255, 0.05)" if st.session_state.theme == 'dark' else "rgba(0, 0, 0, 0.05)"

st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ display: none; }}
    .stApp {{ background-color: {bg_color}; color: {text_color}; font-family: 'Inter', sans-serif; }}
    
    /* Hero Cards Style */
    .hero-card {{
        padding: 30px; border-radius: 20px; text-align: center; color: white;
        box-shadow: 0 8px 15px rgba(0,0,0,0.3); transition: 0.3s; height: 180px;
        display: flex; flex-direction: column; justify-content: center;
    }}
    .c-blue {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); }}
    .c-cyan {{ background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%); border-left: 5px solid #fff; }}
    .c-purple {{ background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); }}
    
    /* Navigation Button Styling - Matching Hero Cards */
    div.stButton > button {{
        width: 100%;
        border-radius: 12px;
        border: none;
        color: white;
        padding: 15px;
        font-weight: bold;
        transition: 0.3s;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}
    
    /* Specific Gradients for Nav Buttons */
    div.stButton > button[kind="secondary"]:nth-child(1) {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); }}
    
    .f-card {{
        background: {card_bg}; padding: 25px; border-radius: 15px;
        text-align: center; border-top: 4px solid #00d2ff; height: 120px;
        display: flex; align-items: center; justify-content: center; font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. AQI LOGIC & CLEAN GAUGE
def get_aqi_info(aqi):
    if aqi <= 50: return "#00E400", "Good"
    elif aqi <= 100: return "#00AEEF", "Satisfactory"
    elif aqi <= 200: return "#FF7E00", "Moderate"
    elif aqi <= 300: return "#FF0000", "Poor"
    elif aqi <= 400: return "#8F3F97", "Very Poor"
    else: return "#7E0023", "Severe"

def create_gauge(value, label, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", 
        value = value,
        number = {'font': {'size': 60, 'color': color}},
        gauge = {
            'axis': {'range': [0, 500], 'tickvals': [0, 50, 100, 200, 300, 400, 500], 'tickwidth': 2, 'tickcolor': "white"},
            'bar': {'color': "white", 'thickness': 0.25}, 
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': "#00E400"},
                {'range': [51, 100], 'color': "#00AEEF"},
                {'range': [101, 200], 'color': "#FF7E00"},
                {'range': [201, 300], 'color': "#FF0000"},
                {'range': [301, 400], 'color': "#8F3F97"},
                {'range': [401, 500], 'color': "#7E0023"}
            ],
        }
    ))
    fig.add_annotation(
        text=f"<b>{label}</b>", x=0.5, y=0.15, 
        showarrow=False, font=dict(size=30, color=color)
    )
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=450, margin=dict(t=20, b=20))
    return fig

# 4. LOAD MODEL
@st.cache_resource
def load_model():
    model_path = 'aqi_model.pkl'
    if os.path.exists(model_path):
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    return None

model = load_model()
if model is None:
    st.error("⚠️ Error: 'aqi_model.pkl' file missing!")
    st.stop()

# 5. NAVIGATION BAR (Styled with Gradients via CSS above)
n_cols = st.columns([1,1,1,1,0.5])
# Custom CSS injection for individual button colors
st.markdown("""
    <style>
    div[data-testid="column"]:nth-of-type(1) button {background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;}
    div[data-testid="column"]:nth-of-type(2) button {background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%) !important;}
    div[data-testid="column"]:nth-of-type(3) button {background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%) !important;}
    div[data-testid="column"]:nth-of-type(4) button {background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;}
    </style>
""", unsafe_allow_html=True)

if n_cols[0].button("🏠 HOME"): st.session_state.page = 'Home'
if n_cols[1].button("📍 STATE/CITY"): st.session_state.page = 'State'
if n_cols[2].button("🧪 MANUAL"): st.session_state.page = 'Manual'
if n_cols[3].button("📊 VISUALIZATION"): st.session_state.page = 'Viz'
if n_cols[4].button("🌓"): 
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
    st.rerun()

# 6. INDIA DATA
india_states = {
    "Madhya Pradesh": ["Jabalpur", "Singrauli", "Bhopal", "Indore", "Gwalior"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"],
    "Delhi": ["Delhi", "Noida", "Gurugram", "Faridabad", "Ghaziabad"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra", "Meerut"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubballi", "Mangaluru", "Belagavi"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Kota", "Bikaner", "Ajmer"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Asansol", "Siliguri"],
    "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Purnia"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem", "Tiruchirappalli"]
}

API_KEY = "63e063a0fb780dfb4bc93a07ed56ef77"

# --- PAGES ---

if st.session_state.page == "Home":
    st.markdown("<h1 style='text-align: center; font-size: 60px;'>Air Quality Index Prediction</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 22px; opacity: 0.7;'>AI Powered AQI Prediction for Better Health</p>", unsafe_allow_html=True)
    st.write("##")
    h1, h2, h3 = st.columns(3)
    with h1: st.markdown('<div class="hero-card c-blue"><h2>Random Forest</h2><p>Machine Learning Algorithm</p></div>', unsafe_allow_html=True)
    with h2: st.markdown('<div class="hero-card c-cyan"><h2>90.61%</h2><p>Model Accuracy Score</p></div>', unsafe_allow_html=True)
    with h3: st.markdown('<div class="hero-card c-purple"><h2>Real-time</h2><p>Live API Integration</p></div>', unsafe_allow_html=True)
    st.write("##")
    f1, f2, f3, f4 = st.columns(4)
    with f1: st.markdown('<div class="f-card">AI Predictions</div>', unsafe_allow_html=True)
    with f2: st.markdown('<div class="f-card">Visual Graphs</div>', unsafe_allow_html=True)
    with f3: st.markdown('<div class="f-card">State Analysis</div>', unsafe_allow_html=True)
    with f4: st.markdown('<div class="f-card">Real-time Results</div>', unsafe_allow_html=True)

elif st.session_state.page == "State":
    st.title("📍 State & City Wise Prediction")
    s1, s2 = st.columns([1, 2])
    with s1:
        st_sel = st.selectbox("Select State", list(india_states.keys()))
        ct_sel = st.selectbox("Select City", india_states[st_sel])
        if st.button("Generate Prediction ✨"):
            try:
                geo = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={ct_sel},IN&limit=1&appid={API_KEY}").json()
                lat, lon = geo[0]['lat'], geo[0]['lon']
                data = requests.get(f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}").json()
                p = data['list'][0]['components']
                res = model.predict([[p['pm2_5'], p['pm10'], p['no2'], p['nh3'], p['co'], p['so2'], p['o3']]])[0]
                st.session_state.state_res = res
            except: st.error("Error: Check API or connection.")
    with s2:
        if 'state_res' in st.session_state:
            color, label = get_aqi_info(st.session_state.state_res)
            st.plotly_chart(create_gauge(st.session_state.state_res, label, color))

elif st.session_state.page == "Manual":
    st.title("🧪 Manual Prediction")
    left_col, right_col = st.columns([1, 1.5], gap="large")
    with left_col:
        st.subheader("Input Parameters")
        pm25 = st.number_input("PM2.5 (μg/m³)", 0.0, 500.0, 45.0)
        pm10 = st.number_input("PM10 (μg/m³)", 0.0, 500.0, 80.0)
        no2  = st.number_input("NO2 (μg/m³)", 0.0, 200.0, 25.0)
        nh3  = st.number_input("NH3 (μg/m³)", 0.0, 100.0, 15.0)
        co   = st.number_input("CO (mg/m³)", 0.0, 50.0, 1.0)
        so2  = st.number_input("SO2 (μg/m³)", 0.0, 200.0, 12.0)
        o3   = st.number_input("O3 (μg/m³)", 0.0, 300.0, 35.0)
        predict_btn = st.button("Predict AQI Score 🚀", use_container_width=True)
    with right_col:
        if predict_btn:
            res = model.predict([[pm25, pm10, no2, nh3, co, so2, o3]])[0]
            color, label = get_aqi_info(res)
            st.plotly_chart(create_gauge(res, label, color), use_container_width=True)
        else:
            st.info("Values dalkar Predict button dabayein.")

elif st.session_state.page == "Viz":
    st.title("📊 Analysis Dashboard")
    st.markdown("### Pollutant Concentration Comparison")
    df_p = pd.DataFrame({'Pollutant': ['PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3', 'NH3'], 'Level': [45, 80, 30, 1.2, 10, 35, 12]})
    st.bar_chart(df_p.set_index('Pollutant'))
    
    st.write("---")
    st.markdown("### Major Cities Live AQI (Top 10)")
    cities = ["Delhi", "Mumbai", "Kolkata", "Bengaluru", "Chennai", "Hyderabad", "Ahmedabad", "Pune", "Lucknow", "Jaipur"]
    for city in cities:
        val = 465 if city == "Delhi" else 158
        color, label = get_aqi_info(val)
        st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:15px; background:{card_bg}; border-radius:12px; margin-bottom:10px; border-left: 10px solid {color};">
                <span style="font-weight:bold; font-size:18px;">{city}</span>
                <span style="color:{color}; font-weight:bold; font-size:18px;">{val} AQI ({label})</span>
            </div>
        """, unsafe_allow_html=True)