# 🔍 DocScan — Vytěžování dat z dokumentů

Webová aplikace pro automatické vytěžování dat z dokumentů pomocí AI.

## Co to dělá

Nahraješ dokumenty → AI vytáhne klíčová data → zobrazí se v dashboardu.

Aktuálně funkční modul vytěžuje data z faktur za energie pro objekt CZLC4 (WEST I – Alza).
* budu rozšířovat možnosti

## Funkční moduly

- ⚡ **Energie** — spotřeba a ceny elektřiny, FSX, plynu a vody
- 📄 **Faktury** — připraveno, aktivace po získání Anthropic API
- 📋 **Smlouvy** — připraveno, aktivace po získání Anthropic API
- 📦 **Objednávky** — připraveno, aktivace po získání Anthropic API

## Podporované formáty

PDF, Word (.docx), Excel (.xlsx, .xls)

## Jak spustit lokálně

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Aplikace

🌐 [docscan-alza.streamlit.app](https://docscan-alza.streamlit.app)

## Soubory

- `app.py` — Streamlit aplikace (DocScan UI ( design, karty, tlačístka atd ) + logika) - Hlaví Python soubor - celá aplikace je zde.
- `requirements.txt` — Python závislosti ( knihovna )
- stremlit - framework který vytváří celou webovou aplikaci, tlačítka, karty, upload souborů, graf
- pandas -  zpracování dat ve formě tabulek, používá se pro zobrazení výsledků v "Digitálním archivu" a export do Excelu
- plotly -  knihovna pro grafy a vizualizace, zatím nevyužitá ale připravená pro budoucí grafy vývoje spotřeby
- requests - odesílání HTTP requestů, konkrétně posílá PDF soubory na n8n webhook
- openyxl - čtení a zápis Excel souborů (.xlsx), stará se o hezké formátování exportu — modré hlavičky, střídající se barvy řádků
- reportlab -  generování PDF souborů, vytváří "Stáhnout PDF" tlačítko s tabulkou výsledků energií  
- `n8n/workflow.json` — záloha n8n workflow
- README.mg  — dokumentace projektu, popis co aplikace dělá, jak ji spustit, jaké technologie používa atd. ( úvodní strana )

## Technologie

- [Streamlit](https://streamlit.io/) — frontend
- [n8n](https://n8n.io/) — automatizace
- [Google Vertex AI](https://cloud.google.com/vertex-ai) — AI vytěžování dat

## n8n workflow

Webhook přijme dokumenty → Code node rozdělí soubory → extrakce textu → Google Vertex AI vytáhne data → vrátí JSON do Streamlitu.

## Poznámky

- Ignoruje data jiných nájemců (Ecologistics, Dominant LibTaur)
- Vrací `n/a` pokud hodnotu nenajde
- Word a Excel: upload funguje, n8n vytěžování bude rozšířeno stejně tak i aplikace

*Projekt: CZLC4 | Jana Sivačenko | 2026*
