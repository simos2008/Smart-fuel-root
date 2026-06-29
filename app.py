import streamlit as st
import pandas as pd
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import re

st.set_page_config(page_title="Έξυπνο Δρομολόγιο με Ωράριο", page_icon="🚗", layout="centered")

st.title("🚗 Smart Fuel Router")
st.write("Η εφαρμογή υπολογίζει αποστάσεις και ωράρια, επιτρέποντας πισωγυρίσματα αν αυτό επιβάλλεται από τον χρόνο παράδοσης.")

START_ADDRESS = "Ευριπίδου 36, Καλλιθέα, Αθήνα"
AVERAGE_SPEED_KMH = 30

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
        geolocator = Nominatim(user_agent="fuel_router_v6_2026")
        location = geolocator.geocode(address + ", Ελλάδα", timeout=10)
        if location:
            return (location.latitude, location.longitude)
    except:
        return None
    return None

uploaded_file = st.file_uploader("Ανεβάστε το αρχείο Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    with st.spinner("Ανάγνωση αρχείου και υπολογισμός βέλτιστης διαδρομής..."):
        try:
            # Διαβάζουμε το Excel
            df = pd.read_excel(uploaded_file, header=1)
            
            # Καθαρισμός στηλών με τη νέα συνάρτηση
            clean_columns = [strip_accents_and_lowercase(c) for c in df.columns]
            
            # Αντιστοίχιση των στηλών του Simos
            c_addr_idx = next((i for i, c in enumerate(clean_columns) if "διευθυνση" in c or "address" in c), 1)
            c_reg_idx = next((i for i, c in enumerate(clean_columns) if "περιοχη" in c or "city" in c), 2)
            c_name_idx = next((i for i, c in enumerate(clean_columns) if "ονομα" in c or "name" in c), 0)
            c_time_idx = next((i for i, c in enumerate(clean_columns) if "ωρα" in c or "time" in c), None)
            
            actual_addr_col = df.columns[c_addr_idx]
            actual_reg_col = df.columns[c_reg_idx]
            actual_name_col = df.columns[c_name_idx]
            actual_time_col = df.columns[c_time_idx] if c_time_idx is not None else None
            
            df = df.dropna(subset=[actual_addr_col])
            df['Full_Address'] = df[actual_addr_col].astype(str) + ", " + df[actual_reg_col].astype(str)
            
            start_coords = get_coordinates(START_ADDRESS)
            stops_data = []
            
            for idx, row in df.iterrows():
                addr = row['Full_Address']
                coords = get_coordinates(addr) or get_coordinates(str(row[actual_reg_col]))
                
                t_window = row[actual_time_col] if actual_time_col else None
                start_m, end_m = time_to_minutes(t_window)
                
                if coords:
                    stops_data.append({
                        'address': addr,
                        'coords': coords,
                        'name': row[actual_name_col],
                        'start_time': start_m,
                        'end_time': end_m
                    })
                time.sleep(0.2)

            # Αλγόριθμος δρομολόγησης
            ordered_stops = []
            current_coords = start_coords
            current_time = 8 * 60
            unvisited = stops_data.copy()
            
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
                    if arrival_time < best_next['start_time']:
                        current_time = best_next['start_time']
                    else:
                        current_time = arrival_time
                    current_time += 10
                    ordered_stops.append(best_next['address'])
                    current_coords = best_next['coords']
                    unvisited.remove(best_next)
            
            if not ordered_stops:
                st.error("Δεν βρέθηκαν έγκυρες διευθύνσεις προς ανάλυση.")
                st.stop()
                
            max_waypoints = 8
            chunks = [ordered_stops[i:i + max_waypoints] for i in range(0, len(ordered_stops), max_waypoints)]
            
            st.success("Το έξυπνο δρομολόγιο δημιουργήθηκε επιτυχώς!")
            
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
                
        except Exception as e:
            st.error(f"Προέκυψε σφάλμα στην επεξεργασία: {e}")
