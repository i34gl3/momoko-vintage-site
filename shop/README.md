# Online bolt (momokovintage.com/shop)

Minden darab egy mappa az `items` mappában. A többit a GitHub és a Stripe intézi.

## Új darab feltöltése (kb. 3 perc darabonként)

1. Készíts egy mappát a gépeden, a neve legyen a darab rövid neve: kisbetű, szám és kötőjel, pl. `burberry-trench-coat`.
2. Tedd bele a fotókat (`1.jpg`, `2.jpg`, …; az első lesz a borítókép), és egy `info.txt` fájlt. Mintának ott a `minta-info.txt`.
3. A github.com-on nyisd meg a `shop/items` mappát → **Add file → Upload files**, húzd be az egész mappát → **Commit changes**.
4. Kb. 3 perc múlva fent van: a fotók 4:5-re vágva, a Stripe fizetési link kész, a „megveszem” gomb él.

## Ha elkelt a boltban

Nyisd meg a Stripe appot → **Payment links** → a darab linkje → **Deactivate**. 15 percen belül az oldalon „eladva” lesz.
(Vagy írd át az info.txt-ben: `sold: yes`.)

Ha online kel el, nem kell semmit tenned: a link csak egyetlen fizetést fogad el, utána magától lezár, és az oldal is „eladva” lesz. A Stripe e-mailt küld a rendelésről a szállítási címmel.

## Ár módosítása

Írd át a `price:` sort az info.txt-ben (github.com-on a ceruza ikonnal). Az új ár és az új fizetési link automatikusan elkészül.

## Darab törlése

Töröld a mappáját az `items`-ből. Az oldala és a fotói maguktól eltűnnek.

## info.txt mezők

| mező | mit írj | kötelező |
|---|---|---|
| title | a darab neve angolul, márka nélkül | igen |
| price | ár euróban, csak szám | igen |
| designer | márka (pl. Prada); ha nincs: Vintage | |
| gender | women / men / unisex | |
| category | angolul: coats, jackets, blazers, knitwear, dresses, skirts, trousers, tops, shoes, boots, bags, accessories | |
| size | pl. `IT 42 · fits M` | |
| condition | new / excellent / great / good | |
| era | pl. `1990s` | |
| material | pl. `100% wool` | |
| measurements | `pit to pit 54 · length 96 · shoulders 42 · sleeve 60` (cm, kiterítve) | |
| flaws | hibák, ha vannak | |
| text_en / text_hu | leírás angolul / magyarul | |
| sold | `yes`, ha elkelt | |

A `stripe`, `stripe_id`, `stripe_price`, `added`, `sold_date` sorokat a rendszer írja, ne nyúlj hozzájuk.

## Egyszeri beállítás

1. **Stripe kulcs:** Stripe → Developers → API keys → **Create restricted key**. Jogok: Products, Prices, Payment Links, Shipping Rates: *Write*. Előbb teszt módban (rk_test_…), élesítéskor élő kulccsal (rk_live_…).
2. **GitHub:** a tároló **Settings → Secrets and variables → Actions → New repository secret**, név: `STRIPE_SECRET_KEY`, érték: a kulcs. Ide biztonságos: a titok a nyilvános tárolóban sem látszik.
3. **Cégadatok:** töltsd ki a `shop/settings.txt` első sorait (cégnév, adószám, cégjegyzékszám). Ezek az impresszumba kerülnek, webshopnál kötelezők.
4. **Stripe beállítások:** Settings → Business → *Customer emails*: kapcsold be a sikeres fizetésről szóló nyugtát. Settings → *Adaptive Pricing*: be (a külföldi vevő a saját pénznemében látja az árat).
