#!/usr/bin/env python3
"""Keep the shop and Stripe in step. Runs in the "Update shop" workflow.

For every piece in shop/items/:
  * no payment link yet  -> creates a Stripe product, an EUR price and a
    Payment Link that accepts exactly ONE payment, then writes the link
    into info.txt (stripe:, stripe_id:, stripe_price:);
  * link no longer active -> the piece sold online (Stripe switches the
    link off after its one payment) or was switched off by hand in the
    Stripe app because it sold in the store: writes sold: yes;
  * "sold: yes" typed by hand while the link is still active -> switches
    the link off, so it can't be bought twice;
  * price changed in info.txt -> switches the old link off and makes a new one.

Needs the GitHub secret STRIPE_SECRET_KEY (a restricted key with write access
to Products, Prices, Payment Links and Shipping Rates). Without it the
script does nothing, and links typed into info.txt by hand still work.
Test with a test-mode key (rk_test_...) first: the links then open Stripe's
test checkout, where the card 4242 4242 4242 4242 pays.
"""
import datetime
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_shop import ROOT, SITE_URL, read_kv, write_kv  # noqa: E402

API = "https://api.stripe.com/v1/"
ITEMS = ROOT / "shop" / "items"
SETTINGS = ROOT / "shop" / "settings.txt"
EU = "AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE".split()


def flat(d, prefix=""):
    out = []
    for k, v in d.items():
        key = "%s[%s]" % (prefix, k) if prefix else k
        if isinstance(v, dict):
            out += flat(v, key)
        elif isinstance(v, list):
            for n, x in enumerate(v):
                out += flat(x, "%s[%d]" % (key, n)) if isinstance(x, dict) else [("%s[%d]" % (key, n), x)]
        else:
            out.append((key, "true" if v is True else "false" if v is False else v))
    return out


def call(method, path, data=None):
    body = urllib.parse.urlencode(flat(data or {})).encode() if data else None
    req = urllib.request.Request(API + path, data=body, method=method, headers={
        "Authorization": "Bearer " + os.environ["STRIPE_SECRET_KEY"],
        "Stripe-Version": "2024-06-20",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit("Stripe %s %s failed: %s" % (method, path, e.read().decode()[:500]))


def shipping_rates(s):
    """Two delivery choices on every checkout, created once and remembered in settings.txt."""
    new = {}
    if not s.get("stripe_rate_eu"):
        eur = int(float(s.get("shipping_eu", "25")))
        r = call("POST", "shipping_rates", {
            "display_name": "EU tracked delivery / nyomkövetett szállítás", "type": "fixed_amount",
            "fixed_amount": {"amount": eur * 100, "currency": "eur"}, "tax_behavior": "inclusive",
            "delivery_estimate": {"minimum": {"unit": "business_day", "value": 3}, "maximum": {"unit": "business_day", "value": 6}},
        })
        new["stripe_rate_eu"] = r["id"]
    if not s.get("stripe_rate_pickup"):
        r = call("POST", "shipping_rates", {
            "display_name": "Pickup in store, Krúdy u. 9 Budapest / személyes átvétel", "type": "fixed_amount",
            "fixed_amount": {"amount": 0, "currency": "eur"}, "tax_behavior": "inclusive",
        })
        new["stripe_rate_pickup"] = r["id"]
    if new:
        write_kv(SETTINGS, new)
        s.update(new)
    return [s["stripe_rate_eu"], s["stripe_rate_pickup"]]


def create_link(slug, d, s, rates):
    name = ("%s %s" % (d.get("designer", ""), d["title"])).strip()
    price = int(float(d["price"].replace("€", "").replace(",", ".")))
    product = call("POST", "products", {
        "name": name, "metadata": {"slug": slug}, "url": "%s/shop/%s/" % (SITE_URL, slug),
        "images": ["%s/shop/%s/1.webp" % (SITE_URL, slug)],
        "description": (d.get("size", "") + " · " + d.get("condition", "")).strip(" ·") or name,
    })
    pr = call("POST", "prices", {"product": product["id"], "currency": "eur", "unit_amount": price * 100, "tax_behavior": "inclusive"})
    countries = s.get("ship_countries", " ".join(EU)).replace(",", " ").split()
    link = call("POST", "payment_links", {
        "line_items": [{"price": pr["id"], "quantity": 1}],
        "restrictions": {"completed_sessions": {"limit": 1}},
        "shipping_address_collection": {"allowed_countries": countries},
        "shipping_options": [{"shipping_rate": r} for r in rates],
        "phone_number_collection": {"enabled": True},
        "allow_promotion_codes": True,
        "billing_address_collection": "auto",
        "inactive_message": "Ez a darab már elkelt. / Sorry, this piece has just sold.",
        "after_completion": {"type": "redirect", "redirect": {"url": SITE_URL + "/shop/thanks/"}},
        "metadata": {"slug": slug},
    })
    write_kv(ITEMS / slug / "info.txt", {"stripe": link["url"], "stripe_id": link["id"], "stripe_price": price})
    print("Payment link made: %s -> %s" % (slug, link["url"]))


def main():
    if not os.environ.get("STRIPE_SECRET_KEY"):
        print("No STRIPE_SECRET_KEY secret: Stripe sync skipped.")
        return 0
    s = read_kv(SETTINGS)
    rates = None
    today = datetime.date.today().isoformat()
    for folder in sorted(p for p in ITEMS.iterdir() if p.is_dir()):
        info = folder / "info.txt"
        d = read_kv(info)
        if not d.get("title") or not d.get("price"):
            continue
        if not list((ROOT / "site" / "shop" / folder.name).glob("1.webp")):
            continue  # photos not processed yet
        sold = d.get("sold", "no").lower() in ("yes", "igen", "true", "1")
        lid = d.get("stripe_id", "")
        if lid.startswith("plink_"):
            link = call("GET", "payment_links/" + lid)
            if sold:
                if link["active"]:
                    call("POST", "payment_links/" + lid, {"active": False})
                    print("Sold by hand, link switched off: %s" % folder.name)
                if not d.get("sold_date"):
                    write_kv(info, {"sold_date": today})
                continue
            if not link["active"]:
                write_kv(info, {"sold": "yes", "sold_date": today})
                print("Sold (link no longer active): %s" % folder.name)
                continue
            try:
                changed = int(float(d["price"].replace("€", "").replace(",", "."))) != int(d.get("stripe_price", "0"))
            except ValueError:
                changed = False
            if not changed:
                continue
            call("POST", "payment_links/" + lid, {"active": False})
            print("Price changed, old link switched off: %s" % folder.name)
        elif sold or d.get("stripe"):
            continue  # sold, or a link pasted by hand
        rates = rates or shipping_rates(s)
        create_link(folder.name, d, s, rates)
    return 0


if __name__ == "__main__":
    sys.exit(main())
