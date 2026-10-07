# Website v1 plan: abliterate.app

Source of decisions: `grill-v1.md`. Copy comes later from `dialogue.md` (a separate session).

## Stack

- Astro + TypeScript, npm, static output, deployed on Cloudflare Pages.
- Cloudflare Web Analytics (no cookies).
- Pages Function `functions/api/waitlist.ts` -> Buttondown API (key in a Cloudflare env var, never in git), tags `plan:<name>`, `source:<page>`.
- Astro i18n set up with `en` as the default; `th` is added later.
- Fonts vendored in `public/fonts/`: Silkscreen, Pixelify Sans, VT323, pixel-fallback, IBM Plex Sans, IBM Plex Mono, IBM Plex Sans Thai Looped.

Note: AGENTS.md rule 5 now means "no runtime CDN". Astro's build step is allowed.

## Single sources of truth

- `src/data/models.ts`: the six fictional models (id, tagline, context length, price per 1M input/output tokens, tags, `fictional: true`).
- `src/data/plans.ts`: Free / Pro $20 / Max $100, credit allowances, `status: "planned"`.
- `src/styles/tokens.css`: Redacted palette (paper, ink, redaction black, action #FF4A1C), fonts, spacing, timing; light and dark.

## Pages (v1, placeholder copy)

| Route | Content |
|---|---|
| `/` | hero (pixel GTX 750 with redaction bars), hook, value propositions, OpenAI-compatible code sample, model strip, pricing teaser, trust row, waitlist |
| `/models` | OpenRouter-style catalogue: filter/search, model cards with a "fictional" tag |
| `/models/[id]` | model detail: specs, pricing, sample request |
| `/pricing` | credits table (from models.ts) + plan cards (from plans.ts); every button opens the waitlist for that plan |
| `/start` | Start Here: what an API is, get a key, first request, Python, connecting SillyTavern / Open WebUI |
| `/faq` | accordion (built in the page, no native widgets that break the rules) |
| `/status` | honest status, written in the dev's voice, lowest priority |
| `/about` | From the dev |
| `/changelog` | list |
| `/legal/terms`, `/legal/privacy`, `/legal/aup` | legal, strictly serious |
| `/404` | in voice |

## Components

`Nav` (Models, Pricing, FAQ, Docs [soon], Join waitlist), `Footer`, `FictionNotice` (banner on every page plus a tag on each card, deadpan), `Aside` (dev voice), `PixelFrame` (notched frame), `Button`, `ModelCard`, `PlanCard`, `PriceTable`, `CodeBlock` (copy button), `WaitlistDialog` (in-page `<dialog>`, takes a plan prop), `Accordion`, `ThemeToggle`, `Icon` (Lucide sprite + pixel icons).

## Art (pixel skills)

1. Logo: a square pixel "a" mark with a red-orange redaction bar (`pixel-art`) -> favicon, apple-touch icon, OG image; Silkscreen wordmark.
2. In-house icons, 16x16 (`pixel-icon`): coin/credits, subscription, model chip, unlocked, token, envelope, status light, step 1-4.
3. Hero: a pixel GTX 750 with redaction bars (`pixel-art`).
4. Lucide sprite: menu, x, arrow-right, copy, check, chevron-down, external-link, sun, moon.

## Progress

- [x] 1-3 scaffold, data, pages (placeholder copy)
- [x] 4 waitlist function + dialog (needs BUTTONDOWN_API_KEY)
- [x] 5 pixel art: logo mark (16/32/180/512), 7 icons (coin, unlocked, chip, subscription, token, envelope, status), GTX hero. Start Here steps use numbers, not step icons.
- [ ] 6 hallmark + ui-ux-pro-max audit, browser check at 375 px / light / dark
- [ ] 7 copy from dialogue.md
- [ ] 8 deploy

## Build order

1. Scaffold Astro + TS, tokens, fonts, layout, nav/footer, FictionNotice.
2. Data files + Models, Pricing pages from data.
3. Remaining pages with placeholder copy.
4. Waitlist Pages Function + dialog + success state.
5. Pixel art: logo -> icons -> hero.
6. Check against hallmark + ui-ux-pro-max: 375 px, light/dark, keyboard focus, reduced motion.
7. Pour in copy from `dialogue.md`; create the voice skill there.
8. Deploy to Cloudflare Pages on abliterate.app.

## Later phases

Try-it box with canned replies, mascot, Thai pages + pixel Thai headline font, Docs (Starlight), Benchmarks, Chat, Rankings, Apps, Ori, real accounts and payments once models exist.
