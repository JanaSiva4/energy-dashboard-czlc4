import streamlit as st
import pandas as pd
import requests
import io
import re
import base64
import json
import qrcode
from datetime import datetime
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm

# --- KONFIGURACE GOOGLE SHEETS ---
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzfRP2cvMrwjbsCgQPzfbQsVABB68OYdpTPajGRT4hbhBbVWoGPJIJJTfMy6PbbhfTwCQ/exec"

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

        def find_val(data, *terms):
            for k, v in data.items():
                k_upper = str(k).upper()
                if any(t.upper() in k_upper for t in terms):
                    return v
            return 0.0

        data_row = [
            rok, mesic,
            to_f(find_val(res, 'SPOTREBA', 'KWH')),
            to_f(find_val(res, 'JEDNOTKOVA')),
            to_f(find_val(res, 'SIL')),
            to_f(find_val(res, 'DIST')),
            to_f(find_val(res, 'ZAKLAD KC', 'CELKEM')),
            to_f(res.get('fsx_spotreba_kwh', 0)),
            to_f(res.get('fsx_jednotkova_cena', 0)),
            to_f(res.get('fsx_cena_bez_dph', 0)),
            to_f(res.get('plyn_spotreba_kwh', 0)),
            to_f(res.get('plyn_jednotkova_cena_kc', 0)),
            to_f(res.get('plyn_cena_celkem_zaklad_kc', 0)),
            to_f(res.get('voda_spotreba_m3', 0)),
            to_f(res.get('voda_jednotkova_cena_kc', 0)),
            to_f(res.get('voda_cena_bez_dph', 0))
        ]

        payload = {"action": "append", "sheet": sklad, "row": data_row}
        requests.post(GOOGLE_SCRIPT_URL, json=payload)
        return True
    except Exception as e:
        st.error(f"Chyba: {e}")
        return False


def odeslat_mcdp_do_sheets(data: dict, sklad: str = "CZLC4") -> bool:
    def yn(val):
        return "ANO" if val else "NE"
    try:
        row = [
            f"MCDP-{sklad}-{datetime.now().strftime('%Y%m%d%H%M')}",
            data.get("datum_vydeje", datetime.now().strftime("%d.%m.%Y")),
            data.get("kvartal", ""),
            datetime.now().year,
            sklad,
            data.get("zamestnanec", ""),
            data.get("email", ""),
            yn(data.get("rucnik")),
            yn(data.get("mydlo")),
            yn(data.get("ariel")),
            yn(data.get("krem")),
            yn(data.get("rucnik") and data.get("mydlo") and data.get("ariel") and data.get("krem")),
            "NE",
            data.get("zadal", ""),
            datetime.now().strftime("%d.%m.%Y %H:%M"),
        ]
        payload = {"action": "append", "sheet": f"MCDP_{sklad}", "row": row}
        r = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Chyba odesílání MČDP: {e}")
        return False


def odeslat_oopp_do_sheets(data: dict, sklad: str = "CZLC4") -> bool:
    def stav_exp(exp_str):
        if not exp_str: return "—"
        try:
            p = exp_str.split("/")
            exp = datetime(int(p[1]), int(p[0]), 1)
            dnes = datetime.now()
            if exp < dnes: return "expirováno"
            if (exp - dnes).days <= 60: return "brzy expiruje"
            return "v pořádku"
        except: return "—"

    try:
        exp = data.get("expirace", "")
        row = [
            f"OOPP-{sklad}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            datetime.now().strftime("%d.%m.%Y"),
            sklad,
            data.get("zamestnanec", ""),
            data.get("email", ""),
            data.get("pomucka", ""),
            data.get("velikost", ""),
            exp,
            stav_exp(exp),
            "",
            "ANO" if data.get("podpis") else "NE",
            data.get("zadal", ""),
            datetime.now().strftime("%d.%m.%Y %H:%M"),
        ]
        payload = {"action": "append", "sheet": f"OOPP_{sklad}", "row": row}
        r = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Chyba odesílání OOPP: {e}")
        return False


