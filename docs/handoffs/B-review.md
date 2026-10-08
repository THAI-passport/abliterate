# Track B Metadata, Security Headers & Fonts: Thought Process & Review Guide

**Problem Log:** `P15` in `problem_solution.md`  
**PR:** [THAI-passport/abliterate#4](https://github.com/THAI-passport/abliterate/pull/4)  
**Branch:** `track-b-meta-headers`  
**Author/Track:** Track B (Share, Search, Headers, Fonts)  
**Date:** 2026-10-08  

---

## 1. Context & Objectives (Findings 5, 6, 13)

Track B resolves Findings 5, 6, and 13 from `docs/IMPROVEMENTS.md`:

1. **Missing Search & Social Metadata (Finding 5):**
   - Links shared on Discord, X, or Telegram displayed bare URLs with no preview card, thumbnail, title, or summary.
   - Missing canonical URLs, `robots.txt`, and XML sitemap for search indexing.
2. **Missing HTTP Security Headers & Asset Caching (Finding 6):**
   - No `_headers` file existed for Cloudflare Pages.
   - Missing Content Security Policy (CSP), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, and `Permissions-Policy`.
   - Hashed static assets under `/_astro/*` and `/fonts/*` lacked long-term immutable caching headers.
3. **Font Bloat & Display Flash (Finding 13):**
   - `@fontsource` imported 25 font files (280 KB on disk) including Cyrillic, Greek, and Vietnamese subsets.
   - Above-the-fold display fonts (`Silkscreen 400` and `IBM Plex Sans 400`) were not preloaded, leading to a flash of unstyled/fallback font on initial load.

---

## 2. Technical Decisions & Thought Process

### 2.1 Metadata Architecture (`src/layouts/Base.astro`)
- **Canonical Trailing Slash Normalization:**
  Cloudflare Pages issues 308 permanent redirects from extensionless URLs without trailing slashes to trailing slash URLs (e.g. `/pricing` -> `/pricing/`).
  To prevent duplicate content and redirect chains, `Base.astro` normalizes all canonical URLs to end with a trailing slash:
  ```typescript
  if (!pathname.endsWith('/') && !pathname.includes('.')) {
    pathname = `${pathname}/`;
  }
  ```
- **Social Preview Meta Tags:**
  Added full Open Graph tags (`og:type`, `og:site_name`, `og:title`, `og:description`, `og:url`, `og:image`, `og:image:width`, `og:image:height`, `og:image:alt`) and Twitter summary card tags (`twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`).
- **Theme Color Synchronization:**
  Meta tags cannot read CSS variables at parse time. We explicitly mapped the `--paper` token values to `<meta name="theme-color">` using media queries:
  ```html
  <meta name="theme-color" content="#f4f2ec" media="(prefers-color-scheme: light)" />
  <meta name="theme-color" content="#0d0d0d" media="(prefers-color-scheme: dark)" />
  ```
- **Fictional Entity Compliance in JSON-LD:**
  On the landing page (`/`), we injected `Organization` and `WebSite` schema. We strictly avoided `Product` or `Offer` schema because the models are fictional placeholders and nothing is for sale (complying with `AGENTS.md`).

### 2.2 Pixel-Art Open Graph Card (`public/og/default.png`)
- Avoided AI generation tools or stock templates.
- Generated `public/og/default.png` (1200x630 px, 10.8 KB) using a deterministic Python Pillow script `art/src/og/_make.py`.
- Adheres strictly to the site's design system:
  - Exact `--paper` background and palette from `art/palette/site.json`.
  - Integer-scaled logo mark (2x = 64x64 px).
  - "Models that say yes." in Silkscreen.
  - The dev's GTX 750 hero card in an integer-scaled (4x = 288x176 px) notched frame with drop shadow.

### 2.3 Lightweight Native Sitemap (`src/pages/sitemap.xml.ts`)
- Rather than installing `@astrojs/sitemap` (which pulls 9 external npm dependencies), we implemented a 15-line native Astro TypeScript endpoint returning an XML sitemap of all 17 public routes.
- Fully dynamic and zero-dependency, adhering to `ponytail`.
- Added `public/robots.txt` allowing indexing and declaring the sitemap URL.

### 2.4 Security Headers & Cloudflare Caching (`public/_headers`)
- Configured Cloudflare Pages `_headers`:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
  - Strict `Content-Security-Policy`:
    `default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com; connect-src 'self' https://cloudflareinsights.com`
  - 1-year immutable caching on hashed build assets: `/_astro/*` and `/fonts/*` (`Cache-Control: public, max-age=31536000, immutable`).

### 2.5 Font Subset Optimization & Preloading
- Removed unused `@fontsource` Cyrillic, Greek, and Vietnamese subsets, retaining only latin, latin-ext, and Thai Looped.
- Preloaded `Silkscreen 400` and `IBM Plex Sans latin 400` using `<link rel="preload" as="font" type="font/woff2" crossorigin>` to eliminate font flash on initial hero render.

---

## 3. Verification Matrix

1. **Build Validation:** `npm run build` generates `sitemap.xml`, `robots.txt`, `_headers`, and optimized font bundles.
2. **Header & Meta Inspection:**
   - `<link rel="canonical">` verified matching trailing slashes across all 18 routes.
   - OG image renders crisp at 1200x630 px with 10.8 KB payload.
3. **Audit Suite:** Passes all 72 automated checks in `npm run audit`.
