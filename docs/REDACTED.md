# Redacted: the bar is the joke

A proposal for making the redaction bar the site's main visual device, not two easter eggs. Status:
**proposal, not yet adopted.** Adopting it replaces the "at most one per page" rule in `docs/DESIGN.md`
(section "Redaction bar in text") with the rules below.

## The idea

The product is a model with the refusals removed. The site's visual language is the opposite: a document
that has been censored by someone who is bad at it. The bars are always slightly wrong: they cover the
obvious word, they miss the one that mattered, they can be peeled off with a mouse, and the sentence still
makes sense. Censorship as theatre, next to a product that is about not censoring. The joke is that the
redaction never hides anything.

One line for the voice: **the dev redacts things that do not need redacting, and never things that do.**

## Rules that do not move

These come from AGENTS.md, DESIGN.md and P3. Every trick below must pass them.

1. **Nothing real is ever hidden.** No bar on prices, rates, legal text, the fictional notice, form labels,
   errors, buttons, links, nav, model ids, code, alt text, headings people navigate by, or anything a person
   must act on.
2. **The word stays in the markup.** Screen readers read it normally. No `aria-hidden` on the hidden word, no
   text replaced by blocks.
3. **Context makes the word obvious.** A sighted reader who never reveals it still gets the sentence.
4. **Forced colors and print:** the word shows, outlined (`forced-colors`); the bar prints as a bar (P3).
5. **Reduced motion:** no slide, no flicker; reveal is instant.
6. **No emoji, no pop-ups, tokens only, no border-radius, no blur.** The bar is a flat block of `--redact`.
7. **Density cap:** at most one bar per paragraph, and at most roughly one per screen of scrolling. Past
   that it stops being a joke and becomes a document nobody can read.

## The tricks

Ordered by payoff per effort. Each has: what it looks like, where it goes, how to build it.

### 1. Peel to reveal (the core interaction)

The bar slides off the word on hover, on focus, or on tap, in 3 stepped frames, then slides back. Revealing
is play; the word underneath is always something deadpan.

- Where: every text bar on the site.
- Build: wrap as `<span class="redact" tabindex="0">word</span>` only where tapping matters (on touch there is
  no hover). The bar is a `::after` pseudo-element over the text, so the text itself is never transparent:
  ```css
  .redact { position: relative; }
  .redact::after {
    content: ''; position: absolute; inset: -0.05em -0.15em;
    background: var(--redact);
    transform-origin: right; transition: transform var(--t-med) var(--step);
  }
  .redact:hover::after, .redact:focus-visible::after, .redact.peeled::after { transform: scaleX(0); }
  @media (prefers-reduced-motion: reduce) { .redact::after { transition: none; } }
  @media (forced-colors: active) { .redact::after { display: none; } .redact { outline: 2px solid CanvasText; } }
  ```
  Tap toggles `.peeled` with a few lines of script. This replaces the current `color: transparent` approach,
  which is what broke forced-colors in P3.
- Note: `tabindex="0"` on non-interactive text adds tab stops; only use it on a handful of bars, or make
  peeling hover/tap-only and keep the word readable to keyboard users through the screen reader path.
  Decide per page; never add more than three tab stops of this kind to one page.

### 2. The bar that missed

The bar sits half a word off, covering the harmless word next to the real one. Funnier than a perfect bar,
and it costs nothing.

- Example, hero hype line: "A world-class, revolutionary model suite, ████████ to supercharge the user
  experience." The bar covers "unleashed" and leaves "supercharge" fully visible.
- Example, About: "The dev, who lives in ████████ and owns one GPU." The city is redacted. The GPU is not.
- Build: just placement. No new code.

### 3. Over-redaction as satire

A whole sentence barred except one word, like a FOIA page. Works because the surviving word is the
punchline.

- Where: one of the fictional quotes on the landing page.
  "████ ███ ██████ ████ ███ ███ █████ **yes** ████." Attribution: "Source withheld at the source's request.
  The source is a text file."
