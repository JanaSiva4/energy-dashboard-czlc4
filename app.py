import streamlit as st
import pandas as pd
import requests
import io
import re
import json
import base64
from datetime import datetime
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm

# --- KONFIGURACE ---
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx29FpdOIPj7eO9BJioDiuf_3RTNsA0xLJuHvBq8Dye9TL0gnBvFaBRftWxge6Flg9FTw/exec"
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

PROMPT = """Jsi expert na analýzu energetických faktur pro logistické centrum WEST I – Alza (CZLC4).

Z poskytnutých dokumentů vytáhni POUZE tyto hodnoty pro subjekt "WEST I - Alza":

1. "el_spotreba_kwh" - Spotřeba elektřiny vlastní [kWh] z přefakturace MD
2. "el_cena_sil_el_bez_dph" - Cena silové elektřiny bez DPH [Kč] z faktury Innogy
3. "el_cena_distribuce_bez_dph" - Cena distribuce bez DPH [Kč] z faktury Innogy  
4. "el_cena_celkem_zaklad_kc" - Elektřina celkem základ [Kč] z faktury Innogy
5. "fsx_spotreba_kwh" - Spotřeba FSX celkem [kWh] - sloupec "Spotřeba celkem (kWh)" NE "Spotřeba vlastní"
   → IGNORUJ řádky: Ecologistics, WEST II, Celkem
   → Pokud existuje Foodtruck, přičti jeho hodnotu
6. "fsx_cena_bez_dph" - Cena FSX bez DPH [Kč]
   → IGNORUJ řádky: Ecologistics, WEST II, Celkem
7. "plyn_spotreba_kwh" - Spotřeba plynu [kWh]
8. "plyn_cena_celkem_zaklad_kc" - Plyn celkem základ [Kč]
9. "voda_spotreba_m3" - Spotřeba vody vlastní [m3]
   → řádek "WEST I - Alza", sloupec "Spotřeba vlastní (m3)"
   → IGNORUJ: Ecologistics, WEST II, Celkem
10. "voda_cena_bez_dph" - Cena vody bez DPH [Kč]
    → STEJNÝ řádek jako spotřeba, sloupec "Cena bez DPH (CZK)"
    → IGNORUJ: Celkem, Ecologistics

PRAVIDLA:
- Pokud hodnotu nenajdeš, vrať "n/a"
- NIKDY nevymýšlej čísla
- Vrať POUZE JSON bez markdown, bez komentářů

Vrať přesně v tomto formátu:
{"obdobi":"RRRR-MM","el_spotreba_kwh":0,"el_cena_sil_el_bez_dph":0,"el_cena_distribuce_bez_dph":0,"el_cena_celkem_zaklad_kc":0,"fsx_spotreba_kwh":0,"fsx_cena_bez_dph":0,"plyn_spotreba_kwh":0,"plyn_cena_celkem_zaklad_kc":0,"voda_spotreba_m3":0,"voda_cena_bez_dph":0}"""

# --- GOOGLE SHEETS ---
def odeslat_do_google_sheets(res, sklad="CZLC4"):
    try:
        obdobi_raw = str(res.get('obdobi', datetime.now().strftime('%Y-%m')))
        rok, mesic = map(int, obdobi_raw.split('-'))

        def to_f(val):
            if not val or str(val).lower() == 'n/a': return 0.0
            try:
                s = str(val).replace('\xa0', '').replace(' ', '')
                s = re.sub(r'[^0-9,.]', '', s)
                if ',' in s and '.' in s: s = s.replace(',', '')
                s = s.replace(',', '.')
                return float(s)
            except:
                return 0.0

        data_row = [
            rok, mesic,
            to_f(res.get('el_spotreba_kwh', 0)),
            to_f(res.get('el_cena_sil_el_bez_dph', 0)) / to_f(res.get('el_spotreba_kwh', 1)) if to_f(res.get('el_spotreba_kwh', 0)) else 0,
            to_f(res.get('el_cena_sil_el_bez_dph', 0)),
            to_f(res.get('el_cena_distribuce_bez_dph', 0)),
            to_f(res.get('el_cena_celkem_zaklad_kc', 0)),
            to_f(res.get('fsx_spotreba_kwh', 0)),
            0,
            to_f(res.get('fsx_cena_bez_dph', 0)),
            to_f(res.get('plyn_spotreba_kwh', 0)),
            0,
            to_f(res.get('plyn_cena_celkem_zaklad_kc', 0)),
            to_f(res.get('voda_spotreba_m3', 0)),
            0,
            to_f(res.get('voda_cena_bez_dph', 0))
        ]

        payload = {"action": "append", "sheet": sklad, "row": data_row}
        requests.post(GOOGLE_SCRIPT_URL, json=payload)
        return True
    except Exception as e:
        st.error(f"Chyba Google Sheets: {e}")
        return False

