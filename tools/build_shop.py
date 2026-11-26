#!/usr/bin/env python3
"""Build the online shop (momokovintage.com/shop/) from simple item folders.

Every piece is one folder in shop/items/, for example
    shop/items/burberry-trench-coat/
        info.txt        title, designer, price, size ... (see shop/README.md)
        1.jpg 2.jpg ... photos, the first one is the cover

Runs in the "Update shop" workflow (.github/workflows/shop.yml):
  1. new photos are rotated upright, cropped to 4:5 and saved as WebP in
     site/shop/<item>/ (1080 px wide + a 540 px grid version); the uploaded
     originals are then removed, like on the home page,
  2. tools/stripe_sync.py makes the Stripe payment links and marks sold pieces,
  3. this script writes every shop page: the grid, one page per piece,
     shipping / terms / privacy, the thank-you page and the shop sitemap.

Local preview:  python3 tools/build_shop.py  (then open site/shop/index.html)
"""
import argparse
import datetime
import html
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE_URL = "https://momokovintage.com"
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}
SOLD_VISIBLE_DAYS = 30

CONDITION = {
    "new": ("új, címkés", "new with tags", "Soha nem hordott darab.", "Never worn."),
    "excellent": ("kiváló", "excellent", "Alig hordott, kopás nem látszik rajta.", "Barely worn, no visible wear."),
    "great": ("nagyon jó", "great", "Hordott, de szép állapotú; apró jelek a leírásban.", "Worn with care; any small marks are listed."),
    "good": ("jó", "good", "Látható használati nyomok, mind lefotózva.", "Visible signs of wear, all photographed."),
}
GENDER = {"women": ("női", "women"), "men": ("férfi", "men"), "unisex": ("uniszex", "unisex")}
MEASURE_EN_HU = {
    "pit to pit": "hónaljtól hónaljig", "chest": "mellbőség", "length": "hossz", "shoulders": "váll",
    "sleeve": "ujjhossz", "waist": "derék", "hips": "csípő", "rise": "ülésmagasság",
    "inseam": "belső szárhossz", "leg opening": "szárbőség", "heel": "sarokmagasság",
    "insole": "talphossz", "width": "szélesség", "height": "magasság", "depth": "mélység", "strap": "pánt",
}


def esc(s):
    return html.escape(str(s or ""), quote=True)


def esc2(s):
    """Plain text for a data-en attribute: shop.js puts that value back as HTML."""
    return esc(esc(s))


def read_kv(path):
    data = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        data[k.strip().lower()] = v.split("  #")[0].strip()
    return data


