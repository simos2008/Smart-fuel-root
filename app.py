import streamlit as st
import pandas as pd
import urllib.parse
from geopy.geocoders import Nominatim
import time
import requests

st.set_page_config(page_title="Έξυπνο Δρομολόγιο v11.6", page_icon="🚗", layout="centered")

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

st.title("🚗 Smart Fuel Router v11.6")

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
        geolocator = Nominatim(user_agent="fuel_router_v116_2026")
        location = geolocator.geocode(address + ", Ελλάδα", timeout=10)
        if location: return (location.latitude, location.longitude)
    except: return None
    return None

def expand_and_get_addresses(url):
    try:
        if "maps.app.goo.gl" in url or "goo.gl" in url:
            response = requests.get(url, allow_redirects=True, timeout=10)
            final_url = response.url
        else: final_url = url
        decoded_url = urllib.parse.unquote(final_url)
        stops = []
        if "dir/" in decoded_url:
            dir_part = decoded_url.split("dir/")[1]
            raw_stops = [s.split("@")[0].replace("+", " ").strip() for s in dir_part.split("/") if s.strip()]
            for s in raw_stops:
                if s and not any(x in strip_accents_and_lowercase(s) for x in ["maps", "data", "am="]):
                    stops.append(s)
        else:
            raw_stops = [s.strip() for s in decoded_url.split("/") if s.strip() and "http" not in s]
            for s in raw_stops:
                if len(s) > 5 and not any(x in strip_accents_and_lowercase(s) for x in ["maps", "data", "viewer"]):
                    stops.append(s)
        return stops
    except: return []

def get_osrm_driving_time(origin, destination):
    try:
        coord1 = get_coordinates(origin)
        coord2 = get_coordinates(destination)
        if coord1 and coord2:
            url = f"http://router.project-osrm.org/route/v1/driving/{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}?overview=false"
            res = requests.get(url, timeout=10).json()
            duration_mins = int(res['routes'][0]['duration'] // 60)
            distance_km = res['routes'][0]['distance'] / 1000
            return max(1, duration_mins), round(distance_km, 1)
    except: pass
    return 12, 4.5

# --- ΕΙΣΑΓΩΓΗ ΔΕΔΟΜΕΝΩΝ ---
tab1, tab2 = st.tabs(["📂 Από Excel", "✍️ Χειροκίνητη Εισαγωγή"])

with tab1:
    uploaded_file = st.file_uploader("Ανεβάστε αρχείο Excel", type=["xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, header=1)
            clean_cols = [strip_accents_and_lowercase(c) for c in df.columns]
            c_addr = next((i for i, c in enumerate(clean_cols) if "διευθυνση" in c or "address" in c), 1)
            c_reg = next((i for i, c in enumerate(clean_cols) if "περιοχη" in c or "city" in c), 2)
            c_name = next((i for i, c in enumerate(clean_cols) if "ονομα" in c or "name" in c), 0)
            
            temp_list = []
            for _, row in df.dropna(subset=[df.columns[c_addr]]).iterrows():
                temp_list.append({'name': str(row[df.columns[c_name]]), 'address': f"{row[df.columns[c_addr]]}, {row[df.columns[c_reg]]}"})
            st.session_state.excel_stops = temp_list
            st.success(f"Φορτώθηκαν {len(temp_list)} στάσεις από Excel.")
        except Exception as e: st.error(f"Σφάλμα: {e}")

with tab2:
    st.write("Προσθήκη στάσης:")
    n_in = st.text_input("Όνομα πελάτη (προαιρετικό):")
    a_in = st.text_input("Διεύθυνση:")
    c_in = st.text_input("Περιοχή ή Χωριό:")
    if st.button("Προσθήκη στη λίστα"):
        if a_in and c_in:
            st.session_state.manual_stops.append({'name': n_in or "Νέα Στάση", 'address': f"{a_in}, {c_in}"})
            st.rerun()
        else: st.warning("Συμπληρώστε Διεύθυνση και Περιοχή.")

# --- ΚΟΥΜΠΙ ΕΠΙΒΕΒΑΙΩΣΗΣ ΓΙΑ ΥΠΟΛΟΓΙΣΜΟ ---
if st.button("✅ Επιβεβαίωση και προετοιμασία διαδρομής"):
    st.session_state.final_stops = st.session_state.excel_stops + st.session_state.manual_stops
    st.rerun()

# --- ΕΜΦΑΝΙΣΗ & ΥΠΟΛΟΓΙΣΜΟΙ ---
if st.session_state.final_stops:
    st.subheader(f"Στάσεις προς δρομολόγηση: {len(st.session_state.final_stops)}")
    for i, s in enumerate(st.session_state.final_stops):
        st.write(f"{i+1}. {s['name']} - {s['address']}")

    st.subheader("1️⃣ ΒΗΜΑ: Links για Google Maps")
    chunks = [st.session_state.final_stops[i:i+8] for i in range(0, len(st.session_state.final_stops), 8)]
    curr_start = START_ADDRESS
    for idx, chunk in enumerate(chunks):
        waypoints = [s['address'] for s in chunk]
        end = START_ADDRESS if idx == len(chunks)-1 else waypoints[-1]
        stops_to_url = [curr_start] + waypoints + [end]
        maps_url = "https://www.google.com/maps/dir/" + "/".join([urllib.parse.quote(s) for s in stops_to_url])
        st.markdown(f"🔗 [📲 Άνοιγμα Μέρους {idx+1} στο Google Maps]({maps_url})")
        curr_start = end

    st.subheader("2️⃣ ΒΗΜΑ: Ανάλυση Πραγματικού Χρόνου")
    l1 = st.text_input("Επικόλληση Link Μέρους 1:")
    l2 = st.text_input("Επικόλληση Link Μέρους 2:")
    
    if st.button("📊 Υπολογισμός Χρόνων"):
        for l_idx, link in enumerate([l for l in [l1, l2] if l]):
            routes = expand_and_get_addresses(link)
            if len(routes) >= 2:
                total_time, total_dist, actual_stops = 0, 0, 0
                for i in range(len(routes)-1):
                    t, d = get_osrm_driving_time(routes[i], routes[i+1])
                    total_time += t
                    total_dist += d
                    if not any(x in strip_accents_and_lowercase(routes[i+1]) for x in ["euripidou", "kallithea"]): actual_stops += 1
                st.info(f"Μέρος {l_idx+1}: {total_dist} χλμ | {total_time} λεπτά οδήγησης | {actual_stops} στάσεις.")
            else: st.error("Δεν βρέθηκαν στάσεις.")
                
