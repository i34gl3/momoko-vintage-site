# Momoko Vintage website: handoff notes

Everything needed to continue work on momokovintage.com in a new chat.

## Where things live

| What | Where |
|---|---|
| Live site | https://momokovintage.com |
| Hosting | GitHub Pages (free), public repository https://github.com/i34gl3/momoko-vintage-site; `.github/workflows/pages.yml` publishes the `site` folder |
| Domain | Bought via Google Workspace, DNS managed at Squarespace |
| DNS records | A `@` → 185.199.108.153 / 109.153 / 110.153 / 111.153 · AAAA `@` → 2606:50c0:8000::153 / 8001 / 8002 / 8003 · CNAME `www` → i34gl3.github.io |
| DNS, do not touch | Google MX (smtp.google.com) and the TXT records (email) |
| Shop email | info@momokovintage.com |
| Instagram | https://www.instagram.com/momoko_vintage/ |
| TikTok | https://www.tiktok.com/@momoko_vintage |
| Facebook | https://www.facebook.com/momokovintage |

## How the site works

- One page: `site/index.html`, no build step. Hungarian by default, English button (auto-English for non-Hungarian browsers).
- Sections (top to bottom): pinned top bar (small logo on the left once you scroll past the big one; live open/closed status centred; hu/en switch on the right. Phones up to 460px use a compact bar), big centred logo, photo carousel, centred intro (big tagline, sub-line, highlighted address "1088 Budapest, Krúdy utca 9, Palotanegyed" between two lines, opening hours with today highlighted, directions button), black restock band ("heti újratöltés hétfőnként" / "weekly restock", then "következő" and a live countdown nap : óra : perc : mp that ticks every second to Monday 11:00 Budapest time; on Monday while open it shows "ma van"), white "kövess minket" with a large @momoko_vintage link and the social boxes (black fill on hover), black footer (phone and email, "vissza a tetejére" button, tagline, copyright). No separate "visit us" section or map; phone and email appear only in the footer.
- Back to top: a floating black square (bottom right) appears after scrolling about one screen; a thin frame inside it fills with scroll progress. It hides when the footer is on screen, where the big "vissza a tetejére" button takes over. Clicking either runs the logo overlay: an ink curtain (`#veilPanel`, with `#veilInner` counter-translated so its contents stay still) slides up, a light logo copy inside it (`#veilMask`/`#veilLight`) rises in the centre, the page jumps to the top instantly underneath, then the curtain lifts and the logo glides into the big logo's spot while the photos settle again. The same overlay plays once per visit on page load (head script sets `html.intro`, sessionStorage key `mv-intro`; a tap skips it; 4.5 s safety fallback). A dark copy (`#veilDark`) under the curtain glides in step, so the logo is light on ink and dark on paper, split exactly at the curtain edge. Built on the Web Animations API with transform only; animations in a group share one start time, and each layer has one animation at a time (otherwise Chrome refuses the GPU path). No clip-path, blend modes, filters or backdrop blur anywhere, so everything runs on the compositor at the display's refresh rate. Reduced-motion visitors get no intro and jump straight to the top.
- Social boxes: each link is one `<a class="s-link">` line. To add Etsy / Grailed / eBay, copy a line, change the link, icon and name, and put it before the "hamarosan" box (remove that box once all shops are live). Desktop fits up to 6 boxes per row.
- Open/closed status uses Budapest time: "nyitva 20:00-ig" when open, "zárva nyitás X óra múlva" when closed (minutes under one hour). Restock countdown: live days : hours : minutes : seconds to the next Monday opening (11:00), digits slide in when they change; "ma van" while open on Monday.
- Photos: carousel of every photo in the pool. Phones show one photo with a slice of the next one peeking in (swipe; counter "1 / 3"); desktop shows three side by side, arrows only when there are more than three. Auto-advances every 5 s until someone browses. The first photo changes every 3 days. Photos are shown in a 4:5 frame; since Nov 23 2026 the photo script also saves them as 4:5 (1080×1350), so nothing is cropped twice. The pool list sits between `/* POOL:START */` and `/* POOL:END */`.
- Photos that are not portrait (e.g. square product shots) get cut by the automatic 4:5 crop; prepare those by hand (the Nov 2026 shoe photo had the wall extended upward instead).

## Design (modern pass, 20 Nov 2026; earlier references: jilsander.com, highsnobiety.com, Zsófi's feedback)

