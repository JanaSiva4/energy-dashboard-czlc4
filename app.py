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
    
    /* TVOJE MODRO-FIALOVÁ PLOCHA */
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
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.4) !important;
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

    /* --- KARTY PRO ELEKTŘINU, PLYN A VODU --- */
    .energy-card {
        background: rgba(10, 10, 20, 0.4) !important;
        border-radius: 18px;
        padding: 22px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        margin-bottom: 25px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5) !important;
    }

    .el-border { border-top: 4px solid #00f2ff !important; box-shadow: 0 -8px 20px rgba(0, 242, 255, 0.3) !important; }
    .gas-border { border-top: 4px solid #d500f9 !important; box-shadow: 0 -8px 20px rgba(213, 0, 249, 0.3) !important; }
    .water-border { border-top: 4px solid #0091ea !important; box-shadow: 0 -8px 20px rgba(0, 145, 234, 0.3) !important; }

    .label-text { font-size: 0.75rem; color: #aabfff; text-transform: uppercase; margin-top: 14px; font-weight: bold; letter-spacing: 0.5px; }
    .value-text { font-size: 1.15rem; color: #ffffff; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 4px; margin-bottom: 2px; }

    /* --- ZELENÁ POZADÍ (OPRAVENO, ABY TO NEBYLO ŠEDÉ) --- */
    
    /* 1. UPLOAD BOX ZELENÝ */
    [data-testid="stFileUploadDropzone"] {
        background-color: rgba(0, 255, 150, 0.15) !important; /* Průhledná neon zelená */
        border: 2px dashed #00ff96 !important;
    }

    /* 2. MULTISELECT POLE ZELENÉ */
    div[data-baseweb="select"] > div {
        background-color: rgba(0, 255, 150, 0.15) !important;
        border: 1px solid #00ff96 !important;
    }

    /* 3. DIGITÁLNÍ ARCHIV (TABULKA) ZELENÝ */
    [data-testid="stDataFrame"] {
        background-color: rgba(0, 255, 150, 0.1) !important;
        border: 1px solid #00ff96 !important;
        border-radius: 10px;
    }

    /* Štítky v multiselectu */
