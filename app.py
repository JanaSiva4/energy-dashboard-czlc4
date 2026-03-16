import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Nastavení stránky
st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# --- NÁVRAT K PŮVODNÍMU TMAVÉMU DESIGNU ---
st.markdown("""
    <style>
    .stApp { 
        background-color: #001529; 
        color: white; 
    }
    [data-testid="stSidebar"] { 
        background-color: #000c17; 
    }
    .stMetric {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
    }
    .stButton>button { 
        background: linear-gradient(90deg, #00aaff 0%, #00ff88 100%); 
        color: #001529; 
        font-weight: bold; 
        border: none; 
        border-radius: 10px;
    }
    /* Úprava barev tabulky, aby byla čitelná na tmavém */
    .stDataFrame { background-color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")

# Horní statistiky (vždy viditelné)
col_a, col_b, col_c = st.columns(3)
col_a.metric("Nahraných faktur", "0")
col_b.metric("Celková suma", "0 Kč")
col_c.metric("Status AI", "Připraven")

st.write("---")

with st.sidebar:
    st.header("Nastavení extrakce")
    vyber = st.multiselect(
        "Co chcete vyčíst?",
        ["Elektřina: Spotřeba (kWh)", "Cena sil. el.", "Cena distribuce", "Cena celkem", "Dodavatel"],
        default=["Elektřina: Spotřeba (kWh)", "Cena celkem"]
    )

uploaded_files = st.file_uploader("Nahrajte faktury (PDF)", accept_multiple_files=True, type=['pdf'])

if st.button("🚀 Spustit AI analýzu"):
    if uploaded_files:
        st.info(f"Zpracovávám {len(uploaded_files)} souborů...")
        results = []
        # TVOJE URL Z n8n
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook-test/faktury-upload"
        
        for file in uploaded_files:
            files = {"file": (file.name, file.getvalue(), "application/pdf")}
            data = {"parametry": str(vyber)}
            
            try:
                # Odeslání do n8n s vypnutou kompresí pro stabilitu
                response = requests.post(webhook_url, files=files, data=data, headers={"Accept-Encoding": "identity"})
                if response.status_code == 200:
                    res_data = response.json()
                    res_data["Soubor"] = file.name
                    results.append(res_data)
                else:
                    st.error(f"Chyba u {file.name}")
            except Exception as e:
                st.error(f"Nepodařilo se připojit k n8n: {e}")

        if results:
            df = pd.DataFrame(results)
            
            # Zobrazení grafu
            if "Cena celkem" in df.columns:
                df["Cena celkem"] = pd.to_numeric(df["Cena celkem"], errors='coerce')
                st.subheader("📊 Srovnání nákladů")
                fig = px.bar(df, x="Soubor", y="Cena celkem", template="plotly_dark", color_discrete_sequence=['#00aaff'])
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Detailní data")
            st.dataframe(df)
    else:
        st.warning("Nejdříve nahrajte faktury.")
