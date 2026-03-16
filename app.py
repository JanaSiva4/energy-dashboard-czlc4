import streamlit as st  # TOTO MUSÍ BÝT PRVNÍ
import pandas as pd
import requests

# Konfigurace musí následovat hned po importu
st.set_page_config(page_title="CZLC4 Energy Intel Pro", layout="wide")

# --- DESIGN SE ZVÝRAZNĚNÝMI OKÉNKY (GLOW) ---
st.markdown("""
<style>
    /* Pozadí Modrá-Fialová */
    .stApp { 
        background: radial-gradient(circle at 10% 20%, rgb(0, 21, 41) 0%, rgb(60, 0, 120) 50%, rgb(0, 0, 0) 100%);
        color: #e0e0e0; 
    }

    /* Karty se zvýrazněním (Glow) */
    .energy-card {
        background: rgba(0, 0, 0, 0.4);
        border-radius: 12px;
        padding: 15px;
        backdrop-filter: blur(10px);
        margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.2s;
    }
    
    .energy-card:hover { transform: scale(1.02); }

    /* Barevné neonové okraje a stíny */
    .el-glow { border-left: 5px solid #FFD700; box-shadow: 0 0 20px rgba(255, 215, 0, 0.2); }
    .gas-glow { border-left: 5px solid #FF8C00; box-shadow: 0 0 20px rgba(255, 140, 0, 0.2); }
    .water-glow { border-left: 5px solid #00BFFF; box-shadow: 0 0 20px rgba(0, 191, 255, 0.2); }

    .label-text { font-size: 0.75rem; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
    .value-text { font-size: 1.2rem; color: #00ff88; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy Intelligence Pro")

# ... (zbytek kódu pro analýzu a třídění dat) ...

# Příklad vykreslení zvýrazněného oknénka dole:
# st.markdown('<div class="energy-card el-glow">...</div>', unsafe_allow_html=True)

# --- ZBYTEK KÓDU JE STEJNÝ ---
# (st.title, inicializace, statistiky, sidebar, logika webhooku, archiv, finální přehled)

st.title("⚡ Energy Intelligence Pro")
st.write("---")

# Inicializace stavu
if 'vysledky' not in st.session_state:
    st.session_state.vysledky = []

# --- 2. HORNÍ STATISTIKY ---
pocet = len(st.session_state.vysledky)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Zpracováno", str(pocet))
with c2: st.metric("Kategorie", "3")
with c3: st.metric("Úspora času", f"{pocet * 5} min")
with c4: st.metric("Stav", "Ready" if pocet == 0 else "Online")

st.write("---")

# --- 3. HLAVNÍ PLOCHA (SIDEBAR + ANALÝZA) ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.caption("Konfigurace")
    uploaded_files = st.file_uploader("Vložte PDF", accept_multiple_files=True, type=['pdf'])

    vyber = st.multiselect(
        "Pole k vytažení:",
        [
            "ELEKTŘINA: Spotřeba (kWh)", 
            "ELEKTŘINA: Cena sil. el. (fakturovaná)", 
            "ELEKTŘINA: Cena distribuce (fakturovaná)",
            "ELEKTŘINA: Cena celkem (fakturovaná)",
            "FSX: Spotřeba (kWh)",
            "FSX: Cena celkem (fakturovaná)",
            "PLYN: Spotřeba (kWh)",
            "PLYN: Cena celkem (fakturovaná)",
            "VODA: Spotřeba (m3)",
            "VODA: Cena celkem (fakturovaná)"
        ],
        default=["ELEKTŘINA: Spotřeba (kWh)", "PLYN: Spotřeba (kWh)", "VODA: Spotřeba (m3)"]
    )
    analyze_btn = st.button("🚀 SPUSTIT ANALÝZU")

with col_main:
    # --- LOGIKA WEBHOOKU ---
    if analyze_btn and uploaded_files:
        st.session_state.vysledky = []
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"

        for file in uploaded_files:
            with st.spinner(f"Analyzuji..."):
                try:
                    files = {"data": (file.name, file.getvalue(), "application/pdf")}
                    payload = {"p": str(vyber)} 
                    response = requests.post(webhook_url, files=files, data=payload)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list): data = data[0]
                        data["Soubor"] = file.name
                        st.session_state.vysledky.append(data)
                except:
                    st.error("Chyba spojení.")
        st.rerun()

    # --- 4. DIGITÁLNÍ ARCHIV ---
    st.subheader("📁 Digitální archiv")
    t1, t2 = st.tabs(["Energie", "Ostatní"])

    with t1:
        if st.session_state.vysledky:
            st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)
        else:
            st.info("Nahrajte faktury.")

    with t2:
        st.markdown('<div class="archive-card">Účtenka PHM</div>', unsafe_allow_html=True)

    # --- 5. FINÁLNÍ WOW PŘEHLED (3 SLOPCE) - MENŠÍ KARTY ---
    if st.session_state.vysledky:
        st.write("---")
        st.subheader("📊 Finální přehled")
        
        # Inicializace kategorií
        data_elektro, data_plyn, data_voda = [], [], []

        for res in st.session_state.vysledky:
            for klic, hodnota in res.items():
                if hodnota and str(hodnota).lower() != "n/a" and klic not in ["Soubor", "Faktura"]:
                    polozka = {"Parametr": klic.split(":")[-1].strip(), "Hodnota": hodnota}

                    if "ELEKTŘINA" in klic.upper() or "FSX" in klic.upper():
                        if polozka not in data_elektro: data_elektro.append(polozka)
                    elif "PLYN" in klic.upper():
                        if polozka not in data_plyn: data_plyn.append(polozka)
                    elif "VODA" in klic.upper():
                        if polozka not in data_voda: data_voda.append(polozka)

        # Vykreslení moderních sloupců s MENŠÍMI KARTAMI
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown('<div class="energy-card el-border"><h4>⚡ Elektřina</h4></div>', unsafe_allow_html=True)
            for item in data_elektro:
                st.markdown(f'<div class="label-text">{item["Parametr"]}</div><div class="value-text">{item["Hodnota"]}</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="energy-card gas-border"><h4>🔥 Plyn</h4></div>', unsafe_allow_html=True)
            for item in data_plyn:
                st.markdown(f'<div class="label-text">{item["Parametr"]}</div><div class="value-text">{item["Hodnota"]}</div>', unsafe_allow_html=True)

        with c3:
            st.markdown('<div class="energy-card water-border"><h4>💧 Voda</h4></div>', unsafe_allow_html=True)
            for item in data_voda:
                st.markdown(f'<div class="label-text">{item["Parametr"]}</div><div class="value-text">{item["Hodnota"]}</div>', unsafe_allow_html=True)
