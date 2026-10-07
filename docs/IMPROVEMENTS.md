# Improvements audit (2026-10-08)

Read of the whole repo plus the live site (https://abliterate.pages.dev) at 800 px and 375 px.
Each finding has a severity, the evidence, and the track that owns the fix. Tracks are written
as standalone prompts in `docs/handoffs/` so several agents can run at once without touching
the same files.

Severity: **S1** broken or untrue today, **S2** real gap a visitor or Google will notice, **S3** polish.

## Findings

| # | Sev | Finding | Evidence | Track |
|---|---|---|---|---|
| 1 | S1 | The waitlist does not work on the live site, but Status says "Waitlist: operational" and the notice says "The waitlist is the only part that works". | P12: POST `/api/waitlist` returns 502 because `BUTTONDOWN_API_KEY` is not set. `src/pages/status.astro` hard-codes `operational`. | A |
| 2 | S1 | Duplicate-subscriber detection is a guess (P5). A 400 for any other reason shows "invalid". | `functions/api/waitlist.ts` regex `/already\|exists/` on a 400 body. | A |
| 3 | S2 | No abuse protection on the waitlist endpoint: no honeypot, no Turnstile, no rate limit, no Origin check. A script can fill the Buttondown list (and Buttondown bills per subscriber). | `functions/api/waitlist.ts` | A |
| 4 | S2 | Double submit: the submit button is never disabled and shows no busy state, so a slow call can create two requests. | `WaitlistDialog.astro` submit handler | A |
| 5 | S2 | No share or search metadata: no Open Graph / Twitter tags, no og:image, no canonical, no `sitemap.xml`, no `robots.txt`, no JSON-LD. A link pasted into Discord or X shows a bare URL. | `src/layouts/Base.astro`, `public/` | B |
| 6 | S2 | No `public/_headers`: no CSP, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and no long cache on hashed `/_astro/*` and `/fonts/*`. | `public/` | B |
| 7 | S2 | Desktop nav is cramped between ~860 and ~1050 px: "Start here" wraps to two lines and the CTA button squeezes. | Screenshot at 800 px. `Nav.astro` breakpoint is 860 px. | C |
| 8 | S2 | Mobile menu: no Escape to close, no close on outside click or on link click, stays open after resizing to desktop, focus is not moved into it. Its offset `top: 4.25rem` is a raw value (AGENTS rule 6) and breaks if the notice bar wraps to 3 lines (it does at 375 px). | `Nav.astro` | C |
| 9 | S3 | Theme button has a static label and no pressed state; screen readers cannot tell the current theme. | `Nav.astro` | C |
| 10 | S3 | Waitlist dialog does not close on backdrop click; focus is not returned explicitly after success close (native does it, but the success panel swap can lose it in Safari). | `WaitlistDialog.astro` | A |
| 11 | S2 | No CI and no checks: deploys are manual direct uploads (P12), no `astro check`, no link check, the 13-page contrast/overflow audit from P11 was a one-off script that is not in the repo. Regressions will ship silently. | `package.json`, no `.github/` | D |
| 12 | S2 | The direct-upload Pages project cannot be switched to Git deploys (P12). Pushing to GitHub does nothing. | P12 | D |
| 13 | S3 | `@fontsource` imports ship `.woff` duplicates and Cyrillic/Greek/Vietnamese subsets (25 font files, 280 KB in `dist/`). Browsers only fetch what they need via `unicode-range`, so this is size on disk, not on the wire, but the display fonts are not preloaded, so the hero H1 flashes in a fallback. | `dist/_astro`, `tokens.css` | B |
| 14 | S2 | Landing has no visual proof of the pixel brand beyond the GPU: model cards are text-heavy, the "What people are saying" quotes are the strongest section but sit low. A hallmark audit of the landing and models pages has not been done since copy was poured in. | `src/pages/index.astro` | E |
| 15 | S3 | Models index has no side-by-side comparison (context, input, output, best for). Pricing has the rate table; models does not link to it from each card. | `src/pages/models/index.astro` | E |
| 16 | S3 | No credit estimator: "1 credit = $1 at each model's rate" is hard to picture. A tiny in-page calculator (tokens per day x model -> credits per month) on Pricing would help, rendered from `models.ts` only. | `src/pages/pricing.astro` | E |
| 17 | S1 (owner) | `[CONFIRM]` markers still visible on pricing, terms, privacy, AUP and changelog (P9). Legal drafts need a lawyer. Only the owner can close this. | P9 | owner |

## Tracks

| Track | Prompt | Owns these files (do not edit others) |
|---|---|---|
| A Waitlist that works and holds up | `docs/handoffs/A-waitlist.md` | `functions/`, `src/components/WaitlistDialog.astro`, `src/pages/status.astro` |
| B Share, search, headers, fonts | `docs/handoffs/B-meta-headers.md` | `src/layouts/Base.astro`, `public/_headers`, `public/robots.txt`, `public/og/`, `astro.config.mjs`, `src/styles/tokens.css` (font-face lines only) |
| C Nav and menu | `docs/handoffs/C-nav.md` | `src/components/Nav.astro`, `src/styles/tokens.css` (one new size token only) |
| D CI and checks | `docs/handoffs/D-ci.md` | `.github/`, `package.json` scripts, `tools/audit/` |
| E Design pass | `docs/handoffs/E-design.md` | `src/pages/index.astro`, `src/pages/models/index.astro`, `src/pages/pricing.astro`, `src/components/ModelCard.astro`, new components |

Shared files every track may append to (append only, keep the P number you were given):
`problem_solution.md` (A: P14, B: P15, C: P16, D: P17, E: P18), `docs/DESIGN.md` (one dated subsection per track).

Order: all five can start now. If B and E both want `tokens.css`, B only touches `@font-face` lines and E only adds tokens at the end of `:root`. Merge order that avoids conflicts: C, A, B, D, E.

## Status

- C: done 2026-10-08 (P16).
- A, B, D, E: prompts written, not started.
