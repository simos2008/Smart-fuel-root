import streamlit as st
import pandas as pd
import urllib.parse
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import re

st.set_page_config(page_title="Έξυπνο Δρομολόγιο v8.0", page_icon="🚗", layout="centered")

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

st.title("🚗 Smart Fuel Router v8.0")
st.write("Υπολογισμός τελικών στατιστικών με Import/Paste των έτοιμων διαδρομών από το Google Maps.")

START_ADDRESS = "Ευριπίδου 36, Καλλιθέα, Αθήνα"
DELIVERY_DURATION_MINS = 20

# --- ΣΥΝΑΡΤΗΣΗ ΑΝΑΛΥΣΗΣ LINK GOOGLE MAPS ---
def analyze_google_maps_link(url):
    try:
        decoded_url = urllib.parse.unquote(url)
        # Αφαίρεση του base url για να μείνουν μόνο οι διευθύνσεις
        clean_path = decoded_url.replace("https://www.google.com/maps/dir/", "")
        clean_path = clean_path.replace("https://googleusercontent.com/maps.google.com/0", "")
        clean_path = clean_path.replace("http://maps.google.com/", "")
        
        # Διαχωρισμός των στάσεων με βάση το κάθετο "/"
        stops = [s.strip() for s in clean_path.split("/") if s.strip()]
        return stops
    except:
        return []

# --- ΦΟΡΤΩΣΗ EXCEL & ΧΕΙΡΟΚΙΝΗΤΑ ---
uploaded_file = st.file_uploader("Ανεβάστε το αρχείο Excel (.xlsx)", type=["xlsx"])

# [Εδώ μπαίνει η κλασική δομή ανάγνωσης Excel και Χειροκίνητων στάσεων...]
# Για να πάμε γρήγορα στο ψητό, ας πάμε στο κομμάτι του Import των Links:

st.markdown("---")
st.subheader("📥 Εισαγωγή Έτοιμης Διαδρομής (Import Link)")
st.write("Κάντε επικόλληση το Link που μοιραστήκατε από το Google Maps για να υπολογιστούν οι χρόνοι αναμονής και οι στάσεις.")

# Πεδία για Paste έως και 3 Μερών
import_link_1 = st.text_input("🔗 Επικόλληση Link για το Μέρος 1:")
import_link_2 = st.text_input("🔗 Επικόλληση Link για το Μέρος 2 (Προαιρετικό):")

if st.button("📊 Υπολογισμός Στατιστικών από τα Links"):
    links_to_process = [l for l in [import_link_1, import_link_2] if l]
    
    if not links_to_process:
        st.error("Παρακαλώ βάλτε τουλάχιστον ένα έγκυρο Link!")
    else:
        for idx, link in enumerate(links_to_process):
            st.markdown(f"### 📊 Απολογισμός για το Μέρος {idx + 1}")
            
            # Διάβασμα των στάσεων μέσα από το Link
            detected_stops = analyze_google_maps_link(link)
            
            if detected_stops:
                # Οι πραγματικές παραδόσεις είναι όλες οι στάσεις εκτός από την αφετηρία και τον τερματισμό
                # Αν η τελευταία στάση είναι η επιστροφή (Καλλιθέα), δεν μετράει ως αναμονή παράδοσης
                actual_deliveries = 0
                for stop in detected_stops[1:]:
                    if "Ευριπίδου 36" not in stop and "Καλλιθέα" not in stop:
                        actual_deliveries += 1
                
                total_waiting_mins = actual_deliveries * DELIVERY_DURATION_MINS
                
                st.info(f"🔍 **Αναγνωρίστηκαν:** {len(detected_stops)} συνολικά σημεία στο χάρτη.")
                st.write(f"📦 **Πραγματικές Παραδόσεις (Στάσεις):** {actual_deliveries}")
                st.write(f"⏳ **Συνολικός Χρόνος Αναμονής για Παραδόσεις:** {total_waiting_mins} λεπτά ({total_waiting_mins/60:.1f} ώρες)")
                st.caption("ℹ️ Διάβασε τον χρόνο οδήγησης και τα χιλιόμετρα απευθείας από την οθόνη του Google Maps στο Link σου και πρόσθεσε τον χρόνο αναμονής για το τελικό σύνολο.")
            else:
                st.error(f"Δεν μπορέσαμε να διαβάσουμε τις στάσεις από το Μέρος {idx + 1}. Σιγουρευτείτε ότι είναι το σωστό Link.")
                
            
