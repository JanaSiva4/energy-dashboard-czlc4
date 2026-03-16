import streamlit as st
import pandas as pd
import requests

# Nastavení stránky
st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# Design
st.markdown("""
    <style>
    .stApp { background-color: #001529; color: white; }
    .stButton>button { 
        background: linear-gradient(90deg, #00aaff 0%, #00ff88 100%); 
        color: #001529; font-weight: bold; border: none; border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")

with st.sidebar:
    st.header("Nastavení extrakce")
    vyber = st.multiselect(
        "Co chcete vyčíst?",
        ["Elektřina: Spotřeba (kWh)", "Cena sil. el.", "Cena distribuce", "Cena celkem", "Plyn: Spotřeba (kWh)", "Voda: Spotřeba (m3)"],
        default=["Elektřina: Spotřeba (kWh)", "Cena celkem"]
    )

uploaded_files = st.file_uploader("Nahrajte faktury (PDF)", accept_multiple_files=True, type=['pdf'])

if st.button("🚀 Spustit AI analýzu"):
    if uploaded_files:
        st.info(f"Zpracovávám {len(uploaded_files)} souborů...")
        results = []
        
        # TVOJE URL Z OBRÁZKU (pro testování používáme Test URL)
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook-test/faktury-upload"
        
        for file in uploaded_files:
            files = {"file": (file.name, file.getvalue(), "application/pdf")}
            data = {"parametry": str(vyber)}
            
            try:
                response = requests.post(webhook_url, files=files, data=data)
                if response.status_code == 200:
                    results.append(response.json())
                else:
                    st.error(f"Chyba u {file.name}: n8n vrátilo {response.status_code}")
            except Exception as e:
                st.error(f"Chyba spojení: {e}")

        if results:
            st.success("Hotovo!")
            st.dataframe(pd.DataFrame(results))
    else:
        st.warning("Nahrajte soubory.")
