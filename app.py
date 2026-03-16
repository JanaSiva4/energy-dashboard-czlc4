import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# Vylepšený "Alza" styl
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .metric-box {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-top: 5px solid #00aaff;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")
st.subheader("Automatizovaný systém pro analýzu energetických nákladů")

# Sidebar
with st.sidebar:
    st.header("⚙️ Konfigurace")
    vyber = st.multiselect(
        "Data k vytažení:",
        ["Cena celkem", "Spotřeba (kWh)", "Dodavatel", "Variabilní symbol"],
        default=["Cena celkem", "Spotřeba (kWh)", "Dodavatel"]
    )
    st.write("---")
    st.write("💡 **Tip:** Nahrajte více faktur najednou pro srovnání.")

# Nahrávání
uploaded_files = st.file_uploader("📂 Sem přetáhněte faktury", accept_multiple_files=True, type=['pdf'])

if st.button("🚀 Spustit AI analýzu"):
    if uploaded_files:
        results = []
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook-test/faktury-upload"
        
        with st.status("AI čte faktury...", expanded=True) as status:
            for file in uploaded_files:
                st.write(f"Skenuji: {file.name}")
                files = {"file": (file.name, file.getvalue(), "application/pdf")}
                data = {"parametry": str(vyber)}
                
                try:
                    res = requests.post(webhook_url, files=files, data=data, headers={"Accept-Encoding": "identity"})
                    if res.status_code == 200:
                        item = res.json()
                        item["Soubor"] = file.name
                        results.append(item)
                except:
                    st.error(f"Nepodařilo se spojit s n8n u {file.name}")
            status.update(label="Analýza dokončena!", state="complete", expanded=False)

        if results:
            df = pd.DataFrame(results)
            # Převod ceny na čísla, aby grafy fungovaly
            if "Cena celkem" in df.columns:
                df["Cena celkem"] = pd.to_numeric(df["Cena celkem"], errors='coerce')

            # --- COOL STATISTIKY ---
            st.write("### 📊 Přehled analýzy")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="metric-box"><h4>Zpracováno</h4><h2>{len(df)} faktur</h2></div>', unsafe_allow_html=True)
            with c2:
                if "Cena celkem" in df.columns:
                    total = df["Cena celkem"].sum()
                    st.markdown(f'<div class="metric-box"><h4>Celková suma</h4><h2>{total:,.0f} Kč</h2></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="metric-box"><h4>Ušetřený čas</h4><h2>~{len(df)*5} min</h2></div>', unsafe_allow_html=True)

            st.write("---")

            # --- GRAFY ---
            col_left, col_right = st.columns(2)
            
            with col_left:
                if "Cena celkem" in df.columns:
                    st.write("#### Srovnání nákladů")
                    fig1 = px.bar(df, x="Soubor", y="Cena celkem", color="Cena celkem", color_continuous_scale="Viridis")
                    st.plotly_chart(fig1, use_container_width=True)

            with col_right:
                if "Dodavatel" in df.columns:
                    st.write("#### Podíl dodavatelů")
                    fig2 = px.pie(df, names="Dodavatel", hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)

            # Tabulka na konci
            st.write("#### 📑 Detailní výpis dat")
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("Prosím, nahrajte faktury.")
