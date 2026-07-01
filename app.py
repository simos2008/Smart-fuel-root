import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import requests
import io
import time

st.set_page_config(page_title="Έξυπνο Δρομολόγιο v12.7", page_icon="🚗", layout="wide")

st.title("🚗 Smart Fuel Router v12.7")
START_ADDRESS = "Ευριπίδου 36, Καλλιθέα, Αθήνα"

if 'final_data' not in st.session_state: st.session_state.final_data = []

def get_osrm_driving_time(origin, destination):
    try:
        # Αυστηροποίηση αναζήτησης για την Ελλάδα
        geolocator = Nominatim(user_agent="fuel_router_v127")
        loc1 = geolocator.geocode(f"{origin}, Greece", timeout=10)
        loc2 = geolocator.geocode(f"{destination}, Greece", timeout=10)
        
        if loc1 and loc2:
            url = f"http://router.project-osrm.org/route/v1/driving/{loc1.longitude},{loc1.latitude};{loc2.longitude},{loc2.latitude}?overview=false"
            res = requests.get(url, timeout=10).json()
            if 'routes' in res and res['routes']:
                dist_km = round(res['routes'][0]['distance'] / 1000, 1)
                # Αποκλεισμός παραλογισμών (αν πάνω από 500χλμ, μάλλον βρήκε λάθος μέρος)
                if dist_km > 500: return 0, 0
                return int(res['routes'][0]['duration'] // 60), dist_km
    except: pass
    return 0, 0

# --- UI (Ίδιο, με βελτιωμένο πίνακα) ---
tab1, tab2 = st.tabs(["📂 Από Excel", "✍️ Χειροκίνητα"])
with tab1:
    uploaded_file = st.file_uploader("Ανέβασε Excel", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file, header=1)
        st.session_state.final_data = df.to_dict('records')
        st.success("Φορτώθηκαν οι στάσεις.")
with tab2:
    col1, col2 = st.columns(2)
    with col1:
        n_in = st.text_input("Όνομα:")
        a_in = st.text_input("Διεύθυνση:")
    with col2:
        c_in = st.text_input("Περιοχή:")
        h_in = st.text_input("Ώρα παράδοσης:")
    if st.button("Προσθήκη"):
        if a_in:
            st.session_state.final_data.append({"Όνομα": n_in, "Διεύθυνση": a_in, "Περιοχή": c_in, "Ώρα": h_in})
            st.rerun()

if st.session_state.final_data:
    st.subheader("📋 Τρέχουσες Στάσεις")
    df_preview = pd.DataFrame(st.session_state.final_data)
    st.dataframe(df_preview)

    if st.button("🚀 Υπολογισμός Διαδρομής"):
        df_final = pd.DataFrame(st.session_state.final_data)
        addr_col = next((c for c in df_final.columns if "διευθυνση" in str(c).lower() or "address" in str(c).lower()), df_final.columns[0])
        
        stops = [START_ADDRESS] + df_final[addr_col].astype(str).tolist() + [START_ADDRESS]
        results = []
        
        for i in range(len(stops)-1):
            t, d = get_osrm_driving_time(stops[i], stops[i+1])
            time.sleep(1) # Για αποφυγή 429
            results.append({"Χρόνος(λ)": t, "Απόσταση(χλμ)": d})
            st.write(f"🚗 {stops[i][:15]} ➔ {stops[i+1][:15]} : {t} λεπτά, {d} χλμ")
        
        df_final = pd.concat([df_final, pd.DataFrame(results)], axis=1)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False)
        st.download_button("📥 Κατέβασμα Excel", data=buffer.getvalue(), file_name="Δρομολογιο.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
