import streamlit as st
import pandas as pd
import requests
import io

st.set_page_config(page_title="DocScan", layout="wide", page_icon="⚡")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

* { font-family: 'DM Sans', sans-serif; }

[data-testid="stMainViewContainer"] .block-container {
    max-width: 1300px !important;
    margin: 0 auto !important;
    padding: 2rem 2rem !important;
}

.stApp {
    background: #080b14 !important;
    color: #e8e6f0;
}

#MainMenu, footer, header { visibility: hidden; }

.app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.5rem 0 2rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 2.5rem;
}
.app-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #fff 0%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.app-subtitle {
    font-size: 0.75rem;
    color: rgba(255,255,255,0.3);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 2px;
}

.category-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 2.5rem;
}
.cat-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 20px 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.cat-card.active {
    background: rgba(167, 139, 250, 0.1);
    border-color: rgba(167, 139, 250, 0.4);
}
.cat-card.coming-soon { opacity: 0.4; cursor: not-allowed; }
.cat-icon { font-size: 1.8rem; margin-bottom: 8px; }
.cat-name {
    font-family: 'Syne', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #fff;
}
.cat-desc { font-size: 0.7rem; color: rgba(255,255,255,0.35); margin-top: 4px; }
.soon-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(255,255,255,0.08);
    border-radius: 6px;
    padding: 2px 6px;
    font-size: 0.6rem;
    color: rgba(255,255,255,0.4);
    letter-spacing: 1px;
    text-transform: uppercase;
}

div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 14px !important;
    padding: 16px !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: #a78bfa !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    color: rgba(255,255,255,0.3) !important;
}

.sidebar-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.3);
    margin-bottom: 16px;
}

[data-testid="stFileUploadDropzone"] {
    background: rgba(167, 139, 250, 0.04) !important;
    border: 1.5px dashed rgba(167, 139, 250, 0.25) !important;
    border-radius: 12px !important;
}

div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #7c3aed 0%, #a78bfa 100%) !important;
    border: none !important;
    color: #fff !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    border-radius: 12px !important;
    height: 48px !important;
    width: 100% !important;
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.3) !important;
}

[data-testid="stDataFrame"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 14px !important;
}

div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
}
span[data-baseweb="tag"] {
    background: rgba(167, 139, 250, 0.15) !important;
    border: 1px solid rgba(167, 139, 250, 0.3) !important;
    color: #a78bfa !important;
    border-radius: 6px !important;
}

