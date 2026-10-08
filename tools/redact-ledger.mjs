// After the build: count every redaction bar in dist/ and write the number into the footer ledger.
// The footer renders before all pages exist, so it holds a placeholder that this script replaces.
import { readdirSync, readFileSync, writeFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
const files = [];
const walk = (d) => readdirSync(d).forEach((f) => { const p = join(d, f); statSync(p).isDirectory() ? walk(p) : p.endsWith('.html') && files.push(p); });
walk('dist');
const n = files.reduce((sum, f) => sum + (readFileSync(f, 'utf8').match(/class="redact"/g) ?? []).length, 0);
for (const f of files) writeFileSync(f, readFileSync(f, 'utf8').replaceAll('__REDACT_COUNT__', String(n)));
console.log(`[ledger] ${n} bars across ${files.length} pages`);
