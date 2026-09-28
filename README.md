# MTI sites

Three static sites built with Astro from one codebase:

| Site | Domain | Build | Cloudflare worker |
| --- | --- | --- | --- |
| MTI SPA (sales to private customers) | mtispa.co.il | `npm run build:spa` | `mti-site` (wrangler.jsonc) |
| MTI BATH (brand site, sold via dealers) | mtibath.co.il | `npm run build:bath` | `mti-bath` (wrangler.bath.jsonc) |
| MTI ISRAEL (group site) | mti-israel.co.il | `npm run build:hub` | `mti-hub` (wrangler.hub.jsonc) |

- `npm run dev:spa` (or `dev:bath`, `dev:hub`) for local preview.
- `npm run build` builds all three into `dist/<site>/`; `npm run deploy` deploys all three.
- Content: `content/<site>/` (products, categories, dealers, posts as Markdown; `settings.json` for contact details and texts). Images: `public/<site>/media/`.
- Editing: `.pages.yml` configures Pages CMS for the office team.
- `scripts/import-old-sites.mjs` and `scripts/convert-import.py` did the one-off import from the old WordPress sites (raw data is on the `import-raw` branch).
