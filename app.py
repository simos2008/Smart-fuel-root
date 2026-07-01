import streamlit as st
import pandas as pd
import urllib.parse
import io

st.set_page_config(page_title="Smart Fuel Router", layout="wide")
st.title("🚗 Smart Fuel Router - Τελική Έκδοση")

if 'final_data' not in st.session_state: st.session_state.final_data = []

# --- 1. ΕΙΣΑΓΩΓΗ ---
uploaded_file = st.file_uploader("Ανέβασε το αρχείο σου", type=["xlsx", "csv"])
if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    st.session_state.final_data = df.to_dict('records')

# Χειροκίνητη εισαγωγή (για να ενσωματώνεται στη λίστα)
with st.expander("➕ Προσθήκη Χειροκίνητης Στάσης"):
    n, a, p, t, h = st.text_input("Όνομα"), st.text_input("Διεύθυνση"), st.text_input("Περιοχή"), st.text_input("Τηλέφωνο"), st.text_input("Επιθυμητή ώρα")
    if st.button("Προσθήκη"):
        st.session_state.final_data.append({"όνομα": n, "Διεύθυνση": a, "περιοχή": p, "τηλέφωνο": t, "επιθυμητή ώρα": h})
        st.rerun()

# --- 2. ΕΠΕΞΕΡΓΑΣΙΑ & ΔΙΑΧΩΡΙΣΜΟΣ ---
if st.session_state.final_data:
    df_all = pd.DataFrame(st.session_state.final_data)
    st.write("### 📋 Συνολική Λίστα (", len(df_all), "στάσεις)")
    st.dataframe(df_all)

    # Διαχωρισμός ανά 7 στάσεις
    CHUNK = 7
    st.subheader("🔗 Δρομολόγια για Google Maps")
    
    for i in range(0, len(df_all), CHUNK):
        part = df_all.iloc[i:i+CHUNK]
        # Χρησιμοποιούμε τη στήλη 'Διεύθυνση' που υπάρχει στο αρχείο σου
        addresses = [str(x) for x in part['Διεύθυνση'].tolist()]
        
        # Κατασκευή URL
        start = "Ευριπίδου 36, Καλλιθέα"
        url = f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(start)}&destination={urllib.parse.quote(addresses[-1])}&waypoints={urllib.parse.quote('|'.join(addresses[:-1]))}&travelmode=driving"
        
        st.markdown(f"**Μέρος {i//CHUNK + 1}:** [📲 Άνοιγμα στο Maps]({url})")

    # --- 3. ΕΞΑΓΩΓΗ ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_all.to_excel(writer, index=False)
    st.download_button("💾 Κατέβασμα Ολοκληρωμένου Excel", buffer.getvalue(), "Δρομολογιο.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
