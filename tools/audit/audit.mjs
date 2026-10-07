// DELIBERATE CI RED TEST
const deliberateTypeError: number = "not a number";

import { chromium } from 'playwright';
import { preview } from 'astro';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

// Discover all built HTML routes from dist/
function getHtmlRoutes(dir, base = '') {
  const routes = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      routes.push(...getHtmlRoutes(full, path.join(base, entry.name)));
    } else if (entry.name.endsWith('.html')) {
      let route = path.join(base, entry.name);
      if (route === 'index.html') route = '/';
      else if (route.endsWith('/index.html')) route = '/' + route.slice(0, -'/index.html'.length);
      else if (route.endsWith('.html')) route = '/' + route.slice(0, -'.html'.length);
      else route = '/' + route;
      routes.push(route);
    }
  }
  return routes;
}

export async function runAudit({ throwOnError = true, port = 4398, shouldBuild = true } = {}) {
  if (shouldBuild) {
    console.log('[audit] Building static site with npm run build...');
    const buildResult = spawnSync('npm', ['run', 'build'], { stdio: 'inherit' });
    if (buildResult.status !== 0) {
      throw new Error('[audit] npm run build failed');
    }
  }

  const distDir = path.resolve('dist');
  if (!fs.existsSync(distDir)) {
    throw new Error('[audit] dist/ directory not found');
  }

  const routes = getHtmlRoutes(distDir);
  console.log(`[audit] Auditing ${routes.length} pages across viewports {375, 1440} and themes {light, dark}...`);

  const server = await preview({ server: { port } });
  const browser = await chromium.launch();
  const page = await browser.newPage();

  const allFailures = [];
  const viewports = [375, 1440];
  const themes = ['light', 'dark'];
  const screenshotsDir = path.resolve('tools/audit/failures');

  // Clean failure screenshots directory
  if (fs.existsSync(screenshotsDir)) {
    fs.rmSync(screenshotsDir, { recursive: true, force: true });
  }

  try {
    for (const route of routes) {
      for (const width of viewports) {
        for (const theme of themes) {
          await page.setViewportSize({ width, height: 900 });
          await page.emulateMedia({ colorScheme: theme });
          
          const url = `http://localhost:${port}${route}`;
          await page.goto(url, { waitUntil: 'domcontentloaded' });
          // Align data-theme with simulated color scheme
          await page.evaluate((th) => {
            document.documentElement.setAttribute('data-theme', th);
          }, theme);

          const issues = await page.evaluate(({ theme }) => {
            const pageIssues = [];
            const doc = document.documentElement;
            const body = document.body;

            // 1. Horizontal scroll (scrollWidth > clientWidth)
            const scrollWidth = Math.max(doc.scrollWidth, body.scrollWidth);
            const clientWidth = doc.clientWidth;
            if (scrollWidth > clientWidth) {
              pageIssues.push({
                rule: 'horizontal_scroll',
                message: `Horizontal scroll detected: scrollWidth ${scrollWidth}px > clientWidth ${clientWidth}px`,
              });
            }

            // 2. Interactive elements under 44x44 px
            const interactiveElements = Array.from(document.querySelectorAll(
              'button:not([disabled]), input:not([type="hidden"]), select, textarea, [role="button"], a[href]'
            ));

            for (const el of interactiveElements) {
              // Ignore offscreen / visually hidden elements (e.g. skip-link)
              if (el.matches('.visually-hidden') || el.closest('.visually-hidden')) {
                continue;
              }

              // Allow-list in-sentence .linkish button per P11 (inline text link button in prose)
              if (el.matches('.linkish') || el.closest('.linkish')) {
                continue;
              }

              // Filter out invisible elements
              const style = window.getComputedStyle(el);
              if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                continue;
              }
              const rect = el.getBoundingClientRect();
              if (rect.width <= 1 && rect.height <= 1) {
                continue;
              }

              // Inline text links in prose paragraphs, table cells, or inline descriptions
              // are exempt per WCAG 2.5.8 / P11 (line-height constrained text links).
              // Standalone controls (buttons, nav links, footer navigation, inputs, cards)
              // must meet 44x44 px.
              const isInlineProseLink = el.tagName === 'A' &&
                (style.display === 'inline' || style.display === 'inline-block') &&
                !el.classList.contains('btn') &&
                !el.closest('nav') &&
                !el.closest('ul') &&
                !el.closest('.actions');

              if (isInlineProseLink) {
                continue;
              }

              if (rect.width < 44 || rect.height < 44) {
                pageIssues.push({
                  rule: 'touch_target',
                  message: `Interactive target <${el.tagName.toLowerCase()} class="${el.className}"> is ${Math.round(rect.width)}x${Math.round(rect.height)}px (under 44x44px). Text: "${el.textContent?.trim().slice(0, 30)}"`,
                });
              }
            }

            // Helper to parse rgb/rgba
            function parseColor(str) {
              if (!str || str === 'transparent') return { r: 0, g: 0, b: 0, a: 0 };
              const match = str.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
              if (!match) return null;
              return {
                r: parseInt(match[1], 10),
                g: parseInt(match[2], 10),
                b: parseInt(match[3], 10),
                a: match[4] !== undefined ? parseFloat(match[4]) : 1,
              };
            }

            // Linear channel for luminance
            function srgbToLinear(c) {
              const v = c / 255;
              return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
            }

            function getLuminance({ r, g, b }) {
              return 0.2126 * srgbToLinear(r) + 0.7152 * srgbToLinear(g) + 0.0722 * srgbToLinear(b);
            }

            function getContrast(lum1, lum2) {
              const l1 = Math.max(lum1, lum2);
              const l2 = Math.min(lum1, lum2);
              return (l1 + 0.05) / (l2 + 0.05);
            }

            // Alpha composite: fg over bg
            function composite(fg, bg) {
              const a = fg.a + bg.a * (1 - fg.a);
              if (a === 0) return { r: 0, g: 0, b: 0, a: 0 };
              return {
                r: Math.round((fg.r * fg.a + bg.r * bg.a * (1 - fg.a)) / a),
                g: Math.round((fg.g * fg.a + bg.g * bg.a * (1 - fg.a)) / a),
                b: Math.round((fg.b * fg.a + bg.b * bg.a * (1 - fg.a)) / a),
                a,
              };
            }

            // 3. Text contrast under 4.5:1 (large text 3:1)
            const textNodes = [];
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let n;
            while ((n = walker.nextNode())) {
              if (n.textContent && n.textContent.trim().length > 0) {
                textNodes.push(n);
              }
            }

            // Fallback background color based on theme
            const defaultBg = theme === 'dark' ? { r: 13, g: 13, b: 13, a: 1 } : { r: 244, g: 242, b: 236, a: 1 };

            for (const textNode of textNodes) {
              const parent = textNode.parentElement;
              if (!parent) continue;

              // Redaction bar deliberately uses color: transparent per docs/DESIGN.md
              if (parent.closest('.redact')) continue;

              const pStyle = window.getComputedStyle(parent);
              if (pStyle.display === 'none' || pStyle.visibility === 'hidden' || pStyle.opacity === '0') continue;
              if (parent.tagName === 'SCRIPT' || parent.tagName === 'STYLE' || parent.tagName === 'NOSCRIPT') continue;

              const fgColor = parseColor(pStyle.color);
              if (!fgColor || fgColor.a === 0) continue;

              // Resolve background color by traversing parents
              let curr = parent;
              let bgColor = { r: 0, g: 0, b: 0, a: 0 };
              while (curr) {
                const bgStyle = window.getComputedStyle(curr);
                const c = parseColor(bgStyle.backgroundColor);
                if (c && c.a > 0) {
                  bgColor = composite(c, bgColor);
                  if (bgColor.a >= 0.99) break;
                }
                curr = curr.parentElement;
              }
              if (bgColor.a < 1) {
                bgColor = composite(bgColor, defaultBg);
              }

              const fgFinal = composite(fgColor, bgColor);
              const fgLum = getLuminance(fgFinal);
              const bgLum = getLuminance(bgColor);
              const contrast = getContrast(fgLum, bgLum);

              const fontSize = parseFloat(pStyle.fontSize);
              const fontWeight = parseInt(pStyle.fontWeight, 10) || 400;
              const isLargeText = fontSize >= 24 || (fontSize >= 18.66 && fontWeight >= 700);
              const minContrast = isLargeText ? 3.0 : 4.5;

              if (contrast < minContrast) {
                pageIssues.push({
                  rule: 'text_contrast',
                  message: `Contrast ${contrast.toFixed(2)}:1 below ${minContrast}:1 on "${textNode.textContent.trim().slice(0, 30)}" in <${parent.tagName.toLowerCase()} class="${parent.className}"> (fg: ${pStyle.color}, bg: rgb(${bgColor.r},${bgColor.g},${bgColor.b}))`,
                });
              }
            }

            // 4. Emoji in text (Unicode \p{Extended_Pictographic})
            const emojiRegex = /\p{Extended_Pictographic}/u;
            if (emojiRegex.test(document.title || '')) {
              pageIssues.push({
                rule: 'emoji',
                message: `Emoji found in document.title: "${document.title}"`,
              });
            }
            for (const textNode of textNodes) {
              if (emojiRegex.test(textNode.textContent || '')) {
                pageIssues.push({
                  rule: 'emoji',
                  message: `Emoji found in text: "${textNode.textContent.trim().slice(0, 40)}"`,
                });
              }
            }

            // 5. any title= attribute
            const titled = Array.from(document.querySelectorAll('[title]'));
            for (const el of titled) {
              pageIssues.push({
                rule: 'title_attribute',
                message: `Element has forbidden title attribute: ${el.outerHTML.slice(0, 80)}`,
              });
            }

            // 6. any native <select>
            const selects = Array.from(document.querySelectorAll('select'));
            for (const el of selects) {
              pageIssues.push({
                rule: 'native_select',
                message: `Forbidden native select menu found: ${el.outerHTML.slice(0, 80)}`,
              });
            }

            // 7. inline alert/confirm/prompt in scripts or event handlers
            const scripts = Array.from(document.querySelectorAll('script:not([src])'));
            for (const s of scripts) {
              if (/\b(alert|confirm|prompt)\s*\(/.test(s.textContent || '')) {
                pageIssues.push({
                  rule: 'inline_dialog_call',
                  message: `Inline script contains alert/confirm/prompt: ${s.textContent.slice(0, 80)}`,
                });
              }
            }
            for (const el of Array.from(document.querySelectorAll('*'))) {
              for (const attr of el.attributes) {
                if (attr.name.startsWith('on') && /\b(alert|confirm|prompt)\s*\(/.test(attr.value)) {
                  pageIssues.push({
                    rule: 'inline_dialog_call',
                    message: `Inline event handler contains alert/confirm/prompt: ${attr.name}="${attr.value}"`,
                  });
                }
              }
            }

            // 8. Missing fictional notice
            const noticeText = 'Every model listed here is fictional and nothing can be run yet. Prices are planned. The waitlist is the only part that works.';
            if (!document.body.textContent?.includes(noticeText)) {
              pageIssues.push({
                rule: 'missing_fictional_notice',
                message: `Page missing mandatory fictional notice text: "${noticeText}"`,
              });
            }

            return pageIssues;
          }, { route, width, theme });

          if (issues.length > 0) {
            fs.mkdirSync(screenshotsDir, { recursive: true });
            const shotName = `${route.replace(/\//g, '_')}_${width}px_${theme}.png`;
            await page.screenshot({ path: path.join(screenshotsDir, shotName), fullPage: true });

            allFailures.push({
              route,
              width,
              theme,
              issues,
            });
          }
        }
      }
    }
  } finally {
    await browser.close();
    await server.stop();
  }

  if (allFailures.length > 0) {
    console.error(`\n[audit] FAILED: Found issues on ${allFailures.length} page/viewport combinations:`);
    for (const f of allFailures) {
      console.error(`\n--- ${f.route} (${f.width}px, ${f.theme}) ---`);
      for (const issue of f.issues) {
        console.error(`  [${issue.rule}] ${issue.message}`);
      }
    }
    if (throwOnError) {
      process.exit(1);
    }
    return false;
  }

  console.log(`\n[audit] SUCCESS: All ${routes.length} pages passed across 375px/1440px and light/dark modes!`);
  return true;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const shouldBuild = !process.argv.includes('--no-build');
  runAudit({ shouldBuild }).catch(err => {
    console.error('[audit] Fatal error:', err);
    process.exit(1);
  });
}