def write_kv(path, updates):
    """Set keys in an info.txt / settings.txt without touching the rest of the file."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    done = set()
    for i, line in enumerate(lines):
        if ":" in line and not line.lstrip().startswith("#"):
            k = line.split(":", 1)[0].strip().lower()
            if k in updates:
                lines[i] = "%s: %s" % (k, updates[k])
                done.add(k)
    for k, v in updates.items():
        if k not in done:
            lines.append("%s: %s" % (k, v))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def slug_ok(name):
    return re.fullmatch(r"[a-z0-9][a-z0-9-]{1,80}", name) is not None


# ---------------------------------------------------------------- photos
def process_photos(items_dir, out_dir):
    from PIL import Image, ImageOps
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    changed = False
    for folder in sorted(p for p in items_dir.iterdir() if p.is_dir()):
        photos = sorted((p for p in folder.iterdir() if p.suffix.lower() in PHOTO_EXTS),
                        key=lambda p: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", p.name.lower())])
        if not photos:
            continue
        if not slug_ok(folder.name):
            print("Skipping %s: folder names may only use a-z, 0-9 and -" % folder.name)
            continue
        dest = out_dir / folder.name
        if dest.exists():
            shutil.rmtree(dest)  # a new upload replaces the whole photo set
        dest.mkdir(parents=True)
        for n, p in enumerate(photos, 1):
            im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
            w, h = im.size
            tw = round(h * 4 / 5)
            if tw < w:
                im = im.crop(((w - tw) // 2, 0, (w - tw) // 2 + tw, h))
            else:
                th = round(w * 5 / 4)
                im = im.crop((0, (h - th) // 2, w, (h - th) // 2 + th))
            im.resize((1080, 1350), Image.LANCZOS).save(dest / ("%d.webp" % n), "WEBP", quality=80, method=6)
            if n <= 2:
                im.resize((540, 675), Image.LANCZOS).save(dest / ("%d-s.webp" % n), "WEBP", quality=78, method=6)
            p.unlink()
        info = folder / "info.txt"
        if info.exists() and not read_kv(info).get("added"):
            write_kv(info, {"added": datetime.date.today().isoformat()})
        print("Photos ready: %s (%d)" % (folder.name, len(photos)))
        changed = True
    return changed


# ---------------------------------------------------------------- data
def load_items(items_dir, out_dir):
    items = []
    for folder in sorted(p for p in items_dir.iterdir() if p.is_dir()):
        d = read_kv(folder / "info.txt")
        if not d.get("title") or not d.get("price"):
            print("Skipping %s: info.txt needs at least title and price" % folder.name)
            continue
        pics = sorted((out_dir / folder.name).glob("[0-9]*.webp"), key=lambda p: p.name)
        pics = [p for p in pics if re.fullmatch(r"\d+\.webp", p.name)]
        pics.sort(key=lambda p: int(p.stem))
        if not pics:
            print("Skipping %s: no photos yet" % folder.name)
            continue
        try:
            price = int(float(d["price"].replace("€", "").replace(",", ".").strip()))
        except ValueError:
            print("Skipping %s: price must be a number in euro" % folder.name)
            continue
        cond = d.get("condition", "great").lower()
        g = d.get("gender", "women").lower()
        items.append({
            "slug": folder.name,
            "title": d["title"],
            "designer": d.get("designer", ""),
            "price": price,
            "gender": g if g in GENDER else "unisex",
            "category": d.get("category", "").lower(),
            "size": d.get("size", ""),
            "condition": cond if cond in CONDITION else "great",
            "measurements": d.get("measurements", ""),
            "material": d.get("material", ""),
            "era": d.get("era", ""),
            "text_hu": d.get("text_hu", "") or d.get("text_en", ""),
            "text_en": d.get("text_en", "") or d.get("text_hu", ""),
            "flaws": d.get("flaws", ""),
            "stripe": d.get("stripe", ""),
            "sold": d.get("sold", "no").lower() in ("yes", "igen", "true", "1"),
            "sold_date": d.get("sold_date", ""),
            "added": d.get("added", "") or "2000-01-01",
            "pics": [p.name for p in pics],
        })
    items.sort(key=lambda i: (i["sold"], [-ord(c) for c in i["added"]]))
    return items


def parse_measurements(s):
    rows = []
    for part in re.split(r"[·,;|]", s):
        m = re.match(r"\s*([a-zA-Z áéíóöőúüűÁÉÍÓÖŐÚÜŰ-]+?)\s*[:=]?\s*([\d.,]+)\s*(cm)?\s*$", part)
        if m:
            label = m.group(1).strip().lower()
            rows.append((MEASURE_EN_HU.get(label, label), label, m.group(2).replace(",", ".")))
    return rows


# ---------------------------------------------------------------- page parts
def head(depth, title_hu, title_en, desc, canonical, extra=""):
    up = "../" * depth
    return """<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#F6F3EC">
