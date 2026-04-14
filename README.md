# 🔍 DocScan-Alza
**AI extrakce dat z dokumentů + Evidence energií & OOPP | Verze 2.0 | Duben 2026**

[![Streamlit App](https://img.shields.io/badge/Streamlit-docscan--alza.streamlit.app-FF4B4B?logo=streamlit)](https://docscan-alza.streamlit.app)
[![Energie Dashboard](https://img.shields.io/badge/GitHub%20Pages-energie--dashboard-222?logo=github)](https://janasiva4.github.io/energie-dashboard)
[![GitHub](https://img.shields.io/badge/GitHub-JanaSiva4%2FDocScan--Alza-181717?logo=github)](https://github.com/JanaSiva4/DocScan-Alza)

---

## 📋 O projektu

DocScan-Alza je sada nástrojů pro facility management skladu CZLC4 (WEST I – Alza, Chrástany):

- **DocScan** — AI extrakce dat z faktur za energie (PDF/Excel/Word) pomocí Google Gemini
- **Energie Dashboard** — webový přehled spotřeby a nákladů na GitHub Pages
- **OOPP & MČDP** — evidence výdeje ochranných pomůcek a mycích prostředků

---

## 📁 Struktura repozitáře

```
DocScan-Alza/
├── app.py                  # Streamlit aplikace — DocScan + OOPP/MČDP
├── requirements.txt        # Python závislosti
├── podpis_2fa.html         # Podpisová stránka pro 2FA (QR kód)
├── Energie CZLC4.json      # Záloha původního n8n workflow
└── README.md               # Tato dokumentace
```

---

## ⚡ Modul 1 — Energie Dashboard

**URL:** [janasiva4.github.io/energie-dashboard](https://janasiva4.github.io/energie-dashboard)

Webová aplikace na GitHub Pages pro sledování měsíční spotřeby a nákladů za energie. Data se načítají z Google Sheets přes Apps Script webhook.

### Záložky

**📊 Přehled**
- Karty s poslední měsíční spotřebou — elektřina (Innogy), FSX, plyn, voda
- Graf spotřeby elektřiny a nákladů po měsících
- 📈 Trendy — meziroční změna — náklady (Kč) a spotřeba el. (kWh) napříč roky
- 📈 Trendy — energetický benchmarking — průměrná cena elektřiny Kč/kWh v čase

**📉 Grafy**
- Podrobné grafy spotřeby a nákladů pro každou kategorii energie
- Elektřina (Innogy + FSX), plyn, voda — spotřeba i náklady zvlášť

**📋 Historie**
- Tabulka všech měsíčních odečtů včetně sloupce 📦 SJL

**📈 Predikce**
- OTE cena — ruční zadání spot ceny z [OTE-CR.cz](https://www.ote-cr.cz/cs/kratkodobe-trhy/elektrina/den-dopredu), ukládá se do localStorage
- Alert — červené upozornění při ceně nad 2 500 Kč/MWh
- SJL kalkulačka — koeficient 0,069 kWh/SJL (průměr 2025–2026, 13 měsíců), auto-předvyplnění z posledního měsíce
- Predikce 2027 — odhad ročních nákladů s +5% nárůstem

**✏️ Zadání dat**
- Formulář pro ruční zadání měsíčních hodnot, uložení do Google Sheets

### Struktura záložky CZLC4 (sloupce A–R)

| Sloupec | Index | Hodnota |
|---------|-------|---------|
| A | 0 | Rok |
| B | 1 | Měsíc |
| C | 2 | Elektřina spotřeba kWh |
| D | 3 | Elektřina Ø cena Kč/kWh |
| E | 4 | Elektřina silová el. Kč |
| F | 5 | Elektřina distribuce Kč |
| G | 6 | Elektřina celkem Kč |
| H | 7 | FSX spotřeba kWh |
| I | 8 | FSX Ø cena Kč/kWh |
| J | 9 | FSX celkem Kč |
| K | 10 | Plyn spotřeba kWh |
| L | 11 | Plyn Ø cena Kč/kWh |
| M | 12 | Plyn celkem Kč |
| N | 13 | Voda spotřeba m³ |
| O | 14 | Voda Ø cena Kč/m³ |
| P | 15 | Voda celkem Kč |
| R | 17 | SJL (Store Job Lines) |

---

## 🦺 Modul 2 — OOPP & MČDP

Evidence výdeje osobních ochranných pracovních prostředků (OOPP) a mycích a čisticích prostředků (MČDP) v souladu s **NV 390/2021 Sb.**

### Funkce

**🧴 MČDP — Mycí a čisticí prostředky**
- Formulář pro výdej prostředků zaměstnanci (ručník Siguro, tekuté mýdlo, abrazivní pasta, Ariel 60ks, krém Indulona)
- Generování QR kódu pro 2FA podpis zaměstnance na telefonu
- Uložení záznamu do Google Sheets — záložka `MCDP_CZLC4`

**🦺 OOPP — Osobní ochranné pracovní prostředky**
- Formulář pro výdej pomůcky (boty, rukavice, vesta, helma atd.)
- Automatický výpočet expirace dle NV 390/2021 Sb.
- Stav: `v pořádku` / `brzy expiruje` / `expirováno`
- Tisk protokolu — PDF dle NV 390/2021 Sb.
- Uložení záznamu do Google Sheets — záložka `OOPP_CZLC4`

**🔔 Týdenní email alert**
- Přehled expirovaných a brzy expirujících pomůcek
- Upozornění na MČDP čekající na podpis v aktuálním kvartálu
- Odesílá se na: petr.jurasek@alza.cz

### Struktura záložky `MCDP_CZLC4`

| Sloupec | Hodnota |
|---------|---------|
| A | ID záznamu |
| B | Datum výdeje |
| C | Kvartál |
| D | Rok |
| E | Sklad |
| F | Zaměstnanec |
| G | Email zaměstnance |
| H–L | Vydané položky (ručník, mýdlo, pasta, Ariel, Indulona) |
| M | Vše vydáno (ANO/NE) |
| N | Podpis potvrzen |
| O | Zadal |
| P | Timestamp |

### Struktura záložky `OOPP_CZLC4`

| Sloupec | Hodnota |
|---------|---------|
| A | ID záznamu |
| B | Datum výdeje |
| C | Sklad |
| D | Zaměstnanec |
| E | Email zaměstnance |
| F | Pomůcka |
| G | Velikost |
| H | Expirace (MM/RRRR) |
| I | Stav |
| J | Dní do expirace |
| K | Podpis |
| L | Zadal |
| M | Timestamp |

---

## 🛠️ Technický stack

| Komponenta | Popis |
|-----------|-------|
| Streamlit | Python webová aplikace — DocScan + OOPP/MČDP |
| Google Gemini 2.5 Flash | AI extrakce dat z faktur |
| GitHub Pages | Energie Dashboard (HTML + Chart.js) |
| Google Sheets | Databáze — záložky CZLC4, MCDP_CZLC4, OOPP_CZLC4 |
| Apps Script | Webhook proxy (doGet / doPost) + email alert |
| pypdf / openpyxl | Extrakce textu z PDF a Excel souborů |
| reportlab + qrcode | Generování PDF protokolů a QR kódů |

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

- OTE cena — zadávána ručně jednou týdně (CORS blokuje přímé načítání z GitHub Pages)
- ENTSO-E API — registrace proběhla, čeká se na token pro live ceny
- Aplikace nemá přihlášení — přístup má kdokoli s odkazem
- Email alert — nutno nastavit trigger v Google Sheets → Rozšíření → Apps Script → Triggery

---

## 🗺️ Plánovaný rozvoj

- ENTSO-E API — automatické načítání live cen OTE
- Více skladů — LCÚ, LCZ, SKLC3
- Google OAuth — omezení přístupu na firemní účty
- Automatické měsíční reporty emailem
- Moduly Faktury a Smlouvy — aktivace Gemini prompty

---

*DocScan-Alza · Jana Sivačenko · Facility CZLC4 · Duben 2026*
