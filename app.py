import streamlit as st
import pandas as pd
import urllib.parse
import time

st.set_page_config(page_title="Έξυπνο Δρομολόγιο v16.0", page_icon="🚗", layout="centered")

st.title("🚗 Smart Fuel Router v16.0")

# --- ΑΡΧΙΚΟΠΟΙΗΣΗ ΛΙΣΤΑΣ ---
if 'stops' not in st.session_state:
    st.session_state.stops = []

# --- 1. ΕΙΣΑΓΩΓΗ (EXCEL ΚΑΙ ΧΕΙΡΟΚΙΝΗΤΑ) ---
uploaded_file = st.file_uploader("📂 Ανέβασε το αρχείο Excel (προαιρετικά)", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file, header=1)
    # Φορτώνουμε τις διευθύνσεις στη λίστα αν δεν έχουν ήδη φορτωθεί
    if not st.session_state.stops:
        st.session_state.stops = df.iloc[:, 1].dropna().tolist()
        st.success("Οι στάσεις φορτώθηκαν από το Excel!")

st.write("---")
new_address = st.text_input("✍️ Πρόσθεσε χειροκίνητα μία στάση (στη λίστα σου):")
if st.button("➕ Προσθήκη στάσης στη λίστα"):
    if new_address:
        st.session_state.stops.append(new_address)
    else:
        st.error("Γράψε μια διεύθυνση!")

if st.button("🗑️ Καθαρισμός όλων"):
    st.session_state.stops = []
    st.rerun()

# --- 2. ΕΜΦΑΝΙΣΗ ΛΙΣΤΑΣ ---
if st.session_state.stops:
    st.write("### Τρέχουσα Λίστα Στάσεων:")
    for i, stop in enumerate(st.session_state.stops):
        st.write(f"{i+1}. {stop}")

    # --- 3. ΔΗΜΙΟΥΡΓΙΑ LINK ---
    st.subheader("🔗 Δημιουργία Link για τον Courier")
    if st.button("🚀 Παραγωγή Link Διαδρομής"):
        base_url = "https://www.google.com/maps/dir/"
        stops_url = "/".join([urllib.parse.quote(s) for s in st.session_state.stops])
        final_url = base_url + stops_url
        st.markdown(f"### [📲 Άνοιγμα Διαδρομής στο Google Maps]({final_url})")

    # --- 4. ΠΡΟΑΙΡΕΤΙΚΗ ΑΝΑΦΟΡΑ ---
    st.markdown("---")
    st.subheader("📊 Προαιρετικά: Υπολογισμός χρόνων")
    times_input = st.text_input("⏱️ Χρόνοι οδήγησης με κόμμα (π.χ. 10, 5, 20):")
    if st.button("Υπολογισμός"):
        times = [int(t.strip()) for t in times_input.split(",")] if times_input else []
        st.info(f"Συνολικός χρόνος: {sum(times) if times else 'Δεν δόθηκαν χρόνοι'} λεπτά.")
        
