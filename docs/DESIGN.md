# Design

Decisions from the grill-me sessions. The full question-and-answer trail is in `grill-v1.md` (site) and `dialogue.md` (voice and copy). The voice rules in short form live in `.claude/skills/abliterate-voice/SKILL.md`; this file says why.

## Product facts the copy must respect

- abliterate.app is a real storefront for a service that will sell real tokens (credits and subscriptions). Today nothing is for sale and no model exists.
- The six models are fictional placeholders and will be renamed. Prices are planned.
- The only working parts: the website and the waitlist (double opt-in, Buttondown).

## Voice

**Speaker.** The default voice is neutral and product-like: plain statements and imperatives, no "we". First person "I" exists only in dev-voice zones (About, Status, Aside notes, 404) and is signed "the dev". There is no name and no location. The dev is one person, and the site never pretends to be a team.

**The joke.** A sincere sentence, then one flat, true-sounding fact, last in the paragraph. No puns, no winks, no exclamation marks. Two sources of humour:

1. The dev's invented circumstances: a GTX 750 with one fan, a landlord who thinks the PC is a heater. All of it is made up, as a nod to people who know the hardware. None of it is a claim about the service.
2. Satirical exaggeration of the fictional models ("could conquer the world if prompted"). It has to be obvious to a careful reader that this is satire (see "Making satire legible").

**Humour levels.** 0 none, 1 one dry line at most, 2 a recurring aside, 3 the voice runs the page.

| Page or element | Level |
|---|---|
| Pricing, terms, privacy, acceptable use, API and code samples, API errors | 0 |
| Models, Start Here, waitlist form errors | 1 |
| Landing, FAQ, changelog | 1 to 2 |
| Fictional-model notice, waitlist success | 2 |
| 404, About, Status | 3 |
| Generic 500, confirmation email | 0 (plain, someone may be stuck) |

Rule inside every level: anything a person has to act on gets the instruction before the joke.

**Hype zones.** Hype words ("world-class", "revolutionary", "unleashed", "supercharge the user experience") are allowed only as obvious satire, and only in: the landing hero sub-line, the model descriptions, and the "What people are saying" section. Never in page titles, meta descriptions, pricing, legal, code, buttons or errors. Every hype line carries a tell: absurd precision, a deadpan asterisk footnote, a spec that contradicts the boast, or an honest caveat straight after.

**Banned.** Emoji, always. Everything else is allowed in its place: ALL CAPS is fine, hype words are fine in the zones above, em dashes are rare (only where a comma or full stop truly cannot do the job; the default is none). Exclamation marks are not banned but are not used.

**Not reading as AI-written.** Every line is checked against `abliterate-voice`: no "not X but Y", no default triplets, no tidy closing summary, no "Whether you're a...", no bold-lead bullets, no filler transitions, specific nouns and numbers over abstractions, sentence length varied on purpose, template-sounding lines rewritten or turned into a joke on the template.

**Rhythm and style.** Short declaratives, mostly under 18 words, one idea per paragraph, at most 4 sentences. US spelling, sentence case for headings and buttons, digits for numbers, present tense (future tense only in Start Here, because nothing exists).

**Vocabulary.** Fixed on every page.

| Concept | Use | Never |
|---|---|---|
| Not built yet | planned | coming soon, upcoming (the nav "Docs" tag says "soon") |
| Pre-launch list | waitlist | early access, beta list |
| Prepaid balance | credits | coins |
| Usage unit | tokens | words |
| What the API serves | models | AI, bots, engine |
| Feature | abliterated (term), uncensored (plain gloss) | unfiltered, jailbroken |
| The owner | the dev | founder, CEO, team, we |
| The service in prose | abliterate (lowercase) | Abliterate.app, the platform |
| Using it | send requests, call the API | leverage, utilize |

**The notice.** Identical on every page: "Every model listed here is fictional and nothing can be run yet. Prices are planned. The waitlist is the only part that works." Fixed short tags on cards: "fictional" on models, "planned" on prices and plans. The humour lives in one extra line per page type, never in the notice.

