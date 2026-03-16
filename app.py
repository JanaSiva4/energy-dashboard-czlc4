import streamlit as st
import pandas as pd
import requests

# Nastavení stránky
st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# --- DESIGN (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #001529; color: white; }
    [data-testid="stSidebar"] { background-color: #000c17; color: white; }
    /* Karty pro soubory */
    .file-card {
        background-color: #000c17;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #00aaff;
        margin-bottom: 10px;
    }
    div[data-testid="stMetric"] {
        background-color: #000c17;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #00aaff;
    }
    div[data-testid="stMetricValue"] { color: #00ff88 !important; font-weight: bold; }
    .stButton>button {
        background-color: #00ff88;
        color: #001529;
        font-weight: bold;
        border-radius: 10px;
    }
    h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")
st.write("---")

# Inicializace paměti
if 'vysledky_data' not in st.session_state:
    st.session_state.vysledky_data = []

# --- 1. STATISTIKY ---
count = len(st.session_state.vysledky_data)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno faktur", count)
with c2: st.metric("Celková suma", "Dle tabulky")
with c3: st.metric("Úspora času", f"{count * 5} min")
with c4: st.metric("Stav AI", "Ready" if count == 0 else "Online")

st.write("---")

col_side, col_main = st.columns([1, 3])

with col_side:
    st.subheader("⚙️ Konfigurace")
    uploaded_files = st.file_uploader("Nahrajte PDF faktury", accept_multiple_files=True, type=['pdf'])
    vyber = st.multiselect("Data k vytažení:", ["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem (fakturovaná)", "PLYN: Cena celkem (fakturovaná)"], default=["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem (fakturovaná)"])
    analyze_btn = st.button("🚀 SPUSTIT AI ANALÝZU")

with col_main:
    if analyze_btn and uploaded_files:
        st.session_state.vysledky_data = []
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook-test/faktury-upload"

        for file in uploaded_files:
            with st.spinner(f"Analyzuji: {file.name}..."):
                try:
                    files = {"data": (file.name, file.getvalue(), "application/pdf")}
                    payload = {"p": str(vyber)}
                    response = requests.post(webhook_url, files=files, data=payload)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list): data = data[0]
                        data["Faktura"] = file.name
                        st.session_state.vysledky_data.append(data)
                except Exception as e:
                    st.error(f"Chyba: {e}")
        st.rerun()

    # --- MÍSTO GRAFU: DIGITÁLNÍ ARCHIV ---
    if st.session_state.vysledky_data:
        st.subheader("📊 Výsledky analýzy")
        df = pd.DataFrame(st.session_state.vysledky_data)
        st.dataframe(df, use_container_width=True)
        
        st.write("---")
        st.subheader("📁 Digitální archiv (Nahráno)")
        cols = st.columns(3)
        for i, res in enumerate(st.session_state.vysledky_data):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="file-card">
                    📄 <b>{res['Faktura'][:20]}...</b><br>
                    <small>Stav: Zpracováno ✅</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Bonus: Tlačítko na stažení Excelu
        st.download_button("📥 Stáhnout data pro Excel", df.to_csv(index=False).encode('utf-8'), "faktury_export.csv", "text/csv")
    
    else:
        st.subheader("📂 Archiv souborů")
        st.info("Zatím nebyly zpracovány žádné dokumenty. Nahrajte faktury vlevo.")
