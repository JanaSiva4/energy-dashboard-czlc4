import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import re

# --- KONFIGURACE GOOGLE SHEETS ---
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzfRP2cvMrwjbsCgQPzfbQsVABB68OYdpTPajGRT4hbhBbVWoGPJIJJTfMy6PbbhfTwCQ/exec"

def odeslat_do_google_sheets(res, sklad="CZLC4"):
    try:
        # 1. Získání roku a měsíce
        obdobi_raw = str(res.get('obdobi', datetime.now().strftime('%Y-%m')))
        rok, mesic = map(int, obdobi_raw.split('-'))

        # AGRESIVNÍ funkce pro převod na číslo
        def to_f(val):
            if not val or str(val).lower() == 'n/a': return 0.0
            try:
                # Odstraní vše kromě číslic, tečky a čárky
                s = str(val).replace('\xa0', '').replace(' ', '')
                s = re.sub(r'[^0-9,.]', '', s)
                if ',' in s and '.' in s: s = s.replace(',', '') # tisíce
                s = s.replace(',', '.')
                return float(s)
            except:
                return 0.0

        # Funkce, která najde hodnotu, i když je název klíče jakýkoliv
        def find_val(data, *terms):
            for k, v in data.items():
                k_upper = str(k).upper()
                if any(t.upper() in k_upper for t in terms):
                    return v
            return 0.0

        # 2. Příprava 16 sloupců (VYLEPŠENÉ MAPOVÁNÍ)
        data_row = [
            rok,                                           # 0: Rok
            mesic,                                         # 1: Mes
            to_f(find_val(res, 'SPOTREBA', 'KWH')),        # 2: El_kWh
            to_f(find_val(res, 'JEDNOTKOVA')),             # 3: El_Cena_kWh
            to_f(find_val(res, 'SIL')),                    # 4: El_Silova (Najde "CENA SIL BEZ DPH")
            to_f(find_val(res, 'DIST')),                   # 5: El_Distr (Najde "CENA DISTRIBUCE")
            to_f(find_val(res, 'ZAKLAD KC', 'CELKEM')),    # 6: El_Celkem
            to_f(res.get('fsx_spotreba_kwh', 0)),          # 7
            to_f(res.get('fsx_jednotkova_cena', 0)),       # 8
            to_f(res.get('fsx_cena_bez_dph', 0)),          # 9
            to_f(res.get('plyn_spotreba_kwh', 0)),         # 10
            to_f(res.get('plyn_jednotkova_cena_kc', 0)),   # 11
            to_f(res.get('plyn_cena_celkem_zaklad_kc', 0)),# 12
            to_f(res.get('voda_spotreba_m3', 0)),          # 13
            to_f(res.get('voda_jednotkova_cena_kc', 0)),   # 14
            to_f(res.get('voda_cena_bez_dph', 0))          # 15
        ]

        payload = {"action": "append", "sheet": sklad, "row": data_row}
        requests.post(GOOGLE_SCRIPT_URL, json=payload)
        return True 
    except Exception as e:
        st.error(f"Chyba: {e}")
        return False

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="DocScan", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0e1117; color: white; }
    .energy-card {
        background: rgba(255,255,255,0.05);
        padding: 15px;
        border-radius: 10px;
        border-top: 3px solid #00f2ff;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 DocScan")

# --- SESSION STATE ---
if 'vysledky' not in st.session_state: st.session_state.vysledky = []
if 'sklad' not in st.session_state: st.session_state.sklad = "CZLC4"

# --- SIDEBAR / NASTAVENÍ ---
with st.sidebar:
    st.session_state.sklad = st.selectbox("Sklad:", ["CZLC4", "LCÚ", "LCZ", "SKLC3"])
    obdobi = st.text_input("Období:", datetime.now().strftime('%Y-%m'))
    files = st.file_uploader("Faktury:", accept_multiple_files=True)
    
    if st.button("🚀 ANALÝZA", use_container_width=True):
        if files:
            with st.spinner("Pracuji..."):
                f = [("data", (x.name, x.getvalue(), "application/pdf")) for x in files]
                r = requests.post("https://n8n.dev.gcp.alza.cz/webhook/faktury-upload", files=f, data={"p": obdobi})
                st.session_state.vysledky = r.json() if isinstance(r.json(), list) else [r.json()]

# --- HLAVNÍ PLOCHA ---
if st.session_state.vysledky:
    res = st.session_state.vysledky[0]
    
    if st.button("✅ ODESLAT DO TABULKY", type="primary"):
        if odeslat_do_google_sheets(res, st.session_state.sklad):
            st.balloons()
            st.success("Uloženo!")

    st.subheader("Data z faktury")
    st.dataframe(pd.DataFrame(st.session_state.vysledky))

    # Náhledové karty
    cols = st.columns(4)
    with cols[0]:
        st.markdown('<div class="energy-card"><h3>⚡ Elektřina</h3></div>', unsafe_allow_html=True)
        # Tady vypíšeme vše, co n8n poslalo, abychom viděli chybu
        for k, v in res.items():
            if any(x in k.upper() for x in ['SIL', 'DIST', 'KWH', 'CELKEM']):
                st.write(f"**{k}:** {v}")
else:
    st.info("Nahrajte faktury v bočním panelu.")