**Calls to action.** Always the waitlist. Button text is literal ("Join the waitlist", "Join the waitlist for Pro"). The joke, if any, goes in the line under the button or in the success message. The confirmation email is plain.

**Uncensored and abliterated.** Both registers are used. Factual: "An abliterated model is an open-weight model with its refusal behavior removed." Hype, in the zones only: "unleashed". The product term is "abliterated", the plain gloss for non-technical readers is "uncensored". "Yes has limits" is stated early: the acceptable use policy is linked from the hero.

**The hero.** H1 is "Models that say yes." Directly under it: the literal definition line, then "Yes has limits. They are in the acceptable use policy." (linked), then the hype sub-line with its footnote. The scaffold's `.redact` span in the H1 is not used.

## The art in the voice

- **Hero (the GTX 750).** Alt text is functional and plain: "A small single-fan graphics card with its label blacked out." Visible caption on the landing page: "The dev's GTX 750. The label is redacted. It still says GTX 750." The same card appears small on the Status page and once on About. Other pages mention it at most once. Never on pricing, legal or Start Here.
- **Logo.** An "a" whose top is a redaction bar. Alt text is plain ("abliterate"). About says once that it reads as an "e" at some sizes (true of two rejected drafts) and the dev has chosen not to discuss it.
- **Icons.** Seven in-house 16x16 icons (coin, unlocked padlock, chip, calendar, token, envelope, status light). They are decorative (`aria-hidden`) next to a literal label. Model cards use these only, never the GPU art, so the gag stays rare.
- **Redaction bar in text.** It may cover a word only when context makes the word obvious. At most one per page. Never on real information, prices, legal text, code, headings, titles, alt text, buttons, links, form labels or anything a person must act on (errors). The word stays in the markup so screen readers read it: the bar is a decoration of text that exists, never a way to hide text. Markup: `<span class="redact">word</span>`. Implementation notes: in dark mode `--redact` is light, which keeps the bar visible; in `forced-colors: active` the text must render normally (the bar's `color: transparent` would make it vanish); in print, same. Used on: 404 ("This page is missing", with "missing" barred) and Status ("GTX 750", with "750" barred).

## Making satire legible

Devices, in order of preference: absurd precision ("14% of a world map, in a spreadsheet"), a deadpan asterisk footnote, a spec that contradicts the boast next to it, an honest caveat directly after the boast. The notice sits above every hype line. Fictional quotes are attributed to obvious non-persons, never to a real person or company, and carry a "fictional quotes" tag. Cartoon, not capability: the antrax joke is a world map and a prompt, never a weapons claim.

## Pricing (copy decisions; numbers live in `src/data/`)

- 1 credit = $1 of usage at each model's per-1M-token rate (`models.ts`). No inflated credit unit.
- No free plan (owner, 2026-10-08): the site sells credits or a subscription. Cheapest way in is the smallest top-up pack ($10, `entryUsd` in `plans.ts`); the landing teaser says "credits start at $10". Taxes are calculated at checkout by Stripe Tax, and Stripe is the payment provider. Pro $20/month: 22 credits per month. Max $100/month: 120 credits per month. Top-up packs of $10, $50 and $200 at 1:1. Unused credits expire after 12 months.
- Everything is tagged "planned" and may change before launch. The allowance numbers go in `plans.ts`; copy files never repeat price numbers in prose.

## Privacy and legal

- No-logging pledge (applies once the API exists): prompts and completions are never stored and never used for training. Billing metadata only (key id, timestamp, model, token counts), kept 90 days.
- Held today: the waitlist email and consent time (Buttondown), plus cookieless Cloudflare Web Analytics.
- Enforcement trade-off, stated in one sentence: with no content logs, abuse is handled through metadata patterns, user reports and valid legal process.
- Entity name, address, governing law and refund terms are `[CONFIRM]` placeholders. The legal pages are drafts for a lawyer to review before launch.
- Acceptable use prohibits: sexual content involving minors, violence against identifiable people, targeted harassment and doxxing, fraud and deceptive impersonation, malware against third parties, mass-casualty instructions, key sharing or resale, rate-limit circumvention. The user is responsible for what they generate and publish. "Abliterated" describes a model, not a service without limits.

## Page copy rules

- Landing: hero stack (above), value propositions, an OpenAI-compatible sample (level 0, marked planned), trust row, model strip, "What people are saying" (fictional quotes, one reads: some might say it is "BASED", with the word underlined and quoted), pricing teaser, waitlist.
- Models: one description per model, hype zone, each with a footnote device. Identities: dong-flash small and fast; house-md blunt reasoning; sonny companion and roleplay; antrax agentic coding (the world-map joke); mable long-form writing; soul the over-adjectived flagship.
- Start Here: 7 steps, future tense, a "what you should see" line per step, example key `ab-demo-not-a-real-key`. Names SillyTavern and Open WebUI factually.
- FAQ: 14 questions in 4 groups; "Do these models exist?" and "What does abliterated mean?" come first; "Will it answer anything?" is answered with a plain no.
- Status: literal component table, one joke status ("degraded" on the dev's GPU), a short incident log in the dev voice, one absurd uptime line.
- About: about 250 words, honest that the storefront and the plan are real and the models are placeholders, ends on a dry line, with a "what is real / what is not" list.
- Changelog: the site's own build history, one or two lines each, the joke is the true thing that happened.
- Errors: 404 level 3, form errors level 1 (instruction first), success level 2, generic 500 plain, API errors level 0.

## Where the copy lives

The final copy per page is in `dialogue.md` (Part 2). Data values (prices, credits, context, plan features, model taglines) go into `src/data/*.ts` only, and pages render from them.

## Build decisions (2026-10-08, copy poured into `src/`)

- Placeholders: `npm run build` fails if any `[COPY:` reaches `dist/`. `[CONFIRM: ...]` markers stay visible on purpose until the owner supplies the fact (list in `problem_solution.md`, P9).
- Prose renders every price number from `src/data/plans.ts` (`creditUsd`, `topUps`, `creditExpiryMonths`, plan prices); nothing is typed into a page twice.
- The waitlist sends only the email. The plan the dialog was opened from is shown ("Joining for: Pro") but not sent, until P4 is decided.
- The function tells the page which of the five copy errors to show: `invalid`, `exists`, `unconfirmed`, `server`; `network` is decided in the browser.
- Pages with no line in `dialogue.md` got none: the scaffold's eyebrows ("Catalogue", "Legal") and the waitlist success heading are gone. Model detail pages had no meta description in the copy; it is built from data: "{name}: {tagline} A planned abliterated model. Fictional, not available yet."
- Section rhythm: `.section` sets block padding only, so `.wrap` keeps the 16 px side gutter at 375 px.
- Redaction bar: exactly two on the site, 404 ("missing") and Status ("750"). In forced-colors mode the word shows, outlined; in print the bar prints as a bar.
- Waitlist (2026-10-08): no plan or source tags (P4 closed, AGENTS.md unchanged). An already-subscribed address gets the same success reply as a new one, so membership is never revealed (P5 closed); the `exists` and `unconfirmed` errors are gone from the function, the dialog and `dialogue.md`. The reply shape for a duplicate is still unverified against the real API.
- Copy decisions (2026-10-08): the Free plan is removed (see Pricing). The FAQ keeps "uncensored AI" in "Who is this for?" on purpose, as what people search for.

## Nav and mobile menu (2026-10-08, Track C)

- Desktop nav breakpoint is 1024 px: below this, nav collapses to hamburger menu; above this, desktop links fit with no wrapping.
- Header has `position: relative`, mobile menu has `top: 100%`, so multi-line notice bars do not displace the dropdown.
- Closing behavior: closes on Escape (focus returned to menu button), outside click, link click, or when crossing above 1024 px via `matchMedia`. Opening focuses the first menu item.
- Theme button has `aria-label="Dark theme"` and `aria-pressed` reflecting dark mode state; icon visibility syncs with system preference and manual theme override.
