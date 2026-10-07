# Problems and solutions

Every pitfall hit and its fix (or OPEN). Never delete an entry.

## P1 Pixel tool warnings on the site palette (OPEN, harmless)

`pixel_tool.py` warns `palette has no named 'floor' subset` and `ramp 'action' has no visible hue shift`. Both checks come from the game the tool was copied from; the action ramp is a flat brand colour on purpose. Ignore them for site art.

## P2 Browser pane refuses localhost for this repo (OPEN)

The in-app browser denied http://localhost:4321 while the session's main folder was the bot repo. The dev server answers (curl 200). Check pages in a normal browser, or start a session rooted in this repo.

## P3 Redaction bar hides its text in forced-colors mode (OPEN)

`.redact` in `src/styles/global.css` uses `color: transparent` over a background. In Windows high contrast (`forced-colors: active`) backgrounds are dropped, so the text vanishes with no bar. Fix: inside `@media (forced-colors: active)` set `.redact { color: CanvasText; background: none; outline: 2px solid CanvasText; }`. Keep the word in the markup so screen readers read it. Rule: at most one bar per page, never in headings, titles, alt text, buttons, links, labels or errors (docs/DESIGN.md).

## P4 Waitlist tags conflict with the AGENTS.md privacy rule (OPEN)

AGENTS.md says mailing-list signup stores only the email and consent time. `website-v1.md` and `grill-v1.md` Q20 tag signups `plan:<name>` and `source:<page>` in Buttondown. The privacy copy in `dialogue.md` currently follows AGENTS.md (email and consent time only). Decide: drop the tags, or amend AGENTS.md and the privacy text to say a plan tag is stored.

## P2 update (2026-10-08)

The in-app browser opened http://localhost:4321 this time; pages were checked there and with headless Chrome screenshots. Status: SOLVED for now.

## P3 update (2026-10-08): SOLVED

`global.css` has the `@media (forced-colors: active)` rule (word shown, `CanvasText`, outlined, `forced-color-adjust: none`) and a print rule (`print-color-adjust: exact`) so the bar prints. Not seen in a real Windows high-contrast session yet.

## P4 update (2026-10-08): still OPEN, tags not sent

Until decided, `WaitlistDialog.astro` sends only `{ email }` and `functions/api/waitlist.ts` creates the subscriber with no tags and no metadata. The plan still shows in the dialog ("Joining for: Pro"). To turn tags on later: send the plan again and add `tags` in the function, after amending AGENTS.md and the privacy page.

## P5 Waitlist "already on the list" detection is unverified (OPEN)

The copy has two errors for an existing address ("already on the list", "waiting for confirmation"). The function treats Buttondown 409, or a 400 whose body says "already", as existing, then looks the subscriber up and reads `type`/`subscriber_type == "unactivated"` as unconfirmed. These Buttondown response shapes come from memory, not a real call: test with a real key on a preview deploy. Also note the trade-off: these messages tell anyone whether an address is on the list (the old function hid it on purpose).

## P6 Astro scoped styles do not reach `set:html` content

Classes inside HTML passed with `set:html` (the Start here "Join the waitlist" inline button, FAQ answer links) get no scoped `<style>` rules, because Astro adds its scope attribute only to elements written in the template. Fix: styles for such content go in `global.css` (`.linkish`).

## P7 `.section` wiped the side gutter at 375 px

`.section { padding: var(--s5) 0 }` came after `.wrap { padding: 0 var(--s2) }`, so `class="wrap section"` lost its side padding and content touched the screen edge on phones. Fix: `.section` sets `padding-block` only.

## P8 `[hidden]` lost to `display: flex`

The waitlist dialog's success panel showed under the form: `.body { display: flex }` beats the `hidden` attribute. Fix: `.body[hidden] { display: none }`. Same trap for any component that sets `display` on something it hides.

## P9 [CONFIRM] markers left visible (OPEN, owner to supply)

- pricing: Refunds and taxes: refund policy, tax handling.
- changelog: 0.0.0 domain registration date.
- legal/aup: unused credits after a violation.
- legal/terms: legal entity name and address; refunds; taxes; liability limit and jurisdiction wording; governing law and venue.
- legal/privacy: payment provider; controller and jurisdiction wording.
Also from dialogue.md "Open items": whether abuse reports and contact use the same address; have a lawyer review the legal drafts.

## P10 Copy lines worth a second look (not changed, per instructions)

- Landing "Pricing teaser" renders as "plans start at $0" (the Free plan price from data). Correct, but reads oddly; "start free" may be what was meant.
- FAQ "Who is this for?" uses "uncensored AI": the fixed vocabulary bans "AI" for what the API serves. It describes what people want, so it may be intended.

## P4 update (2026-10-08): SOLVED, tags dropped

Owner chose email and consent time only. Nothing to amend; the function and dialog already behave that way.

## P5 update (2026-10-08): decision made, API check still OPEN

Owner chose to hide membership: a duplicate gets the same success reply as a new address, and the `exists` / `unconfirmed` copy and parsing were removed. What remains unverified: the status and body Buttondown really returns for a duplicate (the function treats 409, or a 400 mentioning "already" or "exists", as success; any other 400 shows "invalid"). Needs a real call with a key in `.dev.vars` (wrangler is not installed here).

## P10 update (2026-10-08): SOLVED

There is no free plan. Free was removed from `plans.ts`, pricing, FAQ, landing and `dialogue.md`; the landing teaser now reads "credits start at $10" from the smallest top-up. "uncensored AI" stays in the FAQ. Stripe Tax and Stripe are filled into pricing, terms and privacy (P9 payment provider and taxes done).
