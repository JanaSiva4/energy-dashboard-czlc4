import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- KONFIGURACE GOOGLE SHEETS ---
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzfRP2cvMrwjbsCgQPzfbQsVABB68OYdpTPajGRT4hbhBbVWoGPJIJJTfMy6PbbhfTwCQ/exec"

def odeslat_do_google_sheets(res, sklad="CZLC4"):
    """
    Odešle data do Google Sheets ve formátu 16 sloupců.
    Používá inteligentní hledání klíčů (find_val), aby se předešlo prázdným polím.
    """
    try:
        # 1. Získání roku a měsíce
        obdobi_raw = str(res.get('obdobi', datetime.now().strftime('%Y-%m')))
        rok, mesic = map(int, obdobi_raw.split('-'))

        # Pomocná funkce pro bezpečný převod na číslo
        def to_f(val):
            if not val or str(val).lower() == 'n/a': return 0.0
            try: 
                # Odstraní mezery, čárky zamění za tečky a vyhodí "Kč"
                ciste_cislo = str(val).replace(',', '.').replace(' ', '').replace('Kč', '').replace('\xa0', '')
                return float(ciste_cislo)
            except: 
                return 0.0

        # Inteligentní vyhledávač hodnot v datech z n8n
        def find_val(data, search_term):
            for k, v in data.items():
                if search_term.lower() in str(k).lower():
                    return v
            return 0.0

        # 2. Příprava 16 sloupců přesně pro tvůj Dashboard
        data_row = [
            rok,                                         # 0: Rok
            mesic,                                       # 1: Mes
            to_f(find_val(res, 'SPOTREBA KWH')),         # 2: El_kWh
            to_f(find_val(res, 'JEDNOTKOVA')),           # 3: El_Cena_kWh
            to_f(find_val(res, 'SIL')),                  # 4: El_Silova (Najde "CENA SIL BEZ DPH")
            to_f(find_val(res, 'DISTRIBUCE')),           # 5: El_Distr (Najde "CENA DISTRIBUCE BEZ DPH")
            to_f(find_val(res, 'ZAKLAD KC')),            # 6: El_Celkem
            to_f(res.get('fsx_spotreba_kwh', 0)),        # 7
            to_f(res.get('fsx_jednotkova_cena', 0)),     # 8
            to_f(res.get('fsx_cena_bez_dph', 0)),        # 9
            to_f(res.get('plyn_spotreba_kwh', 0)),       # 10
            to_f(res.get('plyn_jednotkova_cena_kc', 0)), # 11
            to_f(res.get('plyn_cena_celkem_zaklad_kc', 0)), # 12
            to_f(res.get('voda_spotreba_m3', 0)),        # 13
            to_f(res.get('voda_jednotkova_cena_kc', 0)), # 14
            to_f(res.get('voda_cena_bez_dph', 0))        # 15
        ]

        payload = {
            "action": "append",
            "sheet": sklad,
            "row": data_row
        }
        
        requests.post(GOOGLE_SCRIPT_URL, json=payload)
        return True 
    except Exception as e:
        st.error(f"Chyba při odesílání: {e}")
        return False

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="DocScan", layout="wide", page_icon="🔍")

