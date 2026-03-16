import streamlit as st  
import pandas as pd
import requests

# 1. Konfigurace stránky
st.set_page_config(page_title="CZLC4 Energy Intel Pro", layout="wide")

# 2. DESIGN (Kompletní CSS pro blesky a barvy)
st.markdown("""
<style>
    .stApp { 
        background: radial-gradient(circle at 10% 20%, rgb(0, 21, 41) 0%, rgb(60, 0, 120) 50%, rgb(0, 0, 0) 100%);
        color: #e0e0e0; 
    }

    /* --- HORNÍ STATISTIKY: ZÁŘÍCÍ BLESKY --- */
    div[data-testid="stMetric"] {
        background: rgba(0, 0, 0, 0.4) !important;
        border: 2px solid #00ff96 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        box-shadow: 0 0 20px rgba(0, 255, 150, 0.5), inset 0 0 10px rgba(0, 255, 150, 0.2) !important;
    }

    /* --- DIGITÁLNÍ ARCHIV: ZELENÁ VÝPLŇ --- */
    [data-testid="stDataFrame"] {
        background-color: rgba(0, 255, 150, 0.1) !important;
        border: 1px solid #00ff96 !important;
        border-radius: 10px;
    }

    /* --- TLAČÍTKO: PRŮHLEDNÝ HOVER EFEKT --- */
    div.stButton > button {
        background-color: transparent !important;
        border: 2px solid #00ff96 !important;
        color: #00ff96 !important;
        font-weight: bold !important;
        transition: all 0.4s ease !important;
    }
    div.stButton > button:hover {
        opacity: 0.3 !important; /* Bleskové zprůhlednění */
        box-shadow: 0 0 30px rgba(0, 255, 150, 0.6) !important;
    }

    /* --- KARTY FINÁLNÍHO PŘEHLEDU --- */
    .f-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border-top: 4px solid #00ff96;
    }
    .val-big { font-size: 1.6rem; font-weight: 800; color: #00ff96; margin-top: 5px; }
    .val-sub { font-size: 0.9rem; color: #888; text-transform: uppercase; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

# 3. NADPIS A STATISTIKY
st.title("⚡ Energy Intelligence Pro")

st.write("---")
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno", "10")
with c2: st.metric("Kategorie", "3")
with c3: st.metric("Úspora času", "50 min")
with c4: st.metric("Stav", "Online")
st.write("---")

# 4. HLAVNÍ ČÁST
col_side, col_main = st.columns([1, 3])

with col_side:
    st.subheader("Konfigurace")
    st.file_uploader("Vložte PDF", accept_multiple_files=True)
    
    # Kompletní seznam polí zpět
    st.multiselect(
        "Pole k vytažení:",
        ["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem", "PLYN: Spotřeba (kWh)", "PLYN: Cena celkem", "VODA: Spotřeba (m3)"],
        default=["ELEKTŘINA: Spotřeba (kWh)", "PLYN: Spotřeba (kWh)"]
    )
    
    if st.button("🚀 SPUSTIT ANALÝZU", use_container_width=True):
        st.success("Blesková analýza spuštěna!")

with col_main:
    st.subheader("📁 Digitální archiv")
    # Ukázková data pro vizualizaci zelené výplně
    df_demo = pd.DataFrame({
        "ELEKTŘINA: Spotřeba": ["363713.00", "n/a", "46933"],
        "PLYN: Spotřeba": ["n/a", "207978.86", "197097,24"],
        "Soubor": ["faktura_01.pdf", "faktura_02.pdf", "faktura_03.pdf"]
    })
    st.dataframe(df_demo, use_container_width=True)

    # --- FINÁLNÍ PŘEHLED (Hned pod archivem) ---
    st.write("---")
    st.subheader("📊 Finální přehled")
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown('<div class="f-card"><h3>⚡ Elektřina</h3><div class="val-sub">SPOTŘEBA (KWH)</div><div class="val-big">363 713.00</div><div class="val-sub">CENA CELKEM</div><div class="val-big">1 156 887.56</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="f-card"><h3>🔥 Plyn</h3><div class="val-sub">SPOTŘEBA (KWH)</div><div class="val-big">207 978.86</div><div class="val-sub">CENA CELKEM</div><div class="val-big">313 419.26</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="f-card"><h3>💧 Voda</h3><div class="val-sub">SPOTŘEBA (M3)</div><div class="val-big">771</div></div>', unsafe_allow_html=True)