# --- GEMINI ANALÝZA ---
def analyzuj_gemini(uploaded_files, obdobi):
    if not GEMINI_API_KEY:
        st.error("Chybí GEMINI_API_KEY v Streamlit Secrets!")
        return None

    parts = [{"text": PROMPT + f"\n\nObdobí: {obdobi}"}]

    for f in uploaded_files:
        data = f.getvalue()
        b64 = base64.b64encode(data).decode('utf-8')

        if f.name.endswith('.pdf'):
            mime = "application/pdf"
        elif f.name.endswith('.docx'):
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif f.name.endswith('.xlsx'):
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            mime = "application/octet-stream"

        parts.append({
            "inline_data": {
                "mime_type": mime,
                "data": b64
            }
        })

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 1000
        }
    }

    try:
        response = requests.post(GEMINI_URL, json=payload, timeout=120)
        if response.status_code == 200:
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            text = text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        else:
            st.error(f"Gemini chyba: {response.status_code} — {response.text[:200]}")
            return None
    except Exception as e:
        st.error(f"Chyba spojení: {e}")
        return None

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="DocScan", layout="wide", page_icon="🔍")

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
    div[data-baseweb="select"] > div {
        background-color: rgba(0,200,100,0.06) !important;
        border: 1px solid rgba(0,200,100,0.3) !important;
    }
    span[data-baseweb="tag"] {
        background-color: rgba(0,200,100,0.15) !important;
        border: 1px solid rgba(0,200,100,0.4) !important;
        color: #00e87a !important;
    }
    [data-testid="stDataFrame"] {
        background-color: rgba(0,82,204,0.05) !important;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid rgba(0,132,255,0.3) !important;
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
    .cat-card:hover {
        background: rgba(255,255,255,0.08);
        border-color: rgba(255,255,255,0.3);
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }
    .cat-card.active {
        background: rgba(0, 135, 90, 0.15);
        border-color: #00875a;
        box-shadow: 0 0 20px rgba(0, 135, 90, 0.3);
    }
    .cat-name { font-weight: bold; color: #fff; font-size: 0.9rem; margin-top: 6px; }
    .cat-desc { font-size: 0.7rem; color: rgba(255,255,255,0.4); margin-top: 4px; }
    .preview-row {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .preview-row:last-child { border-bottom: none; }
    .preview-label { font-size: 0.75rem; color: #888; text-transform: uppercase; }
    .preview-value { font-size: 0.85rem; color: #ccc; font-style: italic; }
    div[data-testid="stDownloadButton"] > button {
        background: rgba(0, 135, 90, 0.15) !important;
        border: 1px solid rgba(0, 135, 90, 0.4) !important;
        color: #00875a !important;
        font-size: 0.8rem !important;
        border-radius: 8px !important;
        height: 36px !important;
        box-shadow: none !important;
        width: auto !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
        font-weight: normal !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 DocScan")
st.write("---")

# --- SESSION STATE ---
if 'vysledky' not in st.session_state: st.session_state.vysledky = []
if 'kategorie' not in st.session_state: st.session_state.kategorie = "Energie"
if 'pocet_souboru' not in st.session_state: st.session_state.pocet_souboru = 0
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
obdobi_stat = st.session_state.vysledky[0].get('obdobi', '—') if st.session_state.vysledky else '—'
celkem_nakladu = 0
if st.session_state.vysledky:
    res = st.session_state.vysledky[0]
    for klic in ['el_cena_celkem_zaklad_kc', 'fsx_cena_bez_dph', 'plyn_cena_celkem_zaklad_kc', 'voda_cena_bez_dph']:
        try:
            hodnota = res.get(klic, 0)
            if hodnota and str(hodnota).lower() != 'n/a':
                celkem_nakladu += float(str(hodnota).replace(',', '.').replace(' ', ''))
        except:
            pass

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Nahráno souborů", str(pocet_souboru) if pocet_souboru > 0 else "—")
with c2: st.metric("Období", obdobi_stat)
with c3: st.metric("Ušetřeno času", "~10 min" if st.session_state.vysledky else "—")
with c4: st.metric("Celkem nákladů", f"{celkem_nakladu:,.0f} Kč".replace(",", " ") if celkem_nakladu > 0 else "—")

st.write("---")

col_side, col_main = st.columns([1, 3])

# ── ENERGIE ───────────────────────────────────────────────────────
if st.session_state.kategorie == "Energie":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        sklad = st.selectbox("Sklad:", ["CZLC4", "LCÚ", "LCZ", "SKLC3"])
        obdobi_input = st.text_input("Období (např. 2026-01)", value=st.session_state.get('obdobi_input', datetime.now().strftime('%Y-%m')), help="Zadejte ve formátu RRRR-MM")
        st.session_state.obdobi_input = obdobi_input
        uploaded_files = st.file_uploader("Vložte dokumenty", accept_multiple_files=True, type=['pdf', 'docx', 'xlsx', 'xls'], help="Nahrajte faktury — PDF, Word nebo Excel.")
        if uploaded_files:
            st.markdown(f'<p style="color:#00c864;font-size:0.8rem;">✓ {len(uploaded_files)} soubor(ů) připraveno</p>', unsafe_allow_html=True)
        st.write("")
        _, mid_btn, _ = st.columns([1.5, 4, 1.5])
        with mid_btn:
            analyze_btn = st.button("🚀 SPUSTIT ANALÝZU")
        if st.session_state.vysledky:
            if st.button("🗑 Nová analýza", use_container_width=True):
                st.session_state.vysledky = []
                st.session_state.pocet_souboru = 0
                st.markdown('<script>window.location.reload();</script>', unsafe_allow_html=True)
                st.rerun()

    with col_main:
        if analyze_btn and uploaded_files:
            st.session_state.vysledky = []
            st.session_state.pocet_souboru = len(uploaded_files)
            st.session_state.datum_analyzy = datetime.now().strftime('%d.%m.%Y %H:%M')
            with st.spinner(f"Gemini analyzuje {len(uploaded_files)} dokumentů..."):
                result = analyzuj_gemini(uploaded_files, st.session_state.get('obdobi_input', datetime.now().strftime('%Y-%m')))
                if result:
                    st.session_state.vysledky = [result]
                    st.success("✅ Analýza dokončena!")
            st.rerun()

        st.subheader("📁 Digitální archiv")
        if st.session_state.vysledky:
            res = st.session_state.vysledky[0]

            if st.button("✅ ODESLAT DO TABULKY"):
                if odeslat_do_google_sheets(res, sklad):
                    st.balloons()
                    st.success("Uloženo do Google Sheets!")

            col_t, col_btns = st.columns([2, 1])
            with col_btns:
                col_e2, col_p2 = st.columns(2)
            df_export = pd.DataFrame(st.session_state.vysledky)
            with col_e2:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Energie')
                    ws = writer.sheets['Energie']
                    header_fill = PatternFill(start_color="0052CC", end_color="0052CC", fill_type="solid")
                    header_font = Font(color="FFFFFF", bold=True)
                    for col in range(1, len(df_export.columns) + 1):
                        cell = ws.cell(row=1, column=col)
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = Alignment(horizontal='center')
                        ws.column_dimensions[get_column_letter(col)].width = 25
                    for row in range(2, len(df_export) + 2):
                        fill = PatternFill(start_color="EBF3FF", end_color="EBF3FF", fill_type="solid") if row % 2 == 0 else PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
                        for col in range(1, len(df_export.columns) + 1):
                            ws.cell(row=row, column=col).fill = fill
                periode = st.session_state.get('obdobi_input', 'export')
                st.download_button("⬇ Export Excel", data=buffer.getvalue(),
                    file_name=f"DocScan_{periode}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with col_p2:
                pdf_buffer = io.BytesIO()
                doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
                elements = []
                title_style = ParagraphStyle('title', fontSize=18, fontName='Helvetica-Bold', textColor=colors.HexColor('#0052cc'), spaceAfter=6)
                sub_style = ParagraphStyle('sub', fontSize=10, fontName='Helvetica', textColor=colors.HexColor('#666666'), spaceAfter=20)
                elements.append(Paragraph("DocScan — Přehled energií", title_style))
                elements.append(Paragraph(f"Období: {res.get('obdobi','—')}  |  Vygenerováno: {datetime.now().strftime('%d.%m.%Y %H:%M')}", sub_style))
                tisk_data = [['Kategorie', 'Parametr', 'Hodnota']]
                kats_pdf = [
                    ('Elektřina', 'el_spotreba_kwh', 'Spotřeba (kWh)'),
                    ('Elektřina', 'el_cena_sil_el_bez_dph', 'Cena sil. el. bez DPH'),
                    ('Elektřina', 'el_cena_distribuce_bez_dph', 'Cena distribuce bez DPH'),
                    ('Elektřina', 'el_cena_celkem_zaklad_kc', 'Cena celkem (Kč)'),
                    ('FSX', 'fsx_spotreba_kwh', 'Spotřeba (kWh)'),
                    ('FSX', 'fsx_cena_bez_dph', 'Cena bez DPH (Kč)'),
                    ('Plyn', 'plyn_spotreba_kwh', 'Spotřeba (kWh)'),
                    ('Plyn', 'plyn_cena_celkem_zaklad_kc', 'Cena celkem (Kč)'),
                    ('Voda', 'voda_spotreba_m3', 'Spotřeba (m³)'),
                    ('Voda', 'voda_cena_bez_dph', 'Cena bez DPH (Kč)'),
                ]
                for kat, klic, label in kats_pdf:
                    tisk_data.append([kat, label, str(res.get(klic, 'n/a'))])
                t = Table(tisk_data, colWidths=[4*cm, 8*cm, 5*cm])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0052cc')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
                    ('ALIGN', (2,0), (2,-1), 'RIGHT'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('LEFTPADDING', (0,0), (-1,-1), 8),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 0.5*cm))
                celkem_style = ParagraphStyle('celkem', fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#0052cc'))
                celkem_val = sum([float(str(res.get(k,0)).replace(',','.').replace(' ','')) for k in ['el_cena_celkem_zaklad_kc','fsx_cena_bez_dph','plyn_cena_celkem_zaklad_kc','voda_cena_bez_dph'] if res.get(k) and str(res.get(k)).lower() != 'n/a'] or [0])
                elements.append(Paragraph(f"Celkem nákladů: {celkem_val:,.2f} Kč".replace(',', ' '), celkem_style))
                doc.build(elements)
                pdf_buffer.seek(0)
                st.download_button("📄 Stáhnout PDF", data=pdf_buffer.getvalue(),
                    file_name=f"DocScan_{periode}.pdf", mime="application/pdf")

            st.dataframe(df_export, use_container_width=True)
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
                    for res_item in st.session_state.vysledky:
                        data_souboru = {k: v for k, v in res_item.items() if k.startswith(key) and v and str(v).lower() != "n/a"}
                        if data_souboru:
                            st.markdown('<div style="margin-bottom:10px;padding:4px;">', unsafe_allow_html=True)
                            for klic, hodnota in data_souboru.items():
                                parametr = klic.replace(key, "").replace("_", " ").upper()
                                try:
                                    num = float(str(hodnota).replace(',', '.').replace(' ', ''))
                                    if 'spotreba' in klic or 'm3' in klic:
                                        hodnota_fmt = f"{num:,.0f}".replace(',', ' ')
                                    else:
                                        hodnota_fmt = f"{num:,.2f} Kč".replace(',', ' ')
                                except:
                                    hodnota_fmt = str(hodnota)
                                st.markdown(f"""<div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,0.1);padding:4px 0;">
                                    <span style="color:#888;font-size:0.75rem;text-transform:uppercase;">{parametr}</span>
                                    <span style="color:#fff;font-weight:bold;font-size:0.85rem;">{hodnota_fmt}</span>
                                </div>""", unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)

            st.write("")
            text_export = f"DocScan — Výsledky analýzy\nObdobí: {res.get('obdobi','—')}\n\n"
            text_export += f"ELEKTŘINA\n  Spotřeba: {res.get('el_spotreba_kwh','n/a')} kWh\n  Cena celkem: {res.get('el_cena_celkem_zaklad_kc','n/a')} Kč\n\n"
            text_export += f"FSX\n  Spotřeba: {res.get('fsx_spotreba_kwh','n/a')} kWh\n  Cena: {res.get('fsx_cena_bez_dph','n/a')} Kč\n\n"
            text_export += f"PLYN\n  Spotřeba: {res.get('plyn_spotreba_kwh','n/a')} kWh\n  Cena celkem: {res.get('plyn_cena_celkem_zaklad_kc','n/a')} Kč\n\n"
            text_export += f"VODA\n  Spotřeba: {res.get('voda_spotreba_m3','n/a')} m³\n  Cena: {res.get('voda_cena_bez_dph','n/a')} Kč"
            st.download_button("📋 Stáhnout jako TXT", data=text_export.encode('utf-8'),
                file_name=f"DocScan_{res.get('obdobi','export')}.txt", mime="text/plain")
        else:
            st.info("Nahrajte faktury a spusťte analýzu.")

# ── FAKTURY ───────────────────────────────────────────────────────
elif st.session_state.kategorie == "Faktury":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        st.file_uploader("Vložte dokumenty", accept_multiple_files=True, type=['pdf', 'docx', 'xlsx', 'xls'])
        st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.75rem;margin-top:10px;">🔒 Dostupné po aktivaci</p>', unsafe_allow_html=True)
    with col_main:
        st.subheader("📄 Faktury — ukázka výstupu")
        cols_f = st.columns(2)
        with cols_f[0]:
            st.markdown('<div class="energy-card fsx-border"><h4 style="color:#0084ff;">🏢 Dodavatel</h4>', unsafe_allow_html=True)
            for pole, val in [("Dodavatel","ABC s.r.o."),("IČ","12345678"),("DIČ","CZ12345678"),("Číslo faktury","FAC-2026-001")]:
                st.markdown(f'<div class="preview-row"><span class="preview-label">{pole}</span><span class="preview-value">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with cols_f[1]:
            st.markdown('<div class="energy-card el-border"><h4 style="color:#FFD700;">💰 Platební údaje</h4>', unsafe_allow_html=True)
            for pole, val in [("Datum splatnosti","15.02.2026"),("Celkem bez DPH","10 000 Kč"),("DPH 21%","2 100 Kč"),("Celkem s DPH","12 100 Kč")]:
                st.markdown(f'<div class="preview-row"><span class="preview-label">{pole}</span><span class="preview-value">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.info("⏳ Funkce bude aktivní brzy.")

# ── SMLOUVY ───────────────────────────────────────────────────────
elif st.session_state.kategorie == "Smlouvy":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        st.file_uploader("Vložte dokumenty", accept_multiple_files=True, type=['pdf', 'docx', 'xlsx', 'xls'])
        st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.75rem;margin-top:10px;">🔒 Dostupné po aktivaci</p>', unsafe_allow_html=True)
    with col_main:
        st.subheader("📋 Smlouvy — ukázka výstupu")
        cols_s = st.columns(2)
        with cols_s[0]:
            st.markdown('<div class="energy-card gas-border"><h4 style="color:#FF5722;">📝 Smluvní strany</h4>', unsafe_allow_html=True)
            for pole, val in [("Objednatel","XYZ a.s."),("Zhotovitel","ABC s.r.o."),("Datum podpisu","01.01.2026"),("Platnost do","31.12.2026")]:
                st.markdown(f'<div class="preview-row"><span class="preview-label">{pole}</span><span class="preview-value">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with cols_s[1]:
            st.markdown('<div class="energy-card water-border"><h4 style="color:#00BFFF;">📌 Klíčové podmínky</h4>', unsafe_allow_html=True)
            for pole, val in [("Předmět","Dodávka služeb"),("Hodnota","120 000 Kč/rok"),("Výpovědní lhůta","3 měsíce"),("Obnova","Automatická")]:
                st.markdown(f'<div class="preview-row"><span class="preview-label">{pole}</span><span class="preview-value">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.info("⏳ Funkce bude aktivní brzy.")

# ── OBJEDNÁVKY ────────────────────────────────────────────────────
elif st.session_state.kategorie == "Objednávky":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        st.file_uploader("Vložte dokumenty", accept_multiple_files=True, type=['pdf', 'docx', 'xlsx', 'xls'])
        st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.75rem;margin-top:10px;">🔒 Dostupné po aktivaci</p>', unsafe_allow_html=True)
    with col_main:
        st.subheader("📦 Objednávky — ukázka výstupu")
        cols_o = st.columns(2)
        with cols_o[0]:
            st.markdown('<div class="energy-card el-border"><h4 style="color:#FFD700;">🛒 Základní údaje</h4>', unsafe_allow_html=True)
            for pole, val in [("Číslo objednávky","OBJ-2026-042"),("Dodavatel","ABC s.r.o."),("Datum","15.03.2026"),("Dodání","30.03.2026")]:
                st.markdown(f'<div class="preview-row"><span class="preview-label">{pole}</span><span class="preview-value">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with cols_o[1]:
            st.markdown('<div class="energy-card fsx-border"><h4 style="color:#0084ff;">💵 Položky & ceny</h4>', unsafe_allow_html=True)
            for pole, val in [("Položka","Kancelářský materiál"),("Množství","50 ks"),("Cena bez DPH","5 000 Kč"),("Cena s DPH","6 050 Kč")]:
                st.markdown(f'<div class="preview-row"><span class="preview-label">{pole}</span><span class="preview-value">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.info("⏳ Funkce bude aktivní brzy.")
