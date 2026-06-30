import streamlit as st
import zipfile
import sqlite3
import os
import uuid
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom

st.set_page_config(page_title="JW to BTNotes XML", page_icon="📚", layout="wide")

st.title("📚 Μετατροπέας JW Library σε BTNotes XML")
st.write("Αυτό το εργαλείο μετατρέπει τις σημειώσεις σας σε μορφή συμβατή με το **Bible Talks Notes XML**, διατηρώντας τη δομή φακέλων.")

BIBLE_BOOKS = {
    1: "Γένεση", 2: "Έξοδος", 3: "Λευιτικό", 4: "Αριθμοί", 5: "Δευτερονόμιο",
    6: "Ιησούς του Ναυή", 7: "Κριτές", 8: "Ρουθ", 9: "Α΄ Σαμουήλ", 10: "Β΄ Σαμουήλ",
    11: "Α΄ Βασιλέων", 12: "Β΄ Βασιλέων", 13: "Α΄ Χρονικών", 14: "Β΄ Χρονικών",
    15: "Έσδρας", 16: "Νεεμίας", 17: "Εσθήρ", 18: "Ιώβ", 19: "Ψαλμοί",
    20: "Παροιμίες", 21: "Εκκλησιαστής", 22: "Άσμα Ασμάτων", 23: "Ησαΐας",
    24: "Ιερεμίας", 25: "Θρήνοι", 26: "Ιεζεκιήλ", 27: "Δανιήλ", 28: "Ωσηέ",
    29: "Ιωήλ", 30: "Αμώς", 31: "Αβδιού", 32: "Ιωνάς", 33: "Μιχαίας",
    34: "Ναούμ", 35: "Αββακούμ", 36: "Σοφονίας", 37: "Αγγαίος", 38: "Ζαχαρίας",
    39: "Μαλαχίας", 40: "Κατά Ματθαίον", 41: "Κατά Μάρκον", 42: "Κατά Λουκάν",
    43: "Κατά Ιωάννην", 44: "Πράξεις", 45: "Ρωμαίους", 46: "Α΄ Κορινθίους",
    47: "Β΄ Κορινθίους", 48: "Γαλάτες", 49: "Εφεσίους", 50: "Φιλιππησίους",
    51: "Κολοσσαείς", 52: "Α΄ Θεσσαλονικείς", 53: "Β΄ Θεσσαλονικείς",
    54: "Α΄ Τιμόθεο", 55: "Β΄ Τιμόθεο", 56: "Τίτο", 57: "Φιλήμονα",
    58: "Εβραίους", 59: "Ιακώβου", 60: "Α΄ Πέτρου", 61: "Β΄ Πέτρου",
    62: "Α΄ Ιωάννη", 63: "Β΄ Ιωάννη", 64: "Γ΄ Ιωάννη", 65: "Ιούδα",
    66: "Αποκάλυψη"
}

uploaded_file = st.file_uploader("Ανεβάστε το αρχείο .jwlibrary", type=["jwlibrary"])

