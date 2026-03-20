import streamlit as st
import pandas as pd
import requests
import io

st.set_page_config(page_title="DocScan", layout="wide", page_icon="🔍")

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
    background: #f0f4ff !important;
    color: #1a1a2e;
}

#MainMenu, footer, header { visibility: hidden; }

.app-header {
    display: flex;
    align-items: center;
    padding: 1rem 0 2rem 0;
    border-bottom: 1px solid rgba(0,0,0,0.08);
    margin-bottom: 2rem;
}
.app-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #1a1a2e;
}
.app-title span { color: #0052cc; }

.category-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 2rem;
}
.cat-card {
    background: #fff;
    border: 2px solid transparent;
    border-radius: 16px;
    padding: 22px 16px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    transition: all 0.3s;
}
.cat-card.active {
    background: #fff;
    border-color: #0052cc;
    box-shadow: 0 4px 20px rgba(0, 82, 204, 0.15);
}
.cat-card.coming-soon { opacity: 0.5; }
.cat-icon { font-size: 2rem; margin-bottom: 10px; }
.cat-name {
    font-family: 'Syne', sans-serif;
    font-size: 0.9rem;
    font-weight: 700;
    color: #1a1a2e;
}
.cat-desc { font-size: 0.72rem; color: #888; margin-top: 4px; }
.soon-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    background: #f3f4f6;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.6rem;
    color: #999;
    letter-spacing: 1px;
    text-transform: uppercase;
}

div[data-testid="stMetric"] {
    background: #fff !important;
    border: 1px solid rgba(0,0,0,0.06) !important;
    border-radius: 14px !important;
    padding: 16px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    color: #0052cc !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    color: #999 !important;
}

.sidebar-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #00875a;
    margin-bottom: 12px;
}

[data-testid="stFileUploadDropzone"] {
    background: rgba(0, 82, 204, 0.03) !important;
    border: 2px dashed #0052cc !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploadDropzone"] p {
    color: #555 !important;
}
[data-testid="stFileUploadDropzone"] small {
    color: #888 !important;
}

div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #0052cc 0%, #0a84ff 100%) !important;
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
    box-shadow: 0 4px 15px rgba(0, 82, 204, 0.3) !important;
}
div[data-testid="stButton"] > button:hover {
    box-shadow: 0 6px 20px rgba(0, 82, 204, 0.45) !important;
    transform: translateY(-1px) !important;
}

[data-testid="stDataFrame"] {
    background: #fff !important;
    border: 1px solid rgba(0,0,0,0.06) !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
}

div[data-baseweb="select"] > div {
    background: #fff !important;
    border: 1px solid #c8d8f0 !important;
    border-radius: 10px !important;
}
span[data-baseweb="tag"] {
    background: #e6f0ff !important;
    border: 1px solid #4d94ff !important;
    color: #0052cc !important;
    border-radius: 6px !important;
}

.energy-card {
    background: #fff;
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 4px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
.energy-card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f3f4f6;
}
.energy-card-icon { font-size: 1.3rem; }
.energy-card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.9rem;
    font-weight: 700;
    color: #1a1a2e;
}
.energy-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid #f9fafb;
}
.energy-row:last-child { border-bottom: none; }
.energy-label { font-size: 0.7rem; color: #999; text-transform: uppercase; letter-spacing: 0.5px; }
.energy-value { font-family: 'Syne', sans-serif; font-size: 0.9rem; font-weight: 700; color: #1a1a2e; }

.el-accent { border-top: 3px solid #f59e0b; }
.fsx-accent { border-top: 3px solid #0052cc; }
.gas-accent { border-top: 3px solid #f97316; }
.water-accent { border-top: 3px solid #00875a; }

.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #999;
    margin-bottom: 10px;
    margin-top: 24px;
}

div[data-testid="stDownloadButton"] > button {
    background: #fff !important;
    border: 1px solid #c8d8f0 !important;
    color: #0052cc !important;
    font-size: 0.75rem !important;
    border-radius: 10px !important;
    height: 36px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
    box-shadow: none !important;
    width: auto !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <div class="app-title">🔍 Doc<span>Scan</span></div>
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
        st.markdown(f'<div style="font-size:0.75rem;color:#00875a;margin:8px 0;font-weight:500;">✓ {len(uploaded_files)} soubor(ů) připraveno</div>', unsafe_allow_html=True)
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
        <div style="background:#fff;border:2px dashed #c8d8f0;border-radius:20px;
            padding:60px;text-align:center;margin-top:20px;box-shadow:0 2px 12px rgba(0,0,0,0.04);">
            <div style="font-size:2.5rem;margin-bottom:16px;">📂</div>
            <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#999;">
                Nahrajte faktury a spusťte analýzu
            </div>
            <div style="font-size:0.8rem;color:#bbb;margin-top:8px;">Podporované formáty: PDF</div>
        </div>""", unsafe_allow_html=True)
