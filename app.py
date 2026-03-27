import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- KONFIGURACE GOOGLE SHEETS ---
# URL tvého Google Apps Scriptu (shodná s tou v HTML dashboardu)
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzfRP2cvMrwjbsCgQPzfbQsVABB68OYdpTPajGRT4hbhBbVWoGPJIJJTfMy6PbbhfTwCQ/exec"

def odeslat_do_google_sheets(res, sklad="CZLC4"):
    """
    Odešle data do Google Sheets ve formátu 16 sloupců, 
    které vyžaduje tvůj HTML dashboard.
    """
    try:
        # 1. Získání roku a měsíce z výsledku nebo aktuálního data
        obdobi_raw = str(res.get('obdobi', datetime.now().strftime('%Y-%m')))
        rok, mesic = map(int, obdobi_raw.split('-'))

        # Pomocná funkce pro bezpečný převod na číslo
        def to_f(val):
            if not val or str(val).lower() == 'n/a': return 0.0
            try: return float(str(val).replace(',', '.').replace(' ', ''))
            except: return 0.0

        # 2. Příprava 16 sloupců přesně podle pořadí v loadData() tvého dashboardu
        # Indexy: 0:Rok, 1:Mes, 2:El_kWh, 3:El_Cena_kWh, 4:El_Silova, 5:El_Distr, 6:El_Celkem...
        data_row = [
            rok,                                      # 0
            mesic,                                    # 1
            to_f(res.get('el_spotreba_kwh')),         # 2
            to_f(res.get('el_jednotkova_cena_kc')),   # 3
            to_f(res.get('el_cena_silova_kc')),       # 4
            to_f(res.get('el_cena_distribuce_kc')),   # 5
            to_f(res.get('el_cena_celkem_zaklad_kc')),# 6
            to_f(res.get('fsx_spotreba_kwh')),        # 7
            to_f(res.get('fsx_jednotkova_cena')),     # 8
            to_f(res.get('fsx_cena_bez_dph')),        # 9
            to_f(res.get('plyn_spotreba_kwh')),       # 10
            to_f(res.get('plyn_jednotkova_cena_kc')), # 11
            to_f(res.get('plyn_cena_celkem_zaklad_kc')), # 12
            to_f(res.get('voda_spotreba_m3')),        # 13
            to_f(res.get('voda_jednotkova_cena_kc')), # 14
            to_f(res.get('voda_cena_bez_dph'))        # 15
        ]

        payload = {
            "action": "append",
            "sheet": sklad,
            "row": data_row
        }
        
        # Odeslání požadavku
        resp = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        return True 
    except Exception as e:
        st.error(f"Chyba při odesílání: {e}")
        return False

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="DocScan", layout="wide", page_icon="🔍")

