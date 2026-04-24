import streamlit as st
import pandas as pd
import requests
import io
import re
import base64
import json
import qrcode
from datetime import datetime, date
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Circle, String

# --- KONFIGURACE GOOGLE SHEETS ---
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxzGV-vnAWMloGczThHXmch7JmgYDNe2WpPzeDeVvGPgcyeRpCEzi4dQfq7IsZWNLt7wg/exec"
FACILITY_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxzGV-vnAWMloGczThHXmch7JmgYDNe2WpPzeDeVvGPgcyeRpCEzi4dQfq7IsZWNLt7wg/exec"

# --- FONTY S CESKOU DIAKRITIKOU ---
import os as _os

def _registruj_font():
    _base = _os.path.dirname(_os.path.abspath(__file__))
    _mozne_cesty = [
        (_os.path.join(_base, 'fonts', 'DejaVuSans.ttf'),
         _os.path.join(_base, 'fonts', 'DejaVuSans-Bold.ttf')),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
    ]
    for _regular, _bold in _mozne_cesty:
        if _os.path.exists(_regular) and _os.path.exists(_bold):
            try:
                pdfmetrics.registerFont(TTFont('DejaVu', _regular))
                pdfmetrics.registerFont(TTFont('DejaVu-Bold', _bold))
                return 'DejaVu', 'DejaVu-Bold'
            except Exception:
                continue
    return 'Helvetica', 'Helvetica-Bold'

PDF_FONT, PDF_FONT_BOLD = _registruj_font()


def odeslat_do_google_sheets(res, sklad="CZLC4"):
    try:
        obdobi_raw = str(res.get('obdobi', datetime.now().strftime('%Y-%m')))
        try:
            if '-' in obdobi_raw and len(obdobi_raw) == 7:
                rok, mesic = map(int, obdobi_raw.split('-'))
            elif '.' in obdobi_raw:
                casti = obdobi_raw.split('.')
                if len(casti) == 2:
                    mesic, rok = int(casti[0]), int(casti[1])
                elif len(casti) == 3:
                    mesic, rok = int(casti[1]), int(casti[2])
                else:
                    rok, mesic = datetime.now().year, datetime.now().month
            else:
                rok, mesic = datetime.now().year, datetime.now().month
        except Exception:
            rok, mesic = datetime.now().year, datetime.now().month

        def to_f(val):
            if not val or str(val).lower() == 'n/a':
                return 0.0
            try:
                s = str(val).replace('\xa0', '').replace(' ', '')
                s = re.sub(r'[^0-9,.]', '', s)
                if ',' in s and '.' in s:
                    s = s.replace(',', '')
                s = s.replace(',', '.')
                return float(s)
            except Exception:
                return 0.0

        data_row = [
            str(rok), str(mesic).zfill(2),
            to_f(res.get('el_spotreba_kwh', 0)), 0.0,
            to_f(res.get('el_cena_sil_el_bez_dph', 0)),
            to_f(res.get('el_cena_distribuce_bez_dph', 0)),
            to_f(res.get('el_cena_celkem_zaklad_kc', 0)),
            to_f(res.get('fsx_spotreba_kwh', 0)), 0.0,
            to_f(res.get('fsx_cena_bez_dph', 0)),
            to_f(res.get('plyn_spotreba_kwh', 0)), 0.0,
            to_f(res.get('plyn_cena_celkem_zaklad_kc', 0)),
            to_f(res.get('voda_spotreba_m3', 0)), 0.0,
            to_f(res.get('voda_cena_bez_dph', 0)),
        ]
        payload = {"action": "append", "sheet": sklad, "row": data_row}
        requests.post(GOOGLE_SCRIPT_URL, json=payload)
        return True
    except Exception as e:
        st.error(f"Chyba: {e}")
        return False


def odeslat_mcdp_do_sheets(data: dict, sklad: str = "CZLC4") -> bool:
    def yn(val):
        return "ANO" if val else "NE"
    try:
        row = [
            f"MCDP-{sklad}-{datetime.now().strftime('%Y%m%d%H%M')}",
            data.get("datum_vydeje", datetime.now().strftime("%d.%m.%Y")),
            data.get("kvartal", ""), datetime.now().year, sklad,
            data.get("zamestnanec", ""), data.get("email", ""),
            yn(data.get("rucnik")), yn(data.get("mydlo")),
            yn(data.get("ariel")), yn(data.get("krem")), yn(data.get("solvina")),
            yn(all([data.get("rucnik"), data.get("mydlo"), data.get("ariel"),
                    data.get("krem"), data.get("solvina")])),
            data.get("zadal", ""), datetime.now().strftime("%d.%m.%Y %H:%M"),
        ]
        payload = {"action": "append", "sheet": f"MCDP_{sklad}", "row": row}
        r = requests.post(FACILITY_SCRIPT_URL, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Chyba odesilani MCDP: {e}")
        return False


def odeslat_oopp_do_sheets(data: dict, sklad: str = "CZLC4") -> bool:
    def stav_exp(exp_str):
        if not exp_str:
            return "—"
        try:
            p = exp_str.split("/")
            exp = datetime(int(p[1]), int(p[0]), 1)
            dnes = datetime.now()
            if exp < dnes:
                return "expirovano"
            if (exp - dnes).days <= 60:
                return "brzy expiruje"
            return "v poradku"
        except Exception:
            return "—"

    try:
        exp = data.get("expirace", "")
        row = [
            f"OOPP-{sklad}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            datetime.now().strftime("%d.%m.%Y"), sklad,
            data.get("zamestnanec", ""), data.get("email", ""),
            data.get("pomucka", ""), data.get("velikost", ""),
            exp, stav_exp(exp), "",
            "ANO" if data.get("podpis") else "NE",
            data.get("zadal", ""), datetime.now().strftime("%d.%m.%Y %H:%M"),
        ]
        payload = {"action": "append", "sheet": f"OOPP_{sklad}", "row": row}
        r = requests.post(FACILITY_SCRIPT_URL, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Chyba odesilani OOPP: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════
# PDF PROTOKOLY — Alza styl (bílý papír, originální logo)
# ═══════════════════════════════════════════════════════════════════

# Originální logo Alza.cz (extrahováno z Alza PDF šablony, 3× upscale)
_ALZA_LOGO_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkI"
    "CQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/2wBDAQMDAwQDBAgEBAgQCwkLEBAQEBAQ"
    "EBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBD/wAARCAJYAlgDASIA"
    "AhEBAxEB/8QAHgABAAEEAwEBAAAAAAAAAAAAAAECAwgJBAYHBQr/xABKEAACAQMCAwYDBQUEBggH"
    "AAAAAQIDBBEFBgcSIQgJEzFBUSIyYRRxgZHRFRYjQlJjcqGxGTNikpPBGCQ1Q1VWgpQlJnN0g/Dx"
    "/8QAGwEBAAIDAQEAAAAAAAAAAAAAAAECAwUGBAf/xAAyEQEAAgIBBAEDAgUDBAMAAAAAAQIDEQQF"
    "EiExQRMiUQYUIzJScbEzQmEVgZGh4fDx/9oADAMBAAIRAxEAPwDamAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/9k="
)

from reportlab.platypus import Image as RLImage

# Barevná paleta Alza
ALZA_BLUE    = colors.HexColor('#0A3D91')   # tmavě modrá (logo)
ALZA_BLUE_DK = colors.HexColor('#072B5E')   # tmavší modrá (akcenty)
TEXT_DARK    = colors.HexColor('#1A1A1A')
TEXT_MUTED   = colors.HexColor('#666666')
LINE_GRAY    = colors.HexColor('#CCCCCC')
ROW_ALT      = colors.HexColor('#F8F9FB')


def _alza_logo_image(width=2.5*cm):
    """Vrátí obrázek loga Alza.cz z embeded base64 (čtvercové logo 600x600)."""
    import base64 as _b64
    logo_bytes = _b64.b64decode(_ALZA_LOGO_B64)
    logo_io = io.BytesIO(logo_bytes)
    # Poměr loga: 600x600 (čtverec) → výška = width
    return RLImage(logo_io, width=width, height=width)


def _hlavicka_alza(titulek_text, W):
    """Hlavička: logo vlevo, nadpis vpravo, pod tím horizontální linka."""
    title_s = ParagraphStyle('t', fontSize=18, fontName=PDF_FONT_BOLD,
                             textColor=TEXT_DARK, alignment=2, leading=22)

    logo_img = _alza_logo_image(width=2.5*cm)
    ht = Table([[logo_img, Paragraph(titulek_text, title_s)]],
               colWidths=[3.0*cm, W - 3.0*cm])
    ht.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    # Horizontální linka pod hlavičkou
    linka = Table([['']], colWidths=[W], rowHeights=[1])
    linka.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, ALZA_BLUE),
    ]))

    return [ht, Spacer(1, 0.3*cm), linka]


