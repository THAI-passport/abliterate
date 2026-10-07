# Track D: CI, checks and Git deploys   (problem_solution entry: P17)

Paste `_common.md` above this.

Findings 11, 12 in `docs/IMPROVEMENTS.md`. Files you own: `.github/`, `package.json` (scripts and devDeps only),
`tools/audit/`.

## 1. Local checks (one command)
- Add `@astrojs/check` and a `check` script: `astro check` (types in .astro and the function).
- Add `npm run audit`: a Playwright (or Puppeteer, whichever is lighter) script in `tools/audit/` that builds,
  serves `dist/` with `astro preview`, and for every built page x {375, 1440} x {light, dark} fails on:
  horizontal scroll (`scrollWidth > clientWidth`), any interactive element under 44x44 px (allow-list the
  in-sentence `.linkish` button with a comment pointing at P11), text contrast under 4.5:1 (compute from computed
  styles; large text 3:1), emoji in text (Unicode `\p{Extended_Pictographic}`), any `title=` attribute, any
  native `<select>`, any element with `alert(`/`confirm(`/`prompt(` in inline scripts, and any page missing the
  fictional notice text. This turns the AGENTS hard rules into a test. Recreate the P11 one-off audit rather than
  inventing new thresholds.
- Keep the existing `[COPY:` guard in `build`.

## 2. GitHub Actions
- `.github/workflows/ci.yml` on pull requests and pushes to `main`: Node 20, `npm ci`, `npm run check`,
  `npm run build`, `npm run audit`. Cache npm. Upload audit screenshots/report as an artifact on failure.
- Deploy: the current Pages project is direct-upload and cannot be Git-connected (P12). Two options; pick the
  first unless the owner objects:
  a. Keep the project and deploy from Actions with `cloudflare/wrangler-action` (`pages deploy dist
     --project-name abliterate --branch ${{ github.head_ref || github.ref_name }}`), so PRs get preview URLs
     and `main` deploys production. Needs repo secrets `CLOUDFLARE_API_TOKEN` (Pages:Edit only) and
     `CLOUDFLARE_ACCOUNT_ID`. The owner creates and pastes them in GitHub settings; you never handle the token.
     Write the exact token permissions in P17.
  b. Create a new Git-connected Pages project in the dashboard (owner clicks) and move the custom domain.
- Comment the preview URL on the PR (wrangler-action outputs `deployment-url`).

## 3. Repo hygiene
- `.nvmrc` with 20. Dependabot for npm, weekly, grouped.

## Verify
Open a PR from your branch and show CI green (and a deliberately broken commit going red, then reverted).
