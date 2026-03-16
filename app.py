import streamlit as st
import pandas as pd
import requests

# --- 1. CONFIG & WOW DESIGN (CSS) ---
st.set_page_config(page_title="Energy Intelligence Pro", layout="wide")

st.markdown("""
<style>
    /* ZAROVNÁNÍ OBSAHU */
    [data-testid="stMainViewContainer"] .block-container {
        max-width: 1200px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    
    /* SYTÁ A TMAVŠÍ MODRO-FIALOVÁ PLOCHA */
    .stApp {
        background: linear-gradient(135deg, #051c3d 0%, #2e0b54 40%, #1a0633 70%, #030821 100%) !important;
        background-attachment: fixed !important;
        color: #f0f0f0;
    }

    /* --- STATISTIKY (HORNÍ BOXY) --- */
    div[data-testid="stMetric"] {
        background: rgba(0, 0, 0, 0.25) !important;
        backdrop-filter: blur(15px);
        padding: 15px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.4) !important;
        height: 90px !important;
    }
    /* Zvětší to velké číslo (hodnotu) */
[data-testid="stMetricValue"] {
    font-size: 1.5rem !important; 
}

/* Zvětší ten malý nápis nad ním */
[data-testid="stMetricLabel"] p {
    font-size: 0.9rem !important;
}
    /* --- TLAČÍTKO (BLESKOVĚ BÍLÉ) --- */
    div[data-testid="stButton"] > button {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 2px solid #ffffff !important;
        color: #ffffff !important;
        box-shadow: 0 0 12px #ffffff, 0 0 25px rgba(0, 212, 255, 0.5) !important;
        transition: all 0.3s ease-in-out !important;
        font-weight: bold !important;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        height: 50px !important;
    }

    div[data-testid="stButton"] > button:hover {
        background-color: rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 0 20px #ffffff, 0 0 40px #00fbff !important;
        transform: scale(1.02);
    }

    /* --- KARTY PRO ELEKTŘINU, FSX, PLYN A VODU --- */
    .energy-card {
        background: rgba(10, 10, 20, 0.4) !important;
        border-radius: 18px;
        padding: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        margin-bottom: 8px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5) !important;
    }

    .el-border { 
        border-top: 1px solid #FFD700 !important; /* Žlutooranžová / Zlatá */
        box-shadow: 0 -8px 20px rgba(255, 215, 0, 0.2) !important; 
    }
    .fsx-border { 
        border-top: 1px solid #BB86FC !important; /* Světle fialová pro FSX */
        box-shadow: 0 -8px 20px rgba(187, 134, 252, 0.2) !important; 
    }
    .gas-border { 
        border-top: 1px solid #FF5722 !important; /* Sytě oranžová pro Plyn */
        box-shadow: 0 -8px 20px rgba(255, 87, 34, 0.2) !important; 
    }
    .water-border { 
        border-top: 1px solid #00BFFF !important; /* Světle modrá pro Vodu */
        box-shadow: 0 -8px 20px rgba(0, 191, 255, 0.2) !important; 
    }

    /* --- ÚPRAVY: MENŠÍ POLE A ZRUŠENÍ ZÁŘE --- */
    
    /* UPLOAD BOX (ZŮSTÁVÁ ZELENÝ) */
    [data-testid="stFileUploadDropzone"] {
        background-color: rgba(0, 255, 100, 0.1) !important;
        border: 2px dashed #00ff96 !important;
    }

    /* MULTISELECT POLE - TEĎ MENŠÍ A NESVÍTÍ */
    div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.05) !important; /* Zrušena zelená */
        border: 1px solid rgba(255, 255, 255, 0.2) !important; /* Decentní šedobílá */
        min-height: 30px !important; /* ZMENŠENÍ KOLONKY */
    }

    /* Štítky v multiselectu - MENŠÍ A NESVÍTÍ */
    span[data-baseweb="tag"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important; /* ZRUŠENA ZELENÁ ZÁŘE */
        color: white !important;
        height: 26px !important; /* MENŠÍ ŠTÍTKY */
        font-size: 0.9rem !important;
    }

    /* DIGITÁLNÍ ARCHIV (TABULKA) (POZADÍ ZELENÝ) */
    [data-testid="stDataFrame"] {
        background-color: rgba(0, 255, 100, 0.05) !important;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #00ff96 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy Intelligence Pro")
st.write("---")

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

# --- 3. HLAVNÍ PLOCHA ---
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
    
    st.write(" ") 
    _, mid_btn, _ = st.columns([1.5, 4, 0.5]) 
    with mid_btn:
        analyze_btn = st.button("🚀 SPUSTIT ANALÝZU")

with col_main:
    if analyze_btn and uploaded_files:
        st.session_state.vysledky = []
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"
        for file in uploaded_files:
            with st.spinner(f"Analyzuji {file.name}..."):
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

    st.subheader("📁 Digitální archiv")
    if st.session_state.vysledky:
        st.dataframe(pd.DataFrame(st.session_state.vysledky), use_container_width=True)
    else:
        st.info("Nahrajte faktury.")

# --- 5. FINÁLNÍ PŘEHLED (PŘEHLEDNÉ KOSTKY) ---
    if st.session_state.vysledky:
        st.write("---")
        st.subheader("📊 Finální přehled")
        
        # Vytvoření 4 sloupců
        c1, c2, c3, c4 = st.columns(4)
        
        # Definice kategorií pro přehlednější kód
        kategorie = [
            {"nadpis": "⚡ Elektřina", "klic": "ELEKTŘINA", "sloupec": c1, "styl": "el-border"},
            {"nadpis": "🏢 FSX", "klic": "FSX", "sloupec": c2, "styl": "fsx-border"},
            {"nadpis": "🔥 Plyn", "klic": "PLYN", "sloupec": c3, "styl": "gas-border"},
            {"nadpis": "💧 Voda", "klic": "VODA", "sloupec": c4, "styl": "water-border"}
        ]

        for kat in kategorie:
            with kat["sloupec"]:
                # Horní barevná karta s názvem energie
                st.markdown(f'<div class="energy-card {kat["styl"]}"><h3>{kat["nadpis"]}</h3></div>', unsafe_allow_html=True)
                
                # Procházíme výsledky a pro každý soubor vytvoříme samostatnou "kostku"
                for res in st.session_state.vysledky:
                    # Najdeme data, která patří do této kategorie v daném souboru
                    data_souboru = {k: v for k, v in res.items() if kat["klic"] in k.upper() and v and str(v).lower() != "n/a"}
                    
                    if data_souboru:
                        # Vizuální "kostka" pro data z jednoho souboru
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 12px; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                            <div style="font-size: 0.65rem; color: #888; text-transform: uppercase; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 4px;">📄 {res.get('Soubor', 'Neznámý soubor')}</div>
                        """, unsafe_allow_html=True)
                        
                        # Vypíšeme parametry uvnitř kostky
                        for klic, hodnota in data_souboru.items():
                            parametr = klic.split(":")[-1].strip()
                            st.markdown(f'<div class="label-text" style="margin-top:8px">{parametr}</div><div class="value-text" style="font-size:1.1rem">{hodnota}</div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
