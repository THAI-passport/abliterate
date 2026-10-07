export const nav = [
  { href: '/models', label: 'Models' },
  { href: '/pricing', label: 'Pricing' },
  { href: '/start', label: 'Start here' },
  { href: '/faq', label: 'FAQ' },
  { href: null, label: 'Docs', soon: true },
];

export const footer = [
  { title: 'Product', links: [['/models', 'Models'], ['/pricing', 'Pricing'], ['/start', 'Start here'], ['/changelog', 'Changelog'], ['/status', 'Status']] },
  { title: 'Company', links: [['/about', 'From the dev'], ['/faq', 'FAQ'], ['mailto:hello@abliterate.app', 'Contact']] },
  { title: 'Legal', links: [['/legal/terms', 'Terms'], ['/legal/privacy', 'Privacy'], ['/legal/aup', 'Acceptable use']] },
] as const;
