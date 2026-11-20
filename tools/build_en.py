#!/usr/bin/env python3
"""Build the English page (site/en/index.html) from the Hungarian one.

site/index.html stays the only file anyone edits. Every element with a
data-en attribute gets its English text written straight into the HTML,
with the Hungarian kept in data-hu, so search engines and visitors get a
real English page at https://momokovintage.com/en/ and the hu/en button
still switches instantly.

Runs in the "Publish website" workflow before upload. To preview locally:
    python3 tools/build_en.py
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site" / "index.html"
OUT = ROOT / "site" / "en" / "index.html"

HEAD = [
    ('<html lang="hu">', '<html lang="en">'),
    ('<title>Momoko Vintage – vintage és designer second hand bolt Budapesten</title>',
     '<title>Momoko Vintage – vintage and designer secondhand shop in Budapest</title>'),
    ('<meta name="description" content="Válogatott vintage és modern klasszikusok: ruhák, cipők, táskák és kiegészítők a Palotanegyedben. Budapest, Krúdy utca 9. Minden hétfőn heti újratöltés.">',
     '<meta name="description" content="Curated vintage and modern classics: clothing, shoes, bags and accessories in Budapest\'s Palace Quarter, Krúdy utca 9. Fresh pieces every Monday.">'),
    ('<link rel="canonical" href="https://momokovintage.com/">',
     '<link rel="canonical" href="https://momokovintage.com/en/">'),
    ('<meta property="og:url" content="https://momokovintage.com/">',
     '<meta property="og:url" content="https://momokovintage.com/en/">'),
    ('<meta property="og:locale" content="hu_HU">\n<meta property="og:locale:alternate" content="en_GB">',
     '<meta property="og:locale" content="en_GB">\n<meta property="og:locale:alternate" content="hu_HU">'),
    ('<meta property="og:title" content="Momoko Vintage – vintage és designer second hand bolt Budapesten">',
     '<meta property="og:title" content="Momoko Vintage – vintage and designer secondhand shop in Budapest">'),
    ('<meta property="og:description" content="Válogatott vintage és modern klasszikusok a Palotanegyedben. Budapest, Krúdy utca 9. Minden hétfőn heti újratöltés.">',
     '<meta property="og:description" content="Curated vintage and modern classics in Budapest\'s Palace Quarter, Krúdy utca 9. Fresh pieces every Monday.">'),
    ('<meta property="og:image:alt" content="Momoko Vintage logó és egy vintage cipő">',
     '<meta property="og:image:alt" content="Momoko Vintage logo and a vintage shoe">'),
    ('aria-label="Switch to English">en</button>', 'aria-label="Váltás magyarra">hu</button>'),
    ("img.alt = 'Momoko Vintage, válogatott vintage darab ' + (i + 1);",
     "img.alt = (document.documentElement.lang === 'en' ? 'Momoko Vintage, curated vintage piece ' : 'Momoko Vintage, válogatott vintage darab ') + (i + 1);"),
]

OPEN_TAG = re.compile(r'<([a-zA-Z][\w-]*)\b([^>]*?)\sdata-en="([^"]*)"([^>]*)>')
LABEL = re.compile(r'aria-label="([^"]*)"(\s+)data-en-label="([^"]*)"')


def close_of(text, tag, start):
    """Index of the </tag> that closes the element whose content starts at start."""
    depth = 1
    pat = re.compile(r'<(/?)%s\b[^>]*>' % re.escape(tag))
    for m in pat.finditer(text, start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return m.start()
    raise ValueError("no closing </%s>" % tag)


def swap_text(text):
    out, pos, count = [], 0, 0
    for m in OPEN_TAG.finditer(text):
        if m.start() < pos:
            sys.exit("nested data-en elements are not supported")
        tag, before, en, after = m.groups()
        inner_start = m.end()
        inner_end = close_of(text, tag, inner_start)
        hu = text[inner_start:inner_end]
        opening = '<%s%s data-en="%s" data-hu="%s"%s>' % (
            tag, before, en, html.escape(hu, quote=True), after)
        out += [text[pos:m.start()], opening, html.unescape(en)]
        pos = inner_end
        count += 1
    out.append(text[pos:])
    return "".join(out), count


def swap_labels(text):
    return LABEL.subn(
        lambda m: 'aria-label="%s"%sdata-en-label="%s" data-hu-label="%s"' % (
            m.group(3), m.group(2), m.group(3), m.group(1)), text)


def main():
    text = SRC.read_text(encoding="utf-8")
    for old, new in HEAD:
        if text.count(old) != 1:
            sys.exit("build_en: expected exactly one match for: %s" % old[:70])
        text = text.replace(old, new)
    text, n_text = swap_text(text)
    text, n_label = swap_labels(text)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print("built %s (%d texts, %d labels)" % (OUT.relative_to(ROOT), n_text, n_label))


if __name__ == "__main__":
    main()
