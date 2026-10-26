"""Génère docs/index.html (français) et docs/en.html (anglais) à partir de menu.json et en.json.
Usage : python build.py
Pour changer un prix ou un plat : modifier menu.json. Pour l'anglais : ajouter la phrase dans en.json."""
import json
from html import escape as e
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
OUT = HERE.parent / "docs"          # site publié sur GitHub Pages
(OUT / "img").mkdir(parents=True, exist_ok=True)
MAX_SIDE = 800                       # photos réduites pour le mobile
data = json.loads((HERE / "menu.json").read_text(encoding="utf-8"))
EN = json.loads((HERE / "en.json").read_text(encoding="utf-8"))
R = data["restaurant"]

FR_UI = {
    "ui:title": f"Menu, Pizzeria {R['name']}",
    "ui:description": f"Le menu de la pizzeria {R['name']} : pizzas napolitaines, sandwichs, poutines et desserts, avec les prix.",
    "ui:logo": f"Logo de la pizzeria {R['name']}",
    "ui:jump": "Aller à une catégorie",
    "ui:tabs": "Catégories du menu",
    "ui:solo": "Solo",
    "ui:trio": "Trio",
    "ui:currency": "Prix en dollars canadiens, taxes en sus.",
    "ui:allergy": "Une allergie ? Parlez-en à l’équipe avant de commander.",
    "ui:lang": "Langue",
}
PAGES = {"fr": "index.html", "en": "en.html"}
lang = "fr"
missing = set()


def t(s):
    """Traduit une phrase du menu vers la langue de la page en cours."""
    if lang == "fr":
        return FR_UI.get(s, s)
    if s not in EN and s not in EN.get("_same_in_english", []) and not s.startswith("ui:"):
        missing.add(s)
    return EN.get(s, s)


def money(v):
    v = str(v).replace(" $", "")
    return f"{v} $" if lang == "fr" else f"${v.replace(',', '.')}"


def publish(src):
    """Copie une image réduite dans docs/img et renvoie son chemin publié."""
    p = Path(src)
    name = (p.parent.name + "-" + p.stem).lower() + (".png" if p.suffix == ".png" else ".jpg")
    dest = OUT / "img" / name
    im = Image.open(HERE / src)
    im.thumbnail((MAX_SIDE, MAX_SIDE))
    if dest.suffix == ".png":
        im.save(dest, optimize=True)
    else:
        im.convert("RGB").save(dest, quality=80, optimize=True, progressive=True)
    return "img/" + name, im.size


def img(src, alt="", cls="photo", eager=False, lazy=True):
    if not src:
        return ""
    src, (w, h) = publish(src)
    load = 'fetchpriority="high"' if eager else ('loading="lazy" decoding="async"' if lazy else 'decoding="async"')
    return f'<img class="{cls}" src="{e(src)}" alt="{e(alt)}" width="{w}" height="{h}" {load}>'


def item(i):
    price = f'<span class="price">{money(i["price"])}</span>'
    if i.get("price2"):
        price = (f'<span class="price"><span class="visually-hidden">{t("ui:solo")} </span>{money(i["price"])}</span>'
                 f'<span class="price-alt">{t("ui:trio")} {money(i["price2"])}</span>')
    desc = f'<p class="desc">{e(t(i["desc"]))}</p>' if i.get("desc") else ""
    extra = f'<p class="extra">{e(t(i["extra"]))}</p>' if i.get("extra") else ""
    return (f'<li class="row{" has-photo" if i.get("img") else ""}"><div class="row-text"><div class="row-head">'
            f'<h3>{e(t(i["name"]))}</h3><span class="leader" aria-hidden="true"></span><div class="prices">{price}</div></div>{desc}{extra}</div>'
            f'{img(i.get("img"), "")}</li>')


def table(tb):
    head = "".join(f'<th scope="col" class="num">{e(t(c))}</th>' for c in tb["cols"])
    rows = "".join(
        f'<tr><th scope="row">{e(t(r[0]))}</th>' + "".join(f'<td class="num">{money(v)}</td>' for v in r[1:]) + "</tr>"
        for r in tb["rows"])
    return f'<table class="prices-table"><thead><tr><th scope="col">{e(t(tb["caption"]))}</th>{head}</tr></thead><tbody>{rows}</tbody></table>'


def extras(xs):
    out = []
    for x in xs:
        chips = "".join(
            f'<li>{e(t(c[0]))} <span class="num">{money(c[1])}</span></li>' if isinstance(c, list) else f"<li>{e(t(c))}</li>"
            for c in x["list"])
        out.append(f'<div class="extras"><h3>{e(t(x["title"]))}</h3><ul class="chips">{chips}</ul></div>')
    return "".join(out)