# --- KOMPLETNÍ CSS STYLY (Z tvého původního návrhu) ---
st.markdown("""
<style>
    [data-testid="stMainViewContainer"] .block-container {
        max-width: 1200px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    .stApp {
        background: linear-gradient(135deg, #051c3d 0%, #2e0b54 40%, #1a0633 70%, #030821 100%) !important;
        background-attachment: fixed !important;
        color: #f0f0f0;
    }
    [data-testid="stHeader"] { background: rgba(0,0,0,0) !important; }
    div[data-testid="stMetric"] {
        background: rgba(0,0,0,0.25) !important;
        backdrop-filter: blur(15px);
        padding: 15px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.6) !important;
        box-shadow: 0 0 15px rgba(0,242,255,0.4) !important;
    }
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #0052cc 0%, #0a84ff 100%) !important;
        border: none !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        border-radius: 8px !important;
    }
    .energy-card {
        background: rgba(10,10,20,0.4) !important;
        border-radius: 12px;
        padding: 10px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(20px);
        margin-bottom: 10px;
    }
    .el-border { border-top: 2px solid #FFD700 !important; }
    .fsx-border { border-top: 2px solid #0084ff !important; }
    .gas-border { border-top: 2px solid #FF5722 !important; }
    .water-border { border-top: 2px solid #00BFFF !important; }
    .cat-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 16px;
        text-align: center;
        transition: all 0.3s;
    }
    .cat-card.active {
        background: rgba(0,82,204,0.15);
        border-color: #0084ff;
        box-shadow: 0 0 20px rgba(0,132,255,0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'vysledky' not in st.session_state: st.session_state.vysledky = []
if 'kategorie' not in st.session_state: st.session_state.kategorie = "Energie"
if 'sklad' not in st.session_state: st.session_state.sklad = "CZLC4"

st.title("🔍 DocScan")
st.write("---")

# --- KATEGORIE (Hlavička s kartami) ---
cols_kat = st.columns(4)
kategorie_list = [
    ("⚡", "Energie", "Spotřeba & náklady"),
    ("📄", "Faktury", "Dodavatel, částky, splatnost"),
    ("📋", "Smlouvy", "Strany, podmínky, datum"),
    ("📦", "Objednávky", "Položky, ceny, dodávky"),
]

for col, (icon, name, desc) in zip(cols_kat, kategorie_list):
    with col:
        is_active = st.session_state.kategorie == name
        active_class = "active" if is_active else ""
        st.markdown(f"""
        <div class="cat-card {active_class}">
            <div style="font-size:1.8rem">{icon}</div>
            <div style="font-weight:bold; color:#fff;">{name}</div>
            <div style="font-size:0.7rem; color:rgba(255,255,255,0.4);">{desc}</div>
        </div>""", unsafe_allow_html=True)
        if st.button(f"Zvolit {name}", key=f"btn_{name}", use_container_width=True):
            st.session_state.kategorie = name
            st.rerun()

st.write("---")

# --- HLAVNÍ OBSAH ---
if st.session_state.kategorie == "Energie":
    col_side, col_main = st.columns([1, 3])

    with col_side:
        st.markdown("### Nastavení")
        # Výběr skladu (shodný s tvým HTML dashboardem)
        st.session_state.sklad = st.selectbox("Cílový sklad:", ["CZLC4", "LCÚ", "LCZ", "SKLC3"])
        
        obdobi_input = st.text_input("Období (RRRR-MM)", value=datetime.now().strftime('%Y-%m'))
        uploaded_files = st.file_uploader("Vložte faktury", accept_multiple_files=True)
        
        if st.button("🚀 SPUSTIT ANALÝZU", use_container_width=True):
            if uploaded_files:
                with st.spinner("Analyzuji přes n8n..."):
                    try:
                        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"
                        files = [("data", (f.name, f.getvalue(), "application/pdf")) for f in uploaded_files]
                        response = requests.post(webhook_url, files=files, data={"p": obdobi_input})
                        if response.status_code == 200:
                            st.session_state.vysledky = response.json() if isinstance(response.json(), list) else [response.json()]
                            st.success("Hotovo!")
                        else:
                            st.error(f"Chyba: {response.status_code}")
                    except Exception as e:
                        st.error(f"Chyba spojení: {e}")

        if st.session_state.vysledky:
            if st.button("🗑 Nová analýza", use_container_width=True):
                st.session_state.vysledky = []
                st.rerun()

    with col_main:
        if st.session_state.vysledky:
            res = st.session_state.vysledky[0]
            
            # Horní tlačítko pro odeslání
            c_top1, c_top2 = st.columns([2, 1])
            with c_top2:
                if st.button("✅ ODESLAT DO DASHBOARDU", use_container_width=True, type="primary"):
                    if odeslat_do_google_sheets(res, st.session_state.sklad):
                        st.balloons()
                        st.success(f"Data uložena do {st.session_state.sklad}!")

            st.subheader("📁 Digitální archiv (Extrahovaná data)")
            st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)

            # Barevné přehledové karty
            st.write("---")
            st.subheader("📊 Detailní náhled")
            cols = st.columns(4)
            
            # Definice zobrazení pro karty
            kats = [
                ("⚡ Elektřina", "el_", "el-border", cols[0]),
                ("🏢 FSX", "fsx_", "fsx-border", cols[1]),
                ("🔥 Plyn", "plyn_", "gas-border", cols[2]),
                ("💧 Voda", "voda_", "water-border", cols[3])
            ]

            for label, prefix, style, col in kats:
                with col:
                    st.markdown(f'<div class="energy-card {style}"><h3>{label}</h3></div>', unsafe_allow_html=True)
                    # Vyfiltrujeme klíče pro danou kategorii
                    data_sub = {k: v for k, v in res.items() if k.startswith(prefix) and v and str(v) != 'n/a'}
                    for k, v in data_sub.items():
                        clean_k = k.replace(prefix, "").replace("_", " ").upper()
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,0.1);padding:4px 0;">
                            <span style="color:#888;font-size:0.75rem;">{clean_k}</span>
                            <span style="color:#fff;font-weight:bold;font-size:0.85rem;">{v}</span>
                        </div>""", unsafe_allow_html=True)
        else:
            st.info("Zde se zobrazí výsledky po spuštění analýzy.")

else:
    st.info(f"Sekce {st.session_state.kategorie} je v přípravě.")
