# DocScan — Facility · Chrástany

Streamlit aplikace pro digitalizaci Facility procesů na skladu Chrástany (CZLC4).

---

## Moduly

### ⚡ Energie
- Nahrání faktur za elektřinu, FSX, plyn a vodu (PDF / Excel)
- Automatická extrakce dat přes n8n webhook
- Odesílání do Google Sheets (záložky CZLC4, LCÚ, LCZ, SKLC3)
- Export do Excel, PDF a TXT

### 🦺 OOPP & MČDP
Evidence osobních ochranných pracovních prostředků a mycích/čisticích prostředků.

**Výdej MČDP (1× za kvartál)**
- Formulář výdeje: ručník Siguro, tekuté mýdlo, Ariel 60 ks, krém Indulona, abrazivní pasta Solvina
- QR kód pro 2FA podpis zaměstnance
- Odesílání záznamu do Google Sheets (záložka `MCDP_CZLC4`)

**2FA podpis zaměstnance** (`podpis_2fa.html`)
- Zaměstnanec naskenuje QR kód telefonem
- Dostane 6místný kód na email (platnost 5 minut) přes EmailJS
- Po ověření kódu podepíše prstem na telefonu
- Podpis se uloží do záložky `Podpisy_MCDP` v Google Sheets

**Evidence OOPP**
- Záznam vydaných pomůcek s expirací
- Automatický výpočet stavu (v pořádku / brzy expiruje / expirováno)
- Odesílání do záložky `OOPP_CZLC4`

**Tisk protokolu**
- Generátor PDF předávacího protokolu
- Obsahuje právní text dle NV 390/2021 Sb.
- Připraveno k tisku a fyzickému podpisu

### 📄 Faktury / 📋 Smlouvy
Připraveno pro budoucí napojení na Anthropic API.

---

## Technologie

- **Frontend:** Streamlit (Python)
- **Podpisová stránka:** HTML + SignaturePad.js + EmailJS
- **Databáze:** Google Sheets (Google Apps Script webhook)
- **Email 2FA:** EmailJS (Gmail)
- **PDF generátor:** ReportLab
- **QR kód:** qrcode[pil]
- **Hosting appky:** Streamlit Cloud
- **Hosting podpisové stránky:** GitHub Pages

---

## Struktura repozitáře

```
DocScan-Alza/
├── app.py                  # Hlavní Streamlit aplikace
├── podpis_2fa.html         # Podpisová stránka (GitHub Pages)
├── requirements.txt        # Python závislosti
└── README.md
```

---

## Google Sheets záložky

| Záložka | Obsah |
|---|---|
| `CZLC4` | Spotřeba energií |
| `MCDP_CZLC4` | Výdej MČDP — kvartální záznamy |
| `OOPP_CZLC4` | Evidence OOPP s expirací |
| `Podpisy_MCDP` | Audit log 2FA podpisů |
| `Přehled_OOPP` | Živý dashboard |

---

## Nastavení (EmailJS)

Pro funkci 2FA podpisu jsou potřeba tyto hodnoty v `podpis_2fa.html`:

```js
emailjs.init("PUBLIC_KEY");
var SERVICE_ID  = "service_...";
var TEMPLATE_ID = "template_...";
```

---

## Automatické alerty

Google Apps Script (`Projekt_Energie LC`) spouští každé pondělí v 8:00 funkci `weeklyAlertOOPP` — odesílá email vedoucímu s přehledem expirujících OOPP a nesplněných MČDP kontrol.

---

*Facility · Sklad Chrástany · 2025–2026*
