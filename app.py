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
    span[data-baseweb="tag"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border-radius: 5px !important;
    }
    div[data-testid="stMetric"] {
        background-color: #000c17;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #00aaff;
        box-shadow: 0 0 10px rgba(0, 170, 255, 0.3);
    }
    div[data-testid="stMetricValue"] { color: #00ff88 !important; font-weight: bold; }
    .stButton>button {
        background-color: #00ff88;
        color: #001529;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        height: 3em;
        width: 100%;
    }
    h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")
st.write("---")

# --- Inicializace Session State (aby data nezmizela) ---
if 'vysledky_data' not in st.session_state:
    st.session_state.vysledky_data = []

# --- 1. HORNÍ STATISTIKY (Teď jsou fixní a hned vidět) ---
count = len(st.session_state.vysledky_data)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(label="Zpracováno faktur", value=str(count))
with c2:
    st.metric(label="Celková suma", value="Aktualizace...")
with c3:
    st.metric(label="Úspora času", value=f"{count * 5} min")
with c4:
    st.metric(label="Stav AI", value="Ready" if count == 0 else "Done")

st.write("---")

# --- 2. SIDEBAR A KONFIGURACE ---
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
        st.subheader("🤖 Průběh AI analýzy")
        st.session_state.vysledky_data = [] # Reset při novém startu
        
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
                    else:
                        st.error(f"Chyba u {file.name}: kód {response.status_code}")
                except Exception as e:
                    st.error(f"Spojení selhalo: {e}")
        
        # Po dokončení analýzy stránku restartujeme, aby se projevily statistiky nahoře
        st.rerun()

    # Zobrazení výsledků, pokud existují
    if st.session_state.vysledky_data:
        df = pd.DataFrame(st.session_state.vysledky_data)
        st.success("✅ Analýza dokončena!")
        st.dataframe(df, use_container_width=True)

        if len(vyber) > 0:
            y_col = vyber[0] if vyber[0] in df.columns else df.columns[0]
            fig = px.bar(df, x="Faktura", y=y_col, title=f"Srovnání: {y_col}", 
                         template="plotly_dark", color_discrete_sequence=['#555555'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 Nahrajte faktury a spusťte analýzu.")
