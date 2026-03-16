import streamlit as st  
import pandas as pd
import requests

# 1. Základní nastavení
st.set_page_config(page_title="CZLC4 Energy Intel Pro", layout="wide")

# 2. DESIGN (CSS)
st.markdown("""
<style>
    .stApp { 
        background: radial-gradient(circle at 10% 20%, rgb(0, 21, 41) 0%, rgb(60, 0, 120) 50%, rgb(0, 0, 0) 100%);
        color: #e0e0e0; 
    }

    /* --- DIGITÁLNÍ ARCHIV: JEMNÁ ZELENÁ VÝPLŇ --- */
    [data-testid="stDataFrame"] {
        background-color: rgba(0, 255, 150, 0.05) !important;
        border: 1px solid rgba(0, 255, 150, 0.3) !important;
        border-radius: 10px;
        transition: opacity 0.3s ease;
    }
    
    [data-testid="stDataFrame"]:hover {
        opacity: 0.6;
    }

    /* --- TLAČÍTKO: PRŮHLEDNOST PŘI NAJETÍ (HOVER) --- */
    div.stButton > button {
        background-color: rgba(0, 255, 150, 0.05) !important;
        border: 1px solid #00ff96 !important;
        color: white !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }

    div.stButton > button:hover {
        opacity: 0.4 !important; /* Průhlednost při najetí */
        background-color: rgba(0, 255, 150, 0.1) !important;
    }

    /* --- KARTY PŘEHLEDU (MENŠÍ, ČÍSLA POD SEBOU) --- */
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

    .card-h3 { font-size: 1.1rem; margin-bottom: 10px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    .label-text { font-size: 0.7rem; color: #888; text-transform: uppercase; margin-top: 8px; }
    .value-text { font-size: 1.2rem; color: #ffffff; font-weight: 700; margin-bottom: 2px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy Intelligence Pro")

if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

# --- STATISTIKY (HORNÍ LIŠTA) ---
st.write("---")
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno", str(len(st.session_state.vysledky)))
with c2: st.metric("Kategorie", "3")
with c3: st.metric("Úspora času", f"{len(st.session_state.vysledky) * 5} min")
with c4: st.metric("Stav", "Online")
st.write("---")

# --- HLAVNÍ PLOCHA ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.caption("Konfigurace")
    uploaded_files = st.file_uploader("Vložte PDF", accept_multiple_files=True, type=['pdf'])
    
    # Kompletní seznam polí zpět
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
    
    if st.button("🚀 SPUSTIT ANALÝZU"):
        if uploaded_files:
            # Simulace úspěšného zpracování
            st.session_state.vysledky = [{"ELEKTŘINA: Spotřeba (kWh)": "363713", "PLYN: Spotřeba (kWh)": "207978", "VODA: Spotřeba (m3)": "771", "Soubor": "faktura.pdf"}]
            st.rerun()

with col_main:
    st.subheader("📁 Digitální archiv")
    if st.session_state.vysledky:
        st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)
        
        # --- FINÁLNÍ PŘEHLED (TŘI SLOUPCE POD SEBOU) ---
        st.write("---")
        st.subheader("📊 Finální přehled")
        
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown("""
            <div class="energy-card el-glow">
                <div class="card-h3">⚡ Elektřina</div>
                <div class="label-text">SPOTŘEBA (KWH)</div>
                <div class="value-text">363 713.00</div>
                <div class="label-text">CENA CELKEM</div>
                <div class="value-text">1 156 887.56</div>
            </div>""", unsafe_allow_html=True)
        with k2:
            st.markdown("""
            <div class="energy-card gas-glow">
                <div class="card-h3">🔥 Plyn</div>
                <div class="label-text">SPOTŘEBA (KWH)</div>
                <div class="value-text">207 978.86</div>
                <div class="label-text">CENA CELKEM</div>
                <div class="value-text">313 419.26</div>
            </div>""", unsafe_allow_html=True)
        with k3:
            st.markdown("""
            <div class="energy-card water-glow">
                <div class="card-h3">💧 Voda</div>
                <div class="label-text">SPOTŘEBA (M3)</div>
                <div class="value-text">771</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("Nahrajte soubory a spusťte analýzu.")
