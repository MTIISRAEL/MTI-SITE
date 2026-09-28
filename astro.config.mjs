import { defineConfig } from 'astro/config';

// One repo, three sites. SITE picks which one to build: spa, bath or hub.
const SITE = process.env.SITE || 'spa';
const DOMAINS = { spa: 'https://mtispa.co.il', bath: 'https://mtibath.co.il', hub: 'https://mti-israel.co.il' };
if (!DOMAINS[SITE]) throw new Error(`Unknown SITE "${SITE}". Use spa, bath or hub.`);

// Pages that exist on one site only.
const SITE_PAGES = {
  spa: [['/sale', 'sale.astro']],
  bath: [['/where-to-buy', 'where-to-buy.astro']],
  hub: [['/blog', 'blog.astro'], ['/blog/[post]', 'blog-post.astro']],
};
const sitePages = {
  name: 'mti-site-pages',
  hooks: {
    'astro:config:setup': ({ injectRoute }) => {
      for (const [pattern, file] of SITE_PAGES[SITE]) injectRoute({ pattern, entrypoint: `./src/site-pages/${file}` });
    },
  },
};

export default defineConfig({
  integrations: [sitePages],
  site: DOMAINS[SITE],
  outDir: `dist/${SITE}`,
  publicDir: `public/${SITE}`,
  trailingSlash: 'ignore',
  vite: { define: { 'import.meta.env.MTI_SITE': JSON.stringify(SITE) } },
});
