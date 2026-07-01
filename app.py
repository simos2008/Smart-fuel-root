import streamlit as st
import pandas as pd
import urllib.parse
import io

st.set_page_config(page_title="Έξυπνο Δρομολόγιο v13.0", layout="centered")

st.title("🚗 Smart Fuel Router v13.0")

# Αρχικοποίηση
if 'final_data' not in st.session_state: st.session_state.final_data = []

# --- 1. ΕΙΣΑΓΩΓΗ (Όπως ακριβώς δούλευε) ---
tab1, tab2 = st.tabs(["📂 Από Excel", "✍️ Χειροκίνητη Εισαγωγή"])

with tab1:
    uploaded_file = st.file_uploader("Ανέβασε το αρχείο Excel", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file, header=1)
        st.session_state.final_data = df.to_dict('records')
        st.success(f"Φορτώθηκαν {len(df)} εγγραφές.")

with tab2:
    n_in = st.text_input("Όνομα:")
    a_in = st.text_input("Διεύθυνση:")
    c_in = st.text_input("Περιοχή:")
    t_in = st.text_input("Τηλέφωνο:")
    h_in = st.text_input("Ώρα παράδοσης (προαιρετικό):")
    if st.button("Προσθήκη στη λίστα"):
        st.session_state.final_data.append({
            "Όνομα": n_in, "Διεύθυνση": a_in, "Περιοχή": c_in, 
            "Τηλέφωνο": t_in, "Ώρα Παράδοσης": h_in
        })
        st.rerun()

# --- 2. ΟΠΤΙΚΗ ΕΠΙΒΕΒΑΙΩΣΗ ---
if st.session_state.final_data:
    st.subheader("📋 Τρέχουσες Στάσεις")
    df_preview = pd.DataFrame(st.session_state.final_data)
    st.dataframe(df_preview)

    # --- 3. ΕΞΑΓΩΓΗ ΣΕ EXCEL (Με όλα τα δεδομένα) ---
    if st.button("💾 Κατέβασμα Λίστας σε Excel"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_preview.to_excel(writer, index=False, sheet_name='Δρομολόγιο')
        
        st.download_button(
            label="📥 Λήψη αρχείου",
            data=buffer.getvalue(),
            file_name="Λίστα_Στάσεων.xlsx",
            mime="application/vnd.ms-excel"
        )
        