<title>{th}</title>
<meta name="title-hu" content="{th}">
<meta name="title-en" content="{te}">
<meta name="description" content="{d}">
<link rel="canonical" href="{c}">
<link rel="icon" type="image/png" href="{up}img/logo.png">
<meta property="og:site_name" content="Momoko Vintage">
<meta property="og:title" content="{te}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{c}">
{extra}<link rel="stylesheet" href="{up}shop/shop.css">
</head>
<body>
<header class="top">
  <div class="wrap">
    <a href="{up}" aria-label="Momoko Vintage, főoldal" data-en-label="Momoko Vintage, home"><span class="logo top-logo" aria-hidden="true"></span></a>
    <a class="top-mid" href="{up}shop/" data-en="online shop">online bolt</a>
    <button class="lang" type="button" id="langBtn" aria-label="Switch to English">en</button>
  </div>
</header>
""".format(th=esc(title_hu), te=esc(title_en), d=esc(desc), c=esc(canonical), up=up, extra=extra)


def foot(depth):
    up = "../" * depth
    return """<footer class="dark">
  <div class="wrap">
    <p class="contact">
      <a href="tel:+36306170265">+36 30 617 0265</a>
      <a class="js-mail" data-u="info" data-d="momokovintage.com" href="#">info [at] momokovintage.com</a>
    </p>
    <ul class="f-links">
      <li><a href="{up}shop/info/#shipping" data-en="shipping &amp; returns">szállítás és visszaküldés</a></li>
      <li><a href="{up}shop/info/#terms" data-en="terms">ászf</a></li>
      <li><a href="{up}shop/info/#privacy" data-en="privacy">adatvédelem</a></li>
      <li><a href="{up}shop/info/#imprint" data-en="imprint">impresszum</a></li>
      <li><a href="https://www.instagram.com/momoko_vintage/" target="_blank" rel="noopener">instagram</a></li>
    </ul>
    <div class="f-bottom">
      <p data-en="1088 budapest, krúdy st. 9, palace quarter">1088 budapest, krúdy utca 9, palotanegyed</p>
      <p>© <span id="year"></span> momoko vintage</p>
    </div>
  </div>
</footer>
<script src="{up}shop/shop.js"></script>
</body>
</html>
""".format(up=up)


def price_txt(p):
    return "€%s" % format(p, ",").replace(",", " ")


def card(i, depth):
    up = "../" * depth
    base = "%sshop/%s/" % (up, i["slug"])
    alt = ' <img class="alt" src="%s2-s.webp" alt="" loading="lazy" decoding="async">' % base if "2.webp" in i["pics"] else ""
    tag = ('<span class="tag" data-en="sold">eladva</span>' if i["sold"]
           else ('<span class="tag" data-en="new">új</span>' if is_new(i) else ""))
    return """<li class="card{sold}" data-g="{g}" data-c="{c}"><a href="{href}">
  <div class="ph">{tag}<img src="{base}1-s.webp" alt="{alt_t}" loading="lazy" decoding="async" width="540" height="675">{alt}</div>
  <div class="meta"><span class="des">{des}</span><span>{t}</span>
  <span class="row"><span class="size">{size}</span><span class="price">{price}</span></span></div>
</a></li>""".format(sold=" sold" if i["sold"] else "", g=esc(i["gender"]), c=esc(i["category"]),
                    href=base, base=base, tag=tag, alt=alt, alt_t=esc(i["designer"] + " " + i["title"]),
                    des=esc(i["designer"] or "vintage"), t=esc(i["title"]), size=esc(i["size"]),
                    price=price_txt(i["price"]))


def is_new(i):
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(i["added"])).days <= 7
    except ValueError:
        return False


def visible_in_grid(i):
    if not i["sold"]:
        return True
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(i["sold_date"])).days <= SOLD_VISIBLE_DAYS
    except ValueError:
        return True


# ---------------------------------------------------------------- pages
def page_grid(items, s):
    shown = [i for i in items if visible_in_grid(i)]
    cats = []
    for i in shown:
        if i["category"] and i["category"] not in cats:
            cats.append(i["category"])
    cat_hu = {k.strip(): v.strip() for k, v in (x.split("=") for x in s.get("categories_hu", "").split(",") if "=" in x)}
    gbtn = ['<button class="f-btn" type="button" data-k="g" data-v="all" aria-pressed="true" data-en="all">mind</button>']
    for g in ("women", "men"):
        if any(i["gender"] in (g, "unisex") for i in shown):
            gbtn.append('<button class="f-btn" type="button" data-k="g" data-v="%s" aria-pressed="false" data-en="%s">%s</button>'
                        % (g, GENDER[g][1], GENDER[g][0]))
    cbtn = ['<button class="f-btn" type="button" data-k="c" data-v="all" aria-pressed="true" data-en="everything">minden</button>']
    for c in cats:
        cbtn.append('<button class="f-btn" type="button" data-k="c" data-v="%s" aria-pressed="false" data-en="%s">%s</button>'
                    % (esc(c), esc2(c), esc(cat_hu.get(c, c))))
    body = head(1, "Online bolt – Momoko Vintage", "Online shop – Momoko Vintage",
                "Válogatott vintage és designer darabok online, a budapesti Momoko Vintage boltból. Curated vintage and designer pieces from our Budapest boutique.",
                SITE_URL + "/shop/")
    body += """<main class="shop-main">
