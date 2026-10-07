import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://abliterate.app',
  i18n: { defaultLocale: 'en', locales: ['en'] }, // add 'th' when Thai pages land
});
