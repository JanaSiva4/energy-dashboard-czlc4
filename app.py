import streamlit as st
import pandas as pd

# Nastavení stránky
st.set_page_config(page_title="CZLC4 Energy Intelligence", layout="wide")

# Tvůj tmavý design (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #001529; color: white; }
    .stButton>button { 
        background: linear-gradient(90deg, #00aaff 0%, #00ff88 100%); 
        color: #001529; font-weight: bold; border: none; border-radius: 10px;
    }
    .stDataFrame { background-color: #0c2135; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ CZLC4 Energy Intelligence")
st.write("Nahrajte faktury za energii (PDF) pro automatickou AI analýzu.")

# Boční panel pro výběr parametrů
with st.sidebar:
    st.header("Nastavení extrakce")
    vyber = st.multiselect(
        "Co chcete vyčíst?",
        ["Elektřina: Spotřeba (kWh)", "Cena sil. el.", "Cena distribuce", "Cena celkem", "Plyn: Spotřeba (kWh)", "Voda: Spotřeba (m3)"],
        default=["Elektřina: Spotřeba (kWh)", "Cena celkem"]
    )
    st.info("Vybrané parametry budou odeslány do n8n k analýze.")

# Hlavní nahrávací zóna
uploaded_files = st.file_uploader("Přetáhněte PDF soubory sem", accept_multiple_files=True, type=['pdf'])

if st.button("🚀 Spustit AI analýzu"):
    if uploaded_files:
        st.write(f"Zpracovávám {len(uploaded_files)} souborů...")
        # Tady později propojíme tvůj n8n Webhook
        st.success("Soubory byly odeslány do n8n. Čekám na data...")

        # Ukázka, jak by vypadala tabulka s výsledky
        test_data = pd.DataFrame({
            "Soubor": [f.name for f in uploaded_files],
            "Stav": ["Zpracováno" for _ in uploaded_files],
            "Celková cena (Kč)": ["Vypočítávám..." for _ in uploaded_files]
        })
        st.table(test_data)
    else:
        st.warning("Nejdříve prosím nahrajte aspoň jednu fakturu.")
