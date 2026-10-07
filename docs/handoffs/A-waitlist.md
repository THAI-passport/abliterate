# Track A: a waitlist that works and holds up   (problem_solution entry: P14)

Paste `_common.md` above this.

The waitlist is the only working part of the site, and today it does not work in production. Fix that, make the
site honest about it, and harden the endpoint. Findings 1, 2, 3, 4, 10 in `docs/IMPROVEMENTS.md`.

Files you own: `functions/`, `src/components/WaitlistDialog.astro`, `src/pages/status.astro`.

## 1. Make it work (needs the owner for one step)
- The owner must set the secret; you never see or type the key. Ask them to run:
  `npx wrangler pages secret put BUTTONDOWN_API_KEY --project-name abliterate`
  then redeploy: `npm run build && npx wrangler pages deploy dist --project-name abliterate --branch main`.
- Then test against production with an address the owner gives you: new address -> 200 and a confirmation email;
  same address again -> 200 (membership never revealed, P5); `not-an-email` -> 400 `invalid`.
- Log the real Buttondown duplicate response (status + body) with the existing `console.error` path or
  `npx wrangler pages deployment tail`, then replace the `/already|exists/` guess with the real match. Close P5.

## 2. Honest status until then
- Status page: the Waitlist row must not say `operational` when it is not. Simplest honest fix: a build-time
  constant in `status.astro` with a dated comment, flipped to `operational` only after step 1 passes. Do not
  build a live health check unless it is a few lines.

## 3. Abuse protection (cheapest first, stop when good enough)
- Honeypot field in the dialog (visually hidden, `tabindex="-1"`, `autocomplete="off"`, labelled for SR users
  as "Leave this empty"); the function returns the normal success reply and does nothing if it is filled.
- Origin check: reject (403, `server` error) when `Origin` is present and is not `https://abliterate.app` or a
  `*.abliterate.pages.dev` preview.
- Body size cap and `content-type: application/json` required.
- Cloudflare Turnstile only if the owner wants it (load `turnstile-spin` skill). Note: Turnstile loads a script
  from challenges.cloudflare.com, which conflicts with AGENTS rule 5 (no runtime CDN). Ask before adding; record
  the decision in DESIGN.md.
- Rate limit: prefer a Cloudflare dashboard WAF rate-limit rule on `/api/waitlist` (no code). Write the exact
  rule in P14 for the owner to click; do not add KV/Durable Objects for this.

## 4. Dialog behaviour
- Disable the submit button and set `aria-busy="true"` while the request runs; label stays literal
  (e.g. "Joining..." is fine, check the voice skill). Re-enable on error.
- Close on backdrop click (click target is the `<dialog>` itself). Escape already works.
- After the success panel shows, focus its Close button (already done); after close, return focus to the button
  that opened the dialog (store it on open).
- No `alert()`, no native validation bubbles (`novalidate` stays).

## Verify
Keyboard-only run through open -> invalid email -> fix -> submit -> success -> close, at 375 px light and dark.
curl the deployed function for: bad JSON, huge body, wrong Origin, honeypot filled, valid. Paste results in P14.
