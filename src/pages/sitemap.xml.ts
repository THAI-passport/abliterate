import type { APIRoute } from 'astro';
import { models } from '../data/models';

const staticPages = [
  '',
  'about/',
  'changelog/',
  'faq/',
  'models/',
  'pricing/',
  'start/',
  'status/',
  'legal/aup/',
  'legal/privacy/',
  'legal/terms/',
];

export const GET: APIRoute = ({ site }) => {
  const base = (site ?? new URL('https://abliterate.app/')).href.replace(/\/$/, '');
  const modelPages = models.map((m) => `models/${m.id}/`);
  const allPages = [...staticPages, ...modelPages];

  const urls = allPages
    .map((p) => `  <url>\n    <loc>${base}/${p}</loc>\n  </url>`)
    .join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
    },
  });
};