def _alza_spolecnost(W):
    """Informace o společnosti Alza.cz a.s."""
    s = ParagraphStyle('c', fontSize=9.5, fontName=PDF_FONT, textColor=TEXT_DARK, leading=13)
    b = ParagraphStyle('cb', fontSize=9.5, fontName=PDF_FONT_BOLD, textColor=TEXT_DARK, leading=13)

    data = [
        [Paragraph('<b>Společnost:</b>', b), Paragraph('Alza.cz a.s.', s)],
        [Paragraph('<b>Sídlo:</b>', b), Paragraph('Jankovcova 1522/53, 170 00 Praha 7', s)],
        [Paragraph('<b>IČO:</b>', b), Paragraph('27082440', s)],
    ]
    t = Table(data, colWidths=[2.5*cm, W - 2.5*cm])
    t.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


def _paticka_alza():
    """Diskrétní patička."""
    footer_s = ParagraphStyle('f', fontSize=7.5, fontName=PDF_FONT,
                              textColor=TEXT_MUTED, alignment=1)
    return Paragraph(
        f"Alza.cz a.s. &nbsp;·&nbsp; Facility &nbsp;·&nbsp; "
        f"Dokument vygenerován {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        footer_s)


def _pravni_text(W):
    """Právní prohlášení — diskrétní, bez barev."""
    legal_s = ParagraphStyle('leg', fontSize=8, fontName=PDF_FONT,
                             textColor=TEXT_DARK, leading=11, alignment=4)
    nadpis_s = ParagraphStyle('ln', fontSize=9, fontName=PDF_FONT_BOLD,
                              textColor=ALZA_BLUE, leading=12)

    elementy = [
        Paragraph("Prohlášení zaměstnance — NV č. 390/2021 Sb.", nadpis_s),
        Spacer(1, 0.15*cm),
    ]
    legal_txt = (
        "Předání a převzetí výše uvedených OOPP a předmětů zaměstnanec i zaměstnavatel "
        "potvrzují svým podpisem. Zaměstnanec byl seznámen se způsobem údržby OOPP "
        "dle nařízení vlády č. 390/2021 Sb. Zaměstnanec se zavazuje řádně hospodařit s OOPP "
        "a předměty svěřenými mu zaměstnavatelem na základě tohoto potvrzení a střežit "
        "a ochraňovat tyto OOPP a předměty zaměstnavatele před poškozením, ztrátou, zničením "
        "a zneužitím. Zaměstnanec se zavazuje svěřené OOPP používat výhradně pro výkon práce "
        "pro zaměstnavatele. Zaměstnanec souhlasí s tím, že v případě ztráty nebo poškození "
        "bude cena sražena ze mzdy v souladu s příslušnou Dohodou o srážkách ze mzdy."
    )
    elementy.append(Paragraph(legal_txt, legal_s))
    return elementy


def _podpisy_alza(W):
    """Podpisová sekce — dvě linky s popiskami 'Předávající' a 'Přebírající'."""
    label_s = ParagraphStyle('pl', fontSize=10, fontName=PDF_FONT_BOLD,
                             textColor=TEXT_DARK, alignment=1)
    date_s = ParagraphStyle('pd', fontSize=9, fontName=PDF_FONT,
                            textColor=TEXT_MUTED, alignment=1)

    data = [
        # prostor pro podpisy
        ['', '', '', ''],
        # linky
        ['', '', '', ''],
        # popisky pod linkami
        [Paragraph('Předávající', label_s), '',
         Paragraph('Přebírající', label_s), ''],
        # datum
        [Paragraph(f'V Chrášťanech dne {datetime.now().strftime("%d.%m.%Y")}', date_s), '',
         Paragraph(f'V Chrášťanech dne {datetime.now().strftime("%d.%m.%Y")}', date_s), ''],
    ]
    t = Table(data,
              colWidths=[W/2 - 0.5*cm, 1.0*cm, W/2 - 0.5*cm, 0],
              rowHeights=[1.5*cm, 0.1*cm, 0.5*cm, 0.4*cm])
    t.setStyle(TableStyle([
        ('LINEABOVE', (0, 1), (0, 1), 1.0, TEXT_DARK),
        ('LINEABOVE', (2, 1), (2, 1), 1.0, TEXT_DARK),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return t


# ═══════════════════════════════════════════════════════════════════
# PDF PROTOKOL — MCDP (mycí a čisticí prostředky)
# ═══════════════════════════════════════════════════════════════════
def generovat_pdf_protokol(zamestnanec, sklad, kvartal, vydane_polozky, vedouci, velikosti=None):
    """Předávací protokol MČDP — čistý Alza styl, originální logo."""
    if velikosti is None:
        velikosti = {}

    body_s  = ParagraphStyle('b', fontSize=10, fontName=PDF_FONT,
                             textColor=TEXT_DARK, leading=14)
    body_b  = ParagraphStyle('bb', fontSize=10, fontName=PDF_FONT_BOLD,
                             textColor=TEXT_DARK, leading=14)
    section_s = ParagraphStyle('sec', fontSize=11, fontName=PDF_FONT_BOLD,
                               textColor=ALZA_BLUE, leading=14, spaceAfter=4)
    th_s = ParagraphStyle('th', fontSize=9.5, fontName=PDF_FONT_BOLD,
                          textColor=colors.white, alignment=1)
    td_s = ParagraphStyle('td', fontSize=10, fontName=PDF_FONT,
                          textColor=TEXT_DARK, leading=13)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=2.0*cm, leftMargin=2.0*cm,
        topMargin=1.0*cm, bottomMargin=1.0*cm,
        title="Předávací protokol MČDP")
    el = []
    W = 17.0 * cm

    # Hlavička s logem
    el.extend(_hlavicka_alza("Předávací protokol — MČDP", W))
    el.append(Spacer(1, 0.4*cm))

    # Společnost
    el.append(_alza_spolecnost(W))
    el.append(Spacer(1, 0.2*cm))
    el.append(Paragraph('Dále jen „předávající"', body_s))
    el.append(Spacer(1, 0.3*cm))
    el.append(Paragraph("<b>a</b>", body_s))
    el.append(Spacer(1, 0.3*cm))

    # Info o zaměstnanci - inline styl (jako originál)
    udaje_data = [
        [Paragraph('<b>Jméno a příjmení:</b>', body_b),
         Paragraph(zamestnanec or '…………………………………………', body_s)],
        [Paragraph('<b>Sklad:</b>', body_b),
         Paragraph(sklad, body_s)],
        [Paragraph('<b>Kvartál / rok:</b>', body_b),
         Paragraph(kvartal, body_s)],
        [Paragraph('<b>Datum výdeje:</b>', body_b),
         Paragraph(datetime.now().strftime('%d.%m.%Y'), body_s)],
        [Paragraph('<b>Vedoucí / zadal:</b>', body_b),
         Paragraph(vedouci or '—', body_s)],
        [Paragraph('<b>Číslo protokolu:</b>', body_b),
         Paragraph(f"MCDP-{sklad}-{datetime.now().strftime('%Y%m%d%H%M')}", body_s)],
    ]
    ut = Table(udaje_data, colWidths=[4.0*cm, W - 4.0*cm])
    ut.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    el.append(ut)
    el.append(Spacer(1, 0.5*cm))

    # Úvodní text — OPRAVENO
    el.append(Paragraph("Předávající předává a přebírající přejímá:", body_s))
    el.append(Spacer(1, 0.3*cm))

    # Tabulka položek
    el.append(Paragraph("Vydávané položky", section_s))

    def mark(val):
        return '✓' if val else '—'

    # OPRAVENO: ručník má False (nemá prázdnou linku na velikost)
    polozky_def = [
        ('1× Ručník Siguro 50×100 cm', 'rucnik',  '50×100 cm, froté',        False),
        ('1× Tekuté mýdlo',             'mydlo',   '500 ml',                   False),
        ('1× Ariel tablety',            'ariel',   '60 ks / balení',           False),
        ('1× Krém Indulona',            'krem',    'originál nebo měsíčkový', False),
        ('1× Abrazivní pasta Solvina',  'solvina', '450 g',                    False),
    ]

    header_row = [
        Paragraph('Položka', th_s),
        Paragraph('Vydáno', th_s),
        Paragraph('Velikost', th_s),
        Paragraph('Specifikace', th_s),
        Paragraph('Podpis', th_s),
    ]
    polozky_data = [header_row]
    for nazev, klic, spec, je_odev in polozky_def:
        vel_val = velikosti.get(klic, '') if je_odev else ''
        velikost_cell = vel_val if vel_val else ('__________' if je_odev else '—')
        polozky_data.append([
            Paragraph(nazev, td_s),
            mark(vydane_polozky.get(klic)),
            velikost_cell,
            Paragraph(spec, td_s),
            '',
        ])

    col_w = [5.8*cm, 1.6*cm, 2.2*cm, 4.0*cm, 3.4*cm]
    pt = Table(polozky_data, colWidths=col_w,
               rowHeights=[0.8*cm] + [0.85*cm]*len(polozky_def))
    pt.setStyle(TableStyle([
        # Hlavička tabulky - tmavě modrá Alza
        ('BACKGROUND', (0, 0), (-1, 0), ALZA_BLUE),
        # Zebrování
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        # Rámeček
        ('BOX', (0, 0), (-1, -1), 0.8, TEXT_DARK),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, LINE_GRAY),
        # Text ve sloupci Vydáno - větší, modrý
        ('FONTNAME', (1, 1), (1, -1), PDF_FONT_BOLD),
        ('FONTSIZE', (1, 1), (1, -1), 14),
        ('TEXTCOLOR', (1, 1), (1, -1), ALZA_BLUE),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        # Linka ve sloupci podpis
        ('LINEBELOW', (4, 1), (4, -1), 0.6, TEXT_MUTED),
    ]))
    el.append(pt)
    el.append(Spacer(1, 0.5*cm))

    # OPRAVENO: Přebírající stvrzuje (ne Předávající)
    el.append(Paragraph(
        "Přebírající stvrzuje, že se řádně seznámil se stavem předmětu "
        "a převzal jej v pořádku.",
        body_s))
    el.append(Spacer(1, 0.2*cm))
    el.append(Paragraph(
        "Pokud je předmět kód, čip nebo klíče, přebírající potvrzuje, "
        "že v případě ztráty je povinen uhradit částku ve výši odpovídající "
        "skutečným nákladům.",
        body_s))
    el.append(Spacer(1, 0.4*cm))

    # Podpisy
    el.append(_podpisy_alza(W))
    el.append(Spacer(1, 0.3*cm))

    # Právní text
    el.extend(_pravni_text(W))

    # Patička
    el.append(Spacer(1, 0.4*cm))
    el.append(_paticka_alza())

    doc.build(el)
    buf.seek(0)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════
# PDF PROTOKOL — OOPP (osobní ochranné pracovní pomůcky)
# ═══════════════════════════════════════════════════════════════════
def generovat_pdf_oopp(zamestnanec, email, sklad, vydane_pomucky, velikosti_oopp,
                        expirace_oopp, vedouci, stredisko="", osobni_cislo=""):
    """Předávací protokol OOPP — čistý Alza styl, originální logo."""
    if velikosti_oopp is None:
        velikosti_oopp = {}
    if expirace_oopp is None:
        expirace_oopp = {}

    body_s  = ParagraphStyle('b', fontSize=10, fontName=PDF_FONT,
                             textColor=TEXT_DARK, leading=14)
    body_b  = ParagraphStyle('bb', fontSize=10, fontName=PDF_FONT_BOLD,
                             textColor=TEXT_DARK, leading=14)
    section_s = ParagraphStyle('sec', fontSize=11, fontName=PDF_FONT_BOLD,
                               textColor=ALZA_BLUE, leading=14, spaceAfter=4)
    th_s = ParagraphStyle('th', fontSize=9.5, fontName=PDF_FONT_BOLD,
                          textColor=colors.white, alignment=1)
    td_s = ParagraphStyle('td', fontSize=9.5, fontName=PDF_FONT,
                          textColor=TEXT_DARK, leading=12)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=2.0*cm, leftMargin=2.0*cm,
        topMargin=1.0*cm, bottomMargin=1.0*cm,
        title="Předávací protokol OOPP")
    el = []
    W = 17.0 * cm

    # Hlavička s logem
    el.extend(_hlavicka_alza("Předávací protokol — OOPP", W))
    el.append(Spacer(1, 0.3*cm))

    # Společnost
    el.append(_alza_spolecnost(W))
    el.append(Spacer(1, 0.25*cm))

    # Info o zaměstnanci - dvousloupcová tabulka pro úsporu místa
    udaje_data = [
        [Paragraph('<b>Jméno a příjmení:</b>', body_b),
         Paragraph(zamestnanec or '…………………………………………', body_s),
         Paragraph('<b>Sklad:</b>', body_b),
         Paragraph(sklad, body_s)],
        [Paragraph('<b>Email:</b>', body_b),
         Paragraph(email or '—', body_s),
         Paragraph('<b>Datum výdeje:</b>', body_b),
         Paragraph(datetime.now().strftime('%d.%m.%Y'), body_s)],
        [Paragraph('<b>Středisko:</b>', body_b),
         Paragraph(stredisko or '—', body_s),
         Paragraph('<b>Vedoucí / zadal:</b>', body_b),
         Paragraph(vedouci or '—', body_s)],
        [Paragraph('<b>Osobní číslo:</b>', body_b),
         Paragraph(osobni_cislo or '—', body_s),
         Paragraph('<b>Číslo protokolu:</b>', body_b),
         Paragraph(f"OOPP-{sklad}-{datetime.now().strftime('%Y%m%d%H%M')}", body_s)],
    ]
    _unused_fix_udaje = []
    ut = Table(udaje_data, colWidths=[3.5*cm, (W/2 - 3.5*cm), 3.5*cm, (W/2 - 3.5*cm)])
    ut.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    el.append(ut)
    el.append(Spacer(1, 0.3*cm))

    # Úvod — OPRAVENO
    el.append(Paragraph("Předávající předává a přebírající přejímá:", body_s))
    el.append(Spacer(1, 0.2*cm))

    # Tabulka pomůcek
    el.append(Paragraph("Vydávané pomůcky", section_s))

    pomucky_def = [
        ('Oděv pracovní (montérky)', 'odev',     'dle standardu firmy'),
        ('Rukavice bezpečnostní',    'rukavice', 'dle potřeby pozice'),
        ('Kabát proti chladu',       'kabat',    'zimní období'),
        ('Tričko',                   'tricko',   'letní období'),
        ('Mikina',                   'mikina',   'přechodné období'),
        ('Čepice / kšiltovka',       'cepice',   'dle potřeby'),
        ('Ochranné brýle',           'bryle',    'dle pracoviště'),
        ('Kraťasy',                  'kratasy',  'letní období'),
        ('Thermo prádlo',            'thermo',   'zimní období'),
        ('Bezpečnostní obuv',        'obuv',     'S1P / S3'),
    ]

    def mark(val):
        return '✓' if val else '—'

    header_row = [
        Paragraph('Pomůcka', th_s),
        Paragraph('Vydáno', th_s),
        Paragraph('Velikost', th_s),
        Paragraph('Expirace', th_s),
        Paragraph('Specifikace', th_s),
        Paragraph('Podpis', th_s),
    ]
    polozky_data = [header_row]
    for nazev, klic, spec in pomucky_def:
        vydano = vydane_pomucky.get(klic, False)
        vel = velikosti_oopp.get(klic, '') if vydano else ''
        exp = expirace_oopp.get(klic, '') if vydano else ''
        polozky_data.append([
            Paragraph(nazev, td_s),
            mark(vydano),
            vel if vel else ('__________' if vydano else '—'),
            exp if exp else '—',
            Paragraph(spec, td_s),
            '',
        ])

    col_w = [4.3*cm, 1.4*cm, 2.2*cm, 2.0*cm, 3.6*cm, 3.5*cm]
    pt = Table(polozky_data, colWidths=col_w,
               rowHeights=[0.75*cm] + [0.7*cm]*len(pomucky_def))
    pt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ALZA_BLUE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ('BOX', (0, 0), (-1, -1), 0.8, TEXT_DARK),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, LINE_GRAY),
        ('FONTNAME', (1, 1), (1, -1), PDF_FONT_BOLD),
        ('FONTSIZE', (1, 1), (1, -1), 13),
        ('TEXTCOLOR', (1, 1), (1, -1), ALZA_BLUE),
        ('ALIGN', (1, 0), (3, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (5, 1), (5, -1), 0.6, TEXT_MUTED),
    ]))
    el.append(pt)
    el.append(Spacer(1, 0.5*cm))

    # OPRAVENO: Přebírající stvrzuje (ne Předávající)
    el.append(Paragraph(
        "Přebírající stvrzuje, že se řádně seznámil se stavem předmětu "
        "a převzal jej v pořádku.",
        body_s))
    el.append(Spacer(1, 0.2*cm))
    el.append(Paragraph(
        "Pokud je předmět kód, čip nebo klíče, přebírající potvrzuje, "
        "že v případě ztráty je povinen uhradit částku ve výši odpovídající "
        "skutečným nákladům.",
        body_s))
    el.append(Spacer(1, 0.4*cm))

    # Podpisy
    el.append(_podpisy_alza(W))
    el.append(Spacer(1, 0.3*cm))

    # Právní text
    el.extend(_pravni_text(W))

    # Patička
    el.append(Spacer(1, 0.4*cm))
    el.append(_paticka_alza())

    doc.build(el)
    buf.seek(0)
    return buf.getvalue()