<section class="head"><div class="wrap">
  <h1 data-en="online shop">online bolt</h1>
  <p data-en="every piece is one of a kind, picked in our budapest store. shipped across the eu.">minden darab egyedi, a budapesti boltunkból. szállítás az egész eu-ba.</p>
</div></section>
<div class="wrap">
  <nav class="filters" aria-label="szűrés" data-en-label="filter">%s</nav>
  %s
  <p class="count" id="count" aria-live="polite"></p>
  <ul class="grid" id="grid">
%s
  </ul>
  <p class="empty" id="empty" hidden data-en="nothing here right now. new pieces every monday.">most nincs itt semmi. új darabok minden hétfőn.</p>
</div>
</main>
""" % ("".join(gbtn), ('<nav class="filters" aria-label="kategória" data-en-label="category">%s</nav>' % "".join(cbtn)) if len(cats) > 1 else "",
       "\n".join(card(i, 1) for i in shown))
    return body + foot(1)


def page_item(i, items, s):
    name = (i["designer"] + " " + i["title"]).strip()
    cond = CONDITION[i["condition"]]
    url = "%s/shop/%s/" % (SITE_URL, i["slug"])
    ld = {
        "@context": "https://schema.org", "@type": "Product", "name": name,
        "image": ["%s/shop/%s/%s" % (SITE_URL, i["slug"], p) for p in i["pics"][:4]],
        "description": i["text_en"] or name, "brand": {"@type": "Brand", "name": i["designer"] or "Vintage"},
        "itemCondition": "https://schema.org/NewCondition" if i["condition"] == "new" else "https://schema.org/UsedCondition",
        "offers": {"@type": "Offer", "url": url, "priceCurrency": "EUR", "price": str(i["price"]),
                   "availability": "https://schema.org/SoldOut" if i["sold"] else "https://schema.org/InStock",
                   "seller": {"@type": "Organization", "name": "Momoko Vintage"}},
    }
    extra = '<meta property="og:type" content="product">\n<meta property="og:image" content="%s/shop/%s/1.webp">\n<script type="application/ld+json">%s</script>\n' % (
        SITE_URL, i["slug"], json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"))
    body = head(2, "%s – Momoko Vintage" % name, "%s – Momoko Vintage" % name,
                (i["text_en"] or name)[:155], url, extra)
    pics = "\n".join('<figure><img src="%s" alt="%s, %d. fotó" %s width="1080" height="1350"></figure>' % (
        p, esc(name), n, 'fetchpriority="high"' if n == 1 else 'loading="lazy" decoding="async"')
        for n, p in enumerate(i["pics"], 1))
    facts = []
    if i["size"]:
        facts.append(("méret", "size", i["size"]))
    facts.append(("állapot", "condition", None))
    if i["era"]:
        facts.append(("korszak", "era", i["era"]))
    if i["material"]:
        facts.append(("anyag", "material", i["material"]))
    fact_html = "".join(
        '<li><span data-en="%s">%s</span><span%s>%s</span></li>' % (
            en, hu, ' data-en="%s"' % esc2(cond[1]) if v is None else "", esc(cond[0] if v is None else v))
        for hu, en, v in facts)
    rows = parse_measurements(i["measurements"])
    meas = ""
    if rows:
        meas = """<details open><summary data-en="measurements (laid flat)">méretek (kiterítve)</summary><div class="body">
