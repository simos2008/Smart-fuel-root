import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import requests
import io

# Ρύθμιση σελίδας
st.set_page_config(page_title="Έξυπνο Δρομολόγιο v12.5", page_icon="🚗", layout="wide")

st.title("🚗 Smart Fuel Router v12.5")
st.markdown("---")

# Σταθερές
START_ADDRESS = "Ευριπίδου 36, Καλλιθέα, Αθήνα"

# Αρχικοποίηση κατάστασης
if 'final_data' not in st.session_state: 
    st.session_state.final_data = []

# --- ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ ---
def get_osrm_driving_time(origin, destination):
    """Υπολογίζει χρόνο και απόσταση χρησιμοποιώντας το OSRM API."""
    try:
        origin, destination = str(origin), str(destination)
        geolocator = Nominatim(user_agent="fuel_router_v125")
        loc1 = geolocator.geocode(origin, timeout=5)
        loc2 = geolocator.geocode(destination, timeout=5)
        if loc1 and loc2:
            url = f"http://router.project-osrm.org/route/v1/driving/{loc1.longitude},{loc1.latitude};{loc2.longitude},{loc2.latitude}?overview=false"
            res = requests.get(url, timeout=5).json()
            if 'routes' in res and res['routes']:
                return int(res['routes'][0]['duration'] // 60), round(res['routes'][0]['distance'] / 1000, 1)
    except Exception as e:
        st.error(f"Σφάλμα σύνδεσης διαδρομής: {e}")
    return 12, 4.5

# --- UI ΕΙΣΑΓΩΓΗΣ ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📂 Εισαγωγή Δεδομένων")
    tab1, tab2 = st.tabs(["Από Excel", "Χειροκίνητα"])
    
    with tab1:
        uploaded_file = st.file_uploader("Ανέβασε αρχείο .xlsx", type=["xlsx"])
        if uploaded_file:
            df = pd.read_excel(uploaded_file, header=1)
            st.session_state.final_data = df.to_dict('records')
            st.success(f"Επιτυχής εισαγωγή {len(df)} εγγραφών.")
            
    with tab2:
        n_in = st.text_input("Όνομα πελάτη:")
        a_in = st.text_input("Διεύθυνση:")
        c_in = st.text_input("Περιοχή:")
        t_in = st.text_input("Τηλέφωνο:")
        if st.button("Προσθήκη στη λίστα"):
            if a_in:
                st.session_state.final_data.append({"Όνομα": n_in, "Διεύθυνση": a_in, "Περιοχή": c_in, "Τηλέφωνο": t_in})
                st.rerun()

# --- ΠΙΝΑΚΑΣ ΕΠΙΒΕΒΑΙΩΣΗΣ ---
if st.session_state.final_data:
    st.subheader("📋 Τρέχουσες Στάσεις")
    df_display = pd.DataFrame(st.session_state.final_data)
    st.dataframe(df_display, use_container_width=True)
    
    if st.button("🗑️ Καθαρισμός όλων"):
        st.session_state.final_data = []
        st.rerun()

    st.markdown("---")
    st.subheader("📊 Υπολογισμοί & Εξαγωγή")
    if st.button("🚀 Υπολογισμός Διαδρομής"):
        df_final = pd.DataFrame(st.session_state.final_data)
        
        # Εύρεση στήλης διεύθυνσης (αυτόματα)
        addr_col = next((c for c in df_final.columns if "διευθυνση" in str(c).lower() or "address" in str(c).lower()), df_final.columns[0])
        
        stops = [START_ADDRESS] + df_final[addr_col].astype(str).tolist() + [START_ADDRESS]
        results = []
        
        with st.spinner("Υπολογισμός διαδρομών..."):
            for i in range(len(stops)-1):
                t, d = get_osrm_driving_time(stops[i], stops[i+1])
                results.append({"Χρόνος_Αναμονής": t, "Απόσταση_χλμ": d})
                st.write(f"🚗 *{str(stops[i])[:20]}...* ➔ *{str(stops[i+1])[:20]}...* | **{t} λεπτά | {d} χλμ**")
        
        # Ενσωμάτωση αποτελεσμάτων
        df_results = pd.DataFrame(results)
        df_final = pd.concat([df_final, df_results], axis=1)
        
        # Εξαγωγή Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False)
            
        st.download_button(
            label="📥 Κατέβασμα Πλήρους Excel",
            data=buffer.getvalue(),
            file_name="Δρομολογιο_Ολοκληρωμενο.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
