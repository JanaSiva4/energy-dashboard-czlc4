import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm

# --- KONFIGURACE GOOGLE SHEETS ---
# Sem vlož URL svého nasazeného Google Apps Scriptu
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzfRP2cvMrwjbsCgQPzfbQsVABB68OYdpTPajGRT4hbhBbVWoGPJIJJTfMy6PbbhfTwCQ/exec"

def odeslat_do_google_sheets(res, nazev_listu="CZLC4"):
    """Převede data z výsledků n8n do řádku pro Google Sheets"""
    try:
        # Rozdělení období (např. 2026-01) na rok a měsíc
        obdobi_raw = str(res.get('obdobi', '2026-01'))
        rok, mesic = obdobi_raw.split('-')

        # Příprava dat pro řádek (pořadí: Rok, Měsíc, Elektřina, Plyn, Voda)
        payload = {
            "sheet": nazev_listu,
            "row": [
                rok,
                mesic,
                res.get('el_spotreba_kwh', 0),
                res.get('plyn_spotreba_kwh', 0),
                res.get('voda_spotreba_m3', 0)
            ]
        }
        resp = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        return resp.status_code == 200
    except Exception as e:
        st.error(f"Chyba při odesílání: {e}")
        return False

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="DocScan", layout="wide", page_icon="🔍")