<table>%s</table><p style="margin-top:.75rem" data-en="compare with a piece you own; vintage sizes run small.">hasonlítsd össze egy saját ruhádéval; a vintage méretek kisebbek.</p></div></details>""" % "".join(
            '<tr><td data-en="%s">%s</td><td>%s cm</td></tr>' % (esc2(en), esc(hu), esc(v)) for hu, en, v in rows)
    flaws = ('<p><strong data-en="notes:">megjegyzés:</strong> %s</p>' % esc(i["flaws"])) if i["flaws"] else ""
    ship_eu = s.get("shipping_eu", "25")
    if i["sold"] or not i["stripe"]:
        buy = '<span class="buy" aria-disabled="true" data-en="%s">%s</span>' % (
            ("sold", "eladva") if i["sold"] else ("coming soon", "hamarosan"))
    else:
        buy = '<a class="buy" href="%s" rel="noopener" data-en="buy now">megveszem</a>' % esc(i["stripe"])
    related = [x for x in items if x["slug"] != i["slug"] and not x["sold"] and
               (x["category"] == i["category"] or x["gender"] == i["gender"])]
    related += [x for x in items if x["slug"] != i["slug"] and not x["sold"] and x not in related]
    related = related[:4]
    more = ""
    if related:
        more = """<section class="more white"><div class="wrap"><h2 data-en="you may also like">ez is tetszhet</h2>
<ul class="grid">%s</ul></div></section>""" % "\n".join(card(x, 2) for x in related)
    body += """<main>
<div class="wrap">
  <p class="crumb"><a href="../" data-en="online shop">online bolt</a> / {des}</p>
  <div class="prod">
    <div>
      <div class="pics" id="pics" tabindex="0" aria-label="fotók" data-en-label="photos">
{pics}
      </div>
      <p class="pic-count" id="picCount" aria-live="polite"></p>
    </div>
    <div class="info">
      <p class="des">{des}</p>
      <h1>{title}</h1>
      <p class="price">{price}<small data-en="incl. vat · eu delivery €{ship} · free pickup in the store">áfával · eu szállítás €{ship} · személyes átvétel a boltban ingyen</small></p>
      <ul class="facts">{facts}</ul>
      {buy}
      <p class="pay" data-en="secure checkout by stripe · card, apple pay, google pay">biztonságos fizetés: stripe · kártya, apple pay, google pay</p>
      <div class="acc">
        <details{open_desc}><summary data-en="description">leírás</summary><div class="body"><p data-en="{text_en}">{text_hu}</p>{flaws}<p data-en="{cond_en}">{cond_hu}</p></div></details>
        {meas}
        <details><summary data-en="shipping &amp; returns">szállítás és visszaküldés</summary><div class="body">
          <p data-en="shipped tracked from budapest within 2 business days. eu delivery €{ship}, 3–6 business days. or pick it up free in the store.">nyomkövetéssel küldjük budapestről 2 munkanapon belül. eu szállítás €{ship}, 3–6 munkanap. vagy vedd át ingyen a boltban.</p>
          <p data-en="14-day return for eu buyers. &lt;a href=&quot;../info/#shipping&quot;&gt;details&lt;/a&gt;">14 napos elállási jog az eu-ban. &lt;a href="../info/#shipping"&gt;részletek&lt;/a&gt;</p>
        </div></details>
        <details><summary data-en="authenticity">eredetiség</summary><div class="body">
          <p data-en="every piece is checked by hand in our store: labels, stitching, hardware and materials. we only sell what we can stand behind.">minden darabot kézzel ellenőrzünk a boltban: címkék, varrás, fémrészek, anyag. csak olyat árulunk, amiért kiállunk.</p>
        </div></details>
      </div>
      <p class="visit" data-en="want to try it on? it's waiting in the store: krúdy st. 9, budapest. questions: &lt;a class=&quot;js-mail&quot; data-u=&quot;info&quot; data-d=&quot;momokovintage.com&quot; href=&quot;#&quot;&gt;info [at] momokovintage.com&lt;/a&gt;">felpróbálnád? a boltban vár: krúdy utca 9, budapest. kérdésed van: &lt;a class="js-mail" data-u="info" data-d="momokovintage.com" href="#"&gt;info [at] momokovintage.com&lt;/a&gt;</p>
    </div>
  </div>
