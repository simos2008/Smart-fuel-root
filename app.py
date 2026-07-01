import streamlit as st
import pandas as pd
import urllib.parse
from geopy.geocoders import Nominatim
import time
import requests

st.set_page_config(page_title="Έξυπνο Δρομολόγιο v12.0", page_icon="🚗", layout="centered")

# --- 🌟 SPLASH SCREEN ---
if 'splash_screen_shown' not in st.session_state:
    st.session_state.splash_screen_shown = False

if not st.session_state.splash_screen_shown:
    st.markdown("""
        <style>
        #splash-container { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: #111111; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 999999; color: white; }
        .splash-logo { font-size: 80px; animation: bounce 1.5s infinite; }
        .splash-title { font-size: 32px; font-weight: bold; margin-top: 20px; letter-spacing: 2px; }
        .spinner { margin-top: 30px; width: 40px; height: 40px; border: 4px solid rgba(255,255,255,0.1); border-radius: 50%; border-top-color: #ff4b4b; animation: spin 1s linear infinite; }
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

st.title("🚗 Smart Fuel Router v12.0")

START_ADDRESS = "Ευριπίδου 36, Καλλιθέα, Αθήνα"
DELIVERY_DURATION_MINS = 20

# Αρχικοποίηση session states
if 'manual_stops' not in st.session_state: st.session_state.manual_stops = []
if 'excel_stops' not in st.session_state: st.session_state.excel_stops = []
if 'final_stops' not in st.session_state: st.session_state.final_stops = []

def strip_accents_and_lowercase(s):
    if not isinstance(s, str): return str(s)
    s = s.lower().strip()
    replacements = {'ά':'α','έ':'ε','ή':'η','ί':'ι','ό':'ο','ύ':'υ','ώ':'ω','ϊ':'ι','ϋ':'υ','ΐ':'ι','ΰ':'υ'}
    for acc, raw in replacements.items(): s = s.replace(acc, raw)
    return s

@st.cache_data(show_spinner=False)
def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="fuel_router_v120_2026")
        location = geolocator.geocode(address + ", Ελλάδα", timeout=10)
        return (location.latitude, location.longitude) if location else None
    except: return None

def get_osrm_driving_time(origin, destination):
    try:
        coord1, coord2 = get_coordinates(origin), get_coordinates(destination)
        if coord1 and coord2:
            url = f"http://router.project-osrm.org/route/v1/driving/{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}?overview=false"
            res = requests.get(url, timeout=10).json()
            return int(res['routes'][0]['duration'] // 60), round(res['routes'][0]['distance'] / 1000, 1)
    except: pass
    return 12, 4.5

# --- UI ΕΙΣΑΓΩΓΗΣ ---
tab1, tab2 = st.tabs(["📂 Από Excel", "✍️ Χειροκίνητη Εισαγωγή"])

with tab1:
    uploaded_file = st.file_uploader("Ανέβασε το αρχείο Excel", type=["xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, header=1)
            clean_cols = [strip_accents_and_lowercase(c) for c in df.columns]
            c_addr = next((i for i, c in enumerate(clean_cols) if "διευθυνση" in c or "address" in c), 1)
            c_reg = next((i for i, c in enumerate(clean_cols) if "περιοχη" in c or "city" in c), 2)
            c_name = next((i for i, c in enumerate(clean_cols) if "ονομα" in c or "name" in c), 0)
            
            temp = []
            for _, row in df.dropna(subset=[df.columns[c_addr]]).iterrows():
                temp.append({'name': str(row[df.columns[c_name]]), 'address': f"{row[df.columns[c_addr]]}, {row[df.columns[c_reg]]}"})
            st.session_state.excel_stops = temp
            st.success(f"Φορτώθηκαν {len(temp)} στάσεις από το Excel.")
        except Exception as e: st.error(f"Σφάλμα ανάγνωσης Excel: {e}")

with tab2:
    n_in = st.text_input("Όνομα πελάτη (προαιρετικό):")
    a_in = st.text_input("Διεύθυνση:")
    c_in = st.text_input("Περιοχή ή Χωριό:")
    if st.button("Προσθήκη στη λίστα"):
        if a_in and c_in:
            st.session_state.manual_stops.append({'name': n_in or "Νέα Στάση", 'address': f"{a_in}, {c_in}"})
            st.rerun()
        else: st.warning("Συμπλήρωσε Διεύθυνση και Περιοχή.")

if st.button("✅ Επιβεβαίωση συνδυασμένης λίστας"):
    st.session_state.final_stops = st.session_state.excel_stops + st.session_state.manual_stops
    st.rerun()

# --- ΑΝΑΛΥΣΗ ---
if st.session_state.final_stops:
    st.subheader(f"Στάσεις: {len(st.session_state.final_stops)}")
    
    # 1. Links για Google Maps
    st.subheader("1️⃣ Links για Google Maps")
    chunks = [st.session_state.final_stops[i:i+8] for i in range(0, len(st.session_state.final_stops), 8)]
    curr_start = START_ADDRESS
    for idx, chunk in enumerate(chunks):
        waypoints = [s['address'] for s in chunk]
        end = START_ADDRESS if idx == len(chunks)-1 else waypoints[-1]
        url = "https://www.google.com/maps/dir/" + "/".join([urllib.parse.quote(s) for s in [curr_start] + waypoints + [end]])
        st.markdown(f"🔗 [📲 Μέρος {idx+1}]({url})")
        curr_start = end

    # 2. Ανάλυση Χρόνων απευθείας από τη λίστα
    st.subheader("2️⃣ Ανάλυση Χρόνων")
    if st.button("📊 Υπολογισμός πραγματικών χρόνων"):
        stops = [START_ADDRESS] + [s['address'] for s in st.session_state.final_stops] + [START_ADDRESS]
        total_time, total_dist = 0, 0
        
        st.markdown("### 📋 Αναλυτικά ανά στάση")
        for i in range(len(stops)-1):
            t, d = get_osrm_driving_time(stops[i], stops[i+1])
            total_time += t
            total_dist += d
            st.write(f"📍 **Στάση {i+1}:** {stops[i][:20]}... $\rightarrow$ {stops[i+1][:20]}... | 🚗 {t} λεπτά ({d} χλμ)")
            st.markdown("---")
            
        st.info(f"📊 **Σύνολα:** {total_dist} χλμ | {total_time} λεπτά καθαρής οδήγησης | {len(st.session_state.final_stops)} στάσεις")
        