.energy-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 4px;
}
.energy-card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.energy-card-icon { font-size: 1.3rem; }
.energy-card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #fff;
}
.energy-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.energy-row:last-child { border-bottom: none; }
.energy-label { font-size: 0.7rem; color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 0.5px; }
.energy-value { font-family: 'Syne', sans-serif; font-size: 0.9rem; font-weight: 700; color: #fff; }

.el-accent { border-top: 2px solid #fbbf24; }
.fsx-accent { border-top: 2px solid #a78bfa; }
.gas-accent { border-top: 2px solid #f97316; }
.water-accent { border-top: 2px solid #38bdf8; }

.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.25);
    margin-bottom: 12px;
    margin-top: 28px;
}

div[data-testid="stDownloadButton"] > button {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: rgba(255,255,255,0.6) !important;
    font-size: 0.75rem !important;
    border-radius: 10px !important;
    height: 36px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    box-shadow: none !important;
    width: auto !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <div>
        <div class="app-title">DocScan</div>
        <div class="app-subtitle"></div>
    </div>
</div>
""", unsafe_allow_html=True)

if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

st.markdown("""
<div class="category-grid">
    <div class="cat-card active">
        <div class="cat-icon">⚡</div>
        <div class="cat-name">Energie</div>
        <div class="cat-desc">Spotřeba & náklady</div>
    </div>
    <div class="cat-card coming-soon">
        <div class="soon-badge">Brzy</div>
        <div class="cat-icon">📄</div>
        <div class="cat-name">Faktury</div>
        <div class="cat-desc">Dodavatel, částky, splatnost</div>
    </div>
    <div class="cat-card coming-soon">
        <div class="soon-badge">Brzy</div>
        <div class="cat-icon">📋</div>
        <div class="cat-name">Smlouvy</div>
        <div class="cat-desc">Strany, podmínky, datum</div>
    </div>
    <div class="cat-card coming-soon">
        <div class="soon-badge">Brzy</div>
        <div class="cat-icon">📦</div>
        <div class="cat-name">Objednávky</div>
        <div class="cat-desc">Položky, ceny, dodávky</div>
    </div>
</div>
""", unsafe_allow_html=True)

pocet = len(st.session_state.vysledky)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno", str(pocet))
with c2: st.metric("Kategorie", "4")
with c3: st.metric("Úspora času", f"{pocet * 5} min")
with c4: st.metric("Stav", "Připraven" if pocet == 0 else "Online")

st.write("")

col_side, col_main = st.columns([1, 3])

with col_side:
    st.markdown('<div class="sidebar-title">Konfigurace</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader("PDF faktury", accept_multiple_files=True, type=['pdf'], label_visibility="collapsed")
    if uploaded_files:
        st.markdown(f'<div style="font-size:0.75rem;color:rgba(255,255,255,0.4);margin:8px 0;">📎 {len(uploaded_files)} soubor(ů)</div>', unsafe_allow_html=True)
    st.write("")
    vyber = st.multiselect("Pole", [
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
    ], label_visibility="collapsed")
    st.write("")
    analyze_btn = st.button("🚀 Spustit analýzu")

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

    if st.session_state.vysledky:
        col_t, col_e = st.columns([3, 1])
        with col_t:
            st.markdown('<div class="section-title">📁 Digitální archiv</div>', unsafe_allow_html=True)
        with col_e:
            df_export = pd.DataFrame(st.session_state.vysledky)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Energie')
            st.download_button("⬇ Export Excel", data=buffer.getvalue(),
                file_name="energie_czlc4.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)

        st.markdown('<div class="section-title">📊 Finální přehled</div>', unsafe_allow_html=True)
        cols = st.columns(4)
        kats = [
            ("⚡", "Elektřina", "el_", "el-accent", cols[0]),
            ("🏢", "FSX", "fsx_", "fsx-accent", cols[1]),
            ("🔥", "Plyn", "plyn_", "gas-accent", cols[2]),
            ("💧", "Voda", "voda_", "water-accent", cols[3])
        ]
        for icon, label, key, accent, col in kats:
            with col:
                rows_html = ""
                for res in st.session_state.vysledky:
                    data_souboru = {k: v for k, v in res.items() if k.startswith(key) and v and str(v).lower() != "n/a"}
                    if data_souboru:
                        for klic, hodnota in data_souboru.items():
                            parametr = klic.replace(key, "").replace("_", " ").upper()
                            rows_html += f'<div class="energy-row"><span class="energy-label">{parametr}</span><span class="energy-value">{hodnota}</span></div>'
                if rows_html:
                    st.markdown(f"""
                    <div class="energy-card {accent}">
                        <div class="energy-card-header">
                            <span class="energy-card-icon">{icon}</span>
                            <span class="energy-card-title">{label}</span>
                        </div>
                        {rows_html}
                    </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.02);border:1px dashed rgba(255,255,255,0.08);
            border-radius:20px;padding:60px;text-align:center;margin-top:20px;">
            <div style="font-size:2.5rem;margin-bottom:16px;">📂</div>
            <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:rgba(255,255,255,0.4);">
                Nahrajte faktury a spusťte analýzu
            </div>
            <div style="font-size:0.8rem;color:rgba(255,255,255,0.2);margin-top:8px;">Podporované formáty: PDF</div>
        </div>""", unsafe_allow_html=True)
