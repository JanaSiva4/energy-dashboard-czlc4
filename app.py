import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Konfigurace stránky
st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# --- ALZA BLUE / PURPLE STYLE (CSS) ---
st.markdown("""
    <style>
    /* Hlavní pozadí v Alza modrofialové */
    .stApp { 
        background: linear-gradient(135deg, #004990 0%, #2b32b2 100%); 
        color: white; 
    }
    
    /* Sidebar v tmavší modré */
    [data-testid="stSidebar"] { 
        background-color: #002d5a; 
        color: white; 
    }
    
    /* Karty se statistikami - bílé s průhledností */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Barva čísel v metrikách */
    div[data-testid="stMetricValue"] { 
        color: #00ff88 !important; 
    }

    /* Tlačítko v Alza zelené */
    .stButton>button {
        background: #00ff88;
        color: #002d5a;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        height: 3em;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: #00cc6e;
        transform: scale(1.02);
    }
    
    /* Nadpisy */
    h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")
st.write("---")

# --- 1. HORNÍ STATISTIKY ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(label="Zpracováno faktur", value="0")
with c2:
    st.metric(label="Celková suma", value="0 Kč")
with c3:
    st.metric(label="Úspora času", value="0 min")
with c4:
    st.metric(label="Stav systému", value="Online")

st.write("---")

# --- 2. HLAVNÍ PLOCHA ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.subheader("📂 Vstupní data")
    uploaded_files = st.file_uploader("Nahrajte PDF faktury", accept_multiple_files=True, type=['pdf'])
    vyber = st.multiselect("Pole k extrakci:", ["Cena celkem", "Spotřeba", "Dodavatel"], default=["Cena celkem", "Spotřeba"])
    analyze_btn = st.button("🚀 SPUSTIT AI ANALÝZU")

with col_main:
    if not uploaded_files:
        st.subheader("📊 Vizualizace")
        # Prázdný graf pro design
        dummy_df = pd.DataFrame({"Faktura": ["-", "-", "-"], "Kč": [0, 0, 0]})
        fig = px.line(dummy_df, x="Faktura", y="Kč", title="Graf se vykreslí po nahrání dat")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    
    if analyze_btn and uploaded_files:
        results = []
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook-test/faktury-upload"
        
        with st.status("AI analyzuje faktury...", expanded=True) as status:
            for f in uploaded_files:
                try:
                    res = requests.post(webhook_url, files={"file": (f.name, f.getvalue())}, data={"p": str(vyber)})
                    if res.status_code == 200:
                        data = res.json()
                        data["Soubor"] = f.name
                        results.append(data)
                except:
                    st.error(f"Chyba spojení u {f.name}")
            status.update(label="Hotovo!", state="complete")

        if results:
            df = pd.DataFrame(results)
            if "Cena celkem" in df.columns:
                df["Cena celkem"] = pd.to_numeric(df["Cena celkem"], errors='coerce')
                st.subheader("📈 Srovnání nákladů")
                fig = px.bar(df, x="Soubor", y="Cena celkem", color_discrete_sequence=['#00ff88'])
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df)
