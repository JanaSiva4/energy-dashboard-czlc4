import streamlit as st  
import pandas as pd
import requests

# 1. Základní nastavení
st.set_page_config(page_title="CZLC4 Energy Intel Pro", layout="wide")

# 2. DESIGN (CSS) - SMARAGDOVÁ + NEON GLOW + BÍLÁ ČÍSLA
st.markdown("""
<style>
    /* Hlavní pozadí */
    .stApp { 
        background: radial-gradient(circle at 10% 20%, rgb(0, 21, 41) 0%, rgb(60, 0, 120) 50%, rgb(0, 0, 0) 100%);
        color: #e0e0e0; 
    }

    /* Zelené prvky (místo šedé) */
    [data-testid="stFileUploadDropzone"], .stMultiSelect div[role="listbox"] {
        border: 1px solid rgba(0, 255, 136, 0.3) !important;
        background-color: rgba(0, 255, 136, 0.05) !important;
    }
    
    /* Zářící karty (Glow efekt) */
    .energy-card {
        background: rgba(0, 0, 0, 0.5);
        border-radius: 12px;
        padding: 20px;
        backdrop-filter: blur(15px);
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }

    /* Specifické záře pro barvy */
    .el-glow { border-top: 3px solid #FFD700; box-shadow: 0 0 30px rgba(255, 215, 0, 0.4); }
    .gas-glow { border-top: 3px solid #FF8C00; box-shadow: 0 0 30px rgba(255, 140, 0, 0.4); }
    .water-glow { border-top: 3px solid #00BFFF; box-shadow: 0 0 30px rgba(0, 191, 255, 0.4); }

    /* Texty a bílá čísla */
    .label-text { font-size: 0.8rem; color: #888; text-transform: uppercase; margin-top: 10px; }
    .value-text { font-size: 1.3rem; color: #ffffff !important; font-weight: 600; } /* Čistě bílá čísla */
    
    /* Úprava nadpisů v kartách */
    .card-title { font-size: 1.5rem; font-weight: bold; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
</style>
""", unsafe_allow_html=True)

# HLAVNÍ TITULEK (jen jednou)
st.title("⚡ Energy Intelligence Pro")
st.write("---")

# Inicializace stavu
if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

# --- STATISTIKY ---
pocet = len(st.session_state.vysledky)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno", str(pocet))
with c2: st.metric("Kategorie", "3")
with c3: st.metric("Úspora času", f"{pocet * 5} min")
with c4: st.metric("Stav", "Online")

st.write("---")

# --- BOČNÍ PANEL A ANALÝZA ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.caption("Konfigurace nahrávání")
    uploaded_files = st.file_uploader("Vložte PDF faktury", accept_multiple_files=True, type=['pdf'])

    vyber = st.multiselect(
        "Pole k analýze:",
        ["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem", "PLYN: Spotřeba (kWh)", "PLYN: Cena celkem", "VODA: Spotřeba (m3)"],
        default=["ELEKTŘINA: Spotřeba (kWh)", "PLYN: Spotřeba (kWh)"]
    )
    
    if st.button("🚀 SPUSTIT ANALÝZU", use_container_width=True):
        if uploaded_files:
            st.session_state.vysledky = []
            webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"
            for file in uploaded_files:
                with st.spinner(f"Zpracování..."):
                    try:
                        files = {"data": (file.name, file.getvalue(), "application/pdf")}
                        payload = {"p": str(vyber)} 
                        response = requests.post(webhook_url, files=files, data=payload)
                        if response.status_code == 200:
                            data = response.json()
                            if isinstance(data, list): data = data[0]
                            data["Soubor"] = file.name
                            st.session_state.vysledky.append(data)
                    except:
                        st.error("Chyba spojení s mozkem AI.")
            st.rerun()

with col_main:
    st.subheader("📁 Digitální archiv")
    t1, t2 = st.tabs(["⚡ Energie", "📦 Ostatní"])
    with t1:
        if st.session_state.vysledky:
            st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)
        else:
            st.info("Zatím nebyla nahrána žádná data.")

    # --- ZÁŘÍCÍ PŘEHLED (3 SLOUPCE) ---
    if st.session_state.vysledky:
        st.write("---")
        st.subheader("📊 Finální přehled")
        
        # Třídění dat
        data_el, data_pl, data_vo = [], [], []
        for res in st.session_state.vysledky:
            for k, v in res.items():
                if v and str(v).lower() != "n/a" and k not in ["Soubor", "Faktura"]:
                    item = {"label": k.split(":")[-1].strip(), "val": v}
                    if "ELEKTŘINA" in k.upper(): data_el.append(item)
                    elif "PLYN" in k.upper(): data_pl.append(item)
                    elif "VODA" in k.upper(): data_vo.append(item)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="energy-card el-glow"><div class="card-title">⚡ Elektřina</div>', unsafe_allow_html=True)
            for i in data_el:
                st.markdown(f'<div class="label-text">{i["label"]}</div><div class="value-text">{i["val"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="energy-card gas-glow"><div class="card-title">🔥 Plyn</div>', unsafe_allow_html=True)
            for i in data_pl:
                st.markdown(f'<div class="label-text">{i["label"]}</div><div class="value-text">{i["val"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="energy-card water-glow"><div class="card-title">💧 Voda</div>', unsafe_allow_html=True)
            for i in data_vo:
                st.markdown(f'<div class="label-text">{i["label"]}</div><div class="value-text">{i["val"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
