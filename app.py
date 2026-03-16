import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & WOW DESIGN (CSS) ---
st.set_page_config(page_title="CZLC4 Energy Intel Pro", layout="wide")

st.markdown("""
<style>
    /* Temné pozadí s gradientem Modrá <-> Fialová */
    .stApp { 
        background: radial-gradient(circle at 10% 20%, rgb(0, 21, 41) 0%, rgb(100, 0, 255) 50%, rgb(0, 0, 0) 100%);
        color: #e0e0e0; 
        font-weight: 300; 
    }
    [data-testid="stSidebar"] { background-color: #000c17; color: white; }

    /* Glassmorphism karty pro výsledky - MENŠÍ A TENČÍ */
    .energy-card {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 10px;
        padding: 10px 15px;      /* Zmenšen vnitřní prostor */
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(8px);
        margin-bottom: 12px;
        font-size: 0.9em;         /* Celkově menší písmo v kartě */
    }
    .el-border { border-top: 3px solid #FFD700; }   /* Zlatá pro elektřinu */
    .gas-border { border-top: 3px solid #FF8C00; }  /* Oranžová pro plyn */
    .water-border { border-top: 3px solid #00BFFF; } /* Modrá pro vodu */

    /* Styl textu v kartách */
    .label-text { font-size: 0.7rem; color: #888; text-transform: uppercase; margin-top: 5px; letter-spacing: 1px; }
    .value-text { font-size: 1rem; color: #ffffff; font-weight: 400; }

    /* Decentní metriky nahoře */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.01);
        padding: 10px;
        border-radius: 8px;
        border: 1px solid rgba(0, 170, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy Intelligence Pro")
st.write("---")

# Inicializace stavu
if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

# --- 2. HORNÍ STATISTIKY ---
pocet = len(st.session_state.vysledky)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno", str(pocet))
with c2: st.metric("Kategorie", "3")
with c3: st.metric("Úspora času", f"{pocet * 5} min")
with c4: st.metric("Stav", "Ready" if pocet == 0 else "Online")

st.write("---")

# --- 3. HLAVNÍ PLOCHA (SIDEBAR + ANALÝZA) ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.caption("Konfigurace")
    uploaded_files = st.file_uploader("Vložte PDF", accept_multiple_files=True, type=['pdf'])

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
    analyze_btn = st.button("🚀 SPUSTIT ANALÝZU")

with col_main:
    # --- LOGIKA WEBHOOKU ---
    if analyze_btn and uploaded_files:
        st.session_state.vysledky = []
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"

        for file in uploaded_files:
            with st.spinner(f"Analyzuji..."):
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

    # --- 4. DIGITÁLNÍ ARCHIV ---
    st.subheader("📁 Digitální archiv")
    t1, t2 = st.tabs(["Energie", "Ostatní"])

    with t1:
        if st.session_state.vysledky:
            st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)
        else:
            st.info("Nahrajte faktury.")

    with t2:
        st.markdown('<div class="archive-card">Účtenka PHM</div>', unsafe_allow_html=True)

    # --- 5. FINÁLNÍ WOW PŘEHLED (3 SLOPCE) - MENŠÍ KARTY ---
    if st.session_state.vysledky:
        st.write("---")
        st.subheader("📊 Finální přehled")
        
        # Inicializace kategorií
        data_elektro, data_plyn, data_voda = [], [], []

        for res in st.session_state.vysledky:
            for klic, hodnota in res.items():
                if hodnota and str(hodnota).lower() != "n/a" and klic not in ["Soubor", "Faktura"]:
                    polozka = {"Parametr": klic.split(":")[-1].strip(), "Hodnota": hodnota}

                    if "ELEKTŘINA" in klic.upper() or "FSX" in klic.upper():
                        if polozka not in data_elektro: data_elektro.append(polozka)
                    elif "PLYN" in klic.upper():
                        if polozka not in data_plyn: data_plyn.append(polozka)
                    elif "VODA" in klic.upper():
                        if polozka not in data_voda: data_voda.append(polozka)

        # Vykreslení moderních sloupců s MENŠÍMI KARTAMI
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown('<div class="energy-card el-border"><h4>⚡ Elektřina</h4></div>', unsafe_allow_html=True)
            for item in data_elektro:
                st.markdown(f'<div class="label-text">{item["Parametr"]}</div><div class="value-text">{item["Hodnota"]}</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="energy-card gas-border"><h4>🔥 Plyn</h4></div>', unsafe_allow_html=True)
            for item in data_plyn:
                st.markdown(f'<div class="label-text">{item["Parametr"]}</div><div class="value-text">{item["Hodnota"]}</div>', unsafe_allow_html=True)

        with c3:
            st.markdown('<div class="energy-card water-border"><h4>💧 Voda</h4></div>', unsafe_allow_html=True)
            for item in data_voda:
                st.markdown(f'<div class="label-text">{item["Parametr"]}</div><div class="value-text">{item["Hodnota"]}</div>', unsafe_allow_html=True)
