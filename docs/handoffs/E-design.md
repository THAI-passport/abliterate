# Track E: design pass on landing, models and pricing   (problem_solution entry: P18)

Paste `_common.md` above this. Load `hallmark` (audit mode first), `ui-ux-pro-max`, `abliterate-voice`.

Findings 14, 15, 16 in `docs/IMPROVEMENTS.md`. Files you own: `src/pages/index.astro`,
`src/pages/models/index.astro`, `src/pages/pricing.astro`, `src/components/ModelCard.astro`, new components,
and new tokens appended at the end of `:root` in `tokens.css`. Do not touch Nav, Base, the waitlist dialog or
the notice.

## 1. Audit before building
Run a hallmark audit of `/`, `/models/`, `/pricing/` on the live site (https://abliterate.pages.dev) at 1440 and
375 px. Write the findings as a short list at the top of P18 with a screenshot path each. Get the owner's ok on
the list before step 2 if anything changes the page structure.

## 2. Likely work (confirm with the audit)
- Landing rhythm: the quotes section is the most on-voice part and sits low; the trust row is dense text.
  Consider tightening the values row and giving the model strip more pixel character (in-house 16 px icons at
  integer scale only, 2x or 3x, never the GPU; P13 says 3x of the rough icons looked bad, so prefer the existing
  Lucide-in-notched-tile pattern for anything large).
- Models index: add a compact comparison table (name, best for, context, input, output) rendered from
  `models.ts`, each row linking to its detail page, with the "fictional" tag per row. Horizontal scroll inside a
  framed container at 375 px is fine (pricing already does this); the page itself must not scroll sideways.
- Pricing: a small credit estimator. Inputs: model (built-in listbox or radio group, not native `<select>`,
  AGENTS rule 2), input tokens per day, output tokens per day. Output: estimated credits per month, and which plan
  covers it. All numbers from `models.ts`/`plans.ts`, no prices typed in the component. Label it "planned rates,
  estimate only". Level 0 humour (pricing). Works without JS as a static rate table (already there).
- Hover/active states: stepped transitions only (`--step`), honour reduced motion.

## 3. Rules that bite here
No border-radius, no blur, no gradients that are not in the palette, no prose prices, no hype words outside the
hype zones (DESIGN.md), fictional tag on every model mention in a card or row.

## Verify
Before/after screenshots at 1440 and 375, light and dark, saved under `build/track-e/` (git-ignored) and
referenced in P18. Keyboard-only use of the estimator.
