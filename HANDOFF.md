# Momoko Vintage website: handoff notes

Everything needed to continue work on momokovintage.com in a new chat.

## Where things live

| What | Where |
|---|---|
| Live site | https://momokovintage.com |
| Hosting | Moving from Netlify (team "info-x86tjkq", project "momoko-vintage") to GitHub Pages (free, public repository, publishes the `site` folder via `.github/workflows/pages.yml`) |
| Domain | Bought via Google Workspace, DNS managed at Squarespace |
| DNS records | GitHub Pages: A `@` → 185.199.108.153 / 109.153 / 110.153 / 111.153 (optional AAAA `@` → 2606:50c0:8000::153 / 8001 / 8002 / 8003) · CNAME `www` → USERNAME.github.io. Old Netlify values: A `@` → 75.2.60.5 · CNAME `www` → momoko-vintage.netlify.app |
| DNS, do not touch | Google MX (smtp.google.com) and the TXT records (email) |
| Shop email | info@momokovintage.com |
| Instagram | https://www.instagram.com/momoko_vintage/ |
| TikTok | https://www.tiktok.com/@momoko_vintage |
| Facebook | https://www.facebook.com/momokovintage |

## How the site works

- One page: `site/index.html`, no build step. Hungarian by default, English button (auto-English for non-Hungarian browsers).
- Sections (top to bottom): pinned top bar (small logo, live open/closed status, HU/EN switch), big logo, full-width photo carousel, intro (tagline, address, directions and Instagram buttons), black weekly restock band with countdown, white "Kövess minket" boxes (instagram, tiktok, facebook, google, "online platformokon is hamarosan"). Each link is one `<a class="s-link">` line; to add Etsy / Grailed / eBay, copy a line, change the link, icon and name, and put it before the "hamarosan" box (remove that box once all shops are live). Desktop fits up to 6 boxes per row., off-white "Látogass el hozzánk" (address, hours, phone, email, black-and-white map), black footer.
- Open/closed status and restock countdown use Budapest time. Opening hours are in two places in `index.html`: the hours table and the `HOURS` list in the script.
- Photos: full-width carousel of every photo in the pool. Phones show one photo at a time (swipe or arrows, counter "01 / 03"); desktop shows three side by side, arrows only appear when there are more than three. Auto-advances every 5 s until someone browses. The first photo changes every 3 days. Photos are shown in a 4:5 frame (cropped from the 2:3 files). The pool list sits between `/* POOL:START */` and `/* POOL:END */`.
- Photos that are not portrait (e.g. square product shots) get cut by the automatic 2:3 crop; prepare those by hand (the Nov 2026 shoe photo had the wall extended upward instead).

## Design (new look, Nov 2026, after Zsófi's feedback; references: jilsander.com, highsnobiety.com)

- Colors: off-white #F6F3EC, white #FFFFFF, black #141413. Sections alternate between them. Olive #6F7140 only for the small "open" square.
- No rounded corners anywhere. Thin 1 px lines, square outlined buttons (black filled for the main action).
- Font: Courier New / Courier Prime, bold (same as the original site). Small uppercase labels; social links in lower case.
- Logo: `site/img/logo.png`, recoloured with CSS. Big black logo centered at the top of the page, photos right under it; the small logo in the pinned bar appears once you scroll past the big one.
- No brand names on photos (preference; the Nov 2026 batch was chosen anyway).

## Hosting and automation (GitHub Pages)

1. The whole folder lives in a public GitHub repository (e.g. `momoko-vintage-site`). Settings → Pages → Source: "GitHub Actions". Custom domain: `momokovintage.com`, "Enforce HTTPS" on.
2. Any change in `site/` on the main branch is published by `.github/workflows/pages.yml` (about a minute).
3. Weekly: upload new portrait photos to `incoming/` on github.com. `.github/workflows/photos.yml` runs `tools/update_photos.py` (compresses them, replaces the photo pool, removes the originals); when it finishes, `pages.yml` publishes automatically.
4. `netlify.toml` and `site/_headers` are only used by Netlify; they can be deleted once Netlify is switched off.

## Open items

- Swap the Google reviews button for the direct "ask for reviews" link from Google Business Profile.
- Add Etsy / Vestiaire Collective / Grailed links when the shops are live.
- Google Business Profile website field → https://momokovintage.com
- Ideas not built yet: short shop video in the hero, hang-tag labels, story-style photo viewer, automatic sale banner.
