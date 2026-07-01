import streamlit as st
import pandas as pd
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import re

st.set_page_config(page_title="Έξυπνο Δρομολόγιο με Ωράριο", page_icon="🚗", layout="centered")

# --- 🌟 SPLASH SCREEN (HTML/CSS) ---
if 'splash_screen_shown' not in st.session_state:
    st.session_state.splash_screen_shown = False

if not st.session_state.splash_screen_shown:
    # Ενέσιμο στυλ για την οθόνη υποδοχής
    st.markdown("""
        <style>
        #splash-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: #111111;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 999999;
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .splash-logo {
            font-size: 80px;
            animation: bounce 1.5s infinite;
        }
        .splash-title {
            font-size: 32px;
            font-weight: bold;
            margin-top: 20px;
            letter-spacing: 2px;
        }
        .splash-subtitle {
            font-size: 16px;
            color: #888;
            margin-top: 10px;
        }
        .spinner {
            margin-top: 30px;
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255,255,255,0.1);
            border-radius: 50%;
            border-top-color: #ff4b4b;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        </style>
        <div id="splash-container">
            <div class="splash-logo">🚗</div>
            <div class="splash-title">SMART FUEL ROUTER</div>
            <div class="splash-subtitle">Φόρτωση έξυπνου αλγορίθμου...</div>
            <div class="spinner"></div>
        </div>
    """, unsafe_allow_html=True)
    
    # Κρατάει την οθόνη για 2.5 δευτερόλεπτα
    time.sleep(2.5)
    st.session_state.splash_screen_shown = True
    st.rerun()

# --- ΚΥΡΙΩΣ ΕΦΑΡΜΟΓΗ ---
st.title("🚗 Smart Fuel Router")
st.write("Η εφαρμογή υπολογίζει αποστάσεις και ωράρια, επιτρέποντας πισωγυρίσματα αν αυτό επιβάλλεται από τον χρόνο παράδοσης.")

START_ADDRESS = "Ευριπίδου 36, Καλλιθέα, Αθήνα"
AVERAGE_SPEED_KMH = 30

if 'manual_stops' not in st.session_state:
    st.session_state.manual_stops = []

def strip_accents_and_lowercase(s):
    if not isinstance(s, str):
        return str(s)
    s = s.lower().strip()
    replacements = {
        'ά': 'α', 'έ': 'ε', 'ή': 'η', 'ί': 'ι', 'ό': 'ο', 'ύ': 'υ', 'ώ': 'ω',
        'ϊ': 'ι', 'ϋ': 'υ', 'ΐ': 'ι', 'ΰ': 'υ'
    }
    for acc, raw in replacements.items():
        s = s.replace(acc, raw)
    return s

def time_to_minutes(time_str):
    if pd.isna(time_str) or str(time_str).strip() == "" or str(time_str).upper() == "NAN":
        return 0, 1440
    time_str = str(time_str).replace(" ", "")
    match_range = re.findall(r'(\d{1,2}):(\d{2})', time_str)
    if len(match_range) >= 2:
        start_min = int(match_range[0][0]) * 60 + int(match_range[0][1])
        end_min = int(match_range[1][0]) * 60 + int(match_range[1][1])
        return start_min, end_min
    elif len(match_range) == 1:
        exact_min = int(match_range[0][0]) * 60 + int(match_range[0][1])
        return max(0, exact_min - 15), min(1440, exact_min + 15)
    return 0, 1440

@st.cache_data(show_spinner=False)
def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="fuel_router_v8_2026")
        location = geolocator.geocode(address + ", Ελλάδα", timeout=10)
        if location:
            return (location.latitude, location.longitude)
    except:
        return None
    return None

# --- ΦΟΡΤΩΣΗ EXCEL ---
uploaded_file = st.file_uploader("Ανεβάστε το αρχείο Excel (.xlsx)", type=["xlsx"])

st.markdown("---")
st.subheader("➕ Χειροκίνητη Προσθήκη Στάσης")
col1, col2 = st.columns(2)
with col1:
    m_name = st.text_input("Όνομα / Κατάστημα")
    m_addr = st.text_input("Διεύθυνση (π.χ. Πατησίων 50)")
with col2:
    m_reg = st.text_input("Περιοχή (π.χ. Αθήνα)")
    m_time = st.text_input("Ωράριο (π.χ. 10:00 - 12:00)", value="09:00 - 17:00")

if st.button("Προσθήκη Στάσης στη Λίστα"):
    if m_addr and m_reg:
        st.session_state.manual_stops.append({
            'name': m_name if m_name else "Χειροκίνητη Στάση",
            'address': m_addr,
            'region': m_reg,
            'time_window': m_time
        })
        st.success(f"Η στάση '{m_addr}' προστέθηκε επιτυχώς!")
    else:
        st.error("Η Διεύθυνση και η Περιοχή είναι υποχρεωτικά πεδία!")

if st.session_state.manual_stops:
    st.write("**Χειροκίνητες στάσεις που θα συμπεριληφθούν:**")
    for i, m_stop in enumerate(st.session_state.manual_stops):
        st.write(f"{i+1}. {m_stop['name']} - {m_stop['address']}, {m_stop['region']} ({m_stop['time_window']})")
    if st.button("Καθαρισμός Χειροκίνητων Στάσεων"):
        st.session_state.manual_stops = []
        st.rerun()

