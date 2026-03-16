import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Konfigurace stránky
st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# --- ALZA STYL (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    [data-testid="stSidebar"] { background-color: #001529; color: white; border-right: 1px solid #00aaff; }
    .stMetricValue { color: #00aaff; font-size: 36px; font-weight: bold; }
    .metric-label { color: #888; font-size: 14px; }
    .stButton>button { width: 100%; border-radius: 20px; background: linear-gradient(90deg, #00aaff, #00ff88); color: black; font-weight: bold; border: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")
st.write("---")

# --- 1. HORNÍ STATISTIKY (Viditelné vždy) ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(label="Zpracováno faktur", value="0")
with c2:
    st.metric(label="Celková suma", value="0 Kč")
with c3:
    st.metric(label="Úspora času", value="0 min")
with c4:
    st.metric(label="Stav AI", value="Ready", delta="Online")

st.write("---")

# --- 2. HLAVNÍ PLOCHA (Sidebar + Main) ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.subheader("📂 Nahrávání")
    uploaded_files = st.file_uploader("Přetáhněte PDF sem", accept_multiple_files=True, type=['pdf'])
    vyber = st.multiselect("Data k vytažení:", ["Cena celkem", "Spotřeba", "Splatnost"], default=["Cena celkem", "Spotřeba"])
    analyze_btn = st.button("🚀 SPUSTIT ANALÝZU")
    st.write("---")
    st.info("💡 **Tip:** Nahrajte více faktur najednou pro srovnání.")

with col_main:
    # --- POKUD NENÍ NAHRÁNO NIC (Designová prázdnota) ---
    if not uploaded_files:
        st.subheader("📈 Vizualizace nákladů")
        # Vytvoříme stínová data, aby graf nevypadal prázdně
        dummy_df = pd.DataFrame({"Faktura": ["#1", "#2", "#3"], "Kč": [0, 0, 0]})
        fig = px.bar(dummy_df, x="Faktura", y="Kč", title="Graf se zobrazí po analýze", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        st.warning("⚠️ Nejsou nahrány žádné faktury. Pro zobrazení grafů nahrajte PDF soubory vlevo.")
    
    # --- POKUD BĚŽÍ ANALÝZA ---
    if analyze_btn and uploaded_files:
        results = []
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook-test/faktury-upload"
        
        with st.status("AI pracuje...", expanded=True) as status:
            for f in uploaded_files:
                st.write(f"Skenuji: {f.name}")
                try:
                    res = requests.post(webhook_url, files={"file": (f.name, f.getvalue())}, data={"p": str(vyber)}, timeout=10)
                    if res.status_code == 200:
                        data = res.json()
                        data["Soubor"] = f.name
                        results.append(data)
                except:
                    st.error(f"Nepodařilo se spojit s n8n u {f.name}")
            status.update(label="Analýza hotova!", state="complete", expanded=False)

        # --- POKUD JSOU VÝSLEDKY ---
        if results:
            df = pd.DataFrame(results)
            
            # --- AKTUALIZACE GRAFU REÁLNÝMI DATY ---
            if "Cena celkem" in df.columns:
                # Převod na čísla
                df["Cena celkem"] = pd.to_numeric(df["Cena celkem"], errors='coerce')
                st.subheader("📊 Srovnání nákladů")
                fig = px.bar(df, x="Soubor", y="Cena celkem", color="Cena celkem", title="Cena za jednotlivé faktury", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                st.balloons() # Malá oslava úspěchu!
            
            # Tabulka
            st.subheader("📑 Detailní výpis")
            st.dataframe(df, use_container_width=True)