- Peel reveals the full sentence, which is mundane ("I asked it what it would do and it said yes, then
  explained.").
- Cap: one per site. It is the loudest trick.

### 4. Redaction ledger (counter)

A tiny line in the footer, VT323 numerals: "Words redacted on this site: 14. Words that needed it: 0."
Built at build time by counting `.redact` spans in the rendered pages (an Astro integration or a script run
in `npm run build`). Accurate, therefore deadpan.

### 5. Section dividers as bars

Replace the plain 2 px rules between landing sections with a short, thick bar in `--redact` with nothing
under it. Purely visual: the site looks like a redacted document even where there is no joke. Pair with a
`::after` caption in `--fs-xs`: "[section intentionally left blank]" on exactly one of them.

- Build: `.rule-bar { height: calc(var(--px) * 3); width: 6rem; background: var(--redact); }`. Decorative,
  `aria-hidden`, `role` none.

### 6. The hero GPU, live

The GTX 750 label is already a redaction bar in the pixel art. Animate it: once on load, the bar slides off
the label one art pixel at a time, shows "GTX 750", and slides back. The caption already says "It still says
GTX 750."

- Build: a second PNG with the label visible, swapped with a 3-frame `steps()` clip-path animation, or a
  `pixel-art` sprite strip. Respect reduced motion (static, bar on).

### 7. Model detail "declassified" stamp

Each model page gets a header strip like a case file: `FILE: abliterate-antrax-v3.0 / STATUS: FICTIONAL /
CLEARANCE: ████`. The clearance level is the only bar; peeled, it says "none required".

- The fictional status is never barred (rule 1). Only the joke field is.

### 8. The 404 as a fully redacted page

The 404 already has "missing" barred. Push it: the whole page body is a redacted document, three paragraphs
of bars, and the only unbarred text is the instruction ("Go to the home page" link) and the plain sentence
saying the page does not exist. Instruction first, joke after (DESIGN.md).

### 9. Waitlist dialog states

- While sending: the submit label gets a bar that grows across it in 3 steps (a progress bar that looks like
  censorship). `aria-busy` carries the real state.
- Success: the success line arrives redacted and peels itself once, revealing "You are on the list once you
  confirm." Reduced motion: no bar at all.
- Errors are never barred (rule 1).

### 10. Select-to-reveal

Selecting text with the mouse already "reveals" a bar if the bar is a `::after`, because `::selection` styles
the text underneath. Make it intentional: `.redact::selection` uses `--action` so a drag across a bar flashes
the word in orange. Free easter egg for the people who try.

### 11. Copy that knows about the bars

The voice does the rest. A few lines that only work because of the device:

- Footnote under a peeled bar: "*Redacted for no reason. The dev was told it looked professional."
- Changelog entry: "Redacted 9 more words. Legal did not ask for this. There is no legal."
- FAQ: "Why are some words blacked out?" "Style. Nothing on this site is actually hidden. Prices, terms and
  the fact that the models are fictional are always shown in full."

That FAQ answer doubles as the trust statement: the bars are a costume, not concealment.

## What not to do

- Do not bar anything that would make a careful reader think the site is hiding a cost, a limit or a risk.
  One misplaced bar on a price undoes every honest line on the site.
- Do not use bars as the only carrier of a joke a screen-reader user would miss; the sentence must be funny
  with the word read aloud too.
- Do not animate more than one bar at a time on screen.
- Do not use real redacted documents, real agency stamps or real case formats (impersonation).
- Do not add bars to the hype line footnotes; the footnote is the honest part.

## Rollout

| Step | Work | Files |
|---|---|---|
| 1 | Replace `.redact` with the `::after` version, peel on hover/focus/tap, forced-colors and print rules; amend DESIGN.md | `global.css`, `docs/DESIGN.md` |
| 2 | Place bars: hero "missed" bar, one per model description, About, the over-redacted quote | `index.astro`, `models.ts`, `about.astro` |
| 3 | Dividers, 404 page, FAQ question | `index.astro`, `404.astro`, `faq.astro` |
| 4 | GPU label animation (pixel art) | `art/src/hero/`, `public/img/` |
| 5 | Ledger counter, waitlist dialog states, model file strip | build script, `WaitlistDialog.astro`, `models/[id].astro` |

After each step: `npm run audit` (add a check that no `.redact` sits inside `a`, `button`, `label`, `th`,
`.num`, `.notice`, `code`, or the legal pages), then 375 px and 1440 px, light and dark, keyboard, and
forced-colors emulation in DevTools for `/` and `/404`.

All new copy goes through the `abliterate-voice` skill before it ships. The examples above are drafts.
