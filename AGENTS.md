# AGENTS.md

Rules for any AI agent (Claude, Grok, Codex, Cursor...) working in this repo. These are binding.
`CLAUDE.md` just imports this file.

## What this is

**abliterate.app**: the storefront for a token service selling API access to abliterated models
(credits and subscriptions), with a mailing list. Pixel-art themed, sleek and clean.

The models advertised for now are **fictional placeholders** (`abliterate-dong-flash-v2.3`,
`abliterate-house-md-v5.2`, `abliterate-sonny-v2.5`, `abliterate-antrax-v3.0`, `abliterate-mable-v4.2`,
`abliterate-soul-5.5`). Every page that lists them shows a clear notice that they are fictional and that
no model is available yet. Never present them as real, never take real payment for them.

| File | Owns |
|---|---|
| `docs/DESIGN.md` | **how everything works and why: read it first, update it with every decision** |
| `problem_solution.md` | **every pitfall hit and its fix (or OPEN): read it before starting, add to it as you go** |
| `src/data/` | `models.ts`, `plans.ts`, `site.ts`: the only place prices, models and nav are defined |
| `src/styles/tokens.css` | every colour, font, size and timing (Redacted palette) |
| `src/pages/`, `src/components/`, `src/layouts/` | Astro + TypeScript site; `[COPY: ...]` marks placeholder text to fill from `dialogue.md` |
| `functions/api/waitlist.ts` | Cloudflare Pages Function: waitlist -> Buttondown |
| `public/fonts/` | vendored pixel fonts (Plex comes from `@fontsource`, bundled at build) |
| `website-v1.md`, `grill-v1.md` | v1 plan and the decisions behind it |
| `art/` | pixel art sources, palette, `build_fallback_font.py` (draws missing glyphs into `art/src/fonts/pixel-fallback/` and `web/fonts/pixel-fallback.woff2`) |
| `.claude/skills/pixel-*`, `image-to-pixel`, `tools/pixel-core/` | pixel art skills and their tool (needs Pillow). The skills were written for a game; read "the game" as "this site" |

## Skills to use

Load these before the matching work. Install any that are missing.

| Skill | Use for | Install |
|---|---|---|
| `hallmark` | any design, redesign, audit, or study/cloning of a reference site for `web/` | `npx skills find hallmark` |
| `ui-ux-pro-max` | UX, accessibility, layout and interaction checks | `npx skills find ui-ux-pro-max` |
| `lucide-icons` | every icon on the website | `npx skills add aksuharun/skills@lucide-icons -g -y` |
| `grill-me` / `grilling` | a relentless interview to sharpen a plan or design before building it | already in `~/.agents/skills/` |
| `ponytail` | all code: simplest thing that works, no new deps without need | `npx skills add dietrichgebert/ponytail@ponytail -g -y` |
| `pixel-art`, `pixel-icon`, `pixel-font`, `pixel-nineslice`, `pixel-refine`, `pixel-cleanup`, `pixel-tileset`, `pixel-rig`, `pixel-face`, `image-to-pixel` | any pixel artwork (logo, sprites, frames, illustrations, in-house icons) | already in `.claude/skills/` |

## Hard rules for the website (`web/`)

1. **No emoji anywhere on the website.** Not in copy, labels, buttons, icons, empty states, toasts or titles.
2. **No system pop-ups.** Never use `alert()`, `confirm()`, `prompt()`, the Notification API, `beforeunload`
   prompts, HTTP Basic auth, native `<select>` menus or `title=` tooltips. Dialogs, menus, tooltips and
   toasts are built in the page.
3. **Icons are Lucide or in-house pixel icons only.** Lucide icons are copied from `lucide-static` into an
   inline `<symbol>` sprite and used as `<svg class="icon"><use href="#i-name"/></svg>`. In-house icons are
   made with `pixel-icon`. No emoji, no icon fonts, no other icon sets.
4. **Pixel look, sleek and clean:** pixel fonts for display and accents (Silkscreen, Pixelify Sans, VT323 for
   numbers and code) with a clean normal font as body/fallback for readability. Notched pixel frames,
   hard offset shadows, no border-radius, no blur. Generous whitespace: pixel detail, not pixel clutter.
5. **No runtime CDN.** Astro + TypeScript build is fine; fonts and icons are vendored, never loaded from a CDN.
6. Colours, fonts, spacing and timing come from tokens in `:root` of the main stylesheet (light and dark
   via `prefers-color-scheme`). No raw values below it.
7. Works at 375 px wide with no sideways scroll, in light and dark mode, with visible keyboard focus,
   44 px touch targets, and `prefers-reduced-motion` respected.

## Hard rules for the service

- **Secrets never go in git**: no API keys, payment keys, mailing-list keys, `.env`.
- The fictional-model notice is never removed while the models are fictional.
- Pricing shown on the site comes from one source of truth (no numbers duplicated across pages).
- Mailing-list signup is double opt-in with a working unsubscribe; store only the email and consent time.

## Working in the repo

- Read `problem_solution.md` before starting. Every problem you hit and every solution you find goes in it
  the same day. Never delete an entry.
- `git pull` before changing anything; small commits with a message saying what and why.
- After changing the site: check it in a browser at desktop width and 375 px, in light and dark mode.

## Commands

```bash
npm install
npx astro dev      # http://localhost:4321
npx astro build    # static output in dist/
```
