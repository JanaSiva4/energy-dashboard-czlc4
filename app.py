import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Nastavení stránky
st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# DESIGN (Tmavě modrá Alza)
st.markdown("""
    <style>
    .stApp { background-color: #001529; color: white; }
    [data-testid="stSidebar"] { background-color: #000c17; color: white; }
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    div[data-testid="stMetricValue"] { color: #00ff88 !important; }
    .stButton>button { 
        background: linear-gradient(90deg, #00aaff 0%, #00ff88 100%); 
        color: #001529; font-weight: bold; border-radius: 10px; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")

# STATISTIKY
st.write("### 📊 Aktuální přehled")
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric(label="Zpracováno faktur", value="0")
with col2: st.metric(label="Celková suma", value="0 Kč")
with col3: st.metric(label="Úspora času", value="0 min")
with col4: st.metric(label="Status AI", value="Ready")

st.write("---")

col_side, col_main = st.columns([1, 3])

with col_side:
    st.subheader("⚙️ Konfigurace")
    uploaded_files = st.file_uploader("Nahrajte PDF faktury", accept_multiple_files=True, type=['pdf'])
    
    # Tady je ten tvůj nový seznam!
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
        default=["ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena celkem (fakturovaná)"]
    )
    analyze_btn = st.button("🚀 SPUSTIT AI ANALÝZU")

with col_main:
    if not uploaded_files:
        st.subheader("📈 Srovnání nákladů")
        dummy_df = pd.DataFrame({"Faktura": ["A", "B", "C"], "Kč": [0, 0, 0]})
        fig = px.bar(dummy_df, x="Faktura", y="Kč", title="Graf se zobrazí po analýze", template="plotly_dark")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    if analyze_btn and uploaded_files:
        results = []
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook-test/faktury-upload"
        
        with st.status("AI čte faktury...", expanded=True) as status:
            for f in uploaded_files:
                try:
                    res = requests.post(webhook_url, files={"file": (f.name, f.getvalue())}, data={"p": str(vyber)})
                    if res.status_code == 200:
                        item = res.json()
                        item["Soubor"] = f.name
                        results.append(item)
                except:
                    st.error(f"Chyba spojení u {f.name}")
            status.update(label="Analýza hotova!", state="complete")

        if results:
            df = pd.DataFrame(results)
            st.subheader("📋 Výsledná data")
            st.dataframe(df)
