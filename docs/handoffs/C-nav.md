# Track C: nav and mobile menu   (problem_solution entry: P16)

Paste `_common.md` above this.

Findings 7, 8, 9 in `docs/IMPROVEMENTS.md`. Files you own: `src/components/Nav.astro`, and one new token in
`src/styles/tokens.css` if needed.

1. Cramped desktop nav (~860-1050 px): "Start here" wraps. Fix with `white-space: nowrap` on links and move the
   breakpoint to where the row actually fits (measure; likely ~1024 px). Put the breakpoint value in one place.
2. Mobile menu: position it from the header itself (`.nav { position: relative }`, menu `top: 100%`) instead of
   the raw `4.25rem`, so a 3-line notice bar does not misplace it.
3. Close on Escape (return focus to the menu button), on a click outside, on a link click, and when the viewport
   grows past the breakpoint (`matchMedia(...).addEventListener('change')`).
4. Theme button: `aria-pressed` reflecting dark, label "Dark theme" so the state reads correctly.
5. Keep 44 px targets, visible focus, no animation added.

Verify keyboard-only at 375 px and ~900 px, light and dark.