</div>
{more}
</main>
""".format(des=esc(i["designer"] or "vintage"), pics=pics, title=esc(i["title"]), price=price_txt(i["price"]),
           ship=esc(ship_eu), facts=fact_html, buy=buy, open_desc=" open" if not rows else "",
           text_en=esc2(i["text_en"]), text_hu=esc(i["text_hu"]), flaws=flaws,
           cond_en=esc2("condition: %s. %s" % (cond[1], cond[3])), cond_hu=esc("állapot: %s. %s" % (cond[0], cond[2])),
           meas=meas, more=more)
    # the visit line holds markup in its data-en; unescape the visible Hungarian copy too
    body = body.replace("&lt;a class=\"js-mail\" data-u=\"info\" data-d=\"momokovintage.com\" href=\"#\"&gt;info [at] momokovintage.com&lt;/a&gt;</p>",
                        '<a class="js-mail" data-u="info" data-d="momokovintage.com" href="#">info [at] momokovintage.com</a></p>')
    body = body.replace('&lt;a href="../info/#shipping"&gt;részletek&lt;/a&gt;</p>', '<a href="../info/#shipping">részletek</a></p>')
    return body + foot(2)


def page_info(s):
    co = {k: esc(s.get(k, "")) for k in ("company", "address", "tax_number", "eu_vat", "registration", "registry_court", "email", "phone", "shipping_eu", "conciliation_board")}
    missing = [k for k in ("company", "tax_number", "registration") if not s.get(k)]
    if missing:
        print("WARNING: shop/settings.txt is missing %s; the imprint shows a placeholder." % ", ".join(missing))
    def v(k):
        return co[k] or "<em>[" + k + "]</em>"
    body = head(2, "Vásárlási információk – Momoko Vintage", "Shop information – Momoko Vintage",
                "Szállítás, visszaküldés, ÁSZF, adatvédelem és impresszum. Shipping, returns, terms, privacy and imprint.",
                SITE_URL + "/shop/info/")
    body += """<main class="page"><div class="wrap"><div class="inner">
<h1 data-en="shop information">vásárlási információk</h1>
<ul class="toc"><li><a href="#shipping" data-en="shipping &amp; returns">szállítás és visszaküldés</a></li><li><a href="#terms" data-en="terms">ászf</a></li><li><a href="#privacy" data-en="privacy">adatvédelem</a></li><li><a href="#imprint" data-en="imprint">impresszum</a></li></ul>

