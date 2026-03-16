import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Nastavení stránky
st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# --- NÁVRAT K TVÉMU OBLÍBENÉMU TMAVĚ MODRÉMU DESIGNU ---
st.markdown("""
    <style>
    /* Původní tmavě modrá Alza barva */
    .stApp { 
        background-color: #001529; 
        color: white; 
    }
    [data-testid="stSidebar"] { 
        background-color: #000c17; 
        color: white;
    }
    /* Karty s čísly (Metrics) - průhledné s jemným okrajem */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    /* Zelená čísla pro "cool" efekt */
    div[data-testid="stMetricValue"] { 
        color: #00ff88 !important; 
    }
    /* Tlačítko s barevným přechodem */
    .stButton>button { 
        background: linear-gradient(90deg, #00aaff 0%, #00ff88 100%); 
        color: #001529; 
        font-weight: bold; 
        border: none; 
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")

# --- 1. HORNÍ STATISTIKY (To "cool" co tam nebylo) ---
st.write("### 📊 Aktuální přehled")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Zpracováno faktur", value="0")
with col2:
    st.metric(label="Celková suma", value="0 Kč")
with col3:
    st.metric(label="Úspora času", value="0 min")
with col4:
    st.metric(label="Status AI", value="Ready")

st.write("---")

# --- 2. HLAVNÍ PLOCHA ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.subheader("⚙️ Konfigurace")
    uploaded_files = st.file_uploader("Nahrajte PDF faktury", accept_multiple_files=True, type=['pdf'])
    vyber = st.multiselect(
        "Data k vytažení:",
        ["Cena celkem", "Spotřeba (kWh)", "Dodavatel", "Datum splatnosti"],
        default=["Cena celkem", "Spotřeba (kWh)"]
    )
    analyze_btn = st.button("🚀 SPUSTIT AI ANALÝZU")

with col_main:
    if not uploaded_files:
        st.subheader("📈 Srovnání nákladů")
        # Prázdný graf pro design, aby to nebylo bílé/prázdné
        dummy_df = pd.DataFrame({"Faktura": ["A", "B", "C"], "Kč": [0, 0, 0]})
        fig = px.bar(dummy_df, x="Faktura", y="Kč", title="Graf se zobrazí po analýze", template="plotly_dark")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Nahrajte faktury v levém panelu pro zobrazení výsledků.")
    
    if analyze_btn and uploaded_files:
        results = []
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook-test/faktury-upload"
        
        with st.status("AI čte faktury...", expanded=True) as status:
            for f in uploaded_files:
                try:
                    # Odeslání do n8n na Alza doméně
                    res = requests.post(webhook_url, files={"file": (f.name, f.getvalue())}, data={"p": str(vyber)})
                    if res.status_code == 200:
                        item = res.json()
                        item["Soubor"] = f.name
                        results.append(item)
                except:
                    st.error(f"Chyba spojení u {f.name}")
            status.update(label="Hotovo!", state="complete")

        if results:
            df = pd.DataFrame(results)
            
            # --- ZOBRAZENÍ REÁLNÉHO GRAFU ---
            if "Cena celkem" in df.columns:
                df["Cena celkem"] = pd.to_numeric(df["Cena celkem"], errors='coerce')
                st.subheader("📊 Výsledné srovnání")
                fig = px.bar(df, x="Soubor", y="Cena celkem", color="Cena celkem", color_continuous_scale="Viridis")
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Detailní tabulka")
            st.dataframe(df)
