import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & WOW DESIGN (CSS) ---
st.set_page_config(page_title="Energy Intelligence Pro", layout="wide")

st.markdown("""
<style>
   /* ZAROVNÁNÍ OBSAHU */
    [data-testid="stMainViewContainer"] .block-container {
        max-width: 1200px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    
    /* VÝRAZNÁ MODRO-FIALOVÁ PLOCHA */
    .stApp {
        /* Přidáno více fialové (#7b1fa2 a #4a148c) pro sytost */
        background: linear-gradient(135deg, #0d47a1 0%, #7b1fa2 40%, #4a148c 70%, #1a237e 100%) !important;
        background-attachment: fixed !important;
        color: #ffffff;
    }

    /* --- STATISTIKY (HORNÍ BOXY) --- */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
        padding: 15px;
        border-radius: 15px;
        border: 2px solid #ffffff !important; 
        box-shadow: 0 0 20px rgba(0, 242, 255, 0.6) !important;
    }

    /* --- TLAČÍTKO (BLESKOVĚ BÍLÉ) --- */
    div[data-testid="stButton"] > button {
        background-color: rgba(255, 255, 255, 0.15) !important;
        border: 2px solid #ffffff !important;
        color: #ffffff !important;
        box-shadow: 0 0 15px #ffffff, 0 0 30px #00d4ff !important;
        transition: all 0.3s ease-in-out !important;
        font-weight: bold !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        height: 50px !important;
    }

    /* --- KARTY PRO ELEKTŘINU, PLYN A VODU (OPRAVENO) --- */
    .energy-card {
        background: rgba(255, 255, 255, 0.07) !important;
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(15px);
        margin-bottom: 20px;
        /* Základní záře pro karty */
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
    }

    /* Barevné horní linky karet s bleskovým efektem */
    .el-border { 
        border-top: 5px solid #00f2ff !important; 
        box-shadow: 0 -5px 20px rgba(0, 242, 255, 0.4) !important;
    }
    .gas-border { 
        border-top: 5px solid #ff00ff !important; 
        box-shadow: 0 -5px 20px rgba(255, 0, 255, 0.4) !important;
    }
    .water-border { 
        border-top: 5px solid #00d4ff !important; 
        box-shadow: 0 -5px 20px rgba(0, 212, 255, 0.4) !important;
    }

    /* Texty uvnitř karet */
    .label-text { font-size: 0.8rem; color: #b0f0ff; text-transform: uppercase; margin-top: 15px; font-weight: bold; }
    .value-text { font-size: 1.2rem; color: #ffffff; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 5px; }

    /* UPLOAD BOX */
    [data-testid="stFileUploadDropzone"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 2px dashed #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy Intelligence Pro")
st.write("---")

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

# --- 3. HLAVNÍ PLOCHA ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.caption("Konfigurace")
    uploaded_files = st.file_uploader("Vložte PDF", accept_multiple_files=True, type=['pdf'])

    # POLE K VYTAŽENÍ - STRIKTNĚ ZACHOVÁNA
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
    st.write(" ") # přidá malou mezeru
    _, mid_btn, _ = st.columns([1.5, 4, 0.5]) # vytvoří 3 pod-sloupečky (kraje malé, střed velký)
    with mid_btn:
        analyze_btn = st.button("🚀 SPUSTIT ANALÝZU")

with col_main:
    if analyze_btn and uploaded_files:
        st.session_state.vysledky = []
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
                        data["Soubor"] = file.name
                        st.session_state.vysledky.append(data)
                except:
                    st.error("Chyba spojení.")
        st.rerun()

    st.subheader("📁 Digitální archiv")
    if st.session_state.vysledky:
        st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)
    else:
        st.info("Nahrajte faktury.")

 # --- 5. FINÁLNÍ PŘEHLED ---
    if st.session_state.vysledky:
        st.write("---")
        st.subheader("📊 Finální přehled")
        
        data_elektro, data_plyn, data_voda = [], [], []
        for res in st.session_state.vysledky:
            for klic, hodnota in res.items():
                if hodnota and str(hodnota).lower() != "n/a" and klic not in ["Soubor", "Faktura", "Kategorie"]:
                    polozka = {"Parametr": klic.split(":")[-1].strip(), "Hodnota": hodnota}
                    if "ELEKTŘINA" in klic.upper() or "FSX" in klic.upper():
                        if polozka not in data_elektro: data_elektro.append(polozka)
                    elif "PLYN" in klic.upper():
                        if polozka not in data_plyn: data_plyn.append(polozka)
                    elif "VODA" in klic.upper():
                        if polozka not in data_voda: data_voda.append(polozka)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<div class="energy-card el-border"><h3>⚡ Elektřina & FSX</h3>', unsafe_allow_html=True)
            for item in data_elektro:
                st.markdown(f'<div class="label-text">{item["Parametr"]}</div><div class="value-text">{item["Hodnota"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="energy-card gas-border"><h3>🔥 Plyn</h3>', unsafe_allow_html=True)
            for item in data_plyn:
                st.markdown(f'<div class="label-text">{item["Parametr"]}</div><div class="value-text">{item["Hodnota"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="energy-card water-border"><h3>💧 Voda</h3>', unsafe_allow_html=True)
            for item in data_voda:
                st.markdown(f'<div class="label-text">{item["Parametr"]}</div><div class="value-text">{item["Hodnota"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