def section(s):
    body = []
    if s.get("note"):
        body.append(f'<p class="note">{e(t(s["note"]))}</p>')
    if s["type"] == "poster":
        p = s["poster"]
        body.append(
            f'<div class="poster"><div class="poster-text"><p class="poster-figure num">{money(p["figure"])}</p>'
            f'<h3 class="poster-name">{e(t(p["name"]))}</h3><p class="desc">{e(t(p["line"]))}</p></div>'
            f'<div class="screen" aria-hidden="true"></div>{img(p["img"], "")}</div>')
    if s["type"] == "breads":
        body.append('<ul class="rows">' + "".join(
            f'<li class="row has-photo"><div class="row-text"><div class="row-head"><h3>{e(t(b["name"]))}</h3></div>'
            f'<p class="desc">{e(t(b["desc"]))}</p></div>{img(b["img"], "")}</li>' for b in s["breads"]) + "</ul>")
    if s["type"] == "table" and s.get("img"):
        body.append(img(s["img"], "", "photo photo-wide"))
    if s.get("table"):
        body.append(table(s["table"]))
    if s.get("items"):
        body.append('<ul class="rows">' + "".join(item(i) for i in s["items"]) + "</ul>")
    if s.get("extras"):
        body.append(extras(s["extras"]))
    cls = ' class="round"' if s.get("round") else ""
    return (f'<section id="{s["id"]}"{cls} aria-labelledby="h-{s["id"]}"><h2 id="h-{s["id"]}">{e(t(s["title"]))}</h2>'
            + "".join(body) + "</section>")


def cover(s):
    if s.get("cover"):
        return s["cover"]
    for src in [s.get("img"), s.get("poster", {}).get("img")] + [x.get("img") for x in s.get("items", []) + s.get("breads", [])]:
        if src:
            return src


def lang_switch():
    """Deux boutons toujours visibles ; celui de la page en cours est plein."""
    out = []
    for code, label, name in (("fr", "FR", "Français"), ("en", "EN", "English")):
        cur = ' aria-current="page"' if code == lang else ""
        out.append(f'<a href="{PAGES[code]}" hreflang="{code}" lang="{code}" class="lang-btn"{cur}>'
                   f'<span aria-hidden="true">{label}</span><span class="visually-hidden">{name}</span></a>')
    return f'<nav class="lang" aria-label="{t("ui:lang")}">{"".join(out)}</nav>'


def page():
    cats = "".join(
        f'<li><a href="#{s["id"]}">{img(cover(s), "", "cat-photo", lazy=False) or "<span class=\"cat-photo cat-blank\"></span>"}'
        f'<span>{e(t(s["title"]))}</span></a></li>'
        for s in data["sections"])
    nav = "".join(f'<li><a href="#{s["id"]}">{e(t(s["title"]))}</a></li>' for s in data["sections"])
    alt = "en" if lang == "fr" else "fr"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{e(t('ui:description'))}">
<meta name="theme-color" content="#f6eed7">
<title>{e(t('ui:title'))}</title>
<link rel="alternate" hreflang="{alt}" href="{PAGES[alt]}">
<link rel="icon" href="{publish('../site-assets/logo/favicon.png')[0]}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Ultra&family=Chivo:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div class="checker" aria-hidden="true"></div>
<header class="masthead container">
  <div class="brand">{img(R['logo'], t('ui:logo'), 'logo', eager=True)}<p class="brand-name">Pizzeria {e(R['name'])}</p>{lang_switch()}</div>
  <h1>Menu</h1>
  <p class="tagline">{e(t(R['tagline']))}</p>
</header>
<nav class="container cat-grid-wrap" aria-label="{e(t('ui:jump'))}"><ul class="cat-grid">{cats}</ul></nav>
<nav class="tabs" aria-label="{e(t('ui:tabs'))}"><ul class="container">{nav}</ul></nav>
<main class="container">
{"".join(section(s) for s in data["sections"])}
</main>
<footer class="foot">
  <div class="checker" aria-hidden="true"></div>
  <div class="container">
    <p>{e(t('ui:currency'))}</p>
    <p>{e(t('ui:allergy'))}</p>
    <p>{e(t(R['address']))}</p>
    <p><a href="tel:{R['phone']}">{e(R['phone_label'])}</a></p>
    {"".join(f'<p class="credit"><a href="{e(c["url"])}">{e(t(c["text"]))}</a></p>' for c in R.get("credits", []))}
  </div>
</footer>
<script src="menu.js" defer></script>
</body>
</html>
"""


for lang in PAGES:
    (OUT / PAGES[lang]).write_text(page(), encoding="utf-8")
    print(PAGES[lang], "généré")
for f in ("styles.css", "tokens.css", "base.css", "menu.js"):
    (OUT / f).write_bytes((HERE / f).read_bytes())
(OUT / ".nojekyll").write_text("")
if missing:
    print("Phrases sans traduction anglaise (laissées en français) :", *sorted(missing), sep="\n  ")
