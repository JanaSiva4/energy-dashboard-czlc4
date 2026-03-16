import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & WOW DESIGN (CSS) ---
st.set_page_config(page_title="Energy Intelligence Pro", layout="wide")

st.markdown("""
<style>
    /* ZAROVNÁNÍ HLAVNÍHO OBSAHU */
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

    /* --- OPRAVA: TLAČÍTKO PŘESNĚ NA STŘED --- */
    div[data-testid="stButton"] {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
        margin-top: 20px !important;
    }

/* --- NOVÁ OPRAVA: TOTÁLNÍ VYCENTROVÁNÍ --- */
    div.stButton {
        text-align: center !important;
    }

    div.stButton > button {
        display: block !important;
        margin-left: auto !important;
        margin-right: auto !important;
        background-color: transparent !important;
        border: 2px solid #00ff96 !important;
        color: #00ff96 !important;
        box-shadow: 0 0 15px rgba(0, 255, 150, 0.3) !important;
        transition: all 0.4s ease !important;
        padding: 10px 25px !important;
        width: auto !important;
    }

    div.stButton > button:hover {
        background-color: rgba(0, 255, 150, 0.1) !important;
        box-shadow: 0 0 30px rgba(0, 255, 150, 0.6) !important;
    }

    div[data-testid="stButton"] > button {
        background-color: transparent !important;
        border: 2px solid #00ff96 !important;
        color: #00ff96 !important;
        box-shadow: 0 0 15px rgba(0, 255, 150, 0.3) !important;
        transition: all 0.4s ease !important;
        width: auto !important; /* Tlačítko se neroztáhne, zůstane kompaktní */
        padding-left: 30px !important;
        padding-right: 30px !important;
        height: 50px !important;
    }

    div[data-testid="stButton"] > button:hover {
        background-color: rgba(0, 255, 150, 0.1) !important;
        box-shadow: 0 0 30px rgba(0, 255, 150, 0.6) !important;
        transform: scale(1.02);
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

    /* Glassmorphism karty */
    .energy-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
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
        col1, col2, col3 = st.columns(3)
 
        with col1:
            st.markdown("### ⚡ Elektřina")
            if data_elektro:
                st.dataframe(pd.DataFrame(data_elektro), hide_index=True, use_container_width=True)
            else:
                st.caption("Žádná data")
 
        with col2:
            st.markdown("### 🔥 Plyn")
            if data_plyn:
                st.dataframe(pd.DataFrame(data_plyn), hide_index=True, use_container_width=True)
            else:
                st.caption("Žádná data")
 
        with col3:
            st.markdown("### 💧 Voda / Ostatní")
            if data_voda:
                st.dataframe(pd.DataFrame(data_voda), hide_index=True, use_container_width=True)
            else:
                st.caption("Žádná data")
