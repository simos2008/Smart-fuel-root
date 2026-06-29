import streamlit as st
import pandas as pd
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import re

st.set_page_config(page_title="Έξυπνο Δρομολόγιο με Ωράριο", page_icon="🚗", layout="centered")

st.title("🚗 Smart Fuel Router (με Ώρες Παράδοσης)")
st.write("Η εφαρμογή υπολογίζει αποστάσεις και ωράρια, επιτρέποντας πισωγυρίσματα αν αυτό επιβάλλεται από τον χρόνο παράδοσης.")

START_ADDRESS = "Ευριπίδου 36, Καλλιθέα, Αθήνα"
AVERAGE_SPEED_KMH = 30  # Μέση ταχύτητα στην κίνηση της πόλης

# 1. Συνάρτηση μετατροπής ώρας σε λεπτά (π.χ. "09:30" -> 570 λεπτά)
def time_to_minutes(time_str):
    if pd.isna(time_str) or str(time_str).strip() == "" or str(time_str).upper() == "NAN":
        return 0, 1440  # Όλη την ημέρα ελεύθερο
    
    time_str = str(time_str).replace(" ", "")
    # Αναζήτηση για εύρος (π.χ. 10:00-12:00)
    match_range = re.findall(r'(\d{1,2}):(\d{2})', time_str)
    
    if len(match_range) >= 2:
        start_min = int(match_range[0][0]) * 60 + int(match_range[0][1])
        end_min = int(match_range[1][0]) * 60 + int(match_range[1][1])
        return start_min, end_min
    elif len(match_range) == 1:
        # Μονή ώρα (π.χ. 12:30), δίνουμε ένα παράθυρο 30 λεπτών πριν/μετά
        exact_min = int(match_range[0][0]) * 60 + int(match_range[0][1])
        return max(0, exact_min - 15), min(1440, exact_min + 15)
    
    return 0, 1440

@st.cache_data(show_spinner=False)
def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="fuel_router_v3_2026")
        location = geolocator.geocode(address + ", Ελλάδα", timeout=10)
        if location:
            return (location.latitude, location.longitude)
    except:
        return None
    return None

uploaded_file = st.file_uploader("Ανεβάστε το αρχείο Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    with St.spinner("Υπολογισμός βέλτιστης διαδρομής βάσει απόστασης και ωραρίων..."):
        df = pd.read_excel(uploaded_file, header=1)
        df = df.dropna(subset=["Διεύθυνση", "περιοχή"])
        df['Full_Address'] = df['Διεύθυνση'].astype(str) + ", " + df['περιοχή'].astype(str)
        
        start_coords = get_coordinates(START_ADDRESS)
        
        # Προετοιμασία δεδομένων
        stops_data = []
        for idx, row in df.iterrows():
            addr = row['Full_Address']
            coords = get_coordinates(addr) or get_coordinates(row['περιοχή'])
            
            # Εξαγωγή ωραρίου (στήλη 'επιθυμητή ώρα')
            time_col = [c for c in df.columns if 'ΩΡΑ' in c.upper() or 'TIME' in c.upper()]
            t_window = row[time_col[0]] if time_col else None
            start_m, end_m = time_to_minutes(t_window)
            
            if coords:
                stops_data.append({
                    'address': addr,
                    'coords': coords,
                    'name': row['όνομα'],
                    'start_time': start_m,
                    'end_time': end_m,
                    'time_text': str(t_window) if pd.notna(t_window) else "Ελεύθερο"
                })
            time.sleep(0.5)

        # ΑΛΓΟΡΙΘΜΟΣ ΔΡΟΜΟΛΟΓΗΣΗΣ ΜΕ ΠΕΡΙΟΡΙΣΜΟ ΧΡΟΝΟΥ
        ordered_stops = []
        current_coords = start_coords
        current_time = 8 * 60  # Ξεκινάμε στις 08:00 το πρωί (480 λεπτά)
        unvisited = stops_data.copy()
        
        while unvisited:
            best_next = None
            best_score = float('inf') # Συνδυαστικό σκορ (απόσταση + ποινή χρόνου)
            best_travel_time = 0
            
            for stop in unvisited:
                dist = geodesic(current_coords, stop['coords']).kilometers
                travel_time_mins = (dist / AVERAGE_SPEED_KMH) * 60
                arrival_time = current_time + travel_time_mins
                
                # Έλεγχος αν προλαβαίνουμε το παράθυρο
                if arrival_time > stop['end_time']:
                    # Αν έχουμε ήδη αργήσει, βάζουμε μεγάλη ποινή
                    time_penalty = (arrival_time - stop['end_time']) * 10
                elif arrival_time < stop['start_time']:
                    # Αν φτάνουμε νωρίτερα, υπολογίζουμε τον χρόνο αναμονής
                    time_penalty = stop['start_time'] - arrival_time
                else:
                    time_penalty = 0
                
                # Το σκορ επιλέγει τον συνδυασμό μικρότερης απόστασης και λιγότερης αναμονής/καθυστέρησης
                score = dist + (time_penalty * 0.1)
                
                if score < best_score:
                    best_score = score
                    best_next = stop
                    best_travel_time = travel_time_mins
            
            if best_next:
                # Ενημέρωση του ρολογιού της ημέρας
                arrival_time = current_time + best_travel_time
                if arrival_time < best_next['start_time']:
                    current_time = best_next['start_time']  # Περιμένουμε να ανοίξει
                else:
                    current_time = arrival_time
                
                # Προσθήκη χρόνου εξυπηρέτησης (π.χ. 10 λεπτά ανά παράδοση)
                current_time += 10 
                
                ordered_stops.append(best_next['address'])
                current_coords = best_next['coords']
                unvisited.remove(best_next)
        
        # Δημιουργία links για Google Maps (ανά 8 στάσεις)
        max_waypoints = 8
        chunks = [ordered_stops[i:i + max_waypoints] for i in range(0, len(ordered_stops), max_waypoints)]
        
        st.success("Το έξυπνο δρομολόγιο δημιουργήθηκε λαμβάνοντας υπόψη τις ώρες!")
        
        current_start = START_ADDRESS
        for idx, chunk in enumerate(chunks):
            current_destination = START_ADDRESS if idx == len(chunks) - 1 else chunk[-1]
            waypoints = chunk[:-1] if idx < len(chunks) - 1 else chunk
            
            base_url = "https://www.google.com/maps/dir/Evripidou+36,+Kallithea,+Hellas/Kanari+65,+Moschato,+Hellas/data=!4m14!4m13!1m5!1m1!19sChIJr8UCc2q8oRQRQKoZl34N1oc!2m2!1d23.6939065!2d37.9435712!1m5!1m1!19sChIJp8ADQXK8oRQRfYOu3nsAthI!2m2!1d23.6782696!2d37.94782!3e0?entry=gemini&utm_source=gemini&utm_campaign=gem-default"
            query_stops = [current_start] + waypoints + [current_destination]
            encoded_stops = [urllib.parse.quote(stop) for stop in query_stops]
            maps_url = base_url + "/".join(encoded_stops)
            
            st.markdown(f"### 📍 Μέρος {idx + 1}")
            st.info(f"🔗 [📲 Άνοιγμα Μέρους {idx + 1} στο Google Maps]({maps_url})")
            current_start = current_destination
