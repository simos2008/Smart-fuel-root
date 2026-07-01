import streamlit as st
import pandas as pd
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import openrouteservice
import time
import re

st.set_page_config(page_title="Έξυπνο Δρομολόγιο (Fast v2.2)", page_icon="🚗", layout="centered")

# --- 🔑 OPENROUTESERVICE CONFIGURATION ---
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImIwNGFkYjBlMDFlZTQxMmFiYjc4ODg1OTExNTEzMTc5IiwiaCI6Im11cm11cjY0In0="
try:
    ors_client = openrouteservice.Client(key=ORS_API_KEY)
except Exception as e:
    st.error(f"Σφάλμα αρχικοποίησης OpenRouteService: {e}")

# --- 🌟 SPLASH SCREEN ---
if 'splash_screen_shown' not in st.session_state:
    st.session_state.splash_screen_shown = False

if not st.session_state.splash_screen_shown:
    st.markdown("""
        <style>
        #splash-container {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background-color: #111111; display: flex; flex-direction: column;
            justify-content: center; align-items: center; z-index: 999999; color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .splash-logo { font-size: 80px; animation: bounce 1.5s infinite; }
        .splash-title { font-size: 32px; font-weight: bold; margin-top: 20px; letter-spacing: 2px; }
        .spinner { margin-top: 30px; width: 40px; height: 40px; border: 4px solid rgba(255,255,255,0.1); border-radius: 50%; border-top-color: #ff4b4b; animation: spin 1s ease-in-out infinite; }
        @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
        @keyframes spin { to { transform: rotate(360deg); } }
        </style>
        <div id="splash-container">
            <div class="splash-logo">🚗</div>
            <div class="splash-title">SMART FUEL ROUTER</div>
            <div class="spinner"></div>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(2.5)
    st.session_state.splash_screen_shown = True
    st.rerun()

st.title("🚗 Smart Fuel Router v2.2")
st.write("Υπολογισμός σειράς με βάση τα ωράρια, 20 λεπτά αναμονή ανά παράδοση και τελικά στατιστικά από πραγματικούς δρόμους.")

START_ADDRESS = "Ευριπίδου 36, Καλλιθέα, Αθήνα"
AVERAGE_SPEED_KMH = 30
DELIVERY_DURATION_MINS = 20 

if 'manual_stops' not in st.session_state:
    st.session_state.manual_stops = []

def strip_accents_and_lowercase(s):
    if not isinstance(s, str): return str(s)
    s = s.lower().strip()
    replacements = {'ά':'α','έ':'ε','ή':'η','ί':'ι','ό':'ο','ύ':'υ','ώ':'ω','ϊ':'ι','ϋ':'υ','ΐ':'ι','ΰ':'υ'}
    for acc, raw in replacements.items(): s = s.replace(acc, raw)
    return s

def time_to_minutes(time_str):
    if pd.isna(time_str) or str(time_str).strip() == "" or str(time_str).upper() == "NAN": return 0, 1440
    time_str = str(time_str).replace(" ", "")
    match_range = re.findall(r'(\d{1,2}):(\d{2})', time_str)
    if len(match_range) >= 2:
        return int(match_range[0][0])*60 + int(match_range[0][1]), int(match_range[1][0])*60 + int(match_range[1][1])
    elif len(match_range) == 1:
        ex = int(match_range[0][0])*60 + int(match_range[0][1])
        return max(0, ex-15), min(1440, ex+15)
    return 0, 1440

@st.cache_data(show_spinner=False)
def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="fuel_router_v8_2026")
        location = geolocator.geocode(address + ", Ελλάδα", timeout=10)
        if location: return (location.latitude, location.longitude)
    except: return None
    return None

def get_final_route_details_ors(waypoints_coords):
    try:
        formatted_coords = [[c[1], c[0]] for c in waypoints_coords]
        routes = ors_client.directions(
            coordinates=formatted_coords,
            profile='driving-car',
            format='geojson'
        )
        duration_mins = routes['features'][0]['properties']['summary']['duration'] / 60
        distance_km = routes['features'][0]['properties']['summary']['distance'] / 1000
        return duration_mins, distance_km
    except:
        return None, None

# --- ΦΟΡΤΩΣΗ EXCEL & ΧΕΙΡΟΚΙΝΗΤΑ ---
uploaded_file = st.file_uploader("Ανεβάστε το αρχείο Excel (.xlsx)", type=["xlsx"])

st.markdown("---")
st.subheader("➕ Χειροκίνητη Προσθήκη Στάσης")
col1, col2 = st.columns(2)
with col1:
    m_name = st.text_input("Όνομα / Κατάστημα")
    m_addr = st.text_input("Διεύθυνση")
with col2:
    m_reg = st.text_input("Περιοχή")
    m_time = st.text_input("Ωράριο", value="09:00 - 17:00")

if st.button("Προσθήκη Στάσης στη Λίστα"):
    if m_addr and m_reg:
        st.session_state.manual_stops.append({'name': m_name if m_name else "Χειροκίνητη Στάση", 'address': m_addr, 'region': m_reg, 'time_window': m_time})
        st.success(f"Η στάση '{m_addr}' προστέθηκε!")
    else: st.error("Διεύθυνση και Περιοχή είναι υποχρεωτικά!")

if st.session_state.manual_stops:
    for i, m_stop in enumerate(st.session_state.manual_stops):
        st.write(f"{i+1}. {m_stop['name']} - {m_stop['address']}, {m_stop['region']}")
    if st.button("Καθαρισμός Χειροκίνητων Στάσεων"):
        st.session_state.manual_stops = []
        st.rerun()

stops_base_list = []
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, header=1)
        clean_columns = [strip_accents_and_lowercase(c) for c in df.columns]
        c_addr_idx = next((i for i, c in enumerate(clean_columns) if "διευθυνση" in c or "address" in c), 1)
        c_reg_idx = next((i for i, c in enumerate(clean_columns) if "περιοχη" in c or "city" in c), 2)
        c_name_idx = next((i for i, c in enumerate(clean_columns) if "ονομα" in c or "name" in c), 0)
        c_time_idx = next((i for i, c in enumerate(clean_columns) if "ωρα" in c or "time" in c), None)
        
        actual_addr_col, actual_reg_col, actual_name_col = df.columns[c_addr_idx], df.columns[c_reg_idx], df.columns[c_name_idx]
        actual_time_col = df.columns
        
