import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & DESIGN ---
st.set_page_config(page_title="Energy Intelligence Pro", layout="wide")

st.markdown("""
<style>
    .stApp { background: #000c17; color: #e0e0e0; }
    
    /* Glassmorphism karty */
    .energy-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    .el-border { border-top: 5px solid #FFD700; }
    .gas-border { border-top: 5px solid #FF8C00; }
    .water-border { border-top: 5px solid #00BFFF; }

    .label-text { font-size: 0.8rem; color: #888; text-transform: uppercase; margin-top: 10px; }
    .value-text { font-size: 1.2rem; color: #00ff88; font-weight: 300; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy Intelligence Pro")
st.write("---")

# Inicializace stavu (aby nebyly NameError chyby)
if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

# --- 2. SIDEBAR / KONFIGURACE ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.subheader("⚙️ Vložit dokumenty")
    uploaded_files = st.file_uploader("Nahrajte PDF faktury", accept_multiple_files=True, type=['pdf'])
    
    vyber = st.multiselect(
        "Data k vytažení:",
        ["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem (fakturovaná)", 
         "FSX: Spotřeba (kWh)", "FSX: Cena celkem (fakturovaná)",
         "PLYN: Spotřeba (kWh)", "PLYN: Cena celkem (fakturovaná)",
         "VODA: Spotřeba (m3)", "VODA: Cena celkem (fakturovaná)"],
        default=["ELEKTŘINA: Spotřeba (kWh)", "PLYN: Spotřeba (kWh)", "VODA: Spotřeba (m3)"]
    )
    analyze_btn = st.button("🚀 SPUSTIT AI ANALÝZU")

# --- 3. LOGIKA ANALÝZY ---
if analyze_btn and uploaded_files:
    st.session_state.vysledky = [] # Reset starých dat
    webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"

    for file in uploaded_files:
        with st.spinner(f"Analyzuji {file.name}..."):
            try:
                files = {"data": (file.name, file.getvalue(), "application/pdf")}
                payload = {"p": str(vyber)} 
                response = requests.post(webhook_url, files=files, data=payload)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list): data = data[0]
                    st.session_state.vysledky.append(data)
            except:
                st.error("Chyba spojení s AI.")
    st.rerun()

# --- 4. ZOBRAZENÍ VÝSLEDKŮ ---
with col_main:
    # Definujeme prázdné seznamy na začátku každého renderu
    elektro, plyn, voda = [], [], []

    if st.session_state.vysledky:
        # Třídění dat (bez duplicit)
        for res in st.session_state.vysledky:
            for k, v in res.items():
                if v and str(v).lower() != "n/a" and k not in ["Soubor", "Faktura"]:
                    item = {"Parametr": k.split(":")[-1].strip(), "Hodnota": v}
                    if "ELEKTŘINA" in k.upper() or "FSX" in k.upper():
                        if item not in elektro: elektro.append(item)
                    elif "PLYN" in k.upper():
                        if item not in plyn: plyn.append(item)
                    elif "VODA" in k.upper():
                        if item not in voda: voda.append(item)

        # Dashboard zobrazení
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown('<div class="energy-card el-border"><h3>⚡ ELEKTŘINA</h3></div>', unsafe_allow_html=True)
            for i in elektro:
                st.markdown(f'<div class="label-text">{i["Parametr"]}</div><div class="value-text">{i["Hodnota"]}</div>', unsafe_allow_html=True)
        
        with c2:
            st.markdown('<div class="energy-card gas-border"><h3>🔥 PLYN</h3></div>', unsafe_allow_html=True)
            for i in plyn:
                st.markdown(f'<div class="label-text">{i["Parametr"]}</div><div class="value-text">{i["Hodnota"]}</div>', unsafe_allow_html=True)
        
        with c3:
            st.markdown('<div class="energy-card water-border"><h3>💧 VODA</h3></div>', unsafe_allow_html=True)
            for i in voda:
                st.markdown(f'<div class="label-text">{i["Parametr"]}</div><div class="value-text">{i["Hodnota"]}</div>', unsafe_allow_html=True)
    else:
        st.info("Plocha připravena. Nahrajte faktury vlevo.")
