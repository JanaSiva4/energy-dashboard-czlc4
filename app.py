import streamlit as st
import pandas as pd
import requests

# Nastavení stránky
st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# --- ULTRA-CLEAN DESIGN (CSS) ---
st.markdown("""
<style>
    .stApp { background-color: #001529; color: #e0e0e0; font-weight: 300; }
    [data-testid="stSidebar"] { background-color: #000c17; color: white; }
    
    /* Zmenšené a zjemněné metriky */
    div[data-testid="stMetric"] {
        background-color: #000c17;
        padding: 15px 20px;
        border-radius: 10px;
        border: 1px solid rgba(0, 170, 255, 0.4);
        min-height: 80px;
    }
    div[data-testid="stMetricValue"] { 
        color: #00ff88 !important; 
        font-weight: 400 !important; 
        font-size: 1.5rem !important;
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 300 !important;
        font-size: 0.8rem !important;
        color: #888 !important;
    }

    /* Jemnější multiselect */
    span[data-baseweb="tag"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        font-weight: 300 !important;
    }

    /* Tlačítko - méně agresivní zelená */
    .stButton>button {
        background-color: #00cc6e;
        color: #001529;
        font-weight: 400;
        border-radius: 8px;
        border: none;
        width: 100%;
    }
    
    /* Archivní karty - velmi decentní */
    .archive-card {
        background-color: rgba(255, 255, 255, 0.02);
        padding: 10px;
        border-radius: 6px;
        border-left: 2px solid #00aaff;
        margin-bottom: 6px;
        font-size: 0.85em;
        font-weight: 300;
        color: #bbb;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")
st.write("---")

if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

# --- 1. ZMENŠENÉ STATISTIKY ---
pocet = len(st.session_state.vysledky)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno faktur", str(pocet))
with c2: st.metric("Kategorie", "3")
with c3: st.metric("Úspora času", f"{pocet * 5} m")
with c4: st.metric("Stav", "Ready" if pocet == 0 else "Online")

st.write("---")

# --- 2. HLAVNÍ PLOCHA ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.caption("Konfigurace")
    uploaded_files = st.file_uploader("Vložte PDF", accept_multiple_files=True, type=['pdf'])
    
    vyber = st.multiselect(
        "Pole k analýze:",
        [
            "ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: průměrná cena (Kč/kWh)",
            "ELEKTŘINA: Cena sil. el. (fakturovaná)", "ELEKTŘINA: Cena distribuce (fakturovaná)",
            "ELEKTŘINA: Cena celkem (fakturovaná)", "FSX (společné prostory): Spotřeba (kWh)",
            "FSX (společné prostory): Cena celkem (fakturovaná)", "PLYN: Spotřeba (m3)",
            "PLYN: Spotřeba (kWh)", "PLYN: průměrná cena (Kč/kWh)", "PLYN: Cena celkem (fakturovaná)"
        ],
        default=["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem (fakturovaná)"]
    )
    analyze_btn = st.button("SPUSTIT ANALÝZU")

with col_main:
    if analyze_btn and uploaded_files:
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
                    st.error("Chyba spojení.")
        st.rerun()

    # --- 3. ARCHIV ---
    st.subheader("📁 Digitální archiv")
    t1, t2, t3 = st.tabs(["Energie", "Cesty", "Ostatní"])

    with t1:
        if st.session_state.vysledky:
            st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)
        else:
            st.info("Žádná data k zobrazení.")

    with t2:
        st.markdown('<div class="archive-card">Účtenka - PHM Shell - 1.250 Kč</div>', unsafe_allow_html=True)
        st.markdown('<div class="archive-card">Jízdenka - ČD Praha - 340 Kč</div>', unsafe_allow_html=True)

    with t3:
        st.markdown('<div class="archive-card">Kancelářské potřeby - 4.200 Kč</div>', unsafe_allow_html=True)
