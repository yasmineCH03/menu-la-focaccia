"""QR code du menu La Focaccia.
Usage : python qr/make_qr.py
Produit :
  qr/qr-code-menu.png   le QR code seul (1200 px)
  qr/qr-code-menu.svg   le QR code seul, vectoriel, pour l'imprimeur
  qr/carte-qr-menu.png  la carte de table bilingue, 4 x 6 po à 300 dpi
"""
from pathlib import Path

import segno
from PIL import Image, ImageDraw, ImageFont

URL = "https://yasminech03.github.io/menu-la-focaccia/"
HERE = Path(__file__).parent
ROOT = HERE.parent

# Couleurs du thème Halftone du menu (tokens.css converti en hex)
PAPER = "#F9F3DB"
PAPER2 = "#F1E6C4"
INK = "#2D160F"
INK2 = "#492D24"
MUTED = "#694A3D"
ACCENT = "#D01A00"


def font(name, size, weight=None):
    f = ImageFont.truetype(str(HERE / "fonts" / name), size)
    if weight:
        f.set_variation_by_axes([weight])
    return f


qr = segno.make(URL, error="q")  # niveau Q : reste lisible si la carte s'abîme un peu

# 1. Le QR code seul
qr.save(HERE / "qr-code-menu.svg", scale=10, border=4, dark=INK, light="#FFFFFF")
qr.save(HERE / "qr-code-menu.png", scale=1200 // (qr.symbol_size(border=4)[0]), border=4, dark=INK, light="#FFFFFF")


# 2. La carte de table
W, H = 1200, 1800
M = 90  # marge
card = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(card)


def checker(y, cell=40, rows=1):
    for r in range(rows):
        for i in range(W // cell + 1):
            if (i + r) % 2 == 0:
                d.rectangle([i * cell, y + r * cell, (i + 1) * cell - 1, y + (r + 1) * cell - 1], fill=ACCENT)


def text(xy, s, f, fill, anchor="la"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def dots(y, h=48, cell=24, r=6):
    """Trame de points rouge qui s'efface vers la droite, comme sur le menu."""
    for row in range(h // cell):
        for i in range((W - 2 * M) // cell + 1):
            x = M + i * cell + cell // 2
            fade = 1 - (x - M) / (W - 2 * M)
            rr = r * fade
            if rr < 1:
                continue
            cy = y + row * cell + cell // 2
            d.ellipse([x - rr, cy - rr, x + rr, cy + rr], fill=ACCENT)


checker(0)
checker(H - 40)

# Logo et nom
logo = Image.open(ROOT / "site-assets/logo/logo-focaccia-tampon.png").convert("RGBA")
logo.thumbnail((140, 140))
card.paste(logo, (M, 100), logo)
text((M + 165, 170), "Pizzeria La Focaccia", font("Chivo.ttf", 52, 700), INK, "lm")

# Le grand "Menu"
text((M - 6, 270), "Menu", font("Ultra-Regular.ttf", 250), ACCENT)

# Appel à l'action, français puis anglais
text((M, 590), "Scannez pour voir le menu", font("Chivo.ttf", 60, 700), INK)
text((M, 668), "Scan to see the menu", font("Chivo.ttf", 52, 400), INK2)

# Le QR code dans un cadre d'encre, comme les cadres du menu
size = 720
qimg = Image.open(HERE / "qr-code-menu.png").convert("RGB")
qimg = qimg.resize((size, size), Image.NEAREST)
x0 = (W - size) // 2
y0 = 790
d.rectangle([x0 - 14, y0 - 14, x0 + size + 13, y0 + size + 13], fill=INK)
card.paste(qimg, (x0, y0))

dots(y0 + size + 50)

# Langues et adresse
text((W // 2, 1640), "Français et English", font("Chivo.ttf", 40, 500), MUTED, "mm")
text((W // 2, 1700), "2202 avenue du Mont-Royal Est, Montréal", font("Chivo.ttf", 34, 400), MUTED, "mm")

card.save(HERE / "carte-qr-menu.png", dpi=(300, 300))
print("QR et carte générés pour", URL)
