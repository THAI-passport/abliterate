# Track A: Waitlist Hardening & Honest Status — Thought Process & Review Guide

**Problem Log:** `P14` (and `P5` update) in `problem_solution.md`  
**PR:** [THAI-passport/abliterate#2](https://github.com/THAI-passport/abliterate/pull/2)  
**Branch:** `track-a-waitlist`  
**Author/Track:** Track A (A waitlist that works and holds up)  
**Date:** 2026-10-08  

---

## 1. Context & Motivation

Track A addresses Findings 1, 2, 3, 4, and 10 in `docs/IMPROVEMENTS.md`.

Before this track:
1. **False Status (Finding 1):** On the live deployment (`https://abliterate.pages.dev`), `POST /api/waitlist` returned `502 Bad Gateway` because the secret `BUTTONDOWN_API_KEY` was not configured in Cloudflare Pages. However, `/status` hard-coded `"Waitlist: operational"` and the fictional-model notice claimed *"The waitlist is the only part that works."*
2. **Unverified Duplicate Detection (Finding 2 / P5):** Buttondown duplicate-subscriber handling relied on an unverified regex guess (`/already|exists/i`) on 400 responses.
3. **Endpoint Vulnerable to Abuse (Finding 3):** No rate limiting, no honeypot, no Origin verification, and no payload size caps. A trivial script could spam `/api/waitlist` and inflate Buttondown subscriber billing.
4. **Double Submissions (Finding 4):** The waitlist modal submit button remained clickable and lacked `aria-busy` state during in-flight network requests.
5. **Modal Focus & Backdrop Gaps (Finding 10):** The native `<dialog>` did not close on backdrop click, and focus restoration to the triggering button could fail in Safari during the form-to-done panel swap.

---

## 2. Thought Process & Architectural Decisions

### 2.1 Honest Status First (`src/pages/status.astro`)
- **Problem:** When the live service fails, displaying "operational" breaks the site's binding commitment to accuracy (and the dev voice: *"The component table is accurate. The incident log is the dev's."*).
- **Decision:** Rather than building an over-engineered runtime health check that burns Cloudflare worker invocations or risks cascading failures, we implemented a build-time constant:
  ```typescript
  // 2026-10-08 (Track A): waitlist secret (BUTTONDOWN_API_KEY) is not yet set in production,
  // returning 502 on submissions. Flipped to 'degraded' until step 1 passes and production is verified.
  const waitlistStatus = 'degraded';
  ```
  The table renders `<span class="st st-degraded">degraded</span>` in amber (`--action-text`). Once the repository owner sets the secret and verifies live submissions, this single constant is flipped back to `'operational'`.

### 2.2 Layered Abuse Protection on `/api/waitlist` (`functions/api/waitlist.ts`)
We applied the **cheapest and most resilient defenses first**, adhering to `ponytail` (minimalism) and `AGENTS.md`:

1. **Strict Content-Type Validation:**
   Requires `Content-Type: application/json`. Non-JSON or missing content types return `400 {"error":"invalid"}` immediately before body parsing.
2. **Body Size Cap (1024 Bytes):**
   A legitimate waitlist payload contains only an email and optional honeypot field (`< 200 bytes`). We enforce a 1024-byte ceiling using `Content-Length` headers and `raw.length` checks, returning `413 {"error":"invalid"}`.
3. **Origin Allow-list Check:**
   If an `Origin` header is present, it is validated against:
   - Production domain: `https://abliterate.app`
   - Cloudflare Pages deployments: `^https:\/\/([a-zA-Z0-9-]+\.)?abliterate\.pages\.dev$`
   - Local development: `localhost` and `127.0.0.1`  
   Unauthorized origins are rejected with `403 {"error":"server"}`. Requests without `Origin` (such as curl scripts or same-origin HTTP navigations) proceed to email validation.
4. **Honeypot Field (`name="hp"`):**
   - In `WaitlistDialog.astro`, an input field is visually clipped using `.hp-field` (`width: 1px; height: 1px; clip: rect(0, 0, 0, 0); overflow: hidden; position: absolute;`).
   - Marked with `tabindex="-1"` and `autocomplete="off"` so sighted keyboard users and browser autofill will not interact with it.
   - Screen readers see an accessible label: `<label for="wl-hp">Leave this empty</label>`.
   - **Silent Sink:** If `body.hp` is populated, the endpoint returns `200 {"ok":true}` immediately without calling Buttondown. Spambots believe they succeeded while zero upstream API quota is spent.
5. **Decision on Cloudflare Turnstile (Omitted):**
   - Cloudflare Turnstile requires loading an external client script from `challenges.cloudflare.com`.
   - **AGENTS Rule 5 strictly dictates:** *"No runtime CDN. Astro + TypeScript build is fine; fonts and icons are vendored, never loaded from a CDN."*
   - Furthermore, CAPTCHAs introduce user friction and privacy leakage.
   - **Conclusion:** We explicitly omitted Turnstile. Honeypot + Origin checks + 1024-byte caps + Cloudflare edge WAF rate limiting provide robust protection without breaking AGENTS Rule 5.
6. **Edge Rate Limiting (Cloudflare WAF):**
   Rather than introducing stateful KV stores or Durable Objects (which add cold-start latency, complexity, and monthly cost), rate limiting should be configured at Cloudflare's edge in the dashboard (see Section 5).

### 2.3 Single-Read Upstream Logging (`functions/api/waitlist.ts`)
- **Fixing Buffer Reuse:** In earlier code, `await r.text()` was invoked conditionally multiple times on the Buttondown response.
- **Implementation:** We read the upstream response once (`const resText = await r.text();`) and log `console.error('buttondown', r.status, resText.slice(0, 500))` before matching.
- **Privacy Preservation:** Existing subscriber masking is preserved: HTTP 409 or HTTP 400 matching `/already|exists/i` returns `200 {"ok":true}` so malicious actors cannot query the endpoint to discover if an email is on the list.

### 2.4 Accessible Dialog State & Safari Focus Restoration (`WaitlistDialog.astro`)
1. **Double-Submit Prevention:**
   When the user submits the form, `setBusy(true)` sets `submitBtn.disabled = true`, adds `aria-busy="true"`, and sets the button text to literal `"Joining..."` (compliant with `abliterate-voice`). On any error, `setBusy(false)` re-enables the button and restores the plan-specific label.
2. **Native Backdrop Click Dismiss:**
   A click listener checks if the click target is the `<dialog>` element outside its bounding client rectangle:
   ```javascript
   dlg.addEventListener('click', (e) => {
     if (e.target === dlg) {
       const rect = dlg.getBoundingClientRect();
       const inDialog =
         rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
         rect.left <= e.clientX && e.clientX <= rect.left + rect.width;
       if (!inDialog) dlg.close();
     }
   });
   ```
3. **Explicit Trigger Focus Cache:**
   When a user opens the dialog from any button (`[data-waitlist]`), we cache `triggerEl = t`. On the dialog's native `'close'` event, we invoke `triggerEl.focus()`. This guarantees keyboard focus returns to the initiating button across all browsers, including Safari when swapping the DOM tree from form to success panel.
4. **No Pop-ups & Preserved `novalidate`:**
   Zero `alert()` calls, zero browser bubble validation. Errors are announced via `<p class="err" role="alert">`.

---

## 3. Verification Matrix & Evidence

### 3.1 Security & Curl Verification
Tested against the local Pages Functions server (`http://localhost:8788/api/waitlist`):

| Test Case | Request Payload / Headers | Expected Status | Actual Result |
|---|---|---|---|
| **Bad JSON** | `POST 'not a json'` | `400 Bad Request` | `{"error":"invalid"}` |
| **Huge Body** | `POST 1200+ byte email payload` | `413 Payload Too Large` | `{"error":"invalid"}` |
| **Disallowed Origin** | `Origin: https://evil.example.com` | `403 Forbidden` | `{"error":"server"}` |
| **Allowed Origin** | `Origin: https://preview.abliterate.pages.dev` | `400 Bad Request` (bad email) | `{"error":"invalid"}` |
| **Honeypot Filled** | `{"email":"bot@spam.com","hp":"bot"}` | `200 OK` (silent sink) | `{"ok":true}` |
| **Missing Secret** | `{"email":"valid@example.com"}` | `502 Bad Gateway` | `{"error":"server"}` |

### 3.2 Automated Browser & Responsive Verification
Executed using Playwright browser subagent across viewports and color schemes:
- **1440 px Desktop:**
  - Status page inspected: Waitlist row verified as `degraded` in amber text.
  - Keyboard navigation: Tabbed to "Join the waitlist", Enter opens modal. Focus trapped properly.
  - Honeypot verified visually hidden and bypassed by keyboard traversal.
  - Form validation: Invalid email shows error line, submit button re-enabled.
  - Backdrop click closes dialog, focus successfully returned to opener button.
- **900 px Tablet:**
  - Dialog opened and closed cleanly via `Escape` key.
- **375 px Mobile (Light & Dark):**
  - Zero horizontal overflow.
  - "Joining..." busy state observed on submit.
  - High-contrast text verified in dark mode.

### 3.3 CI & Audit Suite Verification
- `npm run check` (`astro check`): 0 errors, 0 warnings.
- `npm run audit` (Playwright automated audit across all 18 routes x 2 viewports x 2 themes = 72 checks): **100% SUCCESS**.

---

## 4. File Ownership

| File | Changes Made |
|---|---|
| `functions/api/waitlist.ts` | Origin check, Content-Type check, 1024B cap, honeypot sink, single-read upstream error logging |
| `src/components/WaitlistDialog.astro` | Honeypot field, `aria-busy` state, "Joining..." label, backdrop click, opener focus restoration |
| `src/pages/status.astro` | Build-time constant `waitlistStatus = 'degraded'` with explanatory dated comment |
| `problem_solution.md` | Appended entry `P14` with root causes, fixes, and curl outputs |
| `docs/DESIGN.md` | Documented Track A dated subsection and Turnstile omission rationale |
| `docs/IMPROVEMENTS.md` | Updated Track A status to done |

---

## 5. Guide for Future Sessions & Owner Next Steps

To complete full production verification and close `P5`:

1. **Configure Buttondown Secret (Owner Step):**
   ```bash
   npx wrangler pages secret put BUTTONDOWN_API_KEY --project-name abliterate
   ```
2. **Redeploy Production:**
   ```bash
   npm run build && npx wrangler pages deploy dist --project-name abliterate --branch main
   ```
3. **Verify Live Production Endpoint:**
   - Submit a new test address: Verify `200 OK` and receipt of Buttondown confirmation email.
   - Submit the same address again: Verify `200 OK` is returned (membership unrevealed).
   - In a terminal, run `npx wrangler pages deployment tail` to observe the exact duplicate response status and JSON payload from Buttondown.
   - If Buttondown's duplicate response matches `/already|exists/i`, P5 is verified. If the JSON shape differs, refine the regex in `functions/api/waitlist.ts`.
4. **Restore Status to Operational:**
   In `src/pages/status.astro`, change:
   ```typescript
   const waitlistStatus = 'operational';
   ```
5. **Enable Edge Rate Limiting (Cloudflare Dashboard):**
   - Go to Cloudflare Dashboard -> `abliterate.app` -> **Security** -> **WAF** -> **Rate limiting rules** -> **Create rule**.
   - Expression: `(http.request.uri.path eq "/api/waitlist" and http.request.method eq "POST")`
   - Threshold: `10 requests per 1 minute` per IP address.
   - Action: `Block` (or `Managed Challenge`) for `10 minutes`.
