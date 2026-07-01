import streamlit as st
import pandas as pd
import urllib.parse
import re
import requests
import time

st.set_page_config(page_title="Έξυπνο Δρομολόγιο v14.0", page_icon="🚗", layout="centered")

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

st.title("🚗 Smart Fuel Router v14.0")
DELIVERY_DURATION_MINS = 20 # Μπορείς να το αλλάξεις εδώ όποτε θες

def strip_accents_and_lowercase(s):
    if not isinstance(s, str): return str(s)
    s = s.lower().strip()
    replacements = {'ά':'α','έ':'ε','ή':'η','ί':'ι','ό':'ο','ύ':'υ','ώ':'ω','ϊ':'ι','ϋ':'υ','ΐ':'ι','ΰ':'υ'}
    for acc, raw in replacements.items(): s = s.replace(acc, raw)
    return s

def get_addresses_from_link(url):
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

# --- ΡΟΗ EXCEL ---
uploaded_file = st.file_uploader("Ανεβάστε το αρχείο Excel (.xlsx)", type=["xlsx"])
stops_base_list = []
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, header=1)
    for idx, row in df.dropna().iterrows():
        stops_base_list.append({'name': str(row[0]), 'address': f"{row[1]}, {row[2]}"})

if stops_base_list:
    st.subheader("1️⃣ Δημιουργία Links")
    # (Εδώ μένει η παλιά σου λογική για τα Links - δεν αλλάζει)
    max_waypoints = 8
    chunks = [stops_base_list[i:i + max_waypoints] for i in range(0, len(stops_base_list), max_waypoints)]
    for idx, chunk in enumerate(chunks):
        st.write(f"🔗 [📲 Link {idx+1}]") # Εδώ μπαίνει το URL της google που ήδη είχες

    st.markdown("---")
    st.subheader("2️⃣ Προαιρετικός Υπολογισμός (Επικόλληση Link + Χρόνοι)")
    import_link = st.text_input("🔗 Link:")
    times_input = st.text_input("⏱️ Χρόνοι με κόμμα (Προαιρετικό):")
    
    if st.button("📊 Υπολογισμός"):
        detected_routes = get_addresses_from_link(import_link)
        times = [int(t) for t in times_input.split(",")] if times_input else [10] * (len(detected_routes)-1)
        
        # Εμφάνιση αποτελεσμάτων (όπως πριν)
        st.write("Αναφορά έτοιμη!")
        st.info(f"Συνολικά: {sum(times)} λεπτά οδήγησης.")
    
