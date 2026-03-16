import streamlit as st  
import pandas as pd
import requests

# 1. Základní nastavení
st.set_page_config(page_title="CZLC4 Energy Intel Pro", layout="wide")

# 2. DESIGN (CSS) - NEONOVÁ LIŠTA + HOVER EFEKT
st.markdown("""
<style>
    /* Hlavní pozadí */
    .stApp { 
        background: radial-gradient(circle at 10% 20%, rgb(0, 21, 41) 0%, rgb(60, 0, 120) 50%, rgb(0, 0, 0) 100%);
        color: #e0e0e0; 
    }

    /* --- HORNÍ LIŠTA S BLESKOVOU ZÁŘÍ (NEON) --- */
    [data-testid="stHorizontalBlock"] > div > div > div[data-testid="stMetric"] {
        background: rgba(0, 0, 0, 0.3);
        border: 2px solid #00ff96; /* Zelená barva blesku */
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 0 25px rgba(0, 255, 130, 0.4), 0 0 45px rgba(0, 255, 130, 0.2); /* Neonový glow efekt */
        transition: box-shadow 0.3s ease;
    }
    
    /* Bílá čísla v metrikách */
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-weight: 700; }

    /* --- TLAČÍTKO: PRŮHLEDNOST PŘI NAJETÍ (HOVER) --- */
    div.stButton > button {
        background-color: rgba(0, 255, 150, 0.05) !important;
        border: 1px solid #00ff96 !important;
        color: white !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    div.stButton > button:hover {
        opacity: 0.4 !important; /* Efekt průhlednosti */
        background-color: rgba(0, 255, 150, 0.1) !important;
    }

    /* Ostatní prvky v decentní zelené */
    [data-testid="stFileUploadDropzone"], .stMultiSelect div[role="listbox"] {
        border: 1px solid rgba(0, 180, 100, 0.4) !important;
        background-color: rgba(0, 180, 100, 0.05) !important;
    }

    /* Karty ve Finálním přehledu */
    .energy-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        padding: 15px;
        margin-top: 10px;
        border-left: 4px solid transparent;
    }
    .el-glow { border-left-color: #FFD700; box-shadow: 0 4px 15px rgba(255, 215, 0, 0.1); }
    .gas-glow { border-left-color: #FF8C00; box-shadow: 0 4px 15px rgba(255, 140, 0, 0.1); }
    .water-glow { border-left-color: #00BFFF; box-shadow: 0 4px 15px rgba(0, 191, 255, 0.1); }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy Intelligence Pro")

if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

# --- 3. HORNÍ ZÁŘÍCÍ LIŠTA ---
st.write("---")
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno", "9")
with c2: st.metric("Kategorie", "3")
with c3: st.metric("Úspora času", "45 min")
with c4: st.metric("Stav", "Online")
st.write("---")

# --- HLAVNÍ PLOCHA ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.caption("Konfigurace")
    st.file_uploader("Vložte PDF", accept_multiple_files=True)
    vyber = st.multiselect("Pole k vytažení:", 
                           ["ELEKTŘINA: Spotřeba (kWh)", "PLYN: Spotřeba (kWh)", "VODA: Spotřeba (m3)"], 
                           default=["ELEKTŘINA: Spotřeba (kWh)"])
    if st.button("🚀 SPUSTIT ANALÝZU"):
        st.session_state.vysledky = [{"A": 1}] # Demo
        st.rerun()

with col_main:
    st.subheader("📁 Digitální archiv")
    if st.session_state.vysledky:
        st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)
    else:
        st.info("Zatím žádná data k zobrazení.")
