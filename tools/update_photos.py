"""Turn new photos in /incoming into the website's photo pool.

Runs automatically on GitHub (see .github/workflows/photos.yml) whenever
photos are uploaded to the "incoming" folder:
  1. each photo is rotated upright, cropped to 4:5 portrait (the gallery frame) and resized,
  2. saved as a small WebP file in site/img,
  3. the photo list in site/index.html is replaced with the new batch,
  4. the original uploads are removed.
"""
import datetime
import pathlib
import re
import sys

from PIL import Image, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
INCOMING = ROOT / "incoming"
IMG = ROOT / "site" / "img"
HTML = ROOT / "site" / "index.html"
EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}
WIDTH = 1080


def prepare(path: pathlib.Path) -> Image.Image:
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    w, h = im.size
    target_w = round(h * 4 / 5)
    if target_w < w:  # wider than 4:5: crop the sides
        left = (w - target_w) // 2
        im = im.crop((left, 0, left + target_w, h))
    else:  # taller than 4:5: crop top and bottom
        target_h = round(w * 5 / 4)
        top = (h - target_h) // 2
        im = im.crop((0, top, w, top + target_h))
    return im.resize((WIDTH, round(WIDTH * 5 / 4)), Image.LANCZOS)


def main() -> int:
    files = sorted(p for p in INCOMING.iterdir() if p.suffix.lower() in EXTS)
    if not files:
        print("No new photos in /incoming, nothing to do.")
        return 0

    now = datetime.datetime.now()
    today = now.date()
    stamp = now.strftime("%Y%m%d%H%M")
    new_names = []
    for i, f in enumerate(files, 1):
        name = f"p-{stamp}-{i:02d}.webp"
        prepare(f).save(IMG / name, "WEBP", quality=72, method=6)
        new_names.append(name)
        print(f"{f.name} -> {name}")

    # remove the previous batch of photos (only pool photos, never logo or texture)
    pool_photo = re.compile(r"^p(\d{2}|-\d{8,12}-\d{2})\.webp$")
    for old in IMG.iterdir():
        if pool_photo.match(old.name) and old.name not in new_names:
            old.unlink()

    pool = ",\n".join(f"    '{n}'" for n in new_names)
    block = (
        "/* POOL:START */\n"
        "    var POOL = [\n"
        f"{pool}\n"
        "    ];\n"
        f"    var START = Date.UTC({today.year}, {today.month - 1}, {today.day});\n"
        "    /* POOL:END */"
    )
    html = HTML.read_text(encoding="utf-8")
    html, count = re.subn(r"/\* POOL:START \*/.*?/\* POOL:END \*/", block, html, flags=re.S)
    if count != 1:
        print("Could not find the photo list in site/index.html", file=sys.stderr)
        return 1
    HTML.write_text(html, encoding="utf-8")

    for f in files:
        f.unlink()
    print(f"Photo pool updated with {len(new_names)} photos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
