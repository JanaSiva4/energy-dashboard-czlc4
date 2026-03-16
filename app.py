import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Nastavení stránky
st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# --- ÚPLNĚ NOVÝ "ENERGY HIGH-TECH" DESIGN (CSS) ---
st.markdown("""
<style>
    /* Temné high-tech pozadí */
    .stApp { 
        background-color: #001529; 
        color: white; 
    }

    /* Sidebar v tmavší barvě */
    [data-testid="stSidebar"] { 
        background-color: #000c17; 
        color: white; 
    }

    /* Změna barev multiselect kolonek */
    span[data-baseweb="tag"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border-radius: 5px !important;
    }

    /* Ikona křížku */
    span[data-baseweb="tag"] svg {
        fill: white !important;
    }

    /* Karty se statistikami (Neon Blue) */
    div[data-testid="stMetric"] {
        background-color: #000c17;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #00aaff;
        box-shadow: 0 0 10px rgba(0, 170, 255, 0.3);
    }

    /* Barva čísel v metrikách (Alza Green) */
    div[data-testid="stMetricValue"] { 
        color: #00ff88 !important; 
        font-weight: bold;
    }

    /* Tlačítko v Alza zelené */
    .stButton>button {
        background-color: #00ff88;
        color: #001529;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        height: 3em;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00cc6e;
    }

    /* Nadpisy */
    h1, h2, h3 { color: white !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")
st.write("---")

# Inicializace stavu pro výsledky
if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

# --- 1. HORNÍ STATISTIKY (Napojené na data) ---
pocet = len(st.session_state.vysledky)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(label="Zpracováno faktur", value=str(pocet))
with c2:
    st.metric(label="Celková suma", value="Dle analýzy")
with c3:
    st.metric(label="Úspora času", value=f"{pocet * 5} min")
with c4:
    st.metric(label="Stav AI", value="Ready" if pocet == 0 else "Online")

st.write("---")

# --- 2. HLAVNÍ PLOCHA (Sidebar + Main) ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.subheader("⚙️ Konfigurace")
    uploaded_files = st.file_uploader("Nahrajte PDF faktury", accept_multiple_files=True, type=['pdf'])

    vyber = st.multiselect(
        "Data k vytažení:",
        [
            "ELEKTŘINA: Spotřeba (kWh)", 
            "ELEKTŘINA: průměrná cena (Kč/kWh)",
            "ELEKTŘINA: Cena sil. el. (fakturovaná)", 
            "ELEKTŘINA: Cena distribuce (fakturovaná)",
            "ELEKTŘINA: Cena celkem (fakturovaná)",
            "FSX (společné prostory): Spotřeba (kWh)",
            "FSX (společné prostory): Cena celkem (fakturovaná)",
            "PLYN: Spotřeba (m3)",
            "PLYN: Spotřeba (kWh)",
            "PLYN: průměrná cena (Kč/kWh)",
            "PLYN: Cena celkem (fakturovaná)"
        ],
        default=["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem (fakturovaná)", "PLYN: Cena celkem (fakturovaná)"]
    )
    analyze_btn = st.button("🚀 SPUSTIT AI ANALÝZU")

with col_main:
    # --- LOGIKA ANALÝZY ---
    if analyze_btn and uploaded_files:
        st.subheader("🤖 Průběh AI analýzy")
        st.session_state.vysledky = [] # Resetovat staré výsledky při novém startu

        # Produkční URL (bez -test) pro automatické spouštění
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"

        for file in uploaded_files:
            with st.spinner(f"Analyzuji: {file.name}..."):
                try:
                    # Posíláme jako 'data', aby to n8n uzel 'Extract from File' viděl
                    files = {"data": (file.name, file.getvalue(), "application/pdf")}
                    payload = {"p": str(vyber)} 

                    response = requests.post(webhook_url, files=files, data=payload)

                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list):
                            data = data[0]
                        data["Faktura"] = file.name
                        st.session_state.vysledky.append(data)
                    else:
                        st.error(f"Chyba u {file.name}: n8n vrátilo kód {response.status_code}")
                except Exception as e:
                    st.error(f"Nepodařilo se spojit s n8n: {e}")
        
        # Refresh pro zobrazení statistik
        st.rerun()

    # Zobrazení výsledků
    if st.session_state.vysledky:
        df = pd.DataFrame(st.session_state.vysledky)
        st.success("✅ Analýza dokončena!")

        # Zobrazení tabulky výsledků
        st.dataframe(df, use_container_width=True)

        # Dynamický graf podle prvního vybraného pole
        if len(vyber) > 0:
            y_col = vyber[0] if vyber[0] in df.columns else df.columns[0]
            fig = px.bar(df, x="Faktura", y=y_col, 
                         title=f"Srovnání: {y_col}", 
                         template="plotly_dark",
                         color_discrete_sequence=['#708090']) # Šedá barva

            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    elif not uploaded_files:
        st.subheader("📈 Srovnání nákladů")
        # Prázdný graf pro design
        dummy_df = pd.DataFrame({"Faktura": ["A", "B", "C"], "Kč": [0, 0, 0]})
        fig = px.bar(dummy_df, x="Faktura", y="Kč", title="Graf se zobrazí po analýze", template="plotly_dark")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Nahrajte faktury v levém panelu pro zobrazení výsledků.")
