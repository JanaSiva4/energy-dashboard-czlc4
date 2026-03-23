import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

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
        box-shadow: 0 0 12px #0052cc, 0 0 25px rgba(0,132,255,0.5) !important;
        transition: all 0.3s ease-in-out !important;
        font-weight: bold !important;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        height: 50px !important;
        border-radius: 8px !important;
    }
    div[data-testid="stButton"] > button:hover {
        box-shadow: 0 0 20px #0052cc, 0 0 40px #00c8ff !important;
        transform: scale(1.02);
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
        background: rgba(0,82,204,0.15);
        border-color: #0084ff;
        box-shadow: 0 0 20px rgba(0,132,255,0.3);
    }
    .cat-name { font-weight: bold; color: #fff; font-size: 0.9rem; margin-top: 6px; }
    .cat-desc { font-size: 0.7rem; color: rgba(255,255,255,0.4); margin-top: 4px; }
    .preview-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
    }
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
        background: rgba(0,82,204,0.15) !important;
        border: 1px solid rgba(0,132,255,0.4) !important;
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

if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []
if 'kategorie' not in st.session_state:
    st.session_state.kategorie = "Energie"
if 'datum_analyzy' not in st.session_state:
    st.session_state.datum_analyzy = None

# KATEGORIE — kliknutí přes st.columns s invisible buttons
kategorie_list = [
    ("⚡", "Energie", "Spotřeba & náklady"),
    ("📄", "Faktury", "Dodavatel, částky, splatnost"),
    ("📋", "Smlouvy", "Strany, podmínky, datum"),
    ("📦", "Objednávky", "Položky, ceny, dodávky"),
]

st.markdown("""
<style>
div[data-testid="stButton"].cat-btn > button {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: rgba(255,255,255,0.4) !important;
    box-shadow: none !important;
    height: 28px !important;
    font-size: 0.65rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    border-radius: 6px !important;
    margin-top: 4px !important;
    font-weight: normal !important;
}
div[data-testid="stButton"].cat-btn > button:hover {
    background: rgba(255,255,255,0.08) !important;
    color: rgba(255,255,255,0.8) !important;
    box-shadow: none !important;
    transform: none !important;
}
</style>""", unsafe_allow_html=True)

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

pocet = len(st.session_state.vysledky)
# Výpočet statistik
pocet_souboru = st.session_state.get('pocet_souboru', 0)
obdobi = st.session_state.vysledky[0].get('obdobi', '—') if st.session_state.vysledky else '—'

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
with c2: st.metric("Období", obdobi)
with c3: st.metric("Ušetřeno času", "~10 min" if st.session_state.vysledky else "—")
if st.session_state.get('datum_analyzy'):
    st.markdown(f'<p style="color:rgba(255,255,255,0.3);font-size:0.75rem;text-align:right;margin-top:-10px;">Poslední analýza: {st.session_state.datum_analyzy}</p>', unsafe_allow_html=True)
with c4: st.metric("Celkem nákladů", f"{celkem_nakladu:,.0f} Kč".replace(",", " ") if celkem_nakladu > 0 else "—")

st.write("---")

col_side, col_main = st.columns([1, 3])

