import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & WOW DESIGN (CSS) ---
st.set_page_config(page_title="Energy Intelligence Pro", layout="wide")

st.markdown("""
<style>
    /* ZAROVNÁNÍ NA STŘED */
    [data-testid="stMainViewContainer"] .block-container {
        max-width: 1100px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* Temné pozadí */
    .stApp { 
        background: radial-gradient(circle at 10% 20%, rgb(0, 21, 41) 0%, rgb(0, 10, 20) 90.2%);
        color: #e0e0e0; 
    }

    /* ZÁŘE KOLEM STATISTIK */
    div[data-testid="stMetric"] {
        background-color: rgba(0, 255, 150, 0.05) !important;
        padding: 15px;
        border-radius: 12px;
        border: 2px solid rgba(0, 255, 150, 0.5) !important;
        box-shadow: 0 0 20px rgba(0, 255, 150, 0.3) !important;
    }

    /* ZELENÝ UPLOAD BOX */
    [data-testid="stFileUploadDropzone"] {
        background-color: rgba(0, 255, 100, 0.05) !important;
        border: 2px dashed #00ff96 !important;
    }

    /* ŠEDÉ ŠTÍTKY V MULTISELECTU */
    span[data-baseweb="tag"] {
        background-color: #3d4651 !important;
        border: 1px solid #5d6773 !important;
        color: white !important;
    }

    /* --- KLÍČOVÁ OPRAVA: TLAČÍTKO NA STŘED --- */
    /* Tento blok vynutí, aby se obal tlačítka choval jako flex-kontejner na střed */
    div.stButton {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }

    div.stButton > button {
        background-color: transparent !important;
        border: 2px solid #00ff96 !important;
        color: #00ff96 !important;
        box-shadow: 0 0 15px rgba(0, 255, 150, 0.3) !important;
        transition: all 0.4s ease !important;
        
        /* Vrácení původní velikosti (tlačítko se smrskne k textu) */
        width: auto !important; 
        padding-left: 20px !important;
        padding-right: 20px !important;
    }

    div.stButton > button:hover {
        opacity: 0.3 !important; /* Bleskový efekt */
        box-shadow: 0 0 30px rgba(0, 255, 150, 0.6) !important;
    }

    /* Glassmorphism karty */
    .energy-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
    }
    .el-border { border-top: 5px solid #FFD700; }
    .gas-border { border-top: 5px solid #FF8C00; }
    .water-border { border-top: 5px solid #00BFFF; }
    .label-text { font-size: 0.75rem; color: #888; text-transform: uppercase; margin-top: 12px; }
    .value-text { font-size: 1.1rem; color: #ffffff; }
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
