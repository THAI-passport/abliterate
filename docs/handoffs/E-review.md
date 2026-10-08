# Track E Design Pass: Thought Process, Architecture, and Next Pass Guide

**Problem Log:** `P18` in `problem_solution.md`  
**PR:** [THAI-passport/abliterate#3](https://github.com/THAI-passport/abliterate/pull/3)  
**Branch:** `track-e-design`  
**Author/Track:** Track E (Design pass on Landing, Models, and Pricing)  
**Date:** 2026-10-08  

---

## 1. Context & Motivation

Track E addresses Findings 14, 15, and 16 in `docs/IMPROVEMENTS.md`. 
Prior to this pass, the site had authentic copy and solid foundational styling, but suffered from three specific UX and visual flaws:

1. **Buried Brand Voice on Landing (Finding 14):**
   The deadpan humor and satirical tells ("What people are saying" fictional quotes) were pushed deep down to section 5 beneath a text-heavy values list, a code sample, and 6 large text cards. Visitors had to scroll substantially before discovering what made abliterate culturally distinct.
2. **Lack of Comparative Utility on Models (Finding 15):**
   The `/models` catalogue only displayed 6 standalone cards. A developer deciding between models had to read across multiple columns to compare context windows (32K vs 200K) and token economics ($0.10 vs $3.00).
3. **Cognitive Arithmetic Friction on Pricing (Finding 16):**
   "1 credit = $1 at each model's rate" is mathematically precise, but difficult for developers to translate into monthly cost or determine whether the Pro ($20/mo, 22 credits) or Max ($100/mo, 120 credits) tier would cover their daily usage.

---

## 2. Hallmark Audit & Design Principles Followed

We executed a Hallmark audit against the live site (`https://abliterate.pages.dev`) at 1440 px and 375 px, in both light and dark themes.

Key principles enforced:
- **Stepped Tactile Motion:** Retro aesthetics demand discretized transitions (`var(--t-fast) var(--step)`), not modern smooth bezier glides. Interactive elements depress on click (`transform: translate(var(--px), var(--px))`).
- **Integer-Scaled Pixel Art:** In `P13`, rough 16x16 icons displayed at 3x looked crude and bloated. For Track E, we used in-house pixel icons at **exact 2x integer scale** (32x32 px) rendered with `image-rendering: pixelated` inside notched `.frame` borders.
- **AGENTS.md Compliance:**
  - Zero emoji anywhere.
  - No native `<select>` dropdowns (Rule 2).
  - All numbers rendered dynamically from `src/data/models.ts` and `src/data/plans.ts` (no duplicate prose prices).
  - The `fictional` tag is rendered on every model mention.
  - Zero page-level horizontal overflow at 375 px.

---

## 3. Implementation Rationale & Component Architecture

### A. Landing Rhythm (`src/pages/index.astro`)
- **Quotes Section Elevation:**
  - *Decision:* Moved "What people are saying" immediately after the values row and directly above the code block and catalogue.
  - *Why:* Delivers the brand's deadpan personality early. It sets up the satirical framing before presenting the code sample and models.
- **Values Section Tightening:**
  - *Decision:* Replaced bulky vertical spacing with a compact 4-column strip of notched `.frame` cards with stepped hover translations.
- **Trust Section Restructuring:**
  - *Decision:* Converted the dense 6-item text list into a responsive 2/3-column grid of notched badge cards with minimum 44 px touch targets.

### B. Model Identity & Comparison (`src/components/ModelCard.astro` & `ModelComparisonTable.astro`)
- **Pixel Icon Badging (`ModelCard.astro`):**
  - Mapped each model to an in-house 16 px icon (`chip.png`, `unlocked.png`, `token.png`, `status.png`, `subscription.png`, `coin.png`) scaled at 2x (32 px).
  - Gives each model card immediate visual identity without GPU artwork saturation (reserving the GTX 750 art for the hero and status page as specified in `DESIGN.md`).
- **Comparison Matrix (`ModelComparisonTable.astro` on `/models`):**
  - Displays Model Name, Best for tagline, Context window, Input rate / 1M, and Output rate / 1M.
  - Enclosed in a notched `.scroll.frame`. On narrow mobile screens (375 px), only the table scrolls internally, preserving page-level lock.

### C. Credit Estimator (`src/components/CreditEstimator.astro` on `/pricing`)
- **Non-Native Custom Controls:**
  - Built an accessible radio-card group for model selection using `:has(input[type="radio"]:checked)` for tactile active states, fully navigable via Tab and Arrow/Space keys.
- **30-Day Projection Math:**
  - Computes `monthlyIn = inDaily * 30` and `monthlyOut = outDaily * 30`.
  - Calculates total credits: `((monthlyIn / 1M) * inRate) + ((monthlyOut / 1M) * outRate)`.
  - Compares against allowances parsed directly from `plans.ts` (Pro = 22 credits, Max = 120 credits, Top-ups = $10, $50, $200).
- **Tone Level:**
  - Level 0 humor (strictly serious and factual), labeled `"planned rates, estimate only"`.
- **Zero-JS Static Fallback:**
  - At build time, Astro statically calculates the initial projection for Dong Flash v2.3 (50K in / 10K out = 0.24 credits). If a visitor disables JavaScript, the estimator still renders a functional rate summary and plan recommendation.

---

## 4. Verification Evidence

All tests ran on clean production build (`dist/`):
1. **Build Validation:** `npm run build` succeeds (18 static pages, zero `[COPY:` placeholders).
2. **Visual & Responsive Testing:**
   - 1440 px desktop, 900 px tablet, and 375 px mobile verified in both light and dark mode.
   - Playwright check verified `document.documentElement.scrollWidth <= window.innerWidth` across all viewports.
3. **Keyboard Accessibility:**
   - Tested Tab focus traversal, Space key radio selection, number input typing, and Enter key preset activations on `/pricing/`.
4. **Visual Evidence:**
   - Before and after screenshot suite saved in git-ignored `build/track-e/` and documented in `problem_solution.md` under `P18`.

---

## 5. Guide for the Next Pass / Future Sessions

When continuing work on the frontend or adjacent tracks, keep these in mind:

1. **Waitlist & API Integration (Track A & P19) [COMPLETED]:**
   - The estimator recommends plans and top-up packs. In P19, `#est-cta-btn` was integrated into the recommendation card, passing `data-plan-name` ("Pro", "Max", or generic) directly to `WaitlistDialog.astro` while preserving the zero-JS static calculation fallback.
2. **Metadata & Open Graph (Track B):**
   - Model detail pages and pricing page will benefit from og:image cards showcasing the 2x pixel iconography and credit estimator rates.
3. **Adding New Models in Data:**
   - The estimator, comparison table, pricing table, and model cards all pull strictly from `src/data/models.ts`. If a model is added or edited, provide an in-house 16 px icon in `public/img/icons/` and map it in `ModelCard.astro`.
4. **Guardrails to Preserve:**
   - Never replace the radio-card selector with a native `<select>`.
   - Never remove the `fictional` tag from model cards or comparison rows.
   - Maintain stepped transition curves (`--step`) and `@media (prefers-reduced-motion: reduce)` overrides for any new UI element.
