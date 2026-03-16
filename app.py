import streamlit as st
import pandas as pd

# Nastavení stránky pro "Wide" zobrazení
st.set_page_config(page_title="Energy Intelligence Pro", layout="wide")

# --- TURBO DESIGN (CSS) ---
st.markdown("""
<style>
    /* Temné pozadí s gradientem */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(0, 21, 41) 0%, rgb(0, 10, 20) 90.2%);
        color: #e0e0e0;
    }

    /* Skleněné karty pro sekce */
    .energy-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Speciální okraje pro různé energie */
    .el-border { border-top: 4px solid #FFD700; } /* Zlatá/Žlutá */
    .gas-border { border-top: 4px solid #FF8C00; } /* Oranžová */
    .water-border { border-top: 4px solid #00BFFF; } /* Blankytná */

    /* Úprava nadpisů */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* Styl pro hodnoty (velká a čistá) */
    .value-text {
        font-size: 1.2rem;
        color: #ffffff;
        font-weight: 300;
    }
    .label-text {
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Skrytí Streamlit menu pro profi vzhled */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("⚡ Energy Intelligence Pro")
st.markdown("<p style='color: #888;'>Facility Management AI Analysis Platform</p>", unsafe_allow_html=True)
st.write("---")

# --- LOGIKA ROZDĚLENÍ (Předpokládáme data v session_state) ---
if 'vysledky' in st.session_state and st.session_state.vysledky:
    
    # Příprava dat (podobně jako předtím, ale s lepším designem)
    # ... (zde proběhne tvoje stávající filtrace do elektro, plyn, voda) ...

    col1, col2, col3 = st.columns(3)

    # Vykreslení "WOW" karet
    with col1:
        st.markdown("""
        <div class="energy-card el-border">
            <h3 style="color: #FFD700; margin-top:0;">⚡ ELEKTŘINA & FSX</h3>
        </div>
        """, unsafe_allow_html=True)
        # Tady místo st.table použijeme čistší výpis
        for item in elektro:
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <div class="label-text">{item['Parametr']}</div>
                <div class="value-text">{item['Hodnota']}</div>
                <hr style="margin: 5px 0; border: 0.1px solid rgba(255,255,255,0.05);">
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="energy-card gas-border">
            <h3 style="color: #FF8C00; margin-top:0;">🔥 PLYN</h3>
        </div>
        """, unsafe_allow_html=True)
        for item in plyn:
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <div class="label-text">{item['Parametr']}</div>
                <div class="value-text">{item['Hodnota']}</div>
                <hr style="margin: 5px 0; border: 0.1px solid rgba(255,255,255,0.05);">
            </div>
            """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="energy-card water-border">
            <h3 style="color: #00BFFF; margin-top:0;">💧 VODA</h3>
        </div>
        """, unsafe_allow_html=True)
        for item in voda:
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <div class="label-text">{item['Parametr']}</div>
                <div class="value-text">{item['Hodnota']}</div>
                <hr style="margin: 5px 0; border: 0.1px solid rgba(255,255,255,0.05);">
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Nahrajte dokumenty a spusťte analýzu pro zobrazení dashboardu.")