def generovat_pdf_protokol(zamestnanec, sklad, kvartal, vydane_polozky, vedouci):
    navy   = colors.HexColor('#1a3a6b')
    lgray  = colors.HexColor('#EEF3FA')
    red_bg = colors.HexColor('#FFF3F3')
    dark_red = colors.HexColor('#7B1C1C')

    title_s  = ParagraphStyle('t', fontSize=15, fontName='Helvetica-Bold', textColor=colors.white, alignment=1)
    sub_s    = ParagraphStyle('s', fontSize=9,  fontName='Helvetica', textColor=colors.white, alignment=1)
    label_s  = ParagraphStyle('l', fontSize=9,  fontName='Helvetica-Bold', textColor=navy)
    body_s   = ParagraphStyle('b', fontSize=9,  fontName='Helvetica', textColor=colors.HexColor('#333333'))
    legal_s  = ParagraphStyle('leg', fontSize=7.5, fontName='Helvetica', textColor=colors.HexColor('#444444'), leading=10)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    el = []

    # Hlavička
    ht = Table([[Paragraph("PŘEDÁVACÍ PROTOKOL — MČDP", title_s)],
                [Paragraph(f"Mycí a čisticí prostředky · Sklad {sklad} Chrástany · Facility Management", sub_s)]],
               colWidths=[17*cm])
    ht.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),navy),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',(0,0),(-1,-1),12)]))
    el.append(ht); el.append(Spacer(1, 0.4*cm))

    # Info řádky
    it = Table([
        [Paragraph('Zaměstnanec:', label_s), Paragraph(f'<b>{zamestnanec}</b>', body_s),
         Paragraph('Kvartál / Rok:', label_s), Paragraph(f'<b>{kvartal}</b>', body_s)],
        [Paragraph('Sklad:', label_s), Paragraph(sklad, body_s),
         Paragraph('Datum výdeje:', label_s), Paragraph(datetime.now().strftime('%d.%m.%Y'), body_s)],
        [Paragraph('Vedoucí:', label_s), Paragraph(vedouci or '—', body_s),
         Paragraph('', label_s), Paragraph('', body_s)],
    ], colWidths=[3.5*cm, 5*cm, 3.5*cm, 5*cm])
    it.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),lgray),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#CCCCCC')),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),6)]))
    el.append(it); el.append(Spacer(1, 0.4*cm))

    # Tabulka položek
    ph = ParagraphStyle('ph', fontSize=9, fontName='Helvetica-Bold', textColor=colors.white)
    polozky_data = [[Paragraph('Položka',ph), Paragraph('Vydáno',ph),
                     Paragraph('Specifikace',ph), Paragraph('Převzal (podpis)',ph)],
        ['1× Ručník 50×100cm Siguro', '☑' if vydane_polozky.get('rucnik') else '☐', '50×100 cm, froté', ''],
        ['1× Tekuté mýdlo',           '☑' if vydane_polozky.get('mydlo')  else '☐', '500 ml', ''],
        ['1× Ariel tablety 60 ks',    '☑' if vydane_polozky.get('ariel')  else '☐', '60 ks / balení', ''],
        ['1× Krém Indulona original', '☑' if vydane_polozky.get('krem')   else '☐', 'nebo měsíčkový', ''],
    ]
    pt = Table(polozky_data, colWidths=[6.5*cm, 2*cm, 4.5*cm, 4*cm])
    pt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),navy),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, lgray]),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#CCCCCC')),
        ('FONTSIZE',(0,1),(-1,-1),9),('ALIGN',(1,0),(1,-1),'CENTER'),
        ('FONTSIZE',(1,1),(1,-1),14),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),8),
        ('LINEBELOW',(3,1),(3,-1),1,colors.HexColor('#333333')),
    ]))
    el.append(pt); el.append(Spacer(1, 0.5*cm))

    # Podpisy
    st_tbl = Table([
        [Paragraph('Podpis zaměstnance:', label_s), '',
         Paragraph('Podpis vedoucího / razítko:', label_s), ''],
        ['', '', '', ''], ['', '', '', ''],
    ], colWidths=[4*cm, 4.5*cm, 4*cm, 4.5*cm], rowHeights=[0.5*cm, 1*cm, 0.3*cm])
    st_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),lgray),
        ('LINEBELOW',(1,1),(1,1),1.5,colors.HexColor('#1a3a6b')),
        ('LINEBELOW',(3,1),(3,1),1.5,colors.HexColor('#1a3a6b')),
        ('LEFTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),4),
    ]))
    el.append(st_tbl); el.append(Spacer(1, 0.4*cm))

    # Právní text
    lht = Table([[Paragraph('Prohlášení zaměstnance — NV 390/2021 Sb.',
        ParagraphStyle('lh', fontSize=9, fontName='Helvetica-Bold', textColor=colors.white))]],
        colWidths=[17*cm])
    lht.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),dark_red),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),8)]))
    el.append(lht)

    legal_txt = (
        "Předání a převzetí výše uvedených OOPP a předmětů zaměstnanec i zaměstnavatel potvrzují svým podpisem. "
        "Dále byl zaměstnanec seznámen s způsobem údržby OOPP dle NV 390/2021 Sb. Zaměstnanec se zavazuje řádně "
        "hospodařit s OOPP a předměty svěřenými mu zaměstnavatelem na základě tohoto potvrzení a střežit a "
        "ochraňovat tyto OOPP a předměty zaměstnavatele před poškozením, ztrátou, zničením a zneužitím. "
        "Zaměstnanec se zavazuje svěřené OOPP a předměty používat pouze pro výkon práce pro zaměstnavatele nebo "
        "v jeho souvislosti. Zaměstnanec zároveň souhlasí s tím, že v případě ztráty, zničení nebo poškození "
        "znemožňujícího další používání OOPP a předmětů mu bude zaměstnavatelem svěřen na základě tohoto potvrzení "
        "mu bude uvedena cena ztracené nebo poškozeného předmětu a předmětů, je sražena ze mzdy v souladu "
        "s příslušnou Dohodou o srážkách ze mzdy uzavřenou mezi zaměstnancem a zaměstnavatelem."
    )
    lbt = Table([[Paragraph(legal_txt, legal_s)]], colWidths=[17*cm])
    lbt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),red_bg),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8)]))
    el.append(lbt)

    doc.build(el)
    buf.seek(0)
    return buf.getvalue()


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
    .oopp-border { border-top: 2px solid #00c864 !important; }
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
    ("⚡", "Energie",     "Spotřeba & náklady"),
    ("📄", "Faktury",     "Dodavatel, částky, splatnost"),
    ("📋", "Smlouvy",     "Strany, podmínky, datum"),
    ("🦺", "OOPP & MČDP","Evidence & výdej pomůcek"),
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
                st.rerun()

    with col_main:
        if analyze_btn and uploaded_files:
            st.session_state.vysledky = []
            st.session_state.pocet_souboru = len(uploaded_files)
            st.session_state.datum_analyzy = datetime.now().strftime('%d.%m.%Y %H:%M')
            webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"
            with st.spinner(f"Analyzuji {len(uploaded_files)} faktur..."):
                try:
                    def get_mime(name):
                        if name.endswith('.pdf'): return "application/pdf"
                        if name.endswith('.docx'): return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        if name.endswith('.xlsx'): return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        if name.endswith('.xls'): return "application/vnd.ms-excel"
                        return "application/octet-stream"
                    files = [("data", (f.name, f.getvalue(), get_mime(f.name))) for f in uploaded_files]
                    payload = {"p": st.session_state.get("obdobi_input", datetime.now().strftime('%Y-%m'))}
                    response = requests.post(webhook_url, files=files, data=payload)
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.vysledky = data if isinstance(data, list) else [data]
                    else:
                        st.error(f"Chyba: {response.status_code}")
                except Exception as e:
                    st.error(f"Chyba spojení: {e}")
            st.rerun()

        st.subheader("📁 Digitální archiv")
        if st.session_state.vysledky:
            res = st.session_state.vysledky[0]
            if st.button("✅ ODESLAT DO TABULKY", use_container_width=False):
                if odeslat_do_google_sheets(res, sklad if 'sklad' in dir() else "CZLC4"):
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
                doc = SimpleDocTemplate(pdf_buffer, pagesize=A4,
                    rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
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
                    file_name=f"DocScan_{periode}.pdf",
                    mime="application/pdf")
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
                    for res in st.session_state.vysledky:
                        data_souboru = {k: v for k, v in res.items() if k.startswith(key) and v and str(v).lower() != "n/a"}
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
            res = st.session_state.vysledky[0]
            text_export = f"DocScan — Výsledky analýzy\nObdobí: {res.get('obdobi','—')}\n\n"
            text_export += f"ELEKTŘINA\n  Spotřeba: {res.get('el_spotreba_kwh','n/a')} kWh\n  Cena celkem: {res.get('el_cena_celkem_zaklad_kc','n/a')} Kč\n\n"
            text_export += f"FSX\n  Spotřeba: {res.get('fsx_spotreba_kwh','n/a')} kWh\n  Cena: {res.get('fsx_cena_bez_dph','n/a')} Kč\n\n"
            text_export += f"PLYN\n  Spotřeba: {res.get('plyn_spotreba_kwh','n/a')} kWh\n  Cena celkem: {res.get('plyn_cena_celkem_zaklad_kc','n/a')} Kč\n\n"
            text_export += f"VODA\n  Spotřeba: {res.get('voda_spotreba_m3','n/a')} m³\n  Cena: {res.get('voda_cena_bez_dph','n/a')} Kč"
            st.download_button("📋 Stáhnout jako TXT", data=text_export.encode('utf-8'),
                file_name=f"DocScan_{res.get('obdobi','export')}.txt",
                mime="text/plain")
        else:
            st.info("Nahrajte faktury a spusťte analýzu.")

# ── FAKTURY ───────────────────────────────────────────────────────
elif st.session_state.kategorie == "Faktury":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        st.file_uploader("Vložte dokumenty", accept_multiple_files=True, type=['pdf', 'docx', 'xlsx', 'xls'])
        st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.75rem;margin-top:10px;">🔒 Dostupné po aktivaci API</p>', unsafe_allow_html=True)
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
            for pole, val in [("Datum splatnosti","15.02.2026"),("Celkem bez DPH","10 000 Kč"),("DPH 21%","2 100 Kč"),("Celkem s DPH","12 100 Kč"),("Číslo účtu","123456789/0800"),("Variabilní symbol","20260001")]:
                st.markdown(f'<div class="preview-row"><span class="preview-label">{pole}</span><span class="preview-value">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.info("⏳ Funkce bude aktivní po připojení Anthropic API.")

# ── SMLOUVY ───────────────────────────────────────────────────────
elif st.session_state.kategorie == "Smlouvy":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        st.file_uploader("Vložte dokumenty", accept_multiple_files=True, type=['pdf', 'docx', 'xlsx', 'xls'])
        st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.75rem;margin-top:10px;">🔒 Dostupné po aktivaci API</p>', unsafe_allow_html=True)
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
        st.info("⏳ Funkce bude aktivní po připojení Anthropic API.")

# ── OOPP & MČDP ───────────────────────────────────────────────────
elif st.session_state.kategorie == "OOPP & MČDP":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        sklad_oopp = st.selectbox("Sklad:", ["CZLC4", "LCÚ", "LCZ", "SKLC3"], key="sklad_oopp")
        rezim = st.radio("Režim:", ["Výdej MČDP", "Evidence OOPP", "Tisk protokolu"])

    with col_main:

        # ── Výdej MČDP ──
        if rezim == "Výdej MČDP":
            # ← změň na svoji GitHub Pages URL po zapnutí Pages
            PODPIS_URL = "https://sivacenkojana.github.io/docscan/podpis_2fa.html"

            st.subheader("🧴 Výdej MČDP — kvartální")
            zamestnanec = st.text_input("Zaměstnanec (jméno a příjmení)")
            email_zam   = st.text_input("Email zaměstnance", placeholder="jan.novak@firma.cz")
            stredisko   = st.text_input("Středisko", placeholder="např. Sklad A — příjem")
            user        = st.text_input("Uživatel / osobní číslo", placeholder="např. 12345")
            kvartal_sel = st.selectbox("Kvartál", ["Q1 / 2025", "Q2 / 2025", "Q3 / 2025", "Q4 / 2025",
                                                    "Q1 / 2026", "Q2 / 2026", "Q3 / 2026", "Q4 / 2026"])
            st.write("**Vydávané položky:**")
            c1, c2 = st.columns(2)
            rucnik = c1.checkbox("1× Ručník Siguro 50×100cm", value=True)
            mydlo  = c2.checkbox("1× Tekuté mýdlo", value=True)
            ariel  = c1.checkbox("1× Ariel tablety 60 ks", value=True)
            krem   = c2.checkbox("1× Krém Indulona", value=True)
            vedouci = st.text_input("Zadal / vedoucí")

            # QR kód pro 2FA podpis
            if zamestnanec and email_zam:
                polozky_list = []
                if rucnik: polozky_list.append("Ručník Siguro")
                if mydlo:  polozky_list.append("Tekuté mýdlo")
                if ariel:  polozky_list.append("Ariel 60 ks")
                if krem:   polozky_list.append("Krém Indulona")

                qr_data = {
                    "jmeno": zamestnanec, "email": email_zam,
                    "stredisko": stredisko, "user": user,
                    "sklad": sklad_oopp, "kvartal": kvartal_sel,
                    "polozky": ", ".join(polozky_list),
                }
                qr_json = json.dumps(qr_data, ensure_ascii=False)
                qr_payload = base64.b64encode(qr_json.encode('utf-8')).decode('ascii')
                qr_url = f"{PODPIS_URL}?d={qr_payload}"

                qr = qrcode.QRCode(version=1, box_size=6, border=2)
                qr.add_data(qr_url)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="#1a3a6b", back_color="white")
                buf_qr = io.BytesIO()
                qr_img.save(buf_qr, format="PNG")

                st.write("---")
                col_qr, col_info = st.columns([1, 2])
                with col_qr:
                    st.image(buf_qr.getvalue(), width=180, caption="Zaměstnanec naskenuje pro podpis")
                with col_info:
                    st.markdown(f'''
                    <div class="energy-card oopp-border" style="padding:12px;">
                      <p style="color:#00c864;font-size:0.75rem;font-weight:bold;
                                text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                        Čeká na 2FA podpis
                      </p>
                      <p style="color:#fff;font-size:0.9rem;"><b>{zamestnanec}</b></p>
                      <p style="color:#aaa;font-size:0.8rem;">{email_zam}</p>
                      <p style="color:#aaa;font-size:0.8rem;margin-top:4px;">
                        {kvartal_sel} · {sklad_oopp}
                      </p>
                      <p style="color:#aaa;font-size:0.75rem;margin-top:4px;">
                        {", ".join(polozky_list)}
                      </p>
                    </div>
                    ''', unsafe_allow_html=True)
                st.write("---")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ ODESLAT DO GOOGLE SHEETS", use_container_width=True):
                    if not zamestnanec:
                        st.warning("Zadej jméno zaměstnance.")
                    else:
                        data = {
                            "zamestnanec": zamestnanec, "email": email_zam,
                            "kvartal": kvartal_sel, "rucnik": rucnik,
                            "mydlo": mydlo, "ariel": ariel, "krem": krem,
                            "podpis": True, "zadal": vedouci,
                        }
                        if odeslat_mcdp_do_sheets(data, sklad_oopp):
                            st.balloons()
                            st.success(f"✅ Záznam uložen — {zamestnanec} · {kvartal_sel}")

            with col_btn2:
                if zamestnanec:
                    pdf_bytes = generovat_pdf_protokol(
                        zamestnanec=zamestnanec, sklad=sklad_oopp,
                        kvartal=kvartal_sel,
                        vydane_polozky={"rucnik": rucnik, "mydlo": mydlo, "ariel": ariel, "krem": krem},
                        vedouci=vedouci
                    )
                    jmeno_souboru = zamestnanec.replace(" ", "_")
                    st.download_button("📄 Stáhnout PDF protokol",
                        data=pdf_bytes,
                        file_name=f"Protokol_MCDP_{jmeno_souboru}_{kvartal_sel[:2]}.pdf",
                        mime="application/pdf",
                        use_container_width=True)

        # ── Evidence OOPP ──
        elif rezim == "Evidence OOPP":
            st.subheader("🦺 Evidence OOPP")
            zamestnanec2 = st.text_input("Zaměstnanec")
            email_zam2   = st.text_input("Email zaměstnance", placeholder="jan.novak@firma.cz", key="email2")
            pomucka = st.selectbox("Pomůcka / OOPP", [
                "Rukavice pracovní", "Ochranné brýle", "Helma / přilba",
                "Reflexní vesta", "Bezpečnostní obuv", "Jiné"
            ])
            c1, c2, c3 = st.columns(3)
            velikost = c1.text_input("Velikost / č.")
            expirace = c2.text_input("Expirace (MM/RRRR)", placeholder="12/2026")
            podpis2  = c3.checkbox("Podpis ✓", value=True)
            vedouci2 = st.text_input("Zadal", key="vedouci2")

            if st.button("✅ ULOŽIT DO EVIDENCE", use_container_width=False):
                if not zamestnanec2:
                    st.warning("Zadej jméno zaměstnance.")
                else:
                    data2 = {
                        "zamestnanec": zamestnanec2, "email": email_zam2,
                        "pomucka": pomucka, "velikost": velikost,
                        "expirace": expirace, "podpis": podpis2, "zadal": vedouci2,
                    }
                    if odeslat_oopp_do_sheets(data2, sklad_oopp):
                        st.success(f"✅ Uloženo — {zamestnanec2} · {pomucka}")

        # ── Tisk protokolu ──
        elif rezim == "Tisk protokolu":
            st.subheader("🖨️ Generátor předávacího protokolu")
            st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:0.85rem;">Vyplň údaje — dostaneš PDF připravené k tisku a podpisu zaměstnance.</p>', unsafe_allow_html=True)

            zam_tisk = st.text_input("Zaměstnanec")
            kv_tisk  = st.selectbox("Kvartál", ["Q1 / 2025", "Q2 / 2025", "Q3 / 2025", "Q4 / 2025",
                                                  "Q1 / 2026", "Q2 / 2026", "Q3 / 2026", "Q4 / 2026"], key="kv_tisk")
            ved_tisk = st.text_input("Vedoucí", key="ved_tisk")
            st.write("**Položky pro protokol:**")
            t1, t2 = st.columns(2)
            cb1 = t1.checkbox("Ručník Siguro", value=True, key="p1")
            cb2 = t2.checkbox("Tekuté mýdlo",  value=True, key="p2")
            cb3 = t1.checkbox("Ariel 60 ks",   value=True, key="p3")
            cb4 = t2.checkbox("Krém Indulona",  value=True, key="p4")

            if zam_tisk:
                pdf_tisk = generovat_pdf_protokol(
                    zamestnanec=zam_tisk, sklad=sklad_oopp,
                    kvartal=kv_tisk,
                    vydane_polozky={"rucnik": cb1, "mydlo": cb2, "ariel": cb3, "krem": cb4},
                    vedouci=ved_tisk
                )
                st.download_button("📄 Stáhnout PDF protokol k tisku",
                    data=pdf_tisk,
                    file_name=f"Protokol_MCDP_{zam_tisk.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=False)
            else:
                st.info("Zadej jméno zaměstnance pro vygenerování protokolu.")