if uploaded_file is not None:
    with open("temp_backup.zip", "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    with zipfile.ZipFile("temp_backup.zip", "r") as zip_ref:
        zip_ref.extractall("temp_extracted")
        
    db_path = "temp_extracted/UserData.db"
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ερώτημα για την εξαγωγή των σημειώσεων
        query = """
            SELECT 
                L.BookNumber, 
                L.ChapterNumber, 
                L.VerseNumber, 
                N.Title, 
                N.Content, 
                N.Created
            FROM Note N
            JOIN Location L ON N.LocationId = L.LocationId
            WHERE L.BookNumber IS NOT NULL 
              AND L.KeySymbol IS NULL;
        """
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                st.subheader(f"📊 Βρέθηκαν {len(rows)} σημειώσεις.")
                
                # Δημιουργία της ρίζας του XML όπως το BTNotes
                root = ET.Element("db", serverCounter=str(len(rows) + 50))
                
                # 1. Προσθήκη δομής Φακέλων (<folders>)
                folders_element = ET.SubElement(root, "folders")
                
                # Δημιουργούμε έναν κεντρικό custom φάκελο για το Import
                import_folder_uuid = str(uuid.uuid4())
                ET.SubElement(folders_element, "folder", {
                    "id": "1001",
                    "uuid": import_folder_uuid,
                    "name": "Εισαγωγή από JW Library",
                    "parent": "null",
                    "password": "null"
                })
                
                # 2. Προσθήκη Σημειώσεων (<talks>)
                talks_element = ET.SubElement(root, "talks", number=str(len(rows)))
                
                current_timestamp = str(int(time.time() * 1000))
                
                for idx, row in enumerate(rows, start=1):
                    book_num, chapter, verse, title_text, content_text, created_date = row
                    
                    book_name = BIBLE_BOOKS.get(book_num, "Άγνωστο Βιβλίο")
                    verse_ref = f"{book_name} {chapter}:{verse}"
                    
                    # Καθορισμός Τίτλου
                    final_title = str(title_text) if title_text and str(title_text).strip() != "None" else verse_ref
                    final_content = str(content_text) if content_text else ""
                    
                    # Δημιουργία του <talk>
                    talk_uuid = str(uuid.uuid4())
                    talk_node = ET.SubElement(talk_element, "talk", {
                        "id": str(idx + 100),
                        "uuid": talk_uuid,
                        "last_created": "1",
                        "lang": "64",  # Ελληνικά / Default τιμή εφαρμογής
                        "date": current_timestamp,
                        "last_open": current_timestamp,
                        "folder": import_folder_uuid  # Σύνδεση με τον φάκελο που φτιάξαμε
                    })
                    
                    title = ET.SubElement(talk_node, "title")
                    title.text = final_title
                    
                    speaker = ET.SubElement(talk_node, "speaker")
                    speaker.text = "JW Library"
                    
                    # Δημιουργία παραγράφων εσωτερικά
                    paragrafs = ET.SubElement(talk_node, "paragrafs")
                    paragraf = ET.SubElement(paragrafs, "paragraf", {
                        "id": str(idx + 5000),
                        "orden": "0",
                        "indent": "1",
                        "color": "-1",
                        "created": current_timestamp
                    })
                    
                    text = ET.SubElement(paragraf, "text")
                    text.text = final_content
                    
                    # Προσθήκη συνδέσμου εδαφίου αν υπάρχει
                    verses = ET.SubElement(paragraf, "verses")
                    # Μπορούμε να αφήσουμε το <verses /> κενό ή να το γεμίσουμε αν η εφαρμογή απαιτεί jw εσωτερικά IDs.
                    # Για ασφάλεια το αφήνουμε έτοιμο ως tag.
                
                # Μορφοποίηση του XML αρχείου για να είναι ευανάγνωστο
                xml_str = ET.tostring(root, encoding='utf-8')
                parsed_xml = minidom.parseString(xml_str)
                pretty_xml = parsed_xml.toprettyxml(indent="    ", encoding="utf-8")
                
                # Αποθήκευση
                xml_filename = "jw_btnotes_import.xml"
                with open(xml_filename, "wb") as f:
                    f.write(pretty_xml)
                
                st.markdown("---")
                st.success("Το αρχείο XML για το Bible Talks Notes δημιουργήθηκε με επιτυχία!")
                
                with open(xml_filename, "rb") as f:
                    st.download_button(
                        label="📥 Κατεβάστε το αρχείο .xml",
                        data=f,
                        file_name="jw_to_btnotes.xml",
                        mime="application/xml"
                    )
            else:
                st.warning("Δεν βρέθηκαν σημειώσεις βιβλικών εδαφίων στο αρχείο.")
        except Exception as e:
            st.error(f"Σφάλμα κατά την επεξεργασία της βάσης: {e}")
    else:
        st.error("Το αρχείο δεν περιέχει έγκυρη βάση δεδομένων UserData.db.")
      