<h2 id="shipping" data-en="shipping">szállítás</h2>
<p data-en="we ship tracked from budapest within 2 business days of payment. delivery across the eu costs €{ship} and takes 3–6 business days. you can also choose free pickup in our store (krúdy st. 9, budapest) at checkout. we currently ship to eu countries only.">a fizetéstől számított 2 munkanapon belül nyomkövetéssel adjuk fel budapestről. az eu-n belüli szállítás díja €{ship}, 3–6 munkanap. a fizetésnél ingyenes személyes átvételt is választhatsz a boltban (krúdy utca 9, budapest). jelenleg az eu országaiba szállítunk.</p>
<h2 data-en="returns (14-day right of withdrawal)">visszaküldés (14 napos elállási jog)</h2>
<p data-en="as an eu consumer you can withdraw from the purchase within 14 days of delivery without giving a reason. email us at {email} with your order details; send the piece back unworn, with its tag, within 14 days of telling us. return shipping is paid by the buyer. we refund the price and the original standard shipping within 14 days of receiving the piece, to the original payment method.">eu-s fogyasztóként a kézhezvételtől számított 14 napon belül indoklás nélkül elállhatsz a vásárlástól. írj nekünk a {email} címre a rendelés adataival; a darabot viseletlenül, címkével együtt küldd vissza a jelzésedtől számított 14 napon belül. a visszaküldés költsége a vásárlót terheli. a vételárat és az eredeti szállítási díjat a darab beérkezésétől számított 14 napon belül visszautaljuk az eredeti fizetési módra.</p>
<p data-en="if a piece does not match its description, tell us within 3 days of delivery and we cover the return.">ha a darab nem felel meg a leírásnak, a kézhezvételtől számított 3 napon belül jelezd, és a visszaküldést mi álljuk.</p>
<h2 data-en="payment">fizetés</h2>
<p data-en="payments are handled by stripe (card, apple pay, google pay). we never see or store your card details. prices are in euro and include vat; stripe may show the amount in your own currency.">a fizetést a stripe kezeli (bankkártya, apple pay, google pay). a kártyaadataidat mi soha nem látjuk és nem tároljuk. az árak euróban, áfával értendők; a stripe a saját pénznemedben is mutathatja az összeget.</p>

<h2 id="terms" data-en="terms of sale (summary)">általános szerződési feltételek (összefoglaló)</h2>
<ul>
<li data-en="the seller is {company} (details in the imprint below).">az eladó: {company} (adatai lent, az impresszumban).</li>
<li data-en="every piece is second-hand and one of a kind; its condition is described and photographed on its page. the contract is made when payment is completed.">minden darab használt és egyedi; állapotát a termékoldalon leírjuk és lefotózzuk. a szerződés a fizetés teljesítésével jön létre.</li>
<li data-en="if a piece sells in the store before your payment completes, we refund you in full within 2 business days.">ha egy darab a fizetésed előtt a boltban elkel, 2 munkanapon belül a teljes összeget visszautaljuk.</li>
<li data-en="complaints: {email}. we answer within 30 days. consumers in hungary may turn to the {board}; eu consumers may also use the eu online dispute resolution platform.">panaszkezelés: {email}. 30 napon belül válaszolunk. magyarországi fogyasztók a {board} fordulhatnak; eu-s fogyasztók az eu online vitarendezési platformját is igénybe vehetik.</li>
</ul>

<h2 id="privacy" data-en="privacy">adatvédelem</h2>
<p data-en="for an order we process your name, email, phone and delivery address, only to fulfil and ship it and to meet our accounting duties (kept for 8 years under hungarian accounting law). payment data is processed by stripe payments europe ltd. parcels are delivered by magyar posta. this site uses no tracking cookies. you can ask to see, correct or delete your data at {email}, and you may complain to the hungarian data protection authority (naih).">rendelésnél a neved, e-mail címed, telefonszámod és szállítási címed kezeljük, kizárólag a teljesítéshez és a számviteli kötelezettségeink miatt (a számviteli törvény szerint 8 évig). a fizetési adatokat a stripe payments europe ltd. kezeli. a csomagokat a magyar posta kézbesíti. az oldal nem használ követő sütiket. adataidba betekinthetsz, kérheted a javításukat vagy törlésüket a {email} címen, panasszal a naih-hoz fordulhatsz.</p>