- Centred, symmetric layout on phone and desktop: tagline, address, restock countdown, follow block and footer are all centred.
- One voice: everything in lower case like the logo (status, buttons, headings, footer). The tagline and address are normal sentences.
- Colours: off-white #F6F3EC, white #FFFFFF, black #141413; grey #6E6A62 / #8B877D for secondary text; olive #6F7140 only for the "open" square.
- No rounded corners. Few lines; no section numbers or all-caps labels.
- Font: Courier New / Courier Prime, bold (as on the original site). Large sizes use tight negative letter spacing.
- Loud elements: the tagline, the live restock clock and @momoko_vintage, each in very large type; everything else stays small and quiet.
- Motion: photos settle in once on page load and again after the back-to-top trip; the logo overlay plays on first load and on back to top; the floating button springs in and its arrow loops on hover. All switched off for reduced motion.
- Logo: `site/img/logo.png`, recoloured with CSS.
- No brand names on photos (preference; the Nov 2026 batch was chosen anyway).

## Hosting and automation (GitHub Pages)

1. The whole folder lives in the public GitHub repository `i34gl3/momoko-vintage-site`. Settings → Pages → Source: "GitHub Actions". Custom domain: `momokovintage.com`, "Enforce HTTPS" on. (DNS check and HTTPS certificate confirmed working on 20 Nov 2026.)
2. Any change in `site/` on the main branch is published by `.github/workflows/pages.yml` (about a minute).
3. Weekly: upload new portrait photos to `incoming/` on github.com. `.github/workflows/photos.yml` runs `tools/update_photos.py` (compresses them, replaces the photo pool, removes the originals); when it finishes, `pages.yml` publishes automatically.
4. Status of every run: the repository's Actions tab. A run can be restarted by hand: Actions → Publish website → Run workflow.

## Open items

- Add Etsy / Vestiaire Collective / Grailed links when the shops are live.
- Google Business Profile website field → https://momokovintage.com
- Ideas not built yet: short shop video in the hero, hang-tag labels, story-style photo viewer, automatic sale banner.

## SEO (20 Nov 2026)
- In the head: canonical URL, robots meta, Open Graph and Twitter tags, share image `img/share.jpg` (1200x630), and JSON-LD ClothingStore data with a Hungarian/English description and keywords. `site/robots.txt` and `site/sitemap.xml` exist.
- No visible SEO text block on the page: the owner removed the footer shop description because it didn't look good. Keep the descriptive text in meta/JSON-LD only.

## English page (/en/)
- `site/en/index.html` is generated, never edited: `tools/build_en.py` copies `site/index.html`, writes every `data-en` text straight into the HTML (Hungarian kept in `data-hu`), swaps `aria-label`s, and switches title, description, canonical and Open Graph to English. The "Publish website" workflow runs it before upload; `site/en/` is in .gitignore.
- Both pages carry hreflang links (hu, en, x-default = /). The sitemap lists both URLs with the same alternates.
- The hu/en button still switches instantly; it also updates the address bar (/ or /en/) so shared links open in the right language. Non-Hungarian browsers landing on / switch to English as before; crawlers never auto-switch.
- Image paths in index.html are absolute (`/img/...`) so they work from /en/ too. A new head text needs an English pair in `HEAD` in build_en.py, or the build stops with an error.

## Featured poster (sale, event)
- `FEATURE` in index.html (just below POOL:END) puts one extra image first on phones and in the middle on desktop until `until` (UTC midnight), then hides it by itself. It sits outside POOL, so photo uploads don't touch it, and its file name (`sale-…webp`, not `p-…`) keeps the photo script from deleting it.
- To show a new poster: save it 1080×1350 (4:5) as WebP in site/img, change `name`, `until` and both `alt` texts. Remove the old file when done.
- Optional `video` (e.g. `sale-20261127-motion.mp4`, 4:5, muted, no audio, keep it under ~1 MB): replaces the still in the carousel and plays once from the start each time the slide comes into view (only after the opening logo curtain), then rests on its last frame. Desktop: the poster stays in the middle (no auto-advance while it is featured). Phones: the carousel stays on the poster until its motion has played once, then holds 2.5 s. Start logic checks the real on-screen position on every trigger (intersection, scroll, resize, metadata, intro end, tab visible), retries on the first tap if autoplay was blocked (iPhone Low Power Mode, in-app browsers), rewinds safely and restarts after back/forward navigation; a 20 s watchdog retries once a second. Encode the video at 1080×1350 like the still (crf 30 + light hqdn3d keeps it ~250 KB). The WebP still is its poster frame and is what reduced-motion visitors see. Delete the `video` line (and the file) to go back to the still.

## Working on it
- The owner approves every change: show a preview first, and push to `main` only when he says "deploy". GitHub Actions publishes automatically.
- Owner preferences: everything lower case except the tagline and address sentences; Courier; no rounded corners; minimal, centred, black/white sections. Check phones at 360–430px for overflow before shipping.

