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
        geolocator = Nominatim(user_agent="fuel_router_v4_2026")
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
            # Έξυπνη ανάγνωση: Ψάχνουμε σε ποια γραμμή ξεκινάνε τα πραγματικά δεδομένα
            raw_df = pd.read_excel(uploaded_file, header=None)
            header_row = 0
            for i, row in raw_df.iterrows():
                row_str = row.astype(str).str.upper().values
                if any("ΔΙΕΥΘΥΝΣΗ" in s or "ΠΕΡΙΟΧΗ" in s for s in row_str):
                    header_row = i
                    break
            
            df = pd.read_excel(uploaded_file, header=header_row)
            
            # Καθαρισμός ονομάτων στηλών από κενά
            df.columns = df.columns.astype(str).str.strip()
            
            # Δυναμικός εντοπισμός στηλών
            col_address = [c for c in df.columns if "ΔΙΕΥΘΥΝΣΗ" in c.upper()][0]
            col_region = [c for c in df.columns if "ΠΕΡΙΟΧΗ" in c.upper() or "ΠΕΡΙΟΧΉ" in c.upper()][0]
            col_name = [c for c in df.columns if "ΌΝΟΜΑ" in c.upper() or "ΟΝΟΜΑ" in c.upper()][0]
            col_time = [c for c in df.columns if "ΩΡΑ" in c.upper() or "TIME" in c.upper()]
            
            df = df.dropna(subset=[col_address, col_region])
            df['Full_Address'] = df[col_address].astype(str) + ", " + df[col_region].astype(str)
            
            start_coords = get_coordinates(START_ADDRESS)
            
            stops_data = []
            for idx, row in df.iterrows():
                addr = row['Full_Address']
                coords = get_coordinates(addr) or get_coordinates(row[col_region])
                
                t_window = row[col_time[0]] if col_time else None
                start_m, end_m = time_to_minutes(t_window)
                
                if coords:
                    stops_data.append({
                        'address': addr,
                        'coords': coords,
                        'name': row[col_name],
                        'start_time': start_m,
                        'end_time': end_m
                    })
                time.sleep(0.3)

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
                st.error("Δεν βρέθηκαν έγκυρες διευθύνσεις στο αρχείο.")
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
            st.error(f"Σφάλμα επεξεργασίας του Excel: {e}")
                        
