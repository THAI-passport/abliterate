# Track C Nav & Mobile Menu: Thought Process, Architecture, and Review Guide

**Problem Log:** `P16` in `problem_solution.md`  
**PR:** [THAI-passport/abliterate#1](https://github.com/THAI-passport/abliterate/pull/1)  
**Branch:** `track-c-nav`  
**Author/Track:** Track C (Nav and Mobile Menu)  
**Date:** 2026-10-08  

---

## 1. Context & Objectives (Findings 7, 8, 9)

Track C addresses Findings 7, 8, and 9 from `docs/IMPROVEMENTS.md`:

1. **Cramped Desktop Nav (~860–1050 px) (Finding 7):**
   - *Problem:* At viewports between ~860 px and ~1050 px, the desktop navigation row ran out of horizontal space. "Start here" wrapped onto two awkward lines, and the primary "Join the waitlist" call-to-action button was squeezed against the edge of the viewport.
   - *Root Cause:* The previous media query breakpoint was set too low at `860px`.
2. **Fragile Mobile Menu Positioning & Sticky State (Finding 8):**
   - *Problem:* The mobile dropdown menu was positioned using a hardcoded absolute offset: `top: 4.25rem`. When the top `<FictionNotice />` notice bar wrapped onto 2 or 3 lines (which regularly happens on 375 px mobile devices), the menu overlapped or was detached from the navigation bar.
   - *Behavioral Gaps:* The mobile menu lacked dismissal ergonomics: pressing `Escape` did not close the menu or return focus; clicking outside the menu did not close it; navigating to a link left the menu open; and resizing the window from mobile to desktop left a stale open dropdown.
3. **Theme Button State Accessibility (Finding 9):**
   - *Problem:* The theme button used a static `aria-label="Switch colour theme"` with no state indicator, meaning screen readers could not determine whether the active theme was light or dark.

---

## 2. Technical Decisions & Thought Process

### 2.1 Breakpoint Calculation & Single Source of Truth
- **Width Measurement:**
  - Logo width: ~135 px
  - Navigation links (Models, Start here, FAQ, Status, Pricing, Playground soon) with gaps: ~520 px
  - Action buttons (Theme toggle 44 px + Primary waitlist button ~170 px + gap): ~230 px
  - Outer gutters and internal spacing: ~40 px
  - **Total minimal comfortable row width:** ~925 px.
  - Adding safety margin for different system font metrics and rendering engines yields **1024 px** as the optimal breakpoint.
- **Single-Source Breakpoint:**
  - CSS contains the only media query definition: `@media (max-width: 1024px)`.
  - Links are protected with `white-space: nowrap` so text never breaks into multi-line fragments.
  - At $\le 1024\text{ px}$, the desktop row collapses into the hamburger menu button. Above $1024\text{ px}$, the complete navigation fits with ample breathing room.

### 2.2 Relative Header Positioning (Zero Hardcoded Offsets)
- **Eliminating `4.25rem`:**
  - Header is set to `.nav { position: relative; }`.
  - The mobile menu is positioned at `nav { position: absolute; left: 0; right: 0; top: 100%; }`.
- **Why This Matters:**
  - The top `<FictionNotice />` bar height changes dynamically based on screen width and text length. Because `top: 100%` calculates offset relative to the `<header class="nav">` element itself, the dropdown is guaranteed to dock immediately beneath the header regardless of the notice bar's height.

### 2.3 Dismissal State Machine (`matchMedia` vs `resize`)
- **Requirement:** Close menu when the viewport expands past the breakpoint.
- **Why `matchMedia` was chosen over `window.onresize`:**
  - `window.addEventListener('resize')` fires dozens of times per second during resizing, causing unnecessary layout queries.
  - The initial implementation used `!menu.offsetParent` inside a resize listener. `offsetParent` can be unreliable under complex CSS containment, transforms, or print media queries.
  - Using `const mql = matchMedia('(max-width: 1024px)'); mql.addEventListener('change', (e) => { if (!e.matches) setOpen(false); });` triggers an event **only once** when crossing the 1024 px threshold.
- **Click Dismissal:**
  - Event listener on `document` closes the menu if:
    1. Click occurs outside the header (`!target.closest('.nav')`).
    2. Click occurs on any nav link or waitlist button (`target.closest('#nav-links a, #nav-links [data-waitlist]')`).
    3. Clicking the theme button toggles the theme *without* closing the menu, allowing users to preview their theme before navigating.

### 2.4 Keyboard Navigation & Focus Restoration
- **Focus Management:**
  - When the menu opens via keyboard (`Enter` or `Space` on `.menu`), focus is immediately shifted to the first interactive item inside the menu:
    `if (open) links.querySelector<HTMLElement>('a, button')?.focus();`
  - When closing via `Escape`, focus is explicitly restored to the menu button:
    `else if (focusButton) menu.focus();`
  - When closed, `#nav-links` is set to `display: none;`, completely removing hidden links from the keyboard tab sequence.

### 2.5 Touch Target Compliance (AGENTS.md Rule 7)
- In the mobile menu column layout:
  `@media (max-width: 1024px) { ul a, .soon { width: 100%; } }`
- Making the links full-width ensures the entire row (375 px minus padding) is a valid touch area, with minimum height pinned to `var(--touch)` (44 px).
- Both `.menu` and `.theme` buttons enforce `min-width: var(--touch)` and `min-height: var(--touch)` (44x44 px).

### 2.6 Theme Toggle Accessibility & System Dark Mode
- **Screen Reader State:**
  - Configured `aria-label="Dark theme"`.
  - Added `aria-pressed="true"` when dark mode is active and `aria-pressed="false"` when light mode is active.
- **System Preference Sync:**
  - Added `matchMedia('(prefers-color-scheme: dark)').addEventListener('change')` to dynamically update `aria-pressed` if the user changes OS theme and has not set an explicit override in `localStorage`.
- **CSS Icon Alignment:**
  - Handled the edge case where no explicit `data-theme` attribute is set on `<html>` (using system default):
    ```css
    :root .theme .icon:last-child { display: none; }
    :root[data-theme='dark'] .theme .icon:first-child { display: none; }
    :root[data-theme='dark'] .theme .icon:last-child { display: block; }
    @media (prefers-color-scheme: dark) {
      :root:not([data-theme='light']) .theme .icon:first-child { display: none; }
      :root:not([data-theme='light']) .theme .icon:last-child { display: block; }
    }
    ```
  - Displays the sun icon in light mode and the moon icon in dark mode in all permutations.

### 2.7 Cross-Track Merge Strategy
- The prompt allowed adding one token to `src/styles/tokens.css` "if needed".
- Because standard CSS does not support `var()` within `@media (max-width: ...)`, creating a token in `tokens.css` would have provided no runtime benefit while risking merge conflicts with Track B (font declarations) and Track E (colors/tokens).
- Keeping all Nav styles self-contained within `Nav.astro` ensured clean, conflict-free merging into `main`.

---

## 3. Verification & Evidence

Automated verification was performed with Playwright and static build tooling:

1. **Static Build:** `npm run build` succeeds with zero errors and no leftover `[COPY:` placeholders.
2. **Automated Audit Suite (`npm run audit`):**
   - Verified across 18 routes $\times$ 2 viewports (375 px, 1440 px) $\times$ 2 color schemes (light, dark) = **72 total evaluations**.
   - Zero horizontal overflow (`scrollWidth <= clientWidth`).
   - Zero emoji in nav or theme controls.
   - All interactive touch targets $\ge 44\text{ px}$.
3. **Interactive & Keyboard Verification:**
   - **1440 px:** Desktop nav visible, `.menu` hidden, links do not wrap.
   - **900 px & 375 px:** `.menu` visible, `#nav-links` initially hidden.
   - **Keyboard Enter:** Opens menu, sets `aria-expanded="true"`, shifts focus to `Models` link.
   - **Keyboard Escape:** Closes menu, sets `aria-expanded="false"`, returns focus to `.menu`.
   - **Outside Click:** Clicking outside closes the menu.
   - **Link Click:** Clicking `/faq` navigates to page and closes menu.
   - **Breakpoint Crossing:** Resizing viewport from 900 px to 1100 px cleanly dismisses the open menu.
   - **Theme Toggle:** Toggling flips `aria-pressed` between `"false"` and `"true"`.

---

## 4. Guardrails & Guide for Future Sessions

When modifying the header or global navigation in future tracks, adhere to these rules:

1. **Preserve `1024px` Breakpoint:**
   Do not lower the breakpoint back to 860 px without removing links or shortening labels; doing so will re-introduce wrapping in the 860–1024 px range.
2. **Preserve Relative Header Positioning:**
   Never restore a fixed `top: <rem>` offset on `#nav-links`. The notice bar height fluctuates across devices.
3. **Touch Targets:**
   Any new button or link added to `.actions` or `ul` must retain `min-height: var(--touch)` (44 px) and `min-width: var(--touch)`.
4. **No Transitions on Menu Opening:**
   Per AGENTS.md, keep opening instantaneous (`display: none` / `display: flex`) with no motion or transitions added.
