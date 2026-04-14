# 🔍 DocScan-Alza
**AI extrakce dat z faktur za energie | Verze 2.0 | Duben 2026**

[![Streamlit App](https://img.shields.io/badge/Streamlit-docscan--alza.streamlit.app-FF4B4B?logo=streamlit)](https://docscan-alza.streamlit.app)
[![GitHub](https://img.shields.io/badge/GitHub-JanaSiva4%2FDocScan--Alza-181717?logo=github)](https://github.com/JanaSiva4/DocScan-Alza)

---

## 📋 O projektu

DocScan je webová aplikace pro automatickou extrakci dat z faktur za energie pomocí AI. Uživatel nahraje PDF, Excel nebo Word soubory a aplikace automaticky vytáhne klíčové hodnoty — bez ručního opisování a bez Excelu.

Aktuálně funkční modul zpracovává faktury za energie pro objekt **WEST I – Alza (CZLC4, Chrástany)**. AI extrahuje 10 klíčových hodnot (elektřina, FSX, plyn, voda) z libovolného počtu faktur najednou.

---

## ✅ Co aplikace umí

### ⚡ Extrakce dat z faktur (hlavní funkce)
- Nahrání libovolného počtu PDF, Excel nebo Word faktur najednou
- AI (Google Gemini 2.5 Flash) automaticky extrahuje 10 hodnot pro subjekt WEST I – Alza
- AI ignoruje data ostatních nájemců (Ecologistics, WEST II) — bere pouze správné řádky
- Přehledný dashboard s kartami pro každou kategorii energie
- Digitální archiv — tabulka všech extrahovaných dat v jednom pohledu
- Export výsledků do Excel (.xlsx) a PDF souboru
- Uložení do Google Sheets — historie po měsících → napojení na Energie Dashboard

### 📊 Napojení na Energie Dashboard
Po uložení dat do Google Sheets se hodnoty automaticky promítnou do webového dashboardu na GitHub Pages — grafy spotřeby, nákladů, trendů, predikce 2027 a SJL kalkulačka.

**Dashboard:** [janasiva4.github.io/energie-dashboard](https://janasiva4.github.io/energie-dashboard)

### 🦺 OOPP & MČDP (součást aplikace)
- Evidence výdeje osobních ochranných pracovních prostředků a mycích prostředků
- Podrobnosti viz sekce níže

---

## 🤖 AI extrakce — jak to funguje

```
Uživatel nahraje PDF/Excel/Word faktury
        ↓
pypdf / openpyxl extrahuje text ze souborů
        ↓
Texty se agregují do jednoho vstupu (max 150 000 znaků)
        ↓
Google Gemini 2.5 Flash analyzuje text
        ↓
JSON s 10 hodnotami výhradně pro WEST I – Alza
        ↓
Zobrazení v dashboardu + export Excel/PDF
        ↓
Uložení do Google Sheets → Energie Dashboard
```

### Extrahované hodnoty

| Pole | Popis | Zdroj |
|------|-------|-------|
| `el_spotreba_kwh` | Spotřeba elektřiny vlastní (kWh) | Přefakturace MD |
| `el_cena_sil_el_bez_dph` | Cena silové elektřiny bez DPH | Faktura Innogy |
| `el_cena_distribuce_bez_dph` | Cena distribuce bez DPH | Faktura Innogy |
| `el_cena_celkem_zaklad_kc` | Elektřina celkem základ Kč | Faktura Innogy |
| `fsx_spotreba_kwh` | Spotřeba FSX celkem (kWh) | Přefakturace FSX |
| `fsx_cena_bez_dph` | Cena FSX bez DPH | Přefakturace FSX |
| `plyn_spotreba_kwh` | Spotřeba plynu (kWh) | Faktura plyn |
| `plyn_cena_celkem_zaklad_kc` | Plyn celkem základ Kč | Faktura plyn |
| `voda_spotreba_m3` | Spotřeba vody celkem (m³) | Přefakturace vody |
| `voda_cena_bez_dph` | Cena vody bez DPH | Přefakturace vody |

---

## 🛠️ Technický stack

| Komponenta | Popis |
|-----------|-------|
| Hosting | Streamlit Community Cloud |
| Frontend | Python + Streamlit |
| Verzování | GitHub (JanaSiva4/DocScan-Alza) |
| AI model | Google Gemini 2.5 Flash — API klíč v Streamlit Secrets |
| PDF extrakce | pypdf |
| Excel extrakce | openpyxl |
| Export dat | Excel (.xlsx) + PDF (reportlab) |
| Google Sheets | Apps Script webhook — ukládání dat po měsících |
| Energie Dashboard | GitHub Pages + Chart.js |
| OOPP podpis | QR kód + 2FA + EmailJS |

---

## 📁 Struktura repozitáře

```
DocScan-Alza/
├── app.py                  # Hlavní Streamlit aplikace
├── requirements.txt        # Python závislosti
├── podpis_2fa.html         # Podpisová stránka pro 2FA (QR kód)
├── Energie CZLC4.json      # Záloha původního n8n workflow
└── README.md               # Tato dokumentace
```

---

## ⚙️ Instalace a spuštění

### Závislosti
```
streamlit
pandas
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

## 🦺 Modul OOPP & MČDP

Evidence výdeje ochranných pomůcek a mycích prostředků dle **NV 390/2021 Sb.**

### 🧴 MČDP — Mycí a čisticí prostředky
- Formulář pro výdej prostředků zaměstnanci (ručník Siguro, tekuté mýdlo, abrazivní pasta, Ariel 60ks, krém Indulona)
- Generování QR kódu pro 2FA podpis zaměstnance na telefonu
- Uložení záznamu do Google Sheets — záložka `MCDP_CZLC4`
- Eviduje se: datum výdeje, kvartál, zaměstnanec, vydané položky, stav podpisu

### 🦺 OOPP — Osobní ochranné pracovní prostředky
- Formulář pro výdej pomůcky (boty, rukavice, vesta, helma atd.)
- Automatický výpočet data expirace dle NV 390/2021 Sb.
- Stav pomůcky: `v pořádku` / `brzy expiruje` / `expirováno`
- Tisk protokolu PDF dle NV 390/2021 Sb.
- Uložení záznamu do Google Sheets — záložka `OOPP_CZLC4`

### 🔔 Týdenní email alert
- Automatický přehled expirovaných a brzy expirujících pomůcek
- Upozornění na MČDP čekající na podpis v aktuálním kvartálu
- Odesílá se na: petr.jurasek@alza.cz

---

## 🔗 Klíčové URL

| Služba | URL |
|--------|-----|
| Streamlit aplikace | [docscan-alza.streamlit.app](https://docscan-alza.streamlit.app) |
| Energie Dashboard | [janasiva4.github.io/energie-dashboard](https://janasiva4.github.io/energie-dashboard) |
| Podpisová stránka 2FA | [janasiva4.github.io/DocScan-Alza/podpis_2fa.html](https://janasiva4.github.io/DocScan-Alza/podpis_2fa.html) |

**Apps Script URL:**
```
https://script.google.com/macros/s/AKfycbzfRP2cvMrwjbsCgQPzfbQsVABB68OYdpTPajGRT4hbhBbVWoGPJIJJTfMy6PbbhfTwCQ/exec
```

---

## ⚠️ Známá omezení

- FSX a voda — Gemini občas bere špatný sloupec (probíhá ladění promptu)
- Aplikace nemá přihlášení — přístup má kdokoli s odkazem
- Email alert — nutno nastavit trigger v Google Sheets → Rozšíření → Apps Script → Triggery

---

## 🗺️ Plánovaný rozvoj

- Dopracovat prompt pro FSX a vodu — spolehlivější extrakce
- ENTSO-E API — automatické načítání live cen OTE do dashboardu
- Moduly Faktury a Smlouvy — aktivace Gemini prompty
- Google OAuth — omezení přístupu na firemní účty
- Automatické měsíční reporty emailem

---

*DocScan-Alza · Jana Sivačenko · Facility CZLC4 · Duben 2026*
