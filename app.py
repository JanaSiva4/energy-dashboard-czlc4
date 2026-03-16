import streamlit as st  
import pandas as pd
import requests

# 1. Základní nastavení
st.set_page_config(page_title="CZLC4 Energy Intel Pro", layout="wide")

# 2. DESIGN (CSS) - FIX VNITŘNÍ ZELENÉ VÝPLNĚ A HOVER EFEKTU
st.markdown("""
<style>
    .stApp { 
        background: radial-gradient(circle at 10% 20%, rgb(0, 21, 41) 0%, rgb(60, 0, 120) 50%, rgb(0, 0, 0) 100%);
        color: #e0e0e0; 
    }

    /* --- DIGITÁLNÍ ARCHIV: CELÁ ZELENÁ VÝPLŇ --- */
    [data-testid="stDataFrame"] {
        background-color: #00ff96 !important; /* TVÁ ZELENÁ UVNITŘ */
        border-radius: 10px;
        transition: opacity 0.3s ease;
    }

    /* HOVER EFEKT: PRŮHLEDNOST PŘI NAJETÍ */
    [data-testid="stDataFrame"]:hover {
        opacity: 0.4 !important;
    }

    /* Zajištění, aby text v zelené tabulce byl čitelný (černý) */
    [data-testid="stDataFrame"] div[role="gridcell"] {
        background-color: transparent !important;
        color: #000000 !important;
    }
    
    /* Hlavičky tabulky */
    [data-testid="stDataFrame"] div[role="columnheader"] {
        background-color: rgba(0, 150, 80, 0.5) !important;
        color: white !important;
    }

    /* Ostatní prvky */
    [data-testid="stFileUploadDropzone"], .stMultiSelect div[role="listbox"], .stButton button {
        border: 1px solid rgba(0, 180, 100, 0.4) !important;
        background-color: rgba(0, 180, 100, 0.05) !important;
    }
    
    div[data-testid="stMetric"] {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(0, 255, 150, 0.3);
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 0 15px rgba(0, 255, 130, 0.2);
    }

    .energy-card {
        background: rgba(0, 0, 0, 0.5);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .el-glow { border-top: 3px solid #FFD700; box-shadow: 0 0 30px rgba(255, 215, 0, 0.4); }
    .gas-glow { border-top: 3px solid #FF8C00; box-shadow: 0 0 30px rgba(255, 140, 0, 0.4); }
    .water-glow { border-top: 3px solid #00BFFF; box-shadow: 0 0 30px rgba(0, 191, 255, 0.4); }

    .value-text { font-size: 1.3rem; color: #ffffff !important; font-weight: 600; }
    .label-text { font-size: 0.8rem; color: #888; text-transform: uppercase; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy Intelligence Pro")
st.write("---")

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

# --- HLAVNÍ PLOCHA ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.caption("Konfigurace")
    uploaded_files = st.file_uploader("Vložte PDF", accept_multiple_files=True, type=['pdf'])
    
    # VRÁCENA VŠECHNA POLE K VYTAŽENÍ
    vyber = st.multiselect(
        "Pole k vytažení:",
        [
            "ELEKTŘINA: Spotřeba (kWh)", 
            "ELEKTŘINA: Cena sil. el. (fakturovaná)", 
            "ELEKTŘINA: Cena distribuce (fakturovaná)",
            "ELEKTŘINA: Cena celkem (fakturovaná)",
            "FSX: Spotřeba (kWh)",
            "FSX: Cena celkem (fakturovaná)",
            "PLYN: Spotřeba (kWh)",
            "PLYN: Cena celkem (fakturovaná)",
            "VODA: Spotřeba (m3)",
            "VODA: Cena celkem (fakturovaná)"
        ],
        default=["ELEKTŘINA: Spotřeba (kWh)", "PLYN: Spotřeba (kWh)", "VODA: Spotřeba (m3)"]
    )
    
    if st.button("🚀 SPUSTIT ANALÝZU", use_container_width=True):
        if uploaded_files:
            # Simulace zpracování (zde bude tvůj requests.post)
            st.session_state.vysledky = [{"ELEKTŘINA: Spotřeba (kWh)": "363713", "PLYN: Spotřeba (kWh)": "207978", "VODA: Spotřeba (m3)": "771", "Soubor": "faktura.pdf"}]
            st.rerun()

with col_main:
    st.subheader("📁 Digitální archiv")
    if st.session_state.vysledky:
        st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)
    else:
        st.info("Zatím žádná data k zobrazení.")

# --- 4. FINÁLNÍ PŘEHLED (VRÁCENO) ---
if st.session_state.vysledky:
    st.write("---")
    st.subheader("📊 Finální přehled")
    
    data_el, data_pl, data_vo = [], [], []
    for res in st.session_state.vysledky:
        for k, v in res.items():
            if v and str(v).lower() != "n/a" and k not in ["Soubor"]:
                item = {"label": k.split(":")[-1].strip(), "val": v}
                if "ELEKTŘINA" in k.upper(): data_el.append(item)
                elif "PLYN" in k.upper(): data_pl.append(item)
                elif "VODA" in k.upper(): data_vo.append(item)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="energy-card el-glow"><h3>⚡ Elektřina</h3>', unsafe_allow_html=True)
        for i in data_el: st.markdown(f'<div class="label-text">{i["label"]}</div><div class="value-text">{i["val"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="energy-card gas-glow"><h3>🔥 Plyn</h3>', unsafe_allow_html=True)
        for i in data_pl: st.markdown(f'<div class="label-text">{i["label"]}</div><div class="value-text">{i["val"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="energy-card water-glow"><h3>💧 Voda</h3>', unsafe_allow_html=True)
        for i in data_vo: st.markdown(f'<div class="label-text">{i["label"]}</div><div class="value-text">{i["val"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
