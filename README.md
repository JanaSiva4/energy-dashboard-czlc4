# 🔍 DocScan
**AI extrakce dat z dokumentů | Verze 2.0 | Duben 2026**

[![Streamlit App](https://img.shields.io/badge/Streamlit-docscan--alza.streamlit.app-FF4B4B?logo=streamlit)](https://docscan-alza.streamlit.app)
[![GitHub](https://img.shields.io/badge/GitHub-JanaSiva4%2FDocScan-181717?logo=github)](https://github.com/JanaSiva4/DocScan)

---

## 📋 O projektu

DocScan je webová aplikace pro automatickou extrakci dat z PDF, Excel a Word dokumentů pomocí AI. Uživatel nahraje faktury a aplikace automaticky vytáhne klíčové hodnoty — bez ručního opisování.

Aktuálně funkční modul zpracovává faktury za energie pro objekt **WEST I – Alza (CZLC4)**. AI extrahuje 10 hodnot (elektřina, FSX, plyn, voda) z libovolného počtu faktur najednou.

---

## ✅ Funkce

### ⚡ Energie (funkční)
- Nahrání PDF, Excel nebo Word faktur najednou
- AI extrakce 10 hodnot: spotřeba a ceny elektřiny, FSX, plynu a vody
- Přehledný dashboard s kartami pro každou kategorii
- Export výsledků do Excel a PDF
- Uložení do Google Sheets — historie po měsících

### 🦺 OOPP & MČDP (funkční)
- Výdej MČDP — formulář + QR kód pro 2FA podpis zaměstnance
- Evidence OOPP — výdej pomůcek s automatickým výpočtem expirace
- Tisk protokolu — PDF dle NV 390/2021 Sb.
- Ukládání do Google Sheets (záložky MCDP_CZLC4, OOPP_CZLC4)
- Týdenní email alert pro expirované pomůcky

### 📈 Energie Dashboard (funkční)
- GitHub Pages — [janasiva4.github.io/energie-dashboard](https://janasiva4.github.io/energie-dashboard)
- Grafy spotřeby a nákladů po měsících
- SJL kalkulačka — koeficient 0,069 kWh/SJL (průměr 2025–2026)
- Alert OTE > 2 500 Kč/MWh
- Predikce nákladů 2027

### 📄 Faktury & 📋 Smlouvy (připraveno k aktivaci)

---

## 🛠 Technický stack

| Komponenta | Popis |
|-----------|-------|
| Hosting | Streamlit Community Cloud |
| Frontend | Python + Streamlit |
| Verzování | GitHub (JanaSiva4/DocScan) |
| AI model | Google Gemini 2.5 Flash |
| PDF extrakce | pypdf |
| Excel extrakce | openpyxl |
| Export dat | Excel (.xlsx) + PDF (reportlab) |
| Google Sheets | Apps Script webhook |
| Energie Dashboard | GitHub Pages + Chart.js |
| OOPP podpis | QR kód + 2FA + EmailJS |

---

## 🔄 Tok dat

```
Uživatel nahraje PDF/Excel/Word
        ↓
pypdf / openpyxl extrahuje text
        ↓
Google Gemini 2.5 Flash analyzuje (max 150 000 znaků)
        ↓
JSON výsledky → Dashboard + Export Excel/PDF
        ↓
Uživatel klikne "Odeslat do tabulky"
        ↓
Google Sheets (Apps Script webhook)
```

---

## 📁 Struktura repozitáře

```
DocScan/
├── app.py                    # Hlavní Streamlit aplikace
├── requirements.txt          # Python závislosti
├── README.md                 # Tato dokumentace
└── n8n/
    └── Energie CZLC4.json    # Záloha původního n8n workflow
```

---

## ⚙️ Instalace a spuštění

### Závislosti
```
streamlit
pandas
plotly
requests
openpyxl
reportlab
qrcode[pil]
pypdf
```

### Streamlit Secrets
```toml
GEMINI_API_KEY = "váš_api_klíč"
```

### Lokální spuštění
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🔑 API a integrace

| Služba | Účel | Stav |
|--------|------|------|
| Google Gemini 2.5 Flash | AI extrakce dat | ✅ Aktivní |
| Google Sheets Apps Script | Ukládání dat | ✅ Aktivní |
| ENTSO-E API | Live ceny OTE | ⏳ Čeká na token |
| EmailJS | 2FA podpis OOPP | ✅ Aktivní |

---

## ⚠️ Známá omezení

- FSX a voda — Gemini občas bere špatný sloupec (probíhá ladění promptu)
- OTE cena — zatím fallback 1 650 Kč/MWh, čeká na ENTSO-E token
- Aplikace nemá přihlášení — přístup má kdokoli s odkazem

---

## 🗺 Plánovaný rozvoj

- ENTSO-E API — live ceny elektřiny z trhu OTE
- Dopracovat prompt pro FSX a vodu
- Moduly Faktury a Smlouvy — aktivace Gemini prompty
- Google OAuth — omezení přístupu na firemní účty
- Automatické měsíční reporty emailem

---

*DocScan · Jana Sivačenko · Facility CZLC4 · Duben 2026*
