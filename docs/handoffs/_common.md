# Common preamble (paste above every track prompt)

You are working in the abliterate repo (/Users/puredent/Desktop/abliterate, GitHub THAI-passport/abliterate), an
Astro + TypeScript storefront on Cloudflare Pages. Other agents are working on other tracks at the same time.

Before anything:
1. Read `AGENTS.md` (binding rules: no emoji, no system pop-ups, Lucide or in-house pixel icons only, tokens only,
   375 px / light+dark / focus / 44 px / reduced motion), `docs/DESIGN.md`, `problem_solution.md`, and
   `docs/IMPROVEMENTS.md` (the audit your track comes from).
2. Work in your own git worktree on branch `track-<letter>-<slug>`. `git pull` first.
3. Edit only the files your track owns (table in `docs/IMPROVEMENTS.md`). If you need a change elsewhere, write it
   down in your final report instead of making it.
4. Any user-facing text: load the `abliterate-voice` skill first. Code: `ponytail` (no new deps without need).
   Design: `hallmark` and `ui-ux-pro-max`. Icons: `lucide-icons`.
5. Never commit secrets. Never remove or edit the fictional-model notice.

Done means:
- `npm run build` passes.
- You checked the change in a browser at 1440 px, ~900 px and 375 px, light and dark, keyboard only.
- `problem_solution.md` has your entry under the P number you were given (append, never delete).
- `docs/DESIGN.md` has a dated subsection if you made a decision.
- `docs/IMPROVEMENTS.md` Status line for your track is updated.
- Small commits, message says what and why. Open a PR to `main`; do not merge it.
- Final report: what changed, what you verified and how, what you could not do and why.
