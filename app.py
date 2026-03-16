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
    
    /* Karty metrik */
    div[data-testid="stMetric"] {
        background-color: #000c17;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #00aaff;
    }
    div[data-testid="stMetricValue"] { color: #00ff88 !important; font-weight: bold; }

    /* Tlačítko */
    .stButton>button {
        background-color: #00ff88;
        color: #001529;
        font-weight: bold;
        border-radius: 10px;
        width: 100%;
    }
    
    /* Styl pro Archivní sekce */
    .archive-card {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #00aaff;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")
st.write("---")

# Inicializace stavu
if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

# --- 1. HORNÍ STATISTIKY ---
pocet = len(st.session_state.vysledky)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno faktur", str(pocet))
with c2: st.metric("Typy nákladů", "3 kategorie")
with c3: st.metric("Úspora času", f"{pocet * 5} min")
with c4: st.metric("Stav AI", "Ready" if pocet == 0 else "Online")

st.write("---")

# --- 2. HLAVNÍ PLOCHA ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.subheader("⚙️ Konfigurace")
    uploaded_files = st.file_uploader("Nahrajte PDF faktury", accept_multiple_files=True, type=['pdf'])
    
    vyber = st.multiselect(
        "Data k vytažení:",
        ["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem (fakturovaná)", "PLYN: Cena celkem (fakturovaná)", "FSX: Cena celkem (fakturovaná)"],
        default=["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem (fakturovaná)"]
    )
    analyze_btn = st.button("🚀 SPUSTIT AI ANALÝZU")

with col_main:
    # --- LOGIKA ANALÝZY ---
    if analyze_btn and uploaded_files:
        st.session_state.vysledky = []
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"

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
                        data["Kategorie"] = "Energie"
                        st.session_state.vysledky.append(data)
                except Exception as e:
                    st.error(f"Chyba: {e}")
        st.rerun()

    # --- 3. DIGITÁLNÍ ARCHIV (Místo grafu) ---
    st.subheader("📁 Digitální archiv dokumentů")
    
    tab1, tab2, tab3 = st.tabs(["⚡ Energie & Utility", "🚗 Cestovní náklady", "📄 Ostatní faktury"])

    with tab1:
        if st.session_state.vysledky:
            st.write("### Poslední analýzy energií")
            df = pd.DataFrame(st.session_state.vysledky)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Zatím zde nejsou žádné záznamy o energiích.")

    with tab2:
        st.write("### Evidence cestovních nákladů")
        st.markdown("""
        <div class="archive-card"><b>Vzor:</b> Účtenka - Pohonné hmoty (Shell) - 1.250 Kč <span style='color:#888'>(Čeká na nahrání)</span></div>
        <div class="archive-card"><b>Vzor:</b> Jízdenka - ČD (Praha-Brno) - 340 Kč <span style='color:#888'>(Čeká na nahrání)</span></div>
        """, unsafe_allow_html=True)
        st.warning("Sekce pro Cestovní náklady je v přípravě.")

    with tab3:
        st.write("### Ostatní provozní faktury")
        st.markdown("""
        <div class="archive-card"><b>Vzor:</b> Kancelářské potřeby - 4.200 Kč <span style='color:#888'>(Čeká na nahrání)</span></div>
        <div class="archive-card"><b>Vzor:</b> Čistící prostředky - 1.150 Kč <span style='color:#888'>(Čeká na nahrání)</span></div>
        """, unsafe_allow_html=True)
