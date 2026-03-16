import streamlit as st
import pandas as pd
import requests

# ... (tady nechej svůj stávající CSS design nahoře) ...

# --- 2. KONFIGURACE SIDEBARU ---
col_side, col_main = st.columns([1, 3])

with col_side:
    st.subheader("⚙️ Konfigurace")
    uploaded_files = st.file_uploader("Nahrajte PDF faktury", accept_multiple_files=True, type=['pdf'])
    
    # PŘESNÝ SEZNAM PODLE TVÉHO ZADÁNÍ
    vyber = st.multiselect(
        "Data k vytažení:",
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
    analyze_btn = st.button("🚀 SPUSTIT AI ANALÝZU")

# --- 3. LOGIKA ANALÝZY A DISPLEJ ---
with col_main:
    if analyze_btn and uploaded_files:
        st.session_state.vysledky = []
        webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"

        for file in uploaded_files:
            with st.spinner(f"Analyzuji: {file.name}..."):
                try:
                    files = {"data": (file.name, file.getvalue(), "application/pdf")}
                    payload = {"p": str(vyber)} 
                    response = requests.post(webhook_url, files=files, data=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list): data = data[0]
                        st.session_state.vysledky.append(data)
                except Exception as e:
                    st.error(f"Chyba: {e}")
        st.rerun()

    # --- 4. FINÁLNÍ PŘEHLED (3 SLUPCE) ---
    if st.session_state.vysledky:
        st.write("---")
        st.subheader("📊 Finální přehled podle energií")

        elektro = []
        plyn = []
        voda = []

        for res in st.session_state.vysledky:
            for k, v in res.items():
                if v and str(v).lower() != "n/a" and k not in ["Soubor", "Faktura"]:
                    polozka = {"Parametr": k.split(":")[-1].strip(), "Hodnota": v}
                    
                    # Rozřazení do sloupců
                    if "ELEKTŘINA" in k.upper() or "FSX" in k.upper():
                        if polozka not in elektro: elektro.append(polozka)
                    elif "PLYN" in k.upper():
                        if polozka not in plyn: plyn.append(polozka)
                    elif "VODA" in k.upper():
                        if polozka not in voda: voda.append(polozka)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("#### ⚡ Elektřina & FSX")
            if elektro: st.table(pd.DataFrame(elektro))
            else: st.caption("Žádná data")
        with c2:
            st.markdown("#### 🔥 Plyn")
            if plyn: st.table(pd.DataFrame(plyn))
            else: st.caption("Žádná data")
        with c3:
            st.markdown("#### 💧 Voda")
            if voda: st.table(pd.DataFrame(voda))
            else: st.caption("Žádná data")