# --- CSS STYLY (Tmavý režim a karty) ---
st.markdown("""
<style>
    [data-testid="stMainViewContainer"] .block-container { max-width: 1200px !important; }
    .stApp {
        background: linear-gradient(135deg, #051c3d 0%, #2e0b54 40%, #1a0633 70%, #030821 100%) !important;
        color: #f0f0f0;
    }
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #0052cc 0%, #0a84ff 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold;
    }
    .energy-card {
        background: rgba(10,10,20,0.4) !important;
        border-radius: 12px;
        padding: 15px;
        backdrop-filter: blur(20px);
        margin-bottom: 10px;
    }
    .el-border { border-top: 3px solid #FFD700; }
    .fsx-border { border-top: 3px solid #0084ff; }
    .gas-border { border-top: 3px solid #FF5722; }
    .water-border { border-top: 3px solid #00BFFF; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'vysledky' not in st.session_state: st.session_state.vysledky = []
if 'kategorie' not in st.session_state: st.session_state.kategorie = "Energie"
if 'sklad' not in st.session_state: st.session_state.sklad = "CZLC4"

st.title("🔍 DocScan")
st.write("---")

# --- KATEGORIE ---
cols_kat = st.columns(4)
kats_info = [("⚡", "Energie"), ("📄", "Faktury"), ("📋", "Smlouvy"), ("📦", "Objednávky")]

for col, (icon, name) in zip(cols_kat, kats_info):
    with col:
        if st.button(f"{icon} {name}", use_container_width=True):
            st.session_state.kategorie = name
            st.rerun()

st.write("---")

# --- OBSAH PRO ENERGIE ---
if st.session_state.kategorie == "Energie":
    col_side, col_main = st.columns([1, 3])

    with col_side:
        st.markdown("### Nastavení")
        st.session_state.sklad = st.selectbox("Cílový sklad:", ["CZLC4", "LCÚ", "LCZ", "SKLC3"])
        obdobi_input = st.text_input("Období (RRRR-MM)", value=datetime.now().strftime('%Y-%m'))
        uploaded_files = st.file_uploader("Vložte faktury (PDF)", accept_multiple_files=True)
        
        if st.button("🚀 SPUSTIT ANALÝZU", use_container_width=True):
            if uploaded_files:
                with st.spinner("Analyzuji..."):
                    try:
                        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"
                        files = [("data", (f.name, f.getvalue(), "application/pdf")) for f in uploaded_files]
                        response = requests.post(webhook_url, files=files, data={"p": obdobi_input})
                        if response.status_code == 200:
                            st.session_state.vysledky = response.json() if isinstance(response.json(), list) else [response.json()]
                            st.success("Analýza hotova!")
                        else:
                            st.error(f"Chyba n8n: {response.status_code}")
                    except Exception as e:
                        st.error(f"Chyba spojení: {e}")

    with col_main:
        if st.session_state.vysledky:
            res = st.session_state.vysledky[0]
            
            # Tlačítko pro odeslání
            if st.button("✅ ODESLAT DO DASHBOARDU", type="primary", use_container_width=True):
                if odeslat_do_google_sheets(res, st.session_state.sklad):
                    st.balloons()
                    st.success(f"Data byla úspěšně zapsána do listu {st.session_state.sklad}!")

            st.subheader("📁 Digitální archiv")
            st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)

            # Barevné karty náhledu
            st.write("---")
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.markdown('<div class="energy-card el-border"><h3>⚡ Elektřina</h3></div>', unsafe_allow_html=True)
                for k in ['SPOTREBA KWH', 'CENA SIL BEZ DPH', 'CENA DISTRIBUCE BEZ DPH', 'CENA CELKEM ZAKLAD KC']:
                    val = res.get(k, "0")
                    st.write(f"**{k}:** {val}")

            with c2:
                st.markdown('<div class="energy-card fsx-border"><h3>🏢 FSX</h3></div>', unsafe_allow_html=True)
                for k, v in res.items():
                    if 'fsx' in k.lower(): st.write(f"**{k}:** {v}")

            with c3:
                st.markdown('<div class="energy-card gas-border"><h3>🔥 Plyn</h3></div>', unsafe_allow_html=True)
                for k, v in res.items():
                    if 'plyn' in k.lower(): st.write(f"**{k}:** {v}")

            with c4:
                st.markdown('<div class="energy-card water-border"><h3>💧 Voda</h3></div>', unsafe_allow_html=True)
                for k, v in res.items():
                    if 'voda' in k.lower(): st.write(f"**{k}:** {v}")
        else:
            st.info("Nahrajte soubory a spusťte analýzu.")
else:
    st.info(f"Sekce {st.session_state.kategorie} je v přípravě.")
