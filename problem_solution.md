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

## P5 update 2 (2026-10-08): docs checked, live call still OPEN

Buttondown's create-subscriber docs say a duplicate email returns HTTP 400 ("the subscriber will not be created") and a new one gets double opt-in by default; auth is `Authorization: Token <key>` (matches the function). The 400 body text is not documented, so the function's `/already|exists/` match on a 400 is a guess; a 400 with other text shows "invalid". Still to do: one real call with a key in `.dev.vars` to read the actual body, then tighten the match.

## P11 Contrast and touch-size fixes from the 2026-10-08 audit (SOLVED)

A scripted audit (13 pages x 375/1440 px x light/dark: sideways scroll, targets under 44 px, text contrast under 4.5:1) found: bright orange text on paper at 3.0:1 (Status "degraded", waitlist error line); the green "operational" at 3.9:1; the orange "Notice" tag on the light notice bar in dark mode at 2.8:1; menu, theme and footer FAQ targets 31 to 35 px wide. Fix, tokens only: `--ok` darker, new `--action-text` and `--on-redact-accent`, `min-width: var(--touch)`. After the fix every combination passes. Not covered: the inline "Join the waitlist" link-button in Start step 2 is 27 px tall (in-sentence link, left as is); the print layout of the 404 and Status pages shows the mobile menu button (harmless, bars print as bars). Forced-colors was not emulated (needs DevTools rendering emulation, which this session cannot reach): open `/404` and `/status` with Emulate CSS forced-colors: active and confirm the barred word shows outlined.

## P12 Cloudflare Pages settings (written down, not yet checked in the dashboard)

Build command `npm run build`, output directory `dist`, Node 20 or newer, no root directory. Functions are picked up from `functions/` at the repo root. Secret: `BUTTONDOWN_API_KEY` as an encrypted variable for Production and Preview. No `wrangler.toml` exists; local testing needs `npx wrangler pages dev dist` with a `.dev.vars` file (git-ignored).

## P12 update (2026-10-08): deployed by direct upload

Logged in with `npx wrangler login` (OAuth in the browser). Created Pages project `abliterate` (production branch `main`) and deployed `dist/` with `npx wrangler pages deploy dist --project-name abliterate --branch main`; the `functions/` bundle uploaded with it. Live at https://abliterate.pages.dev. Smoke test: `/` 200, `/nope` 404, `/pricing` 308 (trailing slash redirect), POST `/api/waitlist` with a bad email gives 400 `invalid`, with a good one gives 502 `server` because `BUTTONDOWN_API_KEY` is not set yet (expected). Trade-off: a direct-upload project cannot be switched to Git integration later; to deploy from GitHub pushes, create a second Pages project from the dashboard (Connect to Git, `npm run build`, output `dist`). To redeploy: `npm run build && npx wrangler pages deploy dist --project-name abliterate --branch main`. To finish P5: set the secret with `npx wrangler pages secret put BUTTONDOWN_API_KEY --project-name abliterate` (you type the key), then redeploy and test with a real address.

## P13 In-house pixel icons read as crude and wide at 48 px (SOLVED for the feature row, dialog and pricing)

The 16x16 pixel icons (chip, unlocked, coin, envelope) were shown at 3x on the landing page and looked rough and wide next to the text. Replaced them with Lucide glyphs (`plug`, `lock-open`, `coins`, `shield-check`, `mail`, `calendar-clock`) inside a notched `.tile frame` (global.css), so the pixel look stays in the frame and the glyph stays crisp. The pixel art files remain in `art/` and `public/img/icons/` and are still used by the model cards and Status page.

## P16 Nav cramped at 860-1050 px, mobile menu sticky (SOLVED, Track C)

At ~800-1040 px "Start here" and "Join the waitlist" wrapped to two lines. The mobile menu sat at a raw `top: 4.25rem` (wrong when the notice bar wraps to three lines at 375 px), never closed except by its own button, and stayed open after resizing to desktop. Fix in `Nav.astro`: `white-space: nowrap` on links and actions, breakpoint moved to 1024 px (the only copy of it; the script checks whether the menu button is visible instead of repeating the number), menu positioned `top: 100%` of a `position: relative` header, closes on Escape (focus back to the button), outside click, link or waitlist click, and on growing past the breakpoint; opening moves focus to the first link. Theme button now reads "Dark theme" with `aria-pressed`. Checked at 1040 px and 375 px, light and dark, no sideways scroll.

## P16 update (2026-10-08): Track C verification and matchMedia refinement

Replaced `resize` listener with `matchMedia('(max-width: 1024px)').addEventListener('change')` to close stale mobile menus cleanly on crossing past the breakpoint without resize event overhead. Added system theme change listener (`matchMedia('(prefers-color-scheme: dark)')`) and CSS support so theme icon and `aria-pressed` state stay synchronized when no manual preference is set. Made mobile links full width for easy touch access. Verified keyboard-only (Tab, Enter to open, first link focused, Escape to close with focus returning to menu button), click outside, link click navigation, and touch targets >= 44px at 1440px, 900px, and 375px in both light and dark mode.

## P14 Waitlist hardening, abuse protection, and honest status (SOLVED, Track A)

Findings 1, 2, 3, 4, 10 in `docs/IMPROVEMENTS.md`.

### Problems and Fixes

