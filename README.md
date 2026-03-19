# ⚡ Energy Dashboard — CZLC4

Moje aplikace na sledování energií v budově CZLC4 (objekt WEST I – Alza).

## Co to dělá

Nahraju PDF faktury → n8n je pošle do AI → AI vytáhne čísla → zobrazí se v dashboardu.

Sledované hodnoty:
- **Elektřina** — spotřeba kWh, cena silové el., distribuce, celkem
- **Plyn** — spotřeba kWh, cena celkem
- **Voda** — spotřeba m³, cena
- **FSX** — spotřeba kWh, cena

## Jak to spustit

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Soubory

- `app.py` — Streamlit dashboard
- `index.html` — úvodní stránka
- `requirements.txt` — závislosti
- `n8n/workflow.json` — export n8n workflow (záloha!)

## n8n workflow

Webhook přijme PDF → extrahuje text → Google Vertex AI vytáhne data → vrátí JSON do Streamlitu.

Webhook path: `faktury-upload`  
AI model: Google Vertex AI (credentials: *Vertex AI n8n Service Account*)

## Poznámky

- Ignoruje řádky jiných firem (Ecologistics, WEST II, Dominant LibTaur)
- Vrací `n/a` pokud hodnotu nenajde — nevymýšlí si
