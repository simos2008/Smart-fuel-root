import streamlit as st
import pandas as pd
import urllib.parse
import io

st.set_page_config(page_title="Οργανωτής Δρομολογίων v15.0", layout="wide")
st.title("🚗 Smart Fuel Router v15.0")

if 'final_data' not in st.session_state: st.session_state.final_data = []

# --- 1. ΕΙΣΑΓΩΓΗ ---
tab1, tab2 = st.tabs(["📂 Από Excel", "✍️ Χειροκίνητη Εισαγωγή"])
with tab1:
    uploaded_file = st.file_uploader("Ανέβασε Excel", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.session_state.final_data = df.to_dict('records')
        st.success(f"Φορτώθηκαν {len(df)} στάσεις.")
with tab2:
    n, a, c, t, h = st.text_input("Όνομα"), st.text_input("Διεύθυνση"), st.text_input("Περιοχή"), st.text_input("Τηλέφωνο"), st.text_input("Ώρα")
    if st.button("Προσθήκη"):
        st.session_state.final_data.append({"Όνομα": n, "Διεύθυνση": a, "Περιοχή": c, "Τηλέφωνο": t, "Ώρα Παράδοσης": h})
        st.rerun()

# --- 2. ΠΡΟΕΠΙΣΚΟΠΗΣΗ & ΤΕΜΑΧΙΣΜΟΣ ---
if st.session_state.final_data:
    df_all = pd.DataFrame(st.session_state.final_data)
    st.subheader("📋 Συνολική Λίστα Στάσεων")
    st.dataframe(df_all)

    # Ορίζουμε πόσες στάσεις θέλεις ανά διαδρομή (π.χ. 8 στάσεις ανά μέρος)
    CHUNK_SIZE = 8
    
    if st.button("🚀 Δημιουργία Μερών για Google Maps"):
        # Τεμαχισμός της λίστας
        chunks = [df_all[i:i + CHUNK_SIZE] for i in range(0, len(df_all), CHUNK_SIZE)]
        
        st.subheader("🔗 Links για Google Maps")
        for idx, chunk in enumerate(chunks):
            # Φτιάχνουμε το link για κάθε "μέρος"
            addresses = "/".join(chunk['Διεύθυνση'].astype(str))
            url = f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(chunk['Διεύθυνση'].iloc[-1])}&waypoints={urllib.parse.quote(addresses)}&travelmode=driving"
            st.markdown(f"**Μέρος {idx + 1} ({len(chunk)} στάσεις):** [📲 Άνοιγμα στο Maps]({url})")

    # --- 3. ΕΞΑΓΩΓΗ ---
    if st.button("💾 Εξαγωγή Όλων σε Excel"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_all.to_excel(writer, index=False)
        st.download_button("📥 Κατέβασμα", data=buffer.getvalue(), file_name="Πληρες_Δρομολογιο.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
