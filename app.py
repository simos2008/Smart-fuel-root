import streamlit as st
import pandas as pd
import urllib.parse
from geopy.geocoders import Nominatim
import time
import requests

st.set_page_config(page_title="Έξυπνο Δρομολόγιο v11.8", page_icon="🚗", layout="centered")

# --- 🌟 SPLASH SCREEN ---
if 'splash_screen_shown' not in st.session_state:
    st.session_state.splash_screen_shown = False

if not st.session_state.splash_screen_shown:
    st.markdown("""
        <style>
        #splash-container { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: #111111; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 999999; color: white; }
        .spinner { margin-top: 30px; width: 40px; height: 40px; border: 4px solid rgba(255,255,255,0.1); border-radius: 50%; border-top-color: #ff4b4b; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        </style>
        <div id="splash-container"><div style="font-size: 50px;">🚗</div><div class="spinner"></div></div>
    """, unsafe_allow_html=True)
    time.sleep(2)
    st.session_state.splash_screen_shown = True
    st.rerun()

st.title("🚗 Smart Fuel Router v11.8")

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
        geolocator = Nominatim(user_agent="fuel_router_v118_2026")
        location = geolocator.geocode(address + ", Ελλάδα", timeout=10)
        return (location.latitude, location.longitude) if location else None
    except: return None

def expand_and_get_addresses(url):
    try:
        decoded_url = urllib.parse.unquote(url)
        stops = []
        if "dir/" in decoded_url:
            dir_part = decoded_url.split("dir/")[1]
            raw_stops = [s.split("@")[0].replace("+", " ").strip() for s in dir_part.split("/") if s.strip()]
            for s in raw_stops:
                if s and not any(x in strip_accents_and_lowercase(s) for x in ["maps", "data", "am="]):
                    stops.append(s)
        return stops
    except: return []

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

if st.button("✅ Επιβεβαίωση συνδυασμένης λίστας"):
    st.session_state.final_stops = st.session_state.excel_stops + st.session_state.manual_stops
    st.rerun()

# --- ΑΝΑΛΥΣΗ ---
if st.session_state.final_stops:
    st.subheader(f"Σύνολο Στάσεων: {len(st.session_state.final_stops)}")
    
    st.subheader("1️⃣ Links για Google Maps")
    chunks = [st.session_state.final_stops[i:i+8] for i in range(0, len(st.session_state.final_stops), 8)]
    curr_start = START_ADDRESS
    for idx, chunk in enumerate(chunks):
        waypoints = [s['address'] for s in chunk]
        end = START_ADDRESS if idx == len(chunks)-1 else waypoints[-1]
        url = "https://www.google.com/maps/dir/" + "/".join([urllib.parse.quote(s) for s in [curr_start] + waypoints + [end]])
        st.markdown(f"🔗 [📲 Μέρος {idx+1}]({url})")
        curr_start = end

    st.subheader("2️⃣ Ανάλυση Χρόνων")
    l1 = st.text_input("Επικόλληση Link 1:")
    l2 = st.text_input("Επικόλληση Link 2:")
    
    if st.button("📊 Υπολογισμός Χρόνων ανά Στάση"):
        for l_idx, link in enumerate([l for l in [l1, l2] if l]):
            routes = expand_and_get_addresses(link)
            if len(routes) >= 2:
                total_time, total_dist, actual_stops = 0, 0, 0
                st.markdown(f"### 📋 Αναλυτικά Μέρους {l_idx+1}")
                for i in range(len(routes)-1):
                    t, d = get_osrm_driving_time(routes[i], routes[i+1])
                    total_time += t
                    total_dist += d
                    if not any(x in strip_accents_and_lowercase(routes[i+1]) for x in ["euripidou", "kallithea"]): actual_stops += 1
                    st.write(f"📍 **Στάση {i+1}:** {routes[i][:25]}... $\rightarrow$ {routes[i+1][:25]}... | 🚗 {t} λεπτά ({d} χλμ)")
                    st.markdown("---")
                st.info(f"📊 **Σύνολα Μέρους {l_idx+1}:** {total_dist} χλμ, {total_time} λεπτά οδήγησης, {actual_stops} στάσεις (Αναμονή: {actual_stops * DELIVERY_DURATION_MINS} λ.)")
            else: st.error("Δεν βρέθηκαν στάσεις στο Link.")
                
