# Grill session v1: abliterate.app website

Date: 2026-10-08. Format: question, then decision.

## Round 1

**Q1 Stack.** Decision: npm-based with TypeScript (not necessarily Next.js). See Q10.

**Q2 Pages for v1.** Decision: landing, models, pricing, FAQ, terms and privacy. No dashboard or login.
Build the page scaffold with placeholder text first; the copy comes from a separate copywriting session written to `dialogue.md`.

**Q3 Buy buttons.** Decision: every plan button opens "join the waitlist", tagged with the plan. No real payments.

**Q4 Mailing list.** Decision: Buttondown (double opt-in, unsubscribe built in, free tier).

**Q5 Pricing shape.** Decision: credits priced per model, plus Free (trial), Pro ($20/mo, with a credit allowance) and Max ($100/mo). All shown as "planned".

**Q6 Reference sites.** Decision: OpenRouter (catalogue, nav) and OpenCode. Docs come much later.
Nav in the long-term plan: Models, Benchmarks, Chat, Rankings, Apps, Ori, Pricing, Docs, Sign Up.

**Q7 Colour mood.** Decision: deferred to Q14 (asked for more options).

**Q8 Fonts.** Decision: pixel fonts (Silkscreen, Pixelify Sans, VT323) plus IBM Plex Sans / Plex Mono as the normal fallback, plus a real Thai font (see Q13).

**Q9 Fictional-model notice.** Decision: deadpan satire. It looks serious but hides dry humour. The site itself is not a joke: it will sell real tokens, so it needs a real customer hook, credibility and professionalism.

## Round 2

**Q10 Framework.** Decision: Astro + TypeScript (Starlight for docs later).

**Q11 v1 nav.** Decision: Models, Pricing, FAQ, Docs (tagged "soon"), and a "Join waitlist" button. Benchmarks, Chat, Rankings, Apps and Ori are later phases.

**Q12 Languages.** Decision: launch in English; set up Astro i18n now so Thai can be added later.

**Q13 Thai font.** Decision: IBM Plex Sans Thai Looped (looped, traditional letterforms) for body text; a pixel Thai headline font later with `pixel-font`.

**Q14 Colour.** Decision: "Redacted": paper white, black redaction bars, red-orange #FF4A1C as the action colour (buttons, links, focus). Dark mode: black paper.

**Q15 Audience.** Decision: developers, plus people with no AI knowledge who want uncensored AI. Beginners need a hand-holding walkthrough of using the (fictional) API.

**Q16 Trust signals.** Decision: no-logging pledge, OpenAI-compatible code sample, contact and company details, acceptable-use policy, changelog, and a status page as the lowest-priority item. The status page and similar spots carry the broke dev/owner's inner voice (still on a GTX 750, too late to build a new PC).
The copywriting session must also grill the user on the site's voice and then create a voice skill.

## Round 3

**Q17 Hand-holding.** Decision: a Start Here guide in v1 (what an API is, key, first request, Python, connecting apps such as SillyTavern or Open WebUI); an interactive try-it box with canned in-voice replies in phase 2.

**Q18 Where the dev voice lives.** Decision: both dedicated pages (About / From the dev, Status) and small asides across the site. Pricing, legal and code stay strictly serious.

**Q19 Hosting.** Decision: Cloudflare Pages + Cloudflare Web Analytics (no cookies, no banner).

**Q20 Waitlist form.** Decision: a Cloudflare Pages Function calls the Buttondown API, the success state shows in the page, and signups are tagged by plan.

**Q21 Pixel art v1.** Decision: site logo, in-house icons, and a hero illustration (a pixel GTX 750 with redaction bars). Mascot in phase 2.

## Round 4

**Q22 Logo.** Decision: a square pixel "a" mark with a red-orange redaction bar (favicon and app icon), plus a Silkscreen wordmark.

**Q23 Icons.** Decision: about 10 in-house 16x16 pixel icons for brand concepts (credits/coin, subscription, model chip, unlocked, token, waitlist envelope, status light, Start Here steps); Lucide for interface parts (menu, close, arrows, copy, check, chevron, external link, sun/moon).

## Copywriting session prompt

```
Read AGENTS.md and docs/DESIGN.md first. Then run a grill-me session (grilling skill) in two parts.

Part 1, voice: grill me about the voice of abliterate.app. The site is serious and credible, built to sell real tokens, but it has a deadpan-satire undercurrent and the inner dialogue of a broke solo dev/owner (still on a GTX 750, no money for GPUs yet). Find out where that voice shows (status page, fictional-model notice, about/from-the-dev notes, FAQ, error pages) and where it must stay out (pricing, legal, API docs). Settle vocabulary, sentence rhythm, words that are banned, and how much humour each page type gets. Afterwards, create a reusable voice skill at .claude/skills/abliterate-voice/SKILL.md that captures the rules with do/don't examples.

Part 2, copy: using that voice, write the copy for every page: landing (hero hook, value propositions, trust signals, OpenAI-compatible code sample), models (one description for each fictional model: abliterate-dong-flash-v2.3, abliterate-house-md-v5.2, abliterate-sonny-v2.5, abliterate-antrax-v3.0, abliterate-mable-v4.2, abliterate-soul-5.5), pricing (credits with a rate per model, plus Free/Pro/Max, all marked planned), a Start Here guide for people who have never used an API, FAQ, status, acceptable-use policy, terms and privacy (no-logging pledge). Every page shows the deadpan notice that the models are fictional and that no model exists yet. Calls to action join the waitlist. Audience: developers first, plus non-technical people who want uncensored AI. Never use emoji. Record every question and answer, and the final copy for each page, in dialogue.md.
```
