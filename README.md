# momokovintage.com

A Momoko Vintage egyoldalas weboldala. Ingyenesen a **GitHub Pages** szolgálja ki. Ebben a tárolóban minden változás egy-két percen belül magától kikerül az élő oldalra; külön feltöltésre vagy más szolgáltatásra nincs szükség.

## Heti rutin: új fotók (kb. 5 perc)

1. Nyisd meg a tárolót a github.com-on, és lépj be az **incoming** mappába.
2. **Add file → Upload files**, húzd be az új fotókat, majd **Commit changes**.
3. Kész. Kb. 2 perc múlva az új fotók kint vannak az oldalon, és az előző sorozat lekerül.

Álló (portré) fotókat tölts fel. A rendszer 2:3 arányra vágja őket középre igazítva, az oldalon pedig 4:5-ös keretben jelennek meg. Fekvő vagy négyzetes képnél (pl. tárgyfotó) a széle levágódhat, ezeket érdemes előre kézzel elkészíteni.

## Szöveg vagy kinézet módosítása

1. Nyisd meg a **site** mappát.
2. **Add file → Upload files**, húzd be az új `index.html` fájlt, majd **Commit changes**.
3. Kb. 1 perc múlva élesben van.

A legegyszerűbb, ha a változtatást Claude-dal készítteted el, és csak a kapott `index.html`-t töltöd fel.

## Ami magától frissül

- A felső sávban a nyitvatartás jelzése budapesti idő szerint: „nyitva 20:00-ig”, illetve „zárva nyitás 11 óra múlva”.
- A hétfői újratöltés élő, másodpercre pontos visszaszámlálója (nap : óra : perc : mp, hétfő 11:00-ig), hétfőn nyitvatartás alatt „ma van”.
- A fotók: lapozhatók (telefonon húzással, a következő kép széle belóg; asztali gépen hármasával látszanak, nyilakkal), és 3 naponta más fotó kerül előre.
- Görgetéskor jobb lent megjelenik egy fekete négyzet (a kerete mutatja, hol tartasz az oldalon), az oldal alján pedig egy „vissza a tetejére” gomb. Bármelyikre koppintva fekete függöny húzódik fel, közepén a momoko logóval; mögötte az oldal a tetejére ugrik, a függöny felemelkedik, a logó pedig a helyére siklik. Látogatásonként egyszer, az oldal megnyitásakor is lefut (koppintásra átugorható).
- A nyelv: magyar alapból, a nem magyar böngészőknek angol. Az **en / hu** gombbal lehet váltani.

## Mappák és fájlok

- `site/` – maga a weboldal: `index.html` és a képek (`img/`). Ez a mappa kerül ki a momokovintage.com-ra.
- `incoming/` – ide kell feltölteni az új fotókat.
- `tools/update_photos.py` – a fotókat tömörítő és az oldalba beillesztő program.
- `.github/workflows/photos.yml` – elindítja a fotóprogramot, amikor új fotó érkezik az `incoming` mappába.
- `.github/workflows/pages.yml` – kiteszi a `site` mappát az élő oldalra, ha az változik, és minden fotófrissítés után.
- `HANDOFF.md` – részletes műszaki jegyzetek (angolul) a további munkához.

## Ha valami nem frissül

Az **Actions** fülön látszik minden futás. A zöld pipa azt jelenti, hogy sikerült, a piros X azt, hogy hiba történt. Ha piros, kattints rá, és küldj róla képet Claude-nak. Egy futást kézzel is újra lehet indítani: **Actions → Publish website → Run workflow**.

## Nyitvatartás módosítása

A nyitvatartás két helyen szerepel a `site/index.html` fájlban:
1. a szlogen alatti listában (a mai nap ki van emelve),
2. a `HOURS` listában a fájl végén (ez adja a „Nyitva / Zárva” jelzést és a nyitásig hátralévő időt).

Mindkettőt egyszerre kell átírni. A legegyszerűbb szólni Claude-nak.

## Domain és beállítások

- **Domain:** momokovintage.com. A DNS a Squarespace-nél van.
- **DNS-rekordok:**
  - `A @` → 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
  - `AAAA @` → 2606:50c0:8000::153, 2606:50c0:8001::153, 2606:50c0:8002::153, 2606:50c0:8003::153
  - `CNAME www` → i34gl3.github.io
- **Ne nyúlj hozzá:** a Google MX és TXT rekordokhoz, mert ezek az info@momokovintage.com e-mailt működtetik.
- **GitHub beállítás:** Settings → Pages → Source: „GitHub Actions”, Custom domain: `momokovintage.com`, Enforce HTTPS: bekapcsolva.
- **A tároló nyilvános.** Ez az ingyenes GitHub Pages feltétele, ezért ide soha ne kerüljön jelszó vagy más bizalmas adat.
