import streamlit as st
import pandas as pd
import urllib.parse
from geopy.geocoders import Nominatim
import time
import requests
import io

st.set_page_config(page_title="Έξυπνο Δρομολόγιο v12.2", page_icon="🚗", layout="centered")

st.title("🚗 Smart Fuel Router v12.2")

START_ADDRESS = "Ευριπίδου 36, Καλλιθέα, Αθήνα"

# Αρχικοποίηση
if 'final_data' not in st.session_state: st.session_state.final_data = []

# --- ΛΕΙΤΟΥΡΓΙΕΣ ---
def get_osrm_driving_time(origin, destination):
    try:
        geolocator = Nominatim(user_agent="fuel_router_v122")
        loc1 = geolocator.geocode(origin, timeout=5)
        loc2 = geolocator.geocode(destination, timeout=5)
        if loc1 and loc2:
            url = f"http://router.project-osrm.org/route/v1/driving/{loc1.longitude},{loc1.latitude};{loc2.longitude},{loc2.latitude}?overview=false"
            res = requests.get(url, timeout=5).json()
            return int(res['routes'][0]['duration'] // 60), round(res['routes'][0]['distance'] / 1000, 1)
    except: pass
    return 12, 4.5

# --- ΕΙΣΑΓΩΓΗ ---
tab1, tab2 = st.tabs(["📂 Από Excel", "✍️ Χειροκίνητη Εισαγωγή"])

with tab1:
    uploaded_file = st.file_uploader("Ανέβασε το αρχείο Excel", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file, header=1)
        # Κρατάμε όλο το row ως dictionary
        st.session_state.final_data = df.to_dict('records')
        st.success(f"Φορτώθηκαν {len(df)} εγγραφές με όλες τις στήλες τους.")

with tab2:
    st.write("Πρόσθεσε στάση:")
    # Δημιουργούμε ένα απλό input για τα βασικά
    cols = st.columns(3)
    with cols[0]: name = st.text_input("Όνομα:")
    with cols[1]: addr = st.text_input("Διεύθυνση:")
    with cols[2]: extra = st.text_input("Τηλέφωνο/Ώρα:")
    
    if st.button("Προσθήκη στη λίστα"):
        st.session_state.final_data.append({"Όνομα": name, "Διεύθυνση": addr, "Στοιχεία": extra})
        st.rerun()

# --- ΑΝΑΛΥΣΗ & ΕΞΑΓΩΓΗ ---
if st.session_state.final_data:
    st.subheader("📋 Επεξεργασία")
    if st.button("📊 Υπολογισμός χρόνων και προετοιμασία Excel"):
        df_final = pd.DataFrame(st.session_state.final_data)
        
        # Υπολογισμός διαδρομών
        times, dists = [], []
        # Υποθέτουμε ότι υπάρχει στήλη "Διεύθυνση" ή "Address"
        addr_col = next((c for c in df_final.columns if "διευθυνση" in str(c).lower() or "address" in str(c).lower()), df_final.columns[0])
        
        stops = [START_ADDRESS] + df_final[addr_col].tolist() + [START_ADDRESS]
        
        results = []
        for i in range(len(stops)-1):
            t, d = get_osrm_driving_time(stops[i], stops[i+1])
            results.append({"Χρόνος(λ)": t, "Απόσταση(χλμ)": d})
            st.write(f"🚗 {stops[i][:15]} -> {stops[i+1][:15]} : {t} λεπτά")

        # Προσθήκη αποτελεσμάτων στο DataFrame
        df_results = pd.DataFrame(results)
        df_final = pd.concat([df_final, df_results], axis=1)

        # Εξαγωγή
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False)
            
        st.download_button("📥 Κατέβασμα Πλήρους Excel", data=buffer.getvalue(), file_name="Πλήρες_Δρομολόγιο.xlsx", mime="application/vnd.ms-excel")
        