st.markdown("---")

stops_base_list = []

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, header=1)
        clean_columns = [strip_accents_and_lowercase(c) for c in df.columns]
        
        c_addr_idx = next((i for i, c in enumerate(clean_columns) if "διευθυνση" in c or "address" in c), 1)
        c_reg_idx = next((i for i, c in enumerate(clean_columns) if "περιοχη" in c or "city" in c), 2)
        c_name_idx = next((i for i, c in enumerate(clean_columns) if "ονομα" in c or "name" in c), 0)
        c_time_idx = next((i for i, c in enumerate(clean_columns) if "ωρα" in c or "time" in c), None)
        
        actual_addr_col = df.columns[c_addr_idx]
        actual_reg_col = df.columns[c_reg_idx]
        actual_name_col = df.columns[c_name_idx]
        actual_time_col = df.columns[c_time_idx] if c_time_idx is not None else None
        
        df = df.dropna(subset=[actual_addr_col])
        
        for idx, row in df.iterrows():
            stops_base_list.append({
                'name': str(row[actual_name_col]),
                'address': str(row[actual_addr_col]),
                'region': str(row[actual_reg_col]),
                'time_window': str(row[actual_time_col]) if actual_time_col else None
            })
    except Exception as e:
        st.error(f"Σφάλμα ανάγνωσης Excel: {e}")

for m_stop in st.session_state.manual_stops:
    stops_base_list.append(m_stop)

if stops_base_list:
    with st.spinner("Υπολογισμός συντεταγμένων..."):
        stops_data = []
        start_coords = get_coordinates(START_ADDRESS)
        
        for stop in stops_base_list:
            full_addr = f"{stop['address']}, {stop['region']}"
            coords = get_coordinates(full_addr) or get_coordinates(stop['region'])
            start_m, end_m = time_to_minutes(stop['time_window'])
            
            if coords:
                stops_data.append({
                    'address': full_addr,
                    'coords': coords,
                    'name': stop['name'],
                    'start_time': start_m,
                    'end_time': end_m
                })
            time.sleep(0.1)

    st.subheader("📋 Διαχείριση Παραδόσεων & Απουσιών")
    st.write("Αν κάποιος λείπει, τσεκάρετέ τον για να μεταφερθεί στο τέλος του δρομολογίου:")
    
    postponed_addresses = []
    active_stops = []
    
    for i, stop in enumerate(stops_data):
        is_absent = st.checkbox(f"❌ Λείπει / Κλειστά: {stop['name']} ({stop['address']})", key=f"absent_{i}")
        if is_absent:
            postponed_addresses.append(stop)
        else:
            active_stops.append(stop)

    ordered_stops = []
    current_coords = start_coords
    current_time = 8 * 60
    
    unvisited = active_stops.copy()
    while unvisited:
        best_next = None
        best_score = float('inf')
        best_travel_time = 0
        
        for stop in unvisited:
            dist = geodesic(current_coords, stop['coords']).kilometers
            travel_time_mins = (dist / AVERAGE_SPEED_KMH) * 60
            arrival_time = current_time + travel_time_mins
            
            if arrival_time > stop['end_time']:
                time_penalty = (arrival_time - stop['end_time']) * 10
            elif arrival_time < stop['start_time']:
                time_penalty = stop['start_time'] - arrival_time
            else:
                time_penalty = 0
            
            score = dist + (time_penalty * 0.1)
            if score < best_score:
                best_score = score
                best_next = stop
                best_travel_time = travel_time_mins
        
        if best_next:
            arrival_time = current_time + best_travel_time
            current_time = max(arrival_time, best_next['start_time']) + 10
            ordered_stops.append(best_next['address'])
            current_coords = best_next['coords']
            unvisited.remove(best_next)

    unvisited_postponed = postponed_addresses.copy()
    while unvisited_postponed:
        best_next = None
        best_score = float('inf')
        best_travel_time = 0
        
        for stop in unvisited_postponed:
            dist = geodesic(current_coords, stop['coords']).kilometers
            score = dist
            if score < best_score:
                best_score = score
                best_next = stop
                
        if best_next:
            ordered_stops.append(best_next['address'])
            current_coords = best_next['coords']
            unvisited_postponed.remove(best_next)

    if ordered_stops:
        st.markdown("---")
        st.success("Το δρομολόγιο ενημερώθηκε!")
        
        max_waypoints = 8
        chunks = [ordered_stops[i:i + max_waypoints] for i in range(0, len(ordered_stops), max_waypoints)]
        
        current_start = START_ADDRESS
        for idx, chunk in enumerate(chunks):
            current_destination = START_ADDRESS if idx == len(chunks) - 1 else chunk[-1]
            waypoints = chunk[:-1] if idx < len(chunks) - 1 else chunk
            
            base_url = "https://www.google.com/maps/dir/"
            query_stops = [current_start] + waypoints + [current_destination]
            encoded_stops = [urllib.parse.quote(stop) for stop in query_stops]
            maps_url = base_url + "/".join(encoded_stops)
            
            st.markdown(f"### 📍 Μέρος {idx + 1}")
            st.info(f"🔗 [📲 Άνοιγμα Μέρους {idx + 1} στο Google Maps]({maps_url})")
            current_start = current_destination
            
