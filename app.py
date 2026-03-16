import streamlit as st  
import pandas as pd

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
        background-color: rgba(0, 255, 150, 0.2) !important; /* Méně svítící zelená uvnitř */
        border: 1px solid #00ff96 !important;
        border-radius: 10px;
        transition: opacity 0.3s ease;
    }
    
    /* Hover efekt pro tabulku */
    [data-testid="stDataFrame"]:hover {
        opacity: 0.6;
    }

    /* Vnitřek tabulky - buňky */
    [data-testid="data-grid-canvas"] {
        background-color: rgba(0, 100, 60, 0.1) !important;
    }

    /* --- TLAČÍTKO: HOVER EFEKT (PRŮHLEDNOST) --- */
    div.stButton > button {
        background-color: rgba(0, 180, 100, 0.1) !important;
        border: 1px solid #00ff96 !important;
        color: white !important;
        transition: all 0.3s ease !important;
    }

    div.stButton > button:hover {
        opacity: 0.5 !important; /* Zprůhlednění při najetí */
        background-color: rgba(0, 255, 150, 0.2) !important;
    }

    /* --- KARTY FINÁLNÍHO PŘEHLEDU --- */
    .energy-card {
        background: rgba(0, 0, 0, 0.5);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .el-glow { border-top: 3px solid #FFD700; box-shadow: 0 0 30px rgba(255, 215, 0, 0.3); }
    .gas-glow { border-top: 3px solid #FF8C00; box-shadow: 0 0 30px rgba(255, 140, 0, 0.3); }
    .water-glow { border-top: 3px solid #00BFFF; box-shadow: 0 0 30px rgba(0, 191, 255, 0.3); }

    .value-text { font-size: 1.3rem; color: #ffffff !important; font-weight: 600; }
    .label-text { font-size: 0.8rem; color: #888; text-transform: uppercase; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy Intelligence Pro")
st.write("---")

if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

# --- STATISTIKY ---
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno", "10")
with c2: st.metric("Kategorie", "3")
with c3: st.metric("Úspora času", "50 min")
with c4: st.metric("Stav", "Online")

st.write("---")

# --- HLAVNÍ PLOCHA ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.caption("Konfigurace")
    uploaded_files = st.file_uploader("Vložte PDF", accept_multiple_files=True, type=['pdf'])
    
    vyber = st.multiselect(
        "Pole k vytažení:",
        ["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem", "PLYN: Spotřeba (kWh)", "PLYN: Cena celkem", "VODA: Spotřeba (m3)", "VODA: Cena celkem"],
        default=["ELEKTŘINA: Spotřeba (kWh)", "PLYN: Spotřeba (kWh)", "VODA: Spotřeba (m3)"]
    )
    
    if st.button("🚀 SPUSTIT ANALÝZU", use_container_width=True):
        st.session_state.vysledky = [{"ELEKTŘINA: Spotřeba (kWh)": "363713", "PLYN: Spotřeba (kWh)": "207978", "VODA: Spotřeba (m3)": "771", "Soubor": "faktura_01.pdf"}]
        st.rerun()

with col_main:
    st.subheader("📁 Digitální archiv")
    if st.session_state.vysledky:
        st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)
        
        # --- FINÁLNÍ PŘEHLED PŘÍMO POD ARCHIVEM ---
        st.write("---")
        st.subheader("📊 Finální přehled")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<div class="energy-card el-glow"><h3>⚡ Elektřina</h3><div class="label-text">Spotřeba (kWh)</div><div class="value-text">363 713</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="energy-card gas-glow"><h3>🔥 Plyn</h3><div class="label-text">Spotřeba (kWh)</div><div class="value-text">207 978</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="energy-card water-glow"><h3>💧 Voda</h3><div class="label-text">Spotřeba (m3)</div><div class="value-text">771</div></div>', unsafe_allow_html=True)
    else:
        st.info("Nahrajte soubory a spusťte analýzu.")
