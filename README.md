# momokovintage.com

A Momoko Vintage egyoldalas weboldala. Netlify-on fut, minden változás ebből a tárolóból kerül ki automatikusan.

## Heti rutin (kb. 5–10 perc)

1. Nyisd meg a tárolót a github.com-on, és lépj be az **incoming** mappába.
2. **Add file → Upload files**, húzd be az új fotókat, majd **Commit changes**.
3. Kész. Pár perc múlva az új fotók megjelennek az oldalon, és 3 naponta cserélődnek.

Automatikusan, külön munka nélkül frissül:
- a „Most nyitva / Zárva” jelzés (budapesti idő szerint),
- a hétfői újratöltés visszaszámlálója,
- a fotók 3 napos cseréje (a fotók lapozhatók is: nyilak, pöttyök vagy húzás).

## Mappák

- `site/` – maga a weboldal (`index.html`, képek). Ez kerül ki a Netlify-ra.
- `incoming/` – ide kell feltölteni az új fotókat.
- `tools/update_photos.py` – a fotókat tömörítő és beillesztő program.
- `.github/workflows/photos.yml` – elindítja a programot, amikor új fotó érkezik.

## Nyitvatartás módosítása

A nyitvatartás két helyen szerepel a `site/index.html` fájlban: a táblázatban és a `HOURS` listában (ez adja a „Most nyitva” jelzést). Szövegváltozásnál a legegyszerűbb szólni Claude-nak.
