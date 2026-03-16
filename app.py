import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Nastavení stránky
st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# --- DESIGN (CSS) ---
st.markdown("""
    <style>
    .stApp { 
        background-color: #001529; 
        color: white; 
    }
    [data-testid="stSidebar"] { 
        background-color: #000c17; 
        color: white; 
    }
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
    div[data-testid="stMetricValue"] { 
        color: #00ff88 !important; 
        font-weight: bold;
    }
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

# --- 1. HORNÍ STATISTIKY ---
# Místo pro výsledky analýzy
stat_placeholder = st.empty()

# --- 2. SIDEBAR A KONFIGURACE ---
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
    if analyze_btn and uploaded_files:
        st.subheader("🤖 Průběh AI analýzy")
        vysledky = []
        
        # Tvůj n8n Webhook URL
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook-test/faktury-upload"

        for file in uploaded_files:
            with st.spinner(f"Analyzuji: {file.name}..."):
                try:
                    # Odeslání souboru pod klíčem 'data'
                    files = {"data": (file.name, file.getvalue(), "application/pdf")}
                    payload = {"p": str(vyber)} 
                    
                    response = requests.post(webhook_url, files=files, data=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list): data = data[0]
                        data["Faktura"] = file.name
                        vysledky.append(data)
                    else:
                        st.error(f"Chyba u {file.name}: n8n kód {response.status_code}")
                except Exception as e:
                    st.error(f"Spojení selhalo: {e}")

        if vysledky:
            df = pd.DataFrame(vysledky)
            st.success("✅ Analýza dokončena!")
            
            # Tabulka s výsledky
            st.dataframe(df, use_container_width=True)

            # Graf s novou šedou barvou
            if len(vyber) > 0:
                y_col = vyber[0] if vyber[0] in df.columns else df.columns[0]
                fig = px.bar(df, x="Faktura", y=y_col, 
                             title=f"Srovnání: {y_col}", 
                             template="plotly_dark",
                             color_discrete_sequence=['#555555']) # Změna na šedou
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            
            # Aktualizace horních statistik
            with stat_placeholder.container():
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Zpracováno faktur", len(vysledky))
                c2.metric("Celková suma", "Z tabulky")
                c3.metric("Úspora času", f"{len(vysledky)*5} min")
                c4.metric("Stav AI", "Done")
        else:
            st.warning("Žádná data nebyla zpracována.")

    elif not uploaded_files:
        st.subheader("📈 Srovnání nákladů")
        dummy_df = pd.DataFrame({"Faktura": ["A", "B", "C"], "Kč": [0, 0, 0]})
        fig = px.bar(dummy_df, x="Faktura", y="Kč", title="Graf se zobrazí po analýze", template="plotly_dark")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Nahrajte faktury v levém panelu pro zobrazení výsledků.")
