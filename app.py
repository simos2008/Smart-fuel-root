import streamlit as st
import pandas as pd
import urllib.parse
import time

st.set_page_config(page_title="Έξυπνο Δρομολόγιο v15.0", page_icon="🚗", layout="centered")

st.title("🚗 Smart Fuel Router v15.0")
DELIVERY_DURATION_MINS = 20

# --- ΔΙΑΧΕΙΡΙΣΗ ΣΤΑΣΕΩΝ ---
if 'stops' not in st.session_state:
    st.session_state.stops = []

st.subheader("1️⃣ Επιλογή: Εισαγωγή Στάσεων")
tab1, tab2 = st.tabs(["📂 Από Excel", "✍️ Χειροκίνητα"])

with tab1:
    uploaded_file = st.file_uploader("Ανέβασε το αρχείο Excel", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file, header=1)
        # Υποθέτουμε ότι οι διευθύνσεις είναι στη στήλη που περιέχει "διευθυνση"
        st.session_state.stops = df.iloc[:, 1].dropna().tolist()
        st.success("Οι στάσεις φορτώθηκαν από το Excel!")

with tab2:
    new_address = st.text_input("Πρόσθεσε διεύθυνση (μόνο αυτή είναι υποχρεωτική):")
    if st.button("➕ Προσθήκη Στάσης"):
        if new_address:
            st.session_state.stops.append(new_address)
        else:
            st.error("Η διεύθυνση είναι υποχρεωτική!")
    
    if st.button("🗑️ Καθαρισμός Λίστας"):
        st.session_state.stops = []

# --- ΕΜΦΑΝΙΣΗ ΛΙΣΤΑΣ ---
if st.session_state.stops:
    st.write("### Τρέχουσες Στάσεις:")
    for i, stop in enumerate(st.session_state.stops):
        st.write(f"{i+1}. {stop}")

    # --- 2️⃣ ΔΗΜΙΟΥΡΓΙΑ LINK ---
    st.subheader("2️⃣ Δημιουργία Link για τον Courier")
    if st.button("🔗 Παραγωγή Link Διαδρομής"):
        # Logiki gia dimiourgia link (opws tin eixes)
        base_url = "https://www.google.com/maps/dir/"
        stops_url = "/".join([urllib.parse.quote(s) for s in st.session_state.stops])
        final_url = base_url + stops_url
        st.markdown(f"### [📲 Άνοιγμα Διαδρομής στο Google Maps]({final_url})")

    # --- 3️⃣ ΧΕΙΡΟΚΙΝΗΤΗ ΕΙΣΑΓΩΓΗ ΧΡΟΝΩΝ (ΠΡΟΑΙΡΕΤΙΚΑ) ---
    st.markdown("---")
    st.subheader("3️⃣ Αναφορά (Προαιρετικά)")
    times_input = st.text_input("⏱️ Χρόνοι οδήγησης ανά στάση (π.χ. 10, 5, 20):")
    
    if st.button("📊 Υπολογισμός Στατιστικών"):
        times = [int(t.strip()) for t in times_input.split(",")] if times_input else [10] * len(st.session_state.stops)
        st.info(f"Συνολικός χρόνος οδήγησης: {sum(times)} λεπτά.")
        st.info(f"Συνολικός χρόνος αναμονής ({len(st.session_state.stops)} στάσεις): {len(st.session_state.stops) * DELIVERY_DURATION_MINS} λεπτά.")
        
