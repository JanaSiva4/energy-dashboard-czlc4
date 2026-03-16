import streamlit as st  
import pandas as pd
import requests

# 1. Konfigurace
st.set_page_config(page_title="CZLC4 Energy Intel Pro", layout="wide")

# 2. FINÁLNÍ DESIGN (ZELENÁ + NEONOVÉ BLESKY)
st.markdown("""
<style>
    /* Hlavní pozadí */
    .stApp { 
        background: radial-gradient(circle at 10% 20%, rgb(0, 21, 41) 0%, rgb(60, 0, 120) 50%, rgb(0, 0, 0) 100%);
        color: #e0e0e0; 
    }

    /* --- OPRAVA: DECENTNÍ ZELENÁ MÍSTO ŠEDÉ --- */
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed rgba(0, 255, 150, 0.4) !important;
        background-color: rgba(0, 255, 150, 0.05) !important;
    }
    
    /* Zelené tlačítko a multiselect */
    .stButton button {
        background-color: rgba(0, 200, 100, 0.2) !important;
        border: 1px solid #00ff96 !important;
        color: white !important;
    }
    .stMultiSelect div[role="listbox"] {
        background-color: rgba(0, 200, 100, 0.1) !important;
        border: 1px solid rgba(0, 255, 150, 0.3) !important;
    }

    /* --- HORNÍ METRIKY SE ZELENÝM BLESKEM (GLOW) --- */
    div[data-testid="stMetric"] {
        background: rgba(0, 0, 0, 0.4);
        border: 1px solid #00ff96;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(0, 255, 150, 0.3); /* Zelená záře */
        backdrop-filter: blur(10px);
    }
    
    /* Bílá čísla v metrikách */
    div[data-testid="stMetricValue"] > div {
        color: #ffffff !important;
        font-size: 1.8rem !important;
    }

    /* Spodní zářící karty (Elektřina, Plyn, Voda) */
    .energy-card {
        background: rgba(0, 0, 0, 0.5);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .el-glow { border-top: 4px solid #FFD700; box-shadow: 0 0 35px rgba(255, 215, 0, 0.4); }
    .gas-glow { border-top: 4px solid #FF8C00; box-shadow: 0 0 35px rgba(255, 140, 0, 0.4); }
    .water-glow { border-top: 4px solid #00BFFF; box-shadow: 0 0 35px rgba(0, 191, 255, 0.4); }

    .value-text { font-size: 1.3rem; color: #ffffff !important; font-weight: 600; }
    .label-text { font-size: 0.8rem; color: #aaa; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# HLAVNÍ TITULEK
st.title("⚡ Energy Intelligence Pro")
st.write("---")

# Inicializace session_state
if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

# --- 1. HORNÍ STATISTIKY (S BLESKEM) ---
pocet = len(st.session_state.vysledky)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno", str(pocet))
with c2: st.metric("Kategorie", "3")
with c3: st.metric("Úspora času", f"{pocet * 5} min")
with c4: st.metric("Stav", "Online")

st.write("---")

# --- 2. ANALÝZA A ARCHIV ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.caption("Konfigurace nahrávání")
    uploaded_files = st.file_uploader("Vložte PDF", accept_multiple_files=True, type=['pdf'])
    vyber = st.multiselect("Pole k analýze:", 
                           ["ELEKTŘINA: Spotřeba (kWh)", "PLYN: Spotřeba (kWh)", "VODA: Spotřeba (m3)"],
                           default=["ELEKTŘINA: Spotřeba (kWh)", "PLYN: Spotřeba (kWh)"])
    
    if st.button("🚀 SPUSTIT ANALÝZU", use_container_width=True):
        if uploaded_files:
            st.session_state.vysledky = []
            webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"
            for file in uploaded_files:
                files = {"data": (file.name, file.getvalue(), "application/pdf")}
                response = requests.post(webhook_url, files=files, data={"p": str(vyber)})
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list): data = data[0]
                    data["Soubor"] = file.name
                    st.session_state.vysledky.append(data)
            st.rerun()

with col_main:
    st.subheader("📁 Digitální archiv")
    if st.session_state.vysledky:
        st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)
    else:
        st.info("Nahrajte PDF faktury pro zobrazení archivu.")

    # --- 3. FINÁLNÍ ZÁŘÍCÍ PŘEHLED ---
    if st.session_state.vysledky:
        st.write("---")
        st.subheader("📊 Finální přehled")
        
        data_el, data_pl, data_vo = [], [], []
        for res in st.session_state.vysledky:
            for k, v in res.items():
                if v and str(v).lower() != "n/a" and k not in ["Soubor", "Faktura"]:
                    item = {"label": k.split(":")[-1].strip(), "val": v}
                    if "ELEKTŘINA" in k.upper(): data_el.append(item)
                    elif "PLYN" in k.upper(): data_pl.append(item)
                    elif "VODA" in k.upper(): data_vo.append(item)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<div class="energy-card el-glow"><h3>⚡ Elektřina</h3>', unsafe_allow_html=True)
            for i in data_el:
                st.markdown(f'<div class="label-text">{i["label"]}</div><div class="value-text">{i["val"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="energy-card gas-glow"><h3>🔥 Plyn</h3>', unsafe_allow_html=True)
            for i in data_pl:
                st.markdown(f'<div class="label-text">{i["label"]}</div><div class="value-text">{i["val"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="energy-card water-glow"><h3>💧 Voda</h3>', unsafe_allow_html=True)
            for i in data_vo:
                st.markdown(f'<div class="label-text">{i["label"]}</div><div class="value-text">{i["val"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