# ── ENERGIE ───────────────────────────────────────────────────────
if st.session_state.kategorie == "Energie":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        
        obdobi_input = st.text_input("Období (např. 2026-01)", value=st.session_state.get('obdobi_input', '2026-01'), help="Zadejte ve formátu RRRR-MM, např. 2026-01 pro leden 2026")
        st.session_state.obdobi_input = obdobi_input
        
        uploaded_files = st.file_uploader("Vložte dokumenty", accept_multiple_files=True, type=['pdf', 'docx', 'xlsx', 'xls'], help="Nahrajte všechny faktury najednou — PDF, Word nebo Excel. AI vytáhne data ze všech souborů.")
        if uploaded_files:
            st.markdown(f'<p style="color:#00c864;font-size:0.8rem;">✓ {len(uploaded_files)} soubor(ů) připraveno</p>', unsafe_allow_html=True)
        vyber = st.multiselect("Pole k vytažení:", [
            "ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena sil. el.",
            "ELEKTŘINA: Cena distribuce", "ELEKTŘINA: Cena celkem",
            "FSX: Spotřeba (kWh)", "FSX: Cena celkem",
            "PLYN: Spotřeba (kWh)", "PLYN: Cena celkem",
            "VODA: Spotřeba (m3)", "VODA: Cena celkem"
        ], default=[
            "ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena sil. el.",
            "ELEKTŘINA: Cena distribuce", "ELEKTŘINA: Cena celkem",
            "FSX: Spotřeba (kWh)", "FSX: Cena celkem",
            "PLYN: Spotřeba (kWh)", "PLYN: Cena celkem",
            "VODA: Spotřeba (m3)", "VODA: Cena celkem"
        ])
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
                    payload = {"p": st.session_state.get("obdobi_input", "2026-01")}
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
            col_t, col_e, col_p = st.columns([2, 1, 1])
            with col_p:
                if st.button("🖨 Tisk", use_container_width=True):
                    st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
            with col_e:
                df_export = pd.DataFrame(st.session_state.vysledky)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Energie')
                    wb = writer.book
                    ws = writer.sheets['Energie']
                    # Hlavička - modrá
                    header_fill = PatternFill(start_color="0052CC", end_color="0052CC", fill_type="solid")
                    header_font = Font(color="FFFFFF", bold=True)
                    for col in range(1, len(df_export.columns) + 1):
                        cell = ws.cell(row=1, column=col)
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = Alignment(horizontal='center')
                        ws.column_dimensions[get_column_letter(col)].width = 25
                    # Střídající se barvy řádků
                    for row in range(2, len(df_export) + 2):
                        fill = PatternFill(start_color="EBF3FF", end_color="EBF3FF", fill_type="solid") if row % 2 == 0 else PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
                        for col in range(1, len(df_export.columns) + 1):
                            ws.cell(row=row, column=col).fill = fill
                periode = st.session_state.get('obdobi_input', 'export')
                st.download_button("⬇ Export Excel", data=buffer.getvalue(),
                    file_name=f"DocScan_{periode}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
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
                            st.markdown('<div style="margin-bottom:10px;padding:4px;">', unsafe_allow_html=True)
                            for klic, hodnota in data_souboru.items():
                                parametr = klic.replace(key, "").replace("_", " ").upper()
                                # Formátování čísel
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
            # Sdílení výsledků
            if st.session_state.vysledky:
                st.write("")
                res = st.session_state.vysledky[0]
                text_export = f"DocScan — Výsledky analýzy\nObdobí: {res.get('obdobi','—')}\n\n"
                text_export += f"ELEKTŘINA\n  Spotřeba: {res.get('el_spotreba_kwh','n/a')} kWh\n  Cena celkem: {res.get('el_cena_celkem_zaklad_kc','n/a')} Kč\n\n"
                text_export += f"FSX\n  Spotřeba: {res.get('fsx_spotreba_kwh','n/a')} kWh\n  Cena: {res.get('fsx_cena_bez_dph','n/a')} Kč\n\n"
                text_export += f"PLYN\n  Spotřeba: {res.get('plyn_spotreba_kwh','n/a')} kWh\n  Cena celkem: {res.get('plyn_cena_celkem_zaklad_kc','n/a')} Kč\n\n"
                text_export += f"VODA\n  Spotřeba: {res.get('voda_spotreba_m3','n/a')} m³\n  Cena: {res.get('voda_cena_bez_dph','n/a')} Kč"
                st.download_button("📋 Stáhnout jako TXT", data=text_export.encode('utf-8'),
                    file_name=f"DocScan_{res.get('obdobi','export')}.txt",
                    mime="text/plain", use_container_width=False)
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
        st.markdown('<p style="color:rgba(255,255,255,0.4);font-size:0.85rem;">Takto budou vypadat extrahovaná data:</p>', unsafe_allow_html=True)
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
        st.markdown('<p style="color:rgba(255,255,255,0.4);font-size:0.85rem;">Takto budou vypadat extrahovaná data:</p>', unsafe_allow_html=True)
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

# ── OBJEDNÁVKY ────────────────────────────────────────────────────
elif st.session_state.kategorie == "Objednávky":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        st.file_uploader("Vložte dokumenty", accept_multiple_files=True, type=['pdf', 'docx', 'xlsx', 'xls'])
        st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.75rem;margin-top:10px;">🔒 Dostupné po aktivaci API</p>', unsafe_allow_html=True)
    with col_main:
        st.subheader("📦 Objednávky — ukázka výstupu")
        st.markdown('<p style="color:rgba(255,255,255,0.4);font-size:0.85rem;">Takto budou vypadat extrahovaná data:</p>', unsafe_allow_html=True)
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
        st.info("⏳ Funkce bude aktivní po připojení Anthropic API.")