1. **Honest status (Finding 1)**: In production, the waitlist secret `BUTTONDOWN_API_KEY` was not configured, returning 502 Bad Gateway on submissions while `/status` displayed "Waitlist: operational". Flipped `Waitlist` row in `src/pages/status.astro` to `degraded` via a build-time constant `waitlistStatus = 'degraded'` with a dated comment. Once the owner sets the secret and verifies production submissions, this constant can be flipped to `'operational'`.
2. **Abuse protection (Finding 3)**:
   - **Content-Type**: strictly requires `application/json` (returns 400 `{"error":"invalid"}` otherwise).
   - **Body size cap**: capped at 1024 bytes max, checked via `Content-Length` and `raw.length` (returns 413 `{"error":"invalid"}`).
   - **Origin check**: when `Origin` header is present, rejects requests with 403 `{"error":"server"}` unless matching `https://abliterate.app`, `*.abliterate.pages.dev` previews, or local development origins (`localhost`, `127.0.0.1`).
   - **Honeypot**: added hidden input `name="hp"` in `WaitlistDialog.astro` (`tabindex="-1"`, `autocomplete="off"`, visually hidden with `.hp-field`, labelled for screen readers as "Leave this empty"). The endpoint returns 200 `{"ok":true}` immediately without calling Buttondown if the honeypot is populated.
   - **Cloudflare WAF rate limiting**: rather than expensive KV/Durable Objects, rate limiting should be enabled directly at Cloudflare's edge in the Cloudflare dashboard:
     - Navigation: Cloudflare Dashboard -> `abliterate.app` -> **Security** -> **WAF** -> **Rate limiting rules** -> **Create rule**.
     - Rule name: `Rate limit waitlist submissions`
     - Expression: `(http.request.uri.path eq "/api/waitlist" and http.request.method eq "POST")`
     - Rate limit criteria: `10 requests per 1 minute` per IP address.
     - Action: `Block` (or `Managed Challenge`) for `10 minutes`.
3. **Double submit & busy state (Finding 4)**:
   - Submit button in `WaitlistDialog.astro` is disabled upon submission with `aria-busy="true"` and label updated to literal `"Joining..."`.
   - On error, `aria-busy` is removed, button is re-enabled, and the original plan-aware label is restored.
4. **Dialog backdrop click & focus restoration (Finding 10)**:
   - Added backdrop click listener checking click target is `<dialog>` outside its bounding rect, closing the dialog.
   - Stored the trigger button element upon dialog open; on dialog `'close'` event, keyboard focus is explicitly restored to the triggering element (preventing focus loss in Safari during DOM panel swaps).
5. **Buttondown duplicate logging (P5)**:
   - Single-read response text handling in `functions/api/waitlist.ts` with `console.error('buttondown', r.status, resText.slice(0, 500))` to log upstream response shape for diagnosis in Cloudflare logs or `npx wrangler pages deployment tail`.

### Curl Verification Results

Tested against the local Cloudflare Pages Functions server (`http://localhost:8788/api/waitlist`):

```bash
# 1. Bad JSON
curl -i -s -X POST http://localhost:8788/api/waitlist \
  -H "content-type: application/json" \
  -d 'not a json'
# Result: HTTP/1.1 400 Bad Request
# {"error":"invalid"}

# 2. Huge Body (> 1024 bytes)
curl -i -s -X POST http://localhost:8788/api/waitlist \
  -H "content-type: application/json" \
  -d "{\"email\":\"$(python3 -c 'print("a"*1200)')@example.com\"}"
# Result: HTTP/1.1 413 Payload Too Large
# {"error":"invalid"}

# 3. Disallowed Origin
curl -i -s -X POST http://localhost:8788/api/waitlist \
  -H "content-type: application/json" \
  -H "origin: https://evil.example.com" \
  -d '{"email":"test@example.com"}'
# Result: HTTP/1.1 403 Forbidden
# {"error":"server"}

# 4. Honeypot Filled
curl -i -s -X POST http://localhost:8788/api/waitlist \
  -H "content-type: application/json" \
  -H "origin: https://abliterate.app" \
  -d '{"email":"bot@example.com","hp":"I am a bot"}'
# Result: HTTP/1.1 200 OK
# {"ok":true}

# 5. Valid Format (without secret set in dev)
curl -i -s -X POST http://localhost:8788/api/waitlist \
  -H "content-type: application/json" \
  -H "origin: https://abliterate.app" \
  -d '{"email":"user@example.com"}'
# Result: HTTP/1.1 502 Bad Gateway (logged waitlist: BUTTONDOWN_API_KEY is not set)
# {"error":"server"}
```

### Steps for Owner to Finish Production Setup

1. Set the Buttondown secret in Cloudflare Pages:
   ```bash
   npx wrangler pages secret put BUTTONDOWN_API_KEY --project-name abliterate
   ```
2. Redeploy the project:
   ```bash
   npm run build && npx wrangler pages deploy dist --project-name abliterate --branch main
   ```
3. Test production:
   - Submit new test email: returns 200 and triggers confirmation email.
   - Submit the same email again: returns 200 (membership hidden).
   - Submit `not-an-email`: returns 400 `{"error":"invalid"}`.
   - Check `npx wrangler pages deployment tail` to verify Buttondown status and body payload.
4. Flip `waitlistStatus = 'operational'` in `src/pages/status.astro`.

