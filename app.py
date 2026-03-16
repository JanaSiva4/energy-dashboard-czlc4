import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Nastavení stránky
st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# --- DESIGN (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #001529; color: white; }
    [data-testid="stSidebar"] { background-color: #000c17; color: white; }
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
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")
st.write("---")

# Inicializace paměti pro výsledky
if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

# --- 1. HORNÍ STATISTIKY (Napojené na data) ---
count = len(st.session_state.vysledky)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno faktur", count)
with c2: st.metric("Celková suma", "Dle vytažených dat")
with c3: st.metric("Úspora času", f"{count * 5} min")
with c4: st.metric("Stav AI", "Ready" if count == 0 else "V provozu")

st.write("---")

# --- 2. HLAVNÍ PLOCHA ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.subheader("⚙️ Konfigurace")
    uploaded_files = st.file_uploader("Nahrajte PDF faktury", accept_multiple_files=True, type=['pdf'])
    vyber = st.multiselect(
        "Data k vytažení:",
        ["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem (fakturovaná)", "PLYN: Cena celkem (fakturovaná)"],
        default=["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem (fakturovaná)"]
    )
    analyze_btn = st.button("🚀 SPUSTIT AI ANALÝZU")

with col_main:
    if analyze_btn and uploaded_files:
        st.session_state.vysledky = []
        # POUŽÍVÁME PRODUKČNÍ URL (BEZ -TEST)
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
                        st.session_state.vysledky.append(data)
                    else:
                        st.error(f"Chyba u {file.name}: n8n kód {response.status_code}")
                except Exception as e:
                    st.error(f"Spojení s n8n selhalo: {e}")
        st.rerun()

    # Zobrazení výsledků, pokud nějaké máme
    if st.session_state.vysledky:
        df = pd.DataFrame(st.session_state.vysledky)
        st.success("✅ Analýza dokončena!")
        st.dataframe(df, use_container_width=True)

        # Graf v nové šedé barvě
        if len(vyber) > 0:
            y_col = vyber[0] if vyber[0] in df.columns else df.columns[0]
            fig = px.bar(df, x="Faktura", y=y_col, title=f"Srovnání: {y_col}", 
                         template="plotly_dark", 
                         color_discrete_sequence=['#808080']) # Šedá barva
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 Nahrajte faktury vlevo pro spuštění AI analýzy.")