# --- CSS STYLY ---
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
        height: 90px !important;
    }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    [data-testid="stMetricLabel"] p { font-size: 0.9rem !important; }
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #0052cc 0%, #0a84ff 100%) !important;
        border: none !important;
        color: #ffffff !important;
        box-shadow: 0 0 8px rgba(0,82,204,0.4) !important;
        transition: all 0.2s ease-in-out !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        height: 38px !important;
        font-size: 0.75rem !important;
        border-radius: 8px !important;
    }
    div[data-testid="stButton"] > button:hover {
        box-shadow: 0 0 14px rgba(0,82,204,0.6) !important;
        transform: scale(1.01);
    }
    .energy-card {
        background: rgba(10,10,20,0.4) !important;
        border-radius: 12px;
        padding: 6px 10px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(20px);
        margin-bottom: 6px;
    }
    .energy-card h3 { font-size: 0.9rem !important; margin: 4px 0 !important; }
    .el-border { border-top: 2px solid #FFD700 !important; }
    .fsx-border { border-top: 2px solid #0084ff !important; }
    .gas-border { border-top: 2px solid #FF5722 !important; }
    .water-border { border-top: 2px solid #00BFFF !important; }
    [data-testid="stFileUploadDropzone"],
    section[data-testid="stFileUploadDropzone"],
    section[data-testid="stFileUploadDropzone"] > div {
        background-color: rgba(0,200,100,0.08) !important;
        border: 2px dashed #00c864 !important;
        border-radius: 10px !important;
    }
    .cat-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 16px;
        text-align: center;
        position: relative;
        transition: all 0.3s;
        cursor: pointer;
        margin-bottom: 8px;
    }
    .cat-card.active {
        background: rgba(0,82,204,0.15);
        border-color: #0084ff;
        box-shadow: 0 0 20px rgba(0,132,255,0.3);
    }
    .cat-name { font-weight: bold; color: #fff; font-size: 0.9rem; margin-top: 6px; }
    .cat-desc { font-size: 0.7rem; color: rgba(255,255,255,0.4); margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 DocScan")
st.write("---")

# Session State
if 'vysledky' not in st.session_state: st.session_state.vysledky = []
if 'kategorie' not in st.session_state: st.session_state.kategorie = "Energie"
if 'datum_analyzy' not in st.session_state: st.session_state.datum_analyzy = None

# --- KATEGORIE ---
kategorie_list = [
    ("⚡", "Energie", "Spotřeba & náklady"),
    ("📄", "Faktury", "Dodavatel, částky, splatnost"),
    ("📋", "Smlouvy", "Strany, podmínky, datum"),
    ("📦", "Objednávky", "Položky, ceny, dodávky"),
]

cols_kat = st.columns(4)
for col, (icon, name, desc) in zip(cols_kat, kategorie_list):
    with col:
        active = "active" if st.session_state.kategorie == name else ""
        st.markdown(f"""
        <div class="cat-card {active}">
            <div style="font-size:1.8rem">{icon}</div>
            <div class="cat-name">{name}</div>
            <div class="cat-desc">{desc}</div>
        </div>""", unsafe_allow_html=True)
        if st.button(name, key=f"btn_{name}", use_container_width=True):
            st.session_state.kategorie = name
            st.rerun()

st.write("---")

# --- STATISTIKY ---
pocet_souboru = st.session_state.get('pocet_souboru', 0)
obdobi = st.session_state.vysledky[0].get('obdobi', '—') if st.session_state.vysledky else '—'
celkem_nakladu = 0

if st.session_state.vysledky:
    res = st.session_state.vysledky[0]
    for klic in ['el_cena_celkem_zaklad_kc', 'fsx_cena_bez_dph', 'plyn_cena_celkem_zaklad_kc', 'voda_cena_bez_dph']:
        try:
            val = res.get(klic, 0)
            if val and str(val).lower() != 'n/a':
                celkem_nakladu += float(str(val).replace(',', '.').replace(' ', ''))
        except: pass

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Nahráno souborů", str(pocet_souboru) if pocet_souboru > 0 else "—")
with c2: st.metric("Období", obdobi)
with c3: st.metric("Ušetřeno času", "~10 min" if st.session_state.vysledky else "—")
with c4: st.metric("Celkem nákladů", f"{celkem_nakladu:,.0f} Kč".replace(",", " ") if celkem_nakladu > 0 else "—")

st.write("---")

col_side, col_main = st.columns([1, 3])

# --- SEKCE ENERGIE ---
if st.session_state.kategorie == "Energie":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        obdobi_input = st.text_input("Období (RRRR-MM)", value=st.session_state.get('obdobi_input', '2026-01'))
        st.session_state.obdobi_input = obdobi_input

        uploaded_files = st.file_uploader("Vložte dokumenty", accept_multiple_files=True, type=['pdf', 'docx', 'xlsx', 'xls'])
        
        st.write("")
        _, mid_btn, _ = st.columns([1, 5, 1])
        with mid_btn:
            analyze_btn = st.button("🚀 SPUSTIT ANALÝZU")

        if st.session_state.vysledky:
            if st.button("🗑 Nová analýza", use_container_width=True):
                st.session_state.vysledky = []
                st.session_state.pocet_souboru = 0
                st.rerun()

    with col_main:
        if analyze_btn and uploaded_files:
            st.session_state.vysledky = []
            st.session_state.pocet_souboru = len(uploaded_files)
            st.session_state.datum_analyzy = datetime.now().strftime('%d.%m.%Y %H:%M')
            
            with st.spinner("Analyzuji faktury přes n8n..."):
                try:
                    webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"
                    def get_mime(n):
                        if n.endswith('.pdf'): return "application/pdf"
                        if n.endswith('.xlsx'): return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        return "application/octet-stream"
                    
                    files = [("data", (f.name, f.getvalue(), get_mime(f.name))) for f in uploaded_files]
                    payload = {"p": st.session_state.obdobi_input}
                    response = requests.post(webhook_url, files=files, data=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.vysledky = data if isinstance(data, list) else [data]
                    else:
                        st.error(f"Chyba n8n: {response.status_code}")
                except Exception as e:
                    st.error(f"Spojení selhalo: {e}")
            st.rerun()

        st.subheader("📁 Digitální archiv")
        if st.session_state.vysledky:
            # Tlačítka pod archivem
            c_arch1, c_arch2 = st.columns([2, 1])
            with c_arch2:
                # TLAČÍTKO PRO GOOGLE SHEETS
                if st.button("✅ ODESLAT DO GOOGLE DASHBOARDU", use_container_width=True):
                    with st.spinner("Zapisuji do Google Sheets..."):
                        if odeslat_do_google_sheets(st.session_state.vysledky[0], "CZLC4"):
                            st.success("Data zapsána!")
                            st.balloons()
                        else:
                            st.error("Zápis se nezdařil.")

            st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)
            
            st.write("---")
            st.subheader("📊 Finální přehled")
            cols = st.columns(4)
            kats = [
                ("⚡ Elektřina", "el_", "el-border", cols[0]),
                ("🏢 FSX", "fsx_", "fsx-border", cols[1]),
                ("🔥 Plyn", "plyn_", "gas-border", cols[2]),
                ("💧 Voda", "voda_", "water-border", cols[3])
            ]

            for label, key, style, col in kats:
                with col:
                    st.markdown(f'<div class="energy-card {style}"><h3>{label}</h3></div>', unsafe_allow_html=True)
                    for res in st.session_state.vysledky:
                        data_souboru = {k: v for k, v in res.items() if k.startswith(key) and v and str(v).lower() != "n/a"}
                        if data_souboru:
                            for klic, hodnota in data_souboru.items():
                                parametr = klic.replace(key, "").replace("_", " ").upper()
                                st.markdown(f"""
                                <div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,0.1);padding:4px 0;">
                                    <span style="color:#888;font-size:0.75rem;">{parametr}</span>
                                    <span style="color:#fff;font-weight:bold;font-size:0.85rem;">{hodnota}</span>
                                </div>""", unsafe_allow_html=True)
        else:
            st.info("Nahrajte faktury a spusťte analýzu.")

# --- OSTATNÍ SEKCE (UKÁZKY) ---
elif st.session_state.kategorie == "Faktury":
    st.subheader("📄 Faktury — ukázka")
    st.info("Tato sekce bude napojena na Anthropic API pro obecné faktury.")

elif st.session_state.kategorie == "Smlouvy":
    st.subheader("📋 Smlouvy — ukázka")
    st.info("Analýza právních dokumentů a termínů.")

elif st.session_state.kategorie == "Objednávky":
    st.subheader("📦 Objednávky — ukázka")
    st.info("Sledování položek a dodacích lhůt.")
