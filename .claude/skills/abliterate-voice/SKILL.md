---
name: abliterate-voice
description: Write or review any copy for abliterate.app (pages, buttons, errors, emails, alt text, changelog). Sets the voice: a credible storefront with a deadpan-satire undercurrent and the invented inner voice of a broke solo dev. Use before writing or editing any user-facing text in web/ or src/.
---

# abliterate voice

abliterate.app is a real storefront for a service that will sell real tokens. Today the models are fictional and nothing can be run. The voice is serious on the surface and funny underneath, and it never lets the funny part cost the reader a fact. Full reasoning: `docs/DESIGN.md`. Q and A trail: `dialogue.md`.

## The 6 rules

1. **Speaker.** The default voice is neutral and product-like. First person "I" appears only in dev-voice zones (About, Status, Aside notes, 404) and is signed "the dev". Never "we". No name, no location.
2. **The joke.** A sincere sentence, then one flat, true-sounding fact, last in the paragraph. No puns, no winks, no exclamation marks. The material is the dev's invented circumstances (GTX 750 with one fan, a landlord who thinks the PC is a heater) and obviously satirical exaggeration of the fictional models.
3. **Humour level by page.** 0 none, 1 one dry line, 2 a recurring aside, 3 the voice runs the page.
   - 0: pricing, terms, privacy, acceptable use, code samples, API errors, generic 500, confirmation email.
   - 1: models, Start Here, form errors.
   - 1 to 2: landing, FAQ, changelog. 2: the notice, waitlist success.
   - 3: 404, About, Status.
   Anything a person must act on gets the instruction first and the joke second, or no joke.
4. **Hype is satire, and only in its zones.** Hype words ("world-class", "revolutionary", "unleashed", "supercharge the user experience") appear only in the landing hero sub-line, the model descriptions and "What people are saying". Every hype line carries a tell: absurd precision, a deadpan asterisk footnote, a contradicting spec, or an honest caveat right after. Never in titles, meta descriptions, pricing, legal, code, buttons or errors.
5. **Only emoji is banned.** Everything else is allowed in its place. ALL CAPS is fine as a joke ("BASED"). Em dashes are rare: default none, use a comma, colon or full stop.
6. **Must not read as AI-written.** Run the checklist below on every line.

## Style

Short declaratives, mostly under 18 words. One idea per paragraph, at most 4 sentences. Dry line last. Sentence case for headings and buttons. Digits for numbers. US spelling. Present tense (future only in Start Here, since nothing exists). Specific nouns and numbers beat abstractions. Vary sentence length on purpose; a fragment is allowed.

## Fixed vocabulary

| Concept | Use | Never |
|---|---|---|
| Not built yet | planned | coming soon, upcoming |
| Pre-launch list | waitlist | early access, beta list |
| Prepaid balance | credits | coins |
| Usage unit | tokens | words |
| What the API serves | models | AI, bots, engine |
| The feature | abliterated (term), uncensored (plain gloss) | unfiltered, jailbroken |
| The owner | the dev | founder, CEO, team, we |
| The service in prose | abliterate (lowercase) | Abliterate.app, the platform |
| Using it | send requests, call the API | leverage, utilize |

## The notice (identical on every page, never edited)

"Every model listed here is fictional and nothing can be run yet. Prices are planned. The waitlist is the only part that works."
Card tags: "fictional" on models, "planned" on prices and plans.

## Calls to action

Always the waitlist. Button text is literal: "Join the waitlist", "Join the waitlist for Pro". Humour only in the line under the button or in the success message.

## Redaction bar in text

`<span class="redact">word</span>`. Only where context makes the word obvious, at most once per page. Never on prices, legal text, code, headings, titles, alt text, buttons, links, form labels or errors. The word stays in the markup for screen readers. In forced-colors mode the text must show.

## Anti-AI checklist (every line)

- No "it's not X, it's Y" or "not just X but Y".
- No automatic lists of three.
- No closing sentence that sums up the paragraph. No "Whether you're a... or a...".
- No bold-lead bullets ("**Fast.** Really fast.").
- No filler transitions: "Moreover", "That said", "Here's the thing", "In today's world".
- No stacks of abstract nouns ("seamless experience", "powerful capabilities") outside a hype zone, and inside one they must be doing a joke.
- A line that sounds like a landing-page template is rewritten, or turned into a joke on the template.
- Read it aloud. If it sounds like a press release, cut it by half.

## Do and don't

**Hero.**
- Do: "Models that say yes." then "Yes has limits. They are in the acceptable use policy."
- Don't: "Unlock the full potential of unrestricted AI." (hype outside a zone, "AI", and the promise of no limits)

**Fictional notice.**
- Do: "Every model listed here is fictional and nothing can be run yet. Prices are planned. The waitlist is the only part that works."
- Don't: "Heads up! Our models are coming soon." (exclamation, "coming soon", and it hides the fact)

**Model description (hype zone, with a tell).**
- Do: "Soul is a revolutionary, world-class, fully unleashed flagship engineered to supercharge the user experience of everyone who can afford it.*" with the footnote "*Capability claims are marketing copy. See the notice at the top of this page."
- Don't: "Soul delivers cutting-edge performance and seamless results." (hype with no joke and no tell: it reads as real marketing)

**Antrax (cartoon, never capability).**
- Do: "In testing it conquered 14% of a world map in a spreadsheet. Requires a prompt, which remains your job."
- Don't: any line that describes a real harmful capability, however jokingly.

**Pricing (level 0).**
- Do: "1 credit equals $1 of usage at each model's rate. Prices are planned and may change before launch."
- Don't: "Pricing so simple even the dev's landlord understands it." (a joke on a level 0 page)

**Dev voice (level 3).**
- Do: "The GPU reached 84 C during a test of one prompt. The window was opened. The landlord asked whether the heating was on."
- Don't: "Ugh, money is so tight lately, please support me!" (whining, begging, and it asks for sympathy)

**Form error (level 1, instruction first).**
- Do: "That email address does not look right. Check it and try again."
- Don't: "Oops! Our servers are having a moment." (exclamation, no instruction, filler)

**404 (level 3, one redaction bar).**
- Do: "This page is [missing]. The models do not exist either, but they have pages, which do. Go to the home page."
- Don't: "Lost? Don't worry, we'll get you back on track!" (template, "we", exclamation)

**Privacy pledge (level 0).**
- Do: "Prompts and completions are never stored and never used for training."
- Don't: "We respect your privacy like it's our own." (a slogan on a legal page)

**Quotes (fictional, labelled).**
- Do: Some might say the model is <u>"BASED"</u>. Attributed to "a forum post, location unknown". Tagged "fictional quotes".
- Don't: a quote attributed to a real person, company or journalist, or a testimonial without the tag.

## Before shipping any copy

1. Level for this page type? Does the joke fit it, and does it come last?
2. Fixed vocabulary used? Notice present? Calls to action join the waitlist?
3. Anti-AI checklist run? No emoji? Em dashes only where needed?
4. Numbers (prices, credits, context) pulled from `src/data/`, not typed into prose?
5. Satire legible: a tell on every hype line, no real person or company in a quote?
6. Anything the reader must act on: instruction first?
