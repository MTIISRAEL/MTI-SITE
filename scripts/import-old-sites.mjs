// Crawls the old WordPress sites and saves page text + images under import/.
// Runs in GitHub Actions (see .github/workflows/import-old-sites.yml).
import fs from 'node:fs/promises';
import path from 'node:path';

const SITES = ['mtibath.co.il', 'mtispa.co.il'];
const MAX_PAGES = 400;
const UA = 'Mozilla/5.0 (MTI site migration)';
// Spam URLs injected into the old mtibath sitemap; never crawl them.
const SKIP = [/\/sale\/search\//, /\/wp-(admin|includes|json|login)/, /\.php/, /\/feed\/?$/, /\/cart|\/checkout|\/my-account/, /\?/];

const decode = (s) => s.replace(/&#(\d+);/g, (_, n) => String.fromCharCode(n)).replace(/&quot;/g, '"').replace(/&#039;|&apos;/g, "'").replace(/&amp;/g, '&').replace(/&nbsp;/g, ' ').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
const text = (html) => decode(html.replace(/<(script|style|noscript|svg)[\s\S]*?<\/\1>/gi, ' ').replace(/<br\s*\/?>|<\/(p|h\d|li|div|tr)>/gi, '\n').replace(/<[^>]+>/g, ' ')).replace(/[ \t]+/g, ' ').replace(/\n\s*\n+/g, '\n').trim();

async function get(url) {
  for (let i = 0; i < 3; i++) {
    try {
      const r = await fetch(url, { headers: { 'user-agent': UA }, redirect: 'follow' });
      return r;
    } catch (e) { await new Promise((res) => setTimeout(res, 1500 * (i + 1))); }
  }
  return null;
}

async function crawl(host) {
  const out = path.join('import', host);
  await fs.mkdir(path.join(out, 'images'), { recursive: true });
  const origin = `https://${host}`;
  const queue = [`${origin}/`];
  const seen = new Set(queue);
  const pages = [];
  const images = new Map();

  while (queue.length && pages.length < MAX_PAGES) {
    const url = queue.shift();
    const r = await get(url);
    if (!r || !r.ok || !(r.headers.get('content-type') || '').includes('html')) {
      pages.push({ url, status: r ? r.status : 'error' });
      continue;
    }
    const html = await r.text();
    const title = decode((html.match(/<title[^>]*>([\s\S]*?)<\/title>/i) || [])[1] || '').trim();
    const description = decode((html.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']*)/i) || [])[1] || '');
    const ogImage = (html.match(/<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']*)/i) || [])[1] || '';
    const main = (html.match(/<main[\s\S]*?<\/main>/i) || html.match(/<body[\s\S]*<\/body>/i) || [html])[0];
    const h1 = decode((main.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i) || [])[1] || '').replace(/<[^>]+>/g, '').trim();

    const pageImages = new Set();
    for (const m of main.matchAll(/(?:src|data-src|data-lazy-src|href)=["']([^"']+\/wp-content\/uploads\/[^"']+\.(?:jpe?g|png|webp|gif))["']/gi)) pageImages.add(m[1]);
    for (const m of main.matchAll(/url\(["']?([^"')]+\/wp-content\/uploads\/[^"')]+)["']?\)/gi)) pageImages.add(m[1]);
    for (const m of main.matchAll(/srcset=["']([^"']+)["']/gi)) {
      const best = m[1].split(',').map((s) => s.trim().split(/\s+/)).sort((a, b) => parseInt(b[1] || 0) - parseInt(a[1] || 0))[0];
      if (best && /wp-content\/uploads/.test(best[0])) pageImages.add(best[0]);
    }
    if (ogImage) pageImages.add(ogImage);

    const imgs = [];
    for (const src of pageImages) {
      const abs = new URL(src, url).href;
      if (!images.has(abs)) images.set(abs, null);
      imgs.push(abs);
    }
    pages.push({ url, status: r.status, title, h1, description, ogImage, images: imgs, text: text(main).slice(0, 20000) });

    for (const m of html.matchAll(/href=["']([^"'#]+)["']/gi)) {
      let u;
      try { u = new URL(m[1], url); } catch { continue; }
      if (u.host !== host) continue;
      u.hash = '';
      const href = u.href;
      if (SKIP.some((re) => re.test(href)) || /\.(jpe?g|png|webp|gif|pdf|zip|svg|xml|css|js)$/i.test(u.pathname)) continue;
      if (!seen.has(href)) { seen.add(href); queue.push(href); }
    }
    console.log(host, pages.length, url);
  }

  // Download images, capped so the repo stays small.
  let n = 0;
  for (const src of images.keys()) {
    if (n >= 1500) break;
    const rel = decodeURIComponent(new URL(src).pathname.replace(/^.*\/wp-content\/uploads\//, '')).replace(/[^\w.\-\/֐-׿]/g, '_');
    const file = path.join(out, 'images', rel);
    try {
      const r = await get(src);
      if (!r || !r.ok) continue;
      const buf = Buffer.from(await r.arrayBuffer());
      if (buf.length > 3_000_000) continue;
      await fs.mkdir(path.dirname(file), { recursive: true });
      await fs.writeFile(file, buf);
      images.set(src, path.relative(out, file));
      n++;
    } catch {}
  }

  await fs.writeFile(path.join(out, 'pages.json'), JSON.stringify(pages, null, 1));
  await fs.writeFile(path.join(out, 'images.json'), JSON.stringify(Object.fromEntries(images), null, 1));
  console.log(host, 'pages', pages.length, 'images', n);
}

async function spaProducts() {
  const all = [];
  for (let p = 1; p < 20; p++) {
    const r = await get(`https://mtispa.co.il/wp-json/wp/v2/product?per_page=100&page=${p}&_embed=1`);
    if (!r || !r.ok) break;
    const batch = await r.json();
    if (!batch.length) break;
    all.push(...batch.map((x) => ({
      id: x.id, slug: x.slug, link: x.link, title: decode(x.title?.rendered || ''),
      content: text(x.content?.rendered || ''), excerpt: text(x.excerpt?.rendered || ''),
      image: x._embedded?.['wp:featuredmedia']?.[0]?.source_url || null,
      terms: (x._embedded?.['wp:term'] || []).flat().map((t) => ({ taxonomy: t.taxonomy, name: decode(t.name) })),
      meta: x.meta || null, acf: x.acf || null,
    })));
  }
  await fs.mkdir('import/mtispa.co.il', { recursive: true });
  await fs.writeFile('import/mtispa.co.il/products-api.json', JSON.stringify(all, null, 1));
  console.log('spa products via API', all.length);
}

await spaProducts().catch((e) => console.log('spa API failed', e.message));
for (const s of SITES) await crawl(s);
