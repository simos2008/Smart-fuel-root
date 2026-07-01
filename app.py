import streamlit as st
import pandas as pd
import urllib.parse
import re
import requests
import time

st.set_page_config(page_title="Έξυπνο Δρομολόγιο v13.5", page_icon="🚗", layout="centered")

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

st.title("🚗 Smart Fuel Router v13.5")
st.write("Ανάλυση διαδρομής (χρόνοι προαιρετικοί).")

# Εδώ αλλάζεις τον χρόνο αναμονής αν θες
DELIVERY_DURATION_MINS = 20

def strip_accents_and_lowercase(s):
    if not isinstance(s, str): return str(s)
    s = s.lower().strip()
    replacements = {'ά':'α','έ':'ε','ή':'η','ί':'ι','ό':'ο','ύ':'υ','ώ':'ω','ϊ':'ι','ϋ':'υ','ΐ':'ι','ΰ':'υ'}
    for acc, raw in replacements.items(): s = s.replace(acc, raw)
    return s

def get_addresses_from_link(url):
    try:
        if "maps.app.goo.gl" in url or "goo.gl" in url:
            response = requests.get(url, allow_redirects=True, timeout=10)
            final_url = response.url
        else:
            final_url = url
            
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
    except:
        return []

# --- 2️⃣ ΒΗΜΑ: ΕΠΙΚΟΛΛΗΣΗ ΚΑΙ ΕΙΣΑΓΩΓΗ ΧΡΟΝΩΝ ---
st.subheader("2️⃣ ΒΗΜΑ: Υπολογισμός (Προαιρετικά χρόνοι)")

import_link = st.text_input("🔗 Επικόλληση Link (Απαραίτητο):")
times_input = st.text_input("⏱️ Γράψε τους χρόνους (προαιρετικά, π.χ. 10, 5, 20):")

if st.button("📊 Δημιουργία Αναφοράς"):
    if not import_link:
        st.error("Παρακαλώ βάλε τουλάχιστον ένα Link!")
    else:
        with st.spinner("Ανάγνωση..."):
            detected_routes = get_addresses_from_link(import_link)
            actual_times = []
            
            if times_input:
                try:
                    actual_times = [int(t.strip()) for t in times_input.split(",") if t.strip()]
                except:
                    st.warning("Δεν καταλάβαμε τους χρόνους, θα χρησιμοποιήσουμε μέσο όρο.")
            
            if detected_routes:
                legs_count = len(detected_routes) - 1
                
                # Αν δεν έδωσε χρόνους ή έδωσε λιγότερους, βάζουμε μια default τιμή
                while len(actual_times) < legs_count:
                    actual_times.append(10) 
                    
                st.markdown("### 📋 Αναφορά Διαδρομής")
                
                total_driving = 0
                actual_stops_count = 0
                
                for i in range(legs_count):
                    start_pt = detected_routes[i]
                    end_pt = detected_routes[i+1]
                    driving_time = actual_times[i]
                    
                    is_customer_stop = not any(x in strip_accents_and_lowercase(end_pt) for x in ["euripidou", "eyripidou", "kallithea", "καλλιθεα", "ευριπιδου"])
                    if is_customer_stop:
                        actual_stops_count += 1
                        
                    st.write(f"📍 **Στάση {i+1}:** *{start_pt[:30]}...* $\rightarrow$ *{end_pt[:30]}...* | ⏱️ {driving_time} λεπτά")
                    total_driving += driving_time
                    
                total_waiting = actual_stops_count * DELIVERY_DURATION_MINS
                total_job_time = total_driving + total_waiting
                
                st.info(f"📊 **Σύνολα:** Οδήγηση: {total_driving}λ | Αναμονή: {total_waiting}λ | **Σύνολο: {total_job_time}λ ({total_job_time/60:.1f} ώρες)**")
            else:
                st.error("Δεν βρέθηκαν στάσεις στο Link.")
              