<h2 id="imprint" data-en="imprint">impresszum</h2>
<p><strong>{company_v}</strong><br>{address_v}<br><span data-en="tax number">adószám</span>: {tax_v} · <span data-en="eu vat">közösségi adószám</span>: {euvat_v}<br><span data-en="registration">cégjegyzékszám / nyilvántartási szám</span>: {reg_v}<br>e-mail: {email} · <span data-en="phone">telefon</span>: {phone}<br><span data-en="hosting">tárhely</span>: GitHub, Inc., 88 Colin P. Kelly Jr. St, San Francisco, CA 94107, USA</p>
</div></div></main>
""".format(ship=co["shipping_eu"] or "25", email=co["email"] or "info@momokovintage.com",
           company=co["company"] or "Momoko Vintage", board=co["conciliation_board"] or "budapesti békéltető testülethez",
           company_v=v("company"), address_v=co["address"] or "1088 Budapest, Krúdy utca 9.",
           tax_v=v("tax_number"), euvat_v=v("eu_vat"), reg_v=v("registration"), phone=co["phone"] or "+36 30 617 0265")
    return body + foot(2)


def page_thanks():
    body = head(2, "Köszönjük! – Momoko Vintage", "Thank you! – Momoko Vintage", "Köszönjük a vásárlást.", SITE_URL + "/shop/thanks/",
                '<meta name="robots" content="noindex">\n')
    body += """<main class="page"><div class="wrap"><div class="inner center">
<h1 data-en="thank you!">köszönjük!</h1>
<p class="lead" data-en="your payment went through and stripe has emailed you a receipt. we pack your piece within 2 business days and send the tracking number by email.">a fizetés sikerült, a nyugtát a stripe elküldte e-mailben. 2 munkanapon belül becsomagoljuk a darabot, és e-mailben küldjük a nyomkövetési számot.</p>
<p class="lead" data-en="chose store pickup? we'll email you when it's ready.">személyes átvételt választottál? e-mailben szólunk, ha mehetsz érte.</p>
<p style="margin-top:2rem"><a class="btn" href="../" data-en="back to the shop">vissza a boltba</a></p>
</div></div></main>
"""
    return body + foot(2)


def sitemap(items):
    urls = [SITE_URL + "/shop/", SITE_URL + "/shop/info/"] + ["%s/shop/%s/" % (SITE_URL, i["slug"]) for i in items if not i["sold"]]
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(
        "  <url><loc>%s</loc></url>" % esc(u) for u in urls)


def build(items_dir, out_dir, settings_path):
    s = read_kv(settings_path)
    items = load_items(items_dir, out_dir)
    known = {i["slug"] for i in items}
    for d in out_dir.iterdir():  # photos of deleted items
        if d.is_dir() and d.name not in known | {"info", "thanks"} and slug_ok(d.name) and not (items_dir / d.name).exists():
            shutil.rmtree(d)
            print("Removed %s (its folder is gone)" % d.name)
    (out_dir / "index.html").write_text(page_grid(items, s), encoding="utf-8")
    for i in items:
        (out_dir / i["slug"] / "index.html").write_text(page_item(i, items, s), encoding="utf-8")
    for name, page in (("info", page_info(s)), ("thanks", page_thanks())):
        (out_dir / name).mkdir(exist_ok=True)
        (out_dir / name / "index.html").write_text(page, encoding="utf-8")
    (out_dir / "sitemap.xml").write_text(sitemap(items), encoding="utf-8")
    print("Shop built: %d pieces (%d available)" % (len(items), sum(not i["sold"] for i in items)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default=str(ROOT / "shop" / "items"))
    ap.add_argument("--out", default=str(ROOT / "site" / "shop"))
    ap.add_argument("--settings", default=str(ROOT / "shop" / "settings.txt"))
    ap.add_argument("--photos-only", action="store_true")
    a = ap.parse_args()
    items_dir, out_dir = pathlib.Path(a.items), pathlib.Path(a.out)
    items_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    process_photos(items_dir, out_dir)
    if not a.photos_only:
        build(items_dir, out_dir, pathlib.Path(a.settings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