# ═══════════════════════════════════════════════════════════════════
# KONFIGURACE STRÁNKY
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="DocScan", layout="wide", page_icon="🔍")

st.markdown("""
<style>
    [data-testid="stMainViewContainer"] .block-container { max-width: 1200px !important; margin-left: auto !important; margin-right: auto !important; }
    .stApp { background: linear-gradient(135deg, #051c3d 0%, #2e0b54 40%, #1a0633 70%, #030821 100%) !important; background-attachment: fixed !important; color: #f0f0f0; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0) !important; }
    div[data-testid="stMetric"] { background: rgba(0,0,0,0.25) !important; backdrop-filter: blur(15px); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.6) !important; box-shadow: 0 0 15px rgba(0,242,255,0.4) !important; height: 90px !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    [data-testid="stMetricLabel"] p { font-size: 0.9rem !important; }
    div[data-testid="stButton"] > button { background: linear-gradient(135deg, #0052cc 0%, #0a84ff 100%) !important; border: none !important; color: #ffffff !important; box-shadow: 0 0 8px rgba(0,82,204,0.4) !important; transition: all 0.2s ease-in-out !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 1.5px; height: 38px !important; font-size: 0.75rem !important; border-radius: 8px !important; }
    div[data-testid="stButton"] > button:hover { box-shadow: 0 0 14px rgba(0,82,204,0.6) !important; transform: scale(1.01); }
    .energy-card { background: rgba(10,10,20,0.4) !important; border-radius: 12px; padding: 6px 10px; border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(20px); margin-bottom: 6px; }
    .energy-card h3 { font-size: 0.9rem !important; margin: 4px 0 !important; }
    .el-border { border-top: 2px solid #FFD700 !important; }
    .fsx-border { border-top: 2px solid #0084ff !important; }
    .gas-border { border-top: 2px solid #FF5722 !important; }
    .water-border { border-top: 2px solid #00BFFF !important; }
    .oopp-border { border-top: 2px solid #00c864 !important; }
    [data-testid="stFileUploadDropzone"], section[data-testid="stFileUploadDropzone"], section[data-testid="stFileUploadDropzone"] > div { background-color: rgba(0,200,100,0.08) !important; border: 2px dashed #00c864 !important; border-radius: 10px !important; }
    div[data-baseweb="select"] > div { background-color: rgba(0,200,100,0.06) !important; border: 1px solid rgba(0,200,100,0.3) !important; }
    span[data-baseweb="tag"] { background-color: rgba(0,200,100,0.15) !important; border: 1px solid rgba(0,200,100,0.4) !important; color: #00e87a !important; }
    [data-testid="stDataFrame"] { background-color: rgba(0,82,204,0.05) !important; padding: 10px; border-radius: 10px; border: 1px solid rgba(0,132,255,0.3) !important; }
    .cat-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 16px; text-align: center; position: relative; transition: all 0.3s; cursor: pointer; margin-bottom: 8px; }
    .cat-card:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.3); transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.3); }
    .cat-card.active { background: rgba(0, 135, 90, 0.15); border-color: #00875a; box-shadow: 0 0 20px rgba(0, 135, 90, 0.3); }
    .cat-name { font-weight: bold; color: #fff; font-size: 0.9rem; margin-top: 6px; }
    .cat-desc { font-size: 0.7rem; color: rgba(255,255,255,0.4); margin-top: 4px; }
    .preview-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
    .preview-row:last-child { border-bottom: none; }
    .preview-label { font-size: 0.75rem; color: #888; text-transform: uppercase; }
    .preview-value { font-size: 0.85rem; color: #ccc; font-style: italic; }
    div[data-testid="stDownloadButton"] > button { background: rgba(0, 135, 90, 0.15) !important; border: 1px solid rgba(0, 135, 90, 0.4) !important; color: #00875a !important; font-size: 0.8rem !important; border-radius: 8px !important; height: 36px !important; box-shadow: none !important; width: auto !important; text-transform: none !important; letter-spacing: 0 !important; font-weight: normal !important; }
    .obdobi-box { background: rgba(0,200,100,0.06); border: 1px solid rgba(0,200,100,0.3); border-radius: 10px; padding: 12px 16px; color: #00e87a; font-size: 0.9rem; margin-bottom: 8px; }
    .obdobi-box-empty { background: rgba(0,200,100,0.06); border: 1px solid rgba(0,200,100,0.3); border-radius: 10px; padding: 12px 16px; color: #555; font-size: 0.85rem; font-style: italic; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 DocScan")
st.write("---")

if 'vysledky' not in st.session_state: st.session_state.vysledky = []
if 'kategorie' not in st.session_state: st.session_state.kategorie = "Energie"
if 'pocet_souboru' not in st.session_state: st.session_state.pocet_souboru = 0
if 'datum_analyzy' not in st.session_state: st.session_state.datum_analyzy = None
if 'obdobi_input' not in st.session_state: st.session_state.obdobi_input = ''
if 'file_uploader_key' not in st.session_state: st.session_state.file_uploader_key = 0

kategorie_list = [
    ("⚡", "Energie",      "Spotřeba & náklady"),
    ("📄", "Faktury",      "Dodavatel, částky, splatnost"),
    ("📋", "Smlouvy",      "Strany, podmínky, datum"),
    ("🦺", "OOPP & MČDP", "Evidence & výdej pomůcek"),
]

cols_kat = st.columns(4)
for col, (icon, name, desc) in zip(cols_kat, kategorie_list):
    with col:
        active = "active" if st.session_state.kategorie == name else ""
        st.markdown(
            f'<div class="cat-card {active}"><div style="font-size:1.8rem">{icon}</div>'
            f'<div class="cat-name">{name}</div><div class="cat-desc">{desc}</div></div>',
            unsafe_allow_html=True)
        if st.button(name, key=f"btn_{name}", use_container_width=True):
            st.session_state.kategorie = name
            st.rerun()

st.write("---")

pocet_souboru = st.session_state.get('pocet_souboru', 0)
obdobi_stat = st.session_state.vysledky[0].get('obdobi', '—') if st.session_state.vysledky else '—'
celkem_nakladu = 0
if st.session_state.vysledky:
    res = st.session_state.vysledky[0]
    for klic in ['el_cena_celkem_zaklad_kc', 'fsx_cena_bez_dph', 'plyn_cena_celkem_zaklad_kc', 'voda_cena_bez_dph']:
        try:
            hodnota = res.get(klic, 0)
            if hodnota and str(hodnota).lower() != 'n/a':
                celkem_nakladu += float(str(hodnota).replace(',', '.').replace(' ', ''))
        except Exception:
            pass

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Nahráno souborů", str(pocet_souboru) if pocet_souboru > 0 else "—")
with c2: st.metric("Období", obdobi_stat)
with c3: st.metric("Ušetřeno času", "~10 min" if st.session_state.vysledky else "—")
with c4: st.metric("Celkem nákladů", f"{celkem_nakladu:,.0f} Kč".replace(",", " ") if celkem_nakladu > 0 else "—")

st.write("---")
col_side, col_main = st.columns([1, 3])

# ── ENERGIE ──────────────────────────────────────────────────────
if st.session_state.kategorie == "Energie":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        sklad = st.selectbox("Sklad:", ["CZLC4", "LCÚ", "LCZ", "SKLC3"])
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">Období</p>', unsafe_allow_html=True)
        obdobi_val = st.session_state.get('obdobi_input', '')
        if obdobi_val:
            st.markdown(f'<div class="obdobi-box">📅 {obdobi_val}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="obdobi-box-empty">Vyplní se automaticky po analýze</div>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Vložte dokumenty", accept_multiple_files=True,
            type=['pdf', 'docx', 'xlsx', 'xls'],
            key=f"uploader_{st.session_state.file_uploader_key}")
        if uploaded_files:
            st.markdown(f'<p style="color:#00c864;font-size:0.8rem;">✓ {len(uploaded_files)} soubor(ů) připraveno</p>', unsafe_allow_html=True)
        st.write("")
        _, mid_btn, _ = st.columns([1.5, 4, 1.5])
        with mid_btn:
            analyze_btn = st.button("🚀 SPUSTIT ANALÝZU")
        if st.session_state.vysledky:
            if st.button("🗑 Nová analýza", use_container_width=True):
                st.session_state.vysledky = []
                st.session_state.pocet_souboru = 0
                st.session_state.obdobi_input = ''
                st.session_state.file_uploader_key += 1
                st.rerun()

    with col_main:
        if analyze_btn and uploaded_files:
            st.session_state.vysledky = []
            st.session_state.pocet_souboru = len(uploaded_files)
            st.session_state.datum_analyzy = datetime.now().strftime('%d.%m.%Y %H:%M')
            webhook_url = "https://n8n.dev.gcp.alza.cz/webhook/faktury-upload"
            with st.spinner(f"Analyzuji {len(uploaded_files)} faktur..."):
                try:
                    def get_mime(name):
                        if name.endswith('.pdf'): return "application/pdf"
                        if name.endswith('.docx'): return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        if name.endswith('.xlsx'): return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        if name.endswith('.xls'): return "application/vnd.ms-excel"
                        return "application/octet-stream"
                    files = [("data", (f.name, f.getvalue(), get_mime(f.name))) for f in uploaded_files]
                    payload = {"p": st.session_state.get("obdobi_input", datetime.now().strftime('%Y-%m'))}
                    response = requests.post(webhook_url, files=files, data=payload)
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.vysledky = data if isinstance(data, list) else [data]
                        prvni = st.session_state.vysledky[0] if st.session_state.vysledky else {}
                        if prvni.get('obdobi') and str(prvni.get('obdobi')).lower() != 'n/a':
                            st.session_state.obdobi_input = prvni.get('obdobi')
                    else:
                        st.error(f"Chyba: {response.status_code}")
                except Exception as e:
                    st.error(f"Chyba spojení: {e}")
            st.rerun()

        st.subheader("📁 Digitální archiv")
        if st.session_state.vysledky:
            res = st.session_state.vysledky[0]
            if st.button("✅ ODESLAT DO TABULKY", use_container_width=False):
                if odeslat_do_google_sheets(res, sklad):
                    st.success("Uloženo do Google Sheets!")
            col_t, col_btns = st.columns([2, 1])
            with col_btns:
                col_e2, col_p2 = st.columns(2)
            df_export = pd.DataFrame(st.session_state.vysledky)
            with col_e2:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Energie')
                    ws = writer.sheets['Energie']
                    header_fill = PatternFill(start_color="0052CC", end_color="0052CC", fill_type="solid")
                    header_font = Font(color="FFFFFF", bold=True)
                    for col in range(1, len(df_export.columns) + 1):
                        cell = ws.cell(row=1, column=col)
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = Alignment(horizontal='center')
                        ws.column_dimensions[get_column_letter(col)].width = 25
                    for row in range(2, len(df_export) + 2):
                        fc = "EBF3FF" if row % 2 == 0 else "FFFFFF"
                        fill = PatternFill(start_color=fc, end_color=fc, fill_type="solid")
                        for col in range(1, len(df_export.columns) + 1):
                            ws.cell(row=row, column=col).fill = fill
                periode = st.session_state.get('obdobi_input', 'export')
                st.download_button("⬇ Export Excel", data=buffer.getvalue(),
                    file_name=f"DocScan_{periode}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with col_p2:
                pdf_buffer = io.BytesIO()
                doc = SimpleDocTemplate(pdf_buffer, pagesize=A4,
                    rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
                elements = []
                title_style = ParagraphStyle('title', fontSize=18, fontName=PDF_FONT_BOLD,
                    textColor=colors.HexColor('#0052cc'), spaceAfter=6)
                sub_style = ParagraphStyle('sub', fontSize=10, fontName=PDF_FONT,
                    textColor=colors.HexColor('#666666'), spaceAfter=20)
                elements.append(Paragraph("DocScan — Přehled energií", title_style))
                elements.append(Paragraph(
                    f"Období: {res.get('obdobi','—')}  |  Vygenerováno: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                    sub_style))
                tisk_data = [['Kategorie', 'Parametr', 'Hodnota']]
                kats_pdf = [
                    ('Elektřina', 'el_spotreba_kwh', 'Spotřeba (kWh)'),
                    ('Elektřina', 'el_cena_sil_el_bez_dph', 'Cena sil. el. bez DPH'),
                    ('Elektřina', 'el_cena_distribuce_bez_dph', 'Cena distribuce bez DPH'),
                    ('Elektřina', 'el_cena_celkem_zaklad_kc', 'Cena celkem (Kč)'),
                    ('FSX', 'fsx_spotreba_kwh', 'Spotřeba (kWh)'),
                    ('FSX', 'fsx_cena_bez_dph', 'Cena bez DPH (Kč)'),
                    ('Plyn', 'plyn_spotreba_kwh', 'Spotřeba (kWh)'),
                    ('Plyn', 'plyn_cena_celkem_zaklad_kc', 'Cena celkem (Kč)'),
                    ('Voda', 'voda_spotreba_m3', 'Spotřeba (m³)'),
                    ('Voda', 'voda_cena_bez_dph', 'Cena bez DPH (Kč)'),
                ]
                for kat, klic, label in kats_pdf:
                    tisk_data.append([kat, label, str(res.get(klic, 'n/a'))])
                t = Table(tisk_data, colWidths=[4*cm, 8*cm, 5*cm])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0052cc')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), PDF_FONT_BOLD),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 0.5*cm))
                celkem_style = ParagraphStyle('celkem', fontSize=11, fontName=PDF_FONT_BOLD,
                    textColor=colors.HexColor('#0052cc'))
                celkem_val = sum([
                    float(str(res.get(k, 0)).replace(',', '.').replace(' ', ''))
                    for k in ['el_cena_celkem_zaklad_kc', 'fsx_cena_bez_dph',
                              'plyn_cena_celkem_zaklad_kc', 'voda_cena_bez_dph']
                    if res.get(k) and str(res.get(k)).lower() != 'n/a'
                ] or [0])
                elements.append(Paragraph(
                    f"Celkem nákladů: {celkem_val:,.2f} Kč".replace(',', ' '), celkem_style))
                doc.build(elements)
                pdf_buffer.seek(0)
                st.download_button("📄 Stáhnout PDF", data=pdf_buffer.getvalue(),
                    file_name=f"DocScan_{periode}.pdf", mime="application/pdf")
            st.dataframe(df_export, use_container_width=True)
            st.write("---")
            st.subheader("📊 Finální přehled")
            cols = st.columns(4)
            kats = [
                ("⚡ Elektřina", "el_",   "el-border",    cols[0]),
                ("🏢 FSX",       "fsx_",  "fsx-border",   cols[1]),
                ("🔥 Plyn",      "plyn_", "gas-border",   cols[2]),
                ("💧 Voda",      "voda_", "water-border", cols[3]),
            ]
            for label, key, style, col in kats:
                with col:
                    st.markdown(f'<div class="energy-card {style}"><h3>{label}</h3></div>',
                        unsafe_allow_html=True)
                    for res in st.session_state.vysledky:
                        data_souboru = {k: v for k, v in res.items()
                            if k.startswith(key) and v and str(v).lower() != "n/a"}
                        if data_souboru:
                            st.markdown('<div style="margin-bottom:10px;padding:4px;">', unsafe_allow_html=True)
                            for klic, hodnota in data_souboru.items():
                                parametr = klic.replace(key, "").replace("_", " ").upper()
                                try:
                                    num = float(str(hodnota).replace(',', '.').replace(' ', ''))
                                    if 'spotreba' in klic or 'm3' in klic:
                                        hodnota_fmt = f"{num:,.0f}".replace(',', ' ')
                                    else:
                                        hodnota_fmt = f"{num:,.2f} Kč".replace(',', ' ')
                                except Exception:
                                    hodnota_fmt = str(hodnota)
                                st.markdown(
                                    f'<div style="display:flex;justify-content:space-between;'
                                    f'border-bottom:1px solid rgba(255,255,255,0.1);padding:4px 0;">'
                                    f'<span style="color:#888;font-size:0.75rem;text-transform:uppercase;">{parametr}</span>'
                                    f'<span style="color:#fff;font-weight:bold;font-size:0.85rem;">{hodnota_fmt}</span>'
                                    f'</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
            st.write("")
            res = st.session_state.vysledky[0]
            text_export = f"DocScan — Výsledky analýzy\nObdobí: {res.get('obdobi','—')}\n\n"
            text_export += f"ELEKTŘINA\n  Spotřeba: {res.get('el_spotreba_kwh','n/a')} kWh\n  Cena celkem: {res.get('el_cena_celkem_zaklad_kc','n/a')} Kč\n\n"
            text_export += f"FSX\n  Spotřeba: {res.get('fsx_spotreba_kwh','n/a')} kWh\n  Cena: {res.get('fsx_cena_bez_dph','n/a')} Kč\n\n"
            text_export += f"PLYN\n  Spotřeba: {res.get('plyn_spotreba_kwh','n/a')} kWh\n  Cena celkem: {res.get('plyn_cena_celkem_zaklad_kc','n/a')} Kč\n\n"
            text_export += f"VODA\n  Spotřeba: {res.get('voda_spotreba_m3','n/a')} m³\n  Cena: {res.get('voda_cena_bez_dph','n/a')} Kč"
            st.download_button("📋 Stáhnout jako TXT", data=text_export.encode('utf-8'),
                file_name=f"DocScan_{res.get('obdobi','export')}.txt", mime="text/plain")
        else:
            st.info("Nahrajte faktury a spusťte analýzu.")

# ── FAKTURY ──────────────────────────────────────────────────────
elif st.session_state.kategorie == "Faktury":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        st.file_uploader("Vložte dokumenty", accept_multiple_files=True, type=['pdf', 'docx', 'xlsx', 'xls'])
        st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.75rem;margin-top:10px;">🔒 Dostupné po aktivaci API</p>', unsafe_allow_html=True)
    with col_main:
        st.subheader("📄 Faktury — ukázka výstupu")
        cols_f = st.columns(2)
        with cols_f[0]:
            st.markdown('<div class="energy-card fsx-border"><h4 style="color:#0084ff;">🏢 Dodavatel</h4>', unsafe_allow_html=True)
            for pole, val in [("Dodavatel", "ABC s.r.o."), ("IČ", "12345678"), ("DIČ", "CZ12345678"), ("Číslo faktury", "FAC-2026-001")]:
                st.markdown(f'<div class="preview-row"><span class="preview-label">{pole}</span><span class="preview-value">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with cols_f[1]:
            st.markdown('<div class="energy-card el-border"><h4 style="color:#FFD700;">💰 Platební údaje</h4>', unsafe_allow_html=True)
            for pole, val in [("Datum splatnosti", "15.02.2026"), ("Celkem bez DPH", "10 000 Kč"), ("DPH 21%", "2 100 Kč"), ("Celkem s DPH", "12 100 Kč"), ("Číslo účtu", "123456789/0800"), ("Variabilní symbol", "20260001")]:
                st.markdown(f'<div class="preview-row"><span class="preview-label">{pole}</span><span class="preview-value">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.info("⏳ Funkce bude aktivní po připojení Anthropic API.")

# ── SMLOUVY ──────────────────────────────────────────────────────
elif st.session_state.kategorie == "Smlouvy":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        st.file_uploader("Vložte dokumenty", accept_multiple_files=True, type=['pdf', 'docx', 'xlsx', 'xls'])
        st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.75rem;margin-top:10px;">🔒 Dostupné po aktivaci API</p>', unsafe_allow_html=True)
    with col_main:
        st.subheader("📋 Smlouvy — ukázka výstupu")
        cols_s = st.columns(2)
        with cols_s[0]:
            st.markdown('<div class="energy-card gas-border"><h4 style="color:#FF5722;">📝 Smluvní strany</h4>', unsafe_allow_html=True)
            for pole, val in [("Objednatel", "XYZ a.s."), ("Zhotovitel", "ABC s.r.o."), ("Datum podpisu", "01.01.2026"), ("Platnost do", "31.12.2026")]:
                st.markdown(f'<div class="preview-row"><span class="preview-label">{pole}</span><span class="preview-value">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with cols_s[1]:
            st.markdown('<div class="energy-card water-border"><h4 style="color:#00BFFF;">📌 Klíčové podmínky</h4>', unsafe_allow_html=True)
            for pole, val in [("Předmět", "Dodávka služeb"), ("Hodnota", "120 000 Kč/rok"), ("Výpovědní lhůta", "3 měsíce"), ("Obnova", "Automatická")]:
                st.markdown(f'<div class="preview-row"><span class="preview-label">{pole}</span><span class="preview-value">{val}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.info("⏳ Funkce bude aktivní po připojení Anthropic API.")

# ── OOPP & MCDP ──────────────────────────────────────────────────
elif st.session_state.kategorie == "OOPP & MČDP":
    with col_side:
        st.markdown('<p style="color:#00c864;font-size:0.75rem;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">Konfigurace</p>', unsafe_allow_html=True)
        sklad_oopp = st.selectbox("Sklad:", ["CZLC4", "LCÚ", "LCZ", "SKLC3"], key="sklad_oopp")
        rezim = st.radio("Režim:", ["Výdej MČDP", "Evidence OOPP", "Tisk protokolu MČDP", "Tisk protokolu OOPP"])

    with col_main:
        PODPIS_URL = "https://janasiva4.github.io/DocScan-Alza/podpis_2fa.html"

        # ═══════════════ VÝDEJ MČDP ═══════════════
        if rezim == "Výdej MČDP":
            st.subheader("🧴 Výdej MČDP — kvartální")
            if 'mcdp_reset' not in st.session_state:
                st.session_state.mcdp_reset = 0
            zamestnanec = st.text_input("Zaměstnanec (jméno a příjmení)", key=f"zam_{st.session_state.mcdp_reset}", autocomplete="off")
            email_zam   = st.text_input("Email zaměstnance", placeholder="jan.novak@firma.cz", key=f"email_{st.session_state.mcdp_reset}", autocomplete="off")
            stredisko   = st.text_input("Středisko", placeholder="např. Sklad A — příjem", key=f"stredisko_{st.session_state.mcdp_reset}", autocomplete="off")
            user        = st.text_input("Uživatel / osobní číslo", placeholder="např. 12345", key=f"user_{st.session_state.mcdp_reset}", autocomplete="off")
            rok_akt = datetime.now().year
            kvartal_sel = st.selectbox("Kvartál", [
                f"Q1 / {rok_akt}", f"Q2 / {rok_akt}", f"Q3 / {rok_akt}", f"Q4 / {rok_akt}",
                f"Q1 / {rok_akt+1}", f"Q2 / {rok_akt+1}", f"Q3 / {rok_akt+1}", f"Q4 / {rok_akt+1}"])
            st.write("**Vydávané položky:**")
            c1, c2 = st.columns(2)
            rucnik  = c1.checkbox("1x Ručník Siguro 50x100cm", value=True)
            mydlo   = c2.checkbox("1x Tekuté mýdlo", value=True)
            ariel   = c1.checkbox("1x Ariel tablety 60 ks", value=True)
            krem    = c2.checkbox("1x Krém Indulona", value=True)
            solvina = c1.checkbox("1x Abrazivní pasta Solvina", value=True)
            # Kolonka velikost pro ručník
            velikost_rucnik = st.text_input("Velikost ručníku (volitelně, pro tisk)",
                placeholder="např. 50x100 cm", key=f"velrucnik_{st.session_state.mcdp_reset}")
            vedouci = st.text_input("Zadal / vedoucí")

            if zamestnanec and email_zam:
                polozky_list = []
                if rucnik:  polozky_list.append("Ručník Siguro")
                if mydlo:   polozky_list.append("Tekuté mýdlo")
                if ariel:   polozky_list.append("Ariel 60 ks")
                if krem:    polozky_list.append("Krém Indulona")
                if solvina: polozky_list.append("Solvina")
                qr_data = {"jmeno": zamestnanec, "email": email_zam, "stredisko": stredisko,
                           "user": user, "sklad": sklad_oopp, "kvartal": kvartal_sel,
                           "polozky": ", ".join(polozky_list)}
                qr_json = json.dumps(qr_data, ensure_ascii=False)
                qr_payload = base64.b64encode(qr_json.encode('utf-8')).decode('ascii')
                qr_url = f"{PODPIS_URL}?d={qr_payload}"
                qr = qrcode.QRCode(version=1, box_size=6, border=2)
                qr.add_data(qr_url)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="#1a3a6b", back_color="white")
                buf_qr = io.BytesIO()
                qr_img.save(buf_qr, format="PNG")
                st.write("---")
                col_qr, col_info = st.columns([1, 2])
                with col_qr:
                    st.image(buf_qr.getvalue(), width=180, caption="Zaměstnanec naskenuje pro podpis")
                with col_info:
                    polozky_str = ", ".join(polozky_list)
                    st.markdown(
                        f'<div class="energy-card oopp-border" style="padding:12px;">'
                        f'<p style="color:#00c864;font-size:0.75rem;font-weight:bold;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Čeká na 2FA podpis</p>'
                        f'<p style="color:#fff;font-size:0.9rem;"><b>{zamestnanec}</b></p>'
                        f'<p style="color:#aaa;font-size:0.8rem;">{email_zam}</p>'
                        f'<p style="color:#aaa;font-size:0.8rem;margin-top:4px;">{kvartal_sel} · {sklad_oopp}</p>'
                        f'<p style="color:#aaa;font-size:0.75rem;margin-top:4px;">{polozky_str}</p>'
                        f'</div>', unsafe_allow_html=True)
                st.write("---")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ ODESLAT DO GOOGLE SHEETS", use_container_width=True):
                    if not zamestnanec:
                        st.warning("Zadej jméno zaměstnance.")
                    else:
                        data = {"zamestnanec": zamestnanec, "email": email_zam, "kvartal": kvartal_sel,
                                "rucnik": rucnik, "mydlo": mydlo, "ariel": ariel, "krem": krem,
                                "solvina": solvina, "podpis": True, "zadal": vedouci}
                        if odeslat_mcdp_do_sheets(data, sklad_oopp):
                            st.success(f"✅ Záznam uložen — {zamestnanec} · {kvartal_sel}")
                            st.session_state.mcdp_reset += 1
                            st.rerun()
            with col_btn2:
                if zamestnanec:
                    pdf_bytes = generovat_pdf_protokol(
                        zamestnanec=zamestnanec, sklad=sklad_oopp, kvartal=kvartal_sel,
                        vydane_polozky={"rucnik": rucnik, "mydlo": mydlo, "ariel": ariel,
                                        "krem": krem, "solvina": solvina},
                        vedouci=vedouci,
                        velikosti={"rucnik": velikost_rucnik} if velikost_rucnik else None)
                    jmeno_souboru = zamestnanec.replace(" ", "_")
                    st.download_button(
                        label="📄 Stáhnout PDF protokol",
                        data=bytes(pdf_bytes),
                        file_name=f"Protokol_MCDP_{jmeno_souboru}_{kvartal_sel[:2]}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"dl_mcdp_{st.session_state.mcdp_reset}")

        # ═══════════════ EVIDENCE OOPP ═══════════════
        elif rezim == "Evidence OOPP":
            st.subheader("🦺 Evidence OOPP — výdej pomůcek")
            if 'oopp_reset' not in st.session_state:
                st.session_state.oopp_reset = 0
            zamestnanec2 = st.text_input("Zaměstnanec (jméno a příjmení)", key=f"zam2_{st.session_state.oopp_reset}", autocomplete="off")
            email_zam2   = st.text_input("Email zaměstnance", placeholder="jan.novak@firma.cz", key=f"email2_{st.session_state.oopp_reset}", autocomplete="off")
            stredisko2   = st.text_input("Středisko", placeholder="např. Sklad A — příjem", key=f"stredisko2_{st.session_state.oopp_reset}", autocomplete="off")
            user2        = st.text_input("Uživatel / osobní číslo", placeholder="např. 12345", key=f"user2_{st.session_state.oopp_reset}", autocomplete="off")
            vedouci2     = st.text_input("Zadal / vedoucí", key=f"vedouci2_{st.session_state.oopp_reset}", autocomplete="off")
            st.write("**Vydávané pomůcky:**")
            pomucky_def = [
                ("Oděv pracovní (montérky)", "odev", None),
                ("Rukavice bezpečnostní", "rukavice", None),
                ("Kabát proti chladu", "kabat", 24),
                ("Tričko", "tricko", 12),
                ("Mikina", "mikina", 6),
                ("Čepice / kšiltovka", "cepice", 24),
                ("Ochranné brýle", "bryle", None),
                ("Kraťasy", "kratasy", 12),
                ("Thermo", "thermo", 12),
                ("Bezpečnostní obuv", "obuv", 12),
            ]
            o1, o2 = st.columns(2)
            vydane = {}
            velikosti_vyd = {}
            for i, (nazev, klic, exp_mes) in enumerate(pomucky_def):
                col = o1 if i % 2 == 0 else o2
                if exp_mes and exp_mes >= 12:
                    exp_info = f" ({exp_mes//12}r)"
                elif exp_mes:
                    exp_info = f" ({exp_mes}m)"
                else:
                    exp_info = " (dle potřeby)"
                vydane[klic] = col.checkbox(f"{nazev}{exp_info}", key=f"oopp_{klic}_{st.session_state.oopp_reset}")
                if vydane[klic]:
                    velikosti_vyd[klic] = col.text_input(f"Velikost — {nazev}",
                        key=f"vel_{klic}_{st.session_state.oopp_reset}",
                        placeholder="např. L, XL, 42, …")

            def exp_datum(mesice):
                if not mesice:
                    return None
                d = date.today()
                mes = d.month + mesice
                rok_exp = d.year + (mes - 1) // 12
                mes_exp = (mes - 1) % 12 + 1
                return f"{mes_exp:02d}/{rok_exp}"

            if zamestnanec2 and email_zam2:
                vydane_nazvy = [nazev for nazev, klic, _ in pomucky_def if vydane.get(klic)]
                oopp_qr_data = {"jmeno": zamestnanec2, "email": email_zam2, "stredisko": stredisko2,
                                "user": user2, "sklad": sklad_oopp,
                                "kvartal": f"OOPP {datetime.now().strftime('%m/%Y')}",
                                "polozky": ", ".join(vydane_nazvy) if vydane_nazvy else "—"}
                qr_json2 = json.dumps(oopp_qr_data, ensure_ascii=False)
                qr_payload2 = base64.b64encode(qr_json2.encode('utf-8')).decode('ascii')
                qr_url2 = f"{PODPIS_URL}?d={qr_payload2}"
                qr2 = qrcode.QRCode(version=1, box_size=6, border=2)
                qr2.add_data(qr_url2)
                qr2.make(fit=True)
                qr_img2 = qr2.make_image(fill_color="#0D4F1C", back_color="white")
                buf_qr2 = io.BytesIO()
                qr_img2.save(buf_qr2, format="PNG")
                st.write("---")
                col_qr2, col_info2 = st.columns([1, 2])
                with col_qr2:
                    st.image(buf_qr2.getvalue(), width=180, caption="Zaměstnanec naskenuje pro podpis")
                with col_info2:
                    nazvy_str = ", ".join(vydane_nazvy) if vydane_nazvy else "—"
                    st.markdown(
                        f'<div class="energy-card oopp-border" style="padding:12px;">'
                        f'<p style="color:#00c864;font-size:0.75rem;font-weight:bold;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Čeká na 2FA podpis</p>'
                        f'<p style="color:#fff;font-size:0.9rem;"><b>{zamestnanec2}</b></p>'
                        f'<p style="color:#aaa;font-size:0.8rem;">{email_zam2}</p>'
                        f'<p style="color:#aaa;font-size:0.75rem;margin-top:4px;">{nazvy_str}</p>'
                        f'</div>', unsafe_allow_html=True)
                st.write("---")

                col_btn_o1, col_btn_o2 = st.columns(2)
                with col_btn_o1:
                    if st.button("✅ ULOŽIT DO EVIDENCE", use_container_width=True):
                        ulozeno = 0
                        for nazev, klic, exp_mes in pomucky_def:
                            if vydane.get(klic):
                                exp = exp_datum(exp_mes)
                                data_oopp = {"zamestnanec": zamestnanec2, "email": email_zam2,
                                             "stredisko": stredisko2, "user": user2,
                                             "pomucka": nazev, "velikost": velikosti_vyd.get(klic, ""),
                                             "expirace": exp or "", "podpis": True, "zadal": vedouci2}
                                if odeslat_oopp_do_sheets(data_oopp, sklad_oopp):
                                    ulozeno += 1
                        if ulozeno > 0:
                            st.success(f"✅ Uloženo {ulozeno} pomůcek — {zamestnanec2}")
                            st.session_state.oopp_reset += 1
                            st.rerun()
                with col_btn_o2:
                    # PDF protokol OOPP
                    expirace_dict = {klic: exp_datum(exp_mes) or ""
                                     for nazev, klic, exp_mes in pomucky_def if vydane.get(klic)}
                    pdf_oopp_bytes = generovat_pdf_oopp(
                        zamestnanec=zamestnanec2, email=email_zam2, sklad=sklad_oopp,
                        vydane_pomucky=vydane, velikosti_oopp=velikosti_vyd,
                        expirace_oopp=expirace_dict, vedouci=vedouci2,
                        stredisko=stredisko2, osobni_cislo=user2)
                    jmeno_soub_o = zamestnanec2.replace(" ", "_")
                    st.download_button(
                        label="📄 Stáhnout PDF protokol OOPP",
                        data=bytes(pdf_oopp_bytes),
                        file_name=f"Protokol_OOPP_{jmeno_soub_o}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"dl_oopp_{st.session_state.oopp_reset}")
            else:
                st.info("Vyplň jméno a email zaměstnance pro zobrazení QR kódu.")

        # ═══════════════ TISK PROTOKOLU MČDP ═══════════════
        elif rezim == "Tisk protokolu MČDP":
            st.subheader("🖨️ Generátor předávacího protokolu — MČDP")
            st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:0.85rem;">Vyplň údaje — dostaneš PDF připravené k tisku a podpisu zaměstnance.</p>', unsafe_allow_html=True)
            zam_tisk = st.text_input("Zaměstnanec")
            rok_akt2 = datetime.now().year
            kv_tisk = st.selectbox("Kvartál", [
                f"Q1 / {rok_akt2}", f"Q2 / {rok_akt2}", f"Q3 / {rok_akt2}", f"Q4 / {rok_akt2}",
                f"Q1 / {rok_akt2+1}", f"Q2 / {rok_akt2+1}", f"Q3 / {rok_akt2+1}", f"Q4 / {rok_akt2+1}"],
                key="kv_tisk")
            ved_tisk = st.text_input("Vedoucí", key="ved_tisk")
            st.write("**Položky pro protokol:**")
            t1, t2 = st.columns(2)
            cb1 = t1.checkbox("Ručník Siguro", value=True, key="p1")
            cb2 = t2.checkbox("Tekuté mýdlo",  value=True, key="p2")
            cb3 = t1.checkbox("Ariel 60 ks",   value=True, key="p3")
            cb4 = t2.checkbox("Krém Indulona",  value=True, key="p4")
            cb5 = t1.checkbox("Solvina",        value=True, key="p5")
            vel_rucnik_tisk = st.text_input("Velikost ručníku (volitelně)",
                placeholder="např. 50×100 cm", key="vel_rucnik_tisk")

            pdf_tisk = generovat_pdf_protokol(
                zamestnanec=zam_tisk or "—",
                sklad=sklad_oopp,
                kvartal=kv_tisk,
                vydane_polozky={"rucnik": cb1, "mydlo": cb2, "ariel": cb3, "krem": cb4, "solvina": cb5},
                vedouci=ved_tisk,
                velikosti={"rucnik": vel_rucnik_tisk} if vel_rucnik_tisk else None
            )
            jmeno_souboru = (zam_tisk or "protokol").replace(" ", "_")
            st.download_button(
                label="📄 Stáhnout PDF protokol k tisku",
                data=bytes(pdf_tisk) if pdf_tisk else b"",
                file_name=f"Protokol_MCDP_{jmeno_souboru}.pdf",
                mime="application/pdf",
                use_container_width=False,
                disabled=not zam_tisk,
                key=f"dl_tisk_{zam_tisk or 'empty'}"
            )
            if not zam_tisk:
                st.info("Zadej jméno zaměstnance pro aktivaci tlačítka stažení.")

        # ═══════════════ TISK PROTOKOLU OOPP ═══════════════
        elif rezim == "Tisk protokolu OOPP":
            st.subheader("🖨️ Generátor předávacího protokolu — OOPP")
            st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:0.85rem;">Vyplň údaje — dostaneš PDF připravené k tisku a podpisu zaměstnance. Velikosti lze doplnit ručně na papíru.</p>', unsafe_allow_html=True)
            zam_oopp_tisk = st.text_input("Zaměstnanec", key="zam_oopp_tisk")
            email_oopp_tisk = st.text_input("Email", key="email_oopp_tisk", placeholder="jan.novak@firma.cz")
            stredisko_oopp_tisk = st.text_input("Středisko", key="stredisko_oopp_tisk")
            user_oopp_tisk = st.text_input("Osobní číslo", key="user_oopp_tisk")
            ved_oopp_tisk = st.text_input("Vedoucí", key="ved_oopp_tisk")

            pomucky_tisk_def = [
                ("Oděv pracovní (montérky)", "odev", None),
                ("Rukavice bezpečnostní", "rukavice", None),
                ("Kabát proti chladu", "kabat", 24),
                ("Tričko", "tricko", 12),
                ("Mikina", "mikina", 6),
                ("Čepice / kšiltovka", "cepice", 24),
                ("Ochranné brýle", "bryle", None),
                ("Kraťasy", "kratasy", 12),
                ("Thermo prádlo", "thermo", 12),
                ("Bezpečnostní obuv", "obuv", 12),
            ]
            st.write("**Pomůcky pro protokol:**")
            c_o1, c_o2 = st.columns(2)
            vydane_tisk = {}
            velikosti_tisk = {}
            for i, (nazev, klic, _) in enumerate(pomucky_tisk_def):
                col = c_o1 if i % 2 == 0 else c_o2
                vydane_tisk[klic] = col.checkbox(nazev, key=f"tiskoopp_{klic}", value=True)
                if vydane_tisk[klic]:
                    velikosti_tisk[klic] = col.text_input(f"Velikost — {nazev}",
                        key=f"tiskvel_{klic}",
                        placeholder="např. L, 42, …")

            def exp_datum_tisk(mesice):
                if not mesice:
                    return ""
                d = date.today()
                mes = d.month + mesice
                rok_exp = d.year + (mes - 1) // 12
                mes_exp = (mes - 1) % 12 + 1
                return f"{mes_exp:02d}/{rok_exp}"

            expirace_tisk = {klic: exp_datum_tisk(exp_mes)
                             for nazev, klic, exp_mes in pomucky_tisk_def if vydane_tisk.get(klic)}

            pdf_oopp_tisk = generovat_pdf_oopp(
                zamestnanec=zam_oopp_tisk or "—",
                email=email_oopp_tisk,
                sklad=sklad_oopp,
                vydane_pomucky=vydane_tisk,
                velikosti_oopp=velikosti_tisk,
                expirace_oopp=expirace_tisk,
                vedouci=ved_oopp_tisk,
                stredisko=stredisko_oopp_tisk,
                osobni_cislo=user_oopp_tisk
            )
            jmeno_soub_tisk = (zam_oopp_tisk or "protokol").replace(" ", "_")
            st.download_button(
                label="📄 Stáhnout PDF protokol OOPP k tisku",
                data=bytes(pdf_oopp_tisk) if pdf_oopp_tisk else b"",
                file_name=f"Protokol_OOPP_{jmeno_soub_tisk}.pdf",
                mime="application/pdf",
                use_container_width=False,
                disabled=not zam_oopp_tisk,
                key=f"dl_tisk_oopp_{zam_oopp_tisk or 'empty'}"
            )
            if not zam_oopp_tisk:
                st.info("Zadej jméno zaměstnance pro aktivaci tlačítka stažení.")
