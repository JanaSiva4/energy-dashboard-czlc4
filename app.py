import streamlit as st
import pandas as pd
import requests
import io

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

    [data-testid="stHeader"] {
        background: rgba(0,0,0,0) !important;
    }

    div[data-testid="stMetric"] {
        background: rgba(0, 0, 0, 0.25) !important;
        backdrop-filter: blur(15px);
        padding: 15px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.4) !important;
        height: 90px !important;
    }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    [data-testid="stMetricLabel"] p { font-size: 0.9rem !important; }

    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #0052cc 0%, #0a84ff 100%) !important;
        border: none !important;
        color: #ffffff !important;
        box-shadow: 0 0 12px #0052cc, 0 0 25px rgba(0, 132, 255, 0.5) !important;
        transition: all 0.3s ease-in-out !important;
        font-weight: bold !important;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        height: 50px !important;
        border-radius: 8px !important;
    }
    div[data-testid="stButton"] > button:hover {
        background: linear-gradient(135deg, #0a84ff 0%, #00c8ff 100%) !important;
        box-shadow: 0 0 20px #0052cc, 0 0 40px #00c8ff !important;
        transform: scale(1.02);
    }

    .energy-card {
        background: rgba(10, 10, 20, 0.4) !important;
        border-radius: 18px;
        padding: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        margin-bottom: 8px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5) !important;
    }
    .el-border { border-top: 1px solid #FFD700 !important; box-shadow: 0 -8px 20px rgba(255, 215, 0, 0.2) !important; }
    .fsx-border { border-top: 1px solid #0084ff !important; box-shadow: 0 -8px 20px rgba(0, 132, 255, 0.2) !important; }
    .gas-border { border-top: 1px solid #FF5722 !important; box-shadow: 0 -8px 20px rgba(255, 87, 34, 0.2) !important; }
    .water-border { border-top: 1px solid #00BFFF !important; box-shadow: 0 -8px 20px rgba(0, 191, 255, 0.2) !important; }

    [data-testid="stFileUploadDropzone"],
    section[data-testid="stFileUploadDropzone"],
    section[data-testid="stFileUploadDropzone"] > div,
    div[data-testid="stFileUploadDropzone"] > div {
        background-color: rgba(0, 200, 100, 0.08) !important;
        border: 2px dashed #00c864 !important;
        border-radius: 10px !important;
    }
    [data-testid="stFileUploader"] > div > div {
        background-color: rgba(0, 200, 100, 0.08) !important;
        border: 2px dashed #00c864 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] > div {
        background-color: rgba(0, 200, 100, 0.06) !important;
        border: 1px solid rgba(0, 200, 100, 0.3) !important;
    }
    span[data-baseweb="tag"] {
        background-color: rgba(0, 200, 100, 0.15) !important;
        border: 1px solid rgba(0, 200, 100, 0.4) !important;
        color: #00e87a !important;
    }

    [data-testid="stDataFrame"] {
        background-color: rgba(0, 82, 204, 0.05) !important;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid rgba(0, 132, 255, 0.3) !important;
    }

    .cat-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 20px 16px;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: all 0.3s;
    }
    .cat-card.active {
        background: rgba(0, 82, 204, 0.15);
        border-color: #0084ff;
        box-shadow: 0 0 20px rgba(0, 132, 255, 0.3);
    }
    .cat-card.coming-soon { opacity: 0.4; }
    .cat-name { font-weight: bold; color: #fff; font-size: 0.9rem; margin-top: 8px; }
    .cat-desc { font-size: 0.7rem; color: rgba(255,255,255,0.4); margin-top: 4px; }
    .soon-badge {
        position: absolute; top: 8px; right: 8px;
        background: rgba(255,255,255,0.1);
        border-radius: 6px; padding: 2px 6px;
        font-size: 0.6rem; color: rgba(255,255,255,0.4);
        letter-spacing: 1px; text-transform: uppercase;
    }

    div[data-testid="stDownloadButton"] > button {
        background: rgba(0, 82, 204, 0.15) !important;
        border: 1px solid rgba(0, 132, 255, 0.4) !important;
        color: #0084ff !important;
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

# KATEGORIE
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""<div class="cat-card active">
        <div style="font-size:2rem">⚡</div>
        <div class="cat-name">Energie</div>
        <div class="cat-desc">Spotřeba & náklady</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""<div class="cat-card coming-soon">
        <div class="soon-badge">Brzy</div>
        <div style="font-size:2rem">📄</div>
        <div class="cat-name">Faktury</div>
        <div class="cat-desc">Dodavatel, částky, splatnost</div>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""<div class="cat-card coming-soon">
        <div class="soon-badge">Brzy</div>
        <div style="font-size:2rem">📋</div>
        <div class="cat-name">Smlouvy</div>
        <div class="cat-desc">Strany, podmínky, datum</div>
    </div>""", unsafe_allow_html=True)
with col4:
    st.markdown("""<div class="cat-card coming-soon">
        <div class="soon-badge">Brzy</div>
        <div style="font-size:2rem">📦</div>
        <div class="cat-name">Objednávky</div>
        <div class="cat-desc">Položky, ceny, dodávky</div>
    </div>""", unsafe_allow_html=True)

st.write("---")

# STATISTIKY
pocet = len(st.session_state.vysledky)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno", str(pocet))
with c2: st.metric("Kategorie", "4")
with c3: st.metric("Úspora času", f"{pocet * 5} min")
with c4: st.metric("Stav", "Připraven" if pocet == 0 else "Online")

st.write("---")

col_side, col_main = st.columns([1, 3])

with col_side:
    st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Vložte PDF", accept_multiple_files=True, type=['pdf'])
    if uploaded_files:
        st.markdown(f'<p style="color:#00c864;font-size:0.8rem;">✓ {len(uploaded_files)} soubor(ů) připraveno</p>', unsafe_allow_html=True)
    
    vyber = st.multiselect(
        "Pole k vytažení:",
        [
            "ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena sil. el.",
            "ELEKTŘINA: Cena distribuce", "ELEKTŘINA: Cena celkem",
            "FSX: Spotřeba (kWh)", "FSX: Cena celkem",
            "PLYN: Spotřeba (kWh)", "PLYN: Cena celkem",
            "VODA: Spotřeba (m3)", "VODA: Cena celkem"
        ],
        default=[
            "ELEKTŘINA: Spotřeba (kWh)", "ELEKTŘINA: Cena sil. el.",
            "ELEKTŘINA: Cena distribuce", "ELEKTŘINA: Cena celkem",
            "FSX: Spotřeba (kWh)", "FSX: Cena celkem",
            "PLYN: Spotřeba (kWh)", "PLYN: Cena celkem",
            "VODA: Spotřeba (m3)", "VODA: Cena celkem"
        ]
    )
    
    st.write("")
    _, mid_btn, _ = st.columns([1.5, 4, 1.5])
    with mid_btn:
        analyze_btn = st.button("🚀 SPUSTIT ANALÝZU")

with col_main:
    if analyze_btn and uploaded_files:
        st.session_state.vysledky = []
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"
        with st.spinner(f"Analyzuji {len(uploaded_files)} faktur..."):
            try:
                files = [("data", (f.name, f.getvalue(), "application/pdf")) for f in uploaded_files]
                payload = {"p": "2026-01"}
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
        col_t, col_e = st.columns([3, 1])
        with col_e:
            df_export = pd.DataFrame(st.session_state.vysledky)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Energie')
            st.download_button("⬇ Export Excel", data=buffer.getvalue(),
                file_name="energie_czlc4.xlsx",
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
                        st.markdown('<div style="margin-bottom: 20px; padding: 5px;">', unsafe_allow_html=True)
                        for klic, hodnota in data_souboru.items():
                            parametr = klic.replace(key, "").replace("_", " ").upper()
                            st.markdown(f"""
                                <div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(255,255,255,0.1);padding:5px 0;">
                                    <span style="color:#888;font-size:0.8rem;text-transform:uppercase;">{parametr}</span>
                                    <span style="color:#fff;font-weight:bold;font-size:1rem;">{hodnota}</span>
                                </div>""", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Nahrajte faktury a spusťte analýzu.")
