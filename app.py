import streamlit as st
import requests

def ulozit_do_dashboardu(data_z_n8n):
    # Tvoje URL adresa Apps Scriptu (ponech tu svou stávající)
    url = "https://script.google.com/macros/s/AKfycbzfRP2cvMrwjbsCgQPzfbQsVABB68OYdpTPajGRT4hbhBbVWoGPJIJJTfMy6PbbhfTwCQ/exec"
    
    # Příprava dat pro Google Sheets
    payload = {
        "sheet": "CZLC4",  # Zde explicitně říkáme, že cílem je list CZLC4
        "row": [
            data_z_n8n.get("rok", 2026),
            data_z_n8n.get("mesic", "Leden"),
            data_z_n8n.get("elektrina_kwh", 0),
            data_z_n8n.get("plyn_kwh", 0),
            data_z_n8n.get("voda_m3", 0)
        ]
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.success(f"Data byla úspěšně zapsána do listu CZLC4")
            return True
        else:
            st.error(f"Chyba při zápisu: {response.text}")
            return False
    except Exception as e:
        st.error(f"Nepodařilo se připojit ke Google Sheets: {e}")
        return False

# Zbytek Streamlit kódu (tlačítko atd.) zůstává stejný...
