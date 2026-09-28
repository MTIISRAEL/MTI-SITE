#!/usr/bin/env python3
"""One-off: turn the raw crawl in import/ into content/<site>/ Markdown and public/<site>/media/.

Run after scripts/import-old-sites.mjs has filled import/ (it lives on the import-raw branch).
Re-running overwrites generated files, so hand edits to generated products would be lost.
"""
import json, re, shutil, collections, unicodedata
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
IMPORT = ROOT / 'import'


def load(host):
    pages = [p for p in json.load(open(IMPORT / host / 'pages.json')) if p.get('status') == 200 and p.get('title') is not None]
    images = json.load(open(IMPORT / host / 'images.json'))
    return pages, images


def yaml_str(s):
    return json.dumps(s, ensure_ascii=False)


def slugify(s, used):
    s = unicodedata.normalize('NFKC', s).lower()
    s = re.sub(r'[׳\'"״”“]', '', s)
    s = re.sub(r'[^a-z0-9֐-׿]+', '-', s).strip('-')[:60].strip('-') or 'item'
    base, n = s, 2
    while s in used:
        s = f'{base}-{n}'; n += 1
    used.add(s)
    return s


def clean_title(t, brand):
    return re.sub(rf'\s*[-|–]\s*{brand}\s*$', '', t, flags=re.I).strip()


RESIZED = re.compile(r'-\d{2,4}x\d{2,4}(?=\.\w+$)')


def product_images(page, images, shared, limit=6):
    """Images that belong to this product: not site-wide assets, largest variant, downloaded."""
    out = []
    for src in page.get('images', []):
        key = RESIZED.sub('', src)
        if key in shared or src.lower().endswith('.gif'):
            continue
        # Prefer the original over resized variants when both were downloaded.
        pick = key if images.get(key) else src
        if not images.get(pick):
            continue
        if pick not in out:
            out.append(pick)
    return out[:limit]


def shared_images(pages):
    count = collections.Counter()
    for p in pages:
        for k in {RESIZED.sub('', s) for s in p.get('images', [])}:
            count[k] += 1
    return {k for k, v in count.items() if v > 3}


def copy_media(site, host, images, src):
    rel = images[src]
    dest_name = re.sub(r'[^\w.\-]', '_', unquote(Path(rel).name))
    dest_name = f"{Path(rel).parent.as_posix().replace('/', '-').replace('images-', '')}-{dest_name}"
    dest = ROOT / 'public' / site / 'media' / dest_name
    if not dest.exists():
        shutil.copyfile(IMPORT / host / rel, dest)
    return f'/media/{dest_name}'


def lines(text):
    return [l.strip() for l in text.split('\n') if l.strip()]


def parse_pairs(ls, labels, start=None, stop=None):
    """Label line followed by a value line, inside an optional start/stop window."""
    if start and start in ls:
        ls = ls[ls.index(start):]
    if stop and stop in ls:
        ls = ls[:ls.index(stop)]
    specs, seen = [], set()
    for i, l in enumerate(ls[:-1]):
        if l in labels and l not in seen:
            v = ls[i + 1]
            if v in labels or len(v) > 60:
                continue
            specs.append({'label': labels[l], 'value': v})
            seen.add(l)
    return specs


def write_md(path, data, body=''):
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = ['---']
    for k, v in data.items():
        if v is None or v == [] or v == '':
            continue
        if isinstance(v, list) and v and isinstance(v[0], dict):
            fm.append(f'{k}:')
            for item in v:
                fm.append('  - ' + '\n    '.join(f'{ik}: {yaml_str(iv)}' for ik, iv in item.items()))
        elif isinstance(v, list):
            fm.append(f'{k}:')
            fm += [f'  - {yaml_str(i)}' for i in v]
        elif isinstance(v, bool) or isinstance(v, (int, float)):
            fm.append(f'{k}: {str(v).lower() if isinstance(v, bool) else v}')
        else:
            fm.append(f'{k}: {yaml_str(v)}')
    fm.append('---')
    path.write_text('\n'.join(fm) + '\n' + (body.strip() + '\n' if body else ''), encoding='utf-8')


def reset(site):
    for sub in ('categories', 'products', 'posts'):
        d = ROOT / 'content' / site / sub
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    m = ROOT / 'public' / site / 'media'
    if m.exists():
        shutil.rmtree(m)
    m.mkdir(parents=True)


# ---------------------------------------------------------------- bath
BATH_CATS = [
    ('bathtubs', 'אמבטיות וג׳קוזי', 'אמבטיות אקריליות וג׳קוזי ביתי, פינתיות, מלבניות ועגולות, בכל הגדלים.', 1),
    ('freestanding', 'אמבטיות Free Standing', 'אמבטיות עומדות, אובליות, מלבניות, עגולות ופינתיות, שהופכות את חדר הרחצה לחדר מעוצב.', 2),
    ('shower-trays', 'אגניות', 'אגניות אקריליות לכל סוגי המקלחונים: קלאסיות, עם תעלת ניקוז, אורבן ומלאות.', 3),
    ('showers', 'מקלחונים', 'מקלחונים ואמבטיונים חזיתיים ופינתיים, בסגירה מלאה או חלקית, וגם בהתאמה אישית.', 4),
    ('surplus', 'עודפים', 'דגמי תצוגה ועודפי מלאי במחירים מיוחדים.', 5),
]
BATH_LEAVES = {
    'bath/acrylic-corner-baths-jacuzzi/': ('bathtubs', 'פינתיות'),
    'bath/rectangular-acrylic-jacuzzi-baths/': ('bathtubs', 'מלבניות'),
    'bath/round-acrylic-jacuzzi-baths/': ('bathtubs', 'עגולות'),
    'bath/oval-baths-free-standing/': ('freestanding', 'אובליות'),
    'bath/rectangular-baths-free-standing/': ('freestanding', 'מלבניות'),
    'aganiuot/aganiuot-classics/': ('shower-trays', 'קלאסיות'),
    'aganiuot/aganiuot-drainage-channels/': ('shower-trays', 'תעלת ניקוז'),
    'aganiuot/aganiuot-urban/': ('shower-trays', 'אורבן'),
    'aganiuot/aganiuot-fullness/': ('shower-trays', 'מלאות'),
    'showers/full-closing-bath/': ('showers', 'אמבטיון סגירה מלאה'),
    'showers/shower-baths-partially-closed/': ('showers', 'אמבטיון סגירה חלקית'),
    'showers/front-shower/': ('showers', 'חזיתי'),
    'showers/corner-shower/': ('showers', 'פינתי'),
    'surpluses/': ('surplus', None),
}
BATH_SPEC_LABELS = {
    'אורך (ס"מ)': 'אורך (ס"מ)', 'רוחב (ס"מ)': 'רוחב (ס"מ)', 'גובה (ס"מ)': 'גובה (ס"מ)',
    'מרחק לניקוז (ס"מ)': 'מרחק לניקוז (ס"מ)', 'משקל (ק"ג)': 'משקל (ק"ג)', 'תכולת מים (ליטר)': 'תכולת מים (ליטר)',
    'סוג אמבטיה': 'סוג', 'עיצוב': 'עיצוב', 'כמות רוחצים': 'כמות רוחצים', 'ניקוז': 'ניקוז',
    'אפשרויות התקנה': 'התקנה', 'סוג התקנה': 'התקנה', 'סוג זכוכית': 'זכוכית', 'עובי זכוכית': 'עובי זכוכית',
    'גובה מקלחון': 'גובה מקלחון', 'פרופיל': 'פרופיל', 'צבע פרופיל': 'צבע פרופיל',
}


def bath():
    host, site, brand = 'mtibath.co.il', 'bath', 'MTI BATH'
    pages, images = load(host)
    reset(site)
    shared = shared_images(pages)
    by_path = {p['url'].split('/product-category/')[1]: p for p in pages if '/product-category/' in p['url']}
    prods = [p for p in pages if '/product/' in p['url']]

    # Membership: a product belongs to the leaf category whose listing mentions its title.
    member = {}
    for leaf, (cat, typ) in BATH_LEAVES.items():
        texts = [p['text'] for path, p in by_path.items() if path == leaf or (path.startswith(leaf + 'page/'))]
        blob = '\n'.join(texts)
        for p in prods:
            t = (p['h1'] or clean_title(p['title'], brand)).strip()
            if t and t in blob and p['url'] not in member:
                member[p['url']] = (cat, typ)

    used, n = set(), 0
    cat_images = {}
    for p in prods:
        title = (p['h1'] or clean_title(p['title'], brand)).strip()
        crumb = next((l for l in lines(p['text'])[:3] if l.startswith('דף הבית /')), '')
        cat, typ = member.get(p['url'], (None, None))
        if not cat:
            top = crumb.split('/')[1].strip() if crumb.count('/') >= 2 else ''
            cat = {'אמבטיות וג\'קוזי': 'bathtubs', 'אגניות': 'shower-trays', 'מקלחונים': 'showers', 'עודפים': 'surplus'}.get(top)
            if 'Free Standing' in title:
                cat = 'freestanding'
            if 'התאמה אישית' in title:
                cat, typ = 'showers', 'בהתאמה אישית'
        if not cat:
            print('bath: no category for', title)
            continue
        ls = lines(p['text'])
        specs = parse_pairs(ls, BATH_SPEC_LABELS, start='מפרט טכני', stop='לקבלת פרטים על המוצר')
        if 'מפרט צבעים' in ls and 'מפרט טכני' in ls:
            window = ls[ls.index('מפרט צבעים') + 1:ls.index('מפרט טכני')]
            colors = list(dict.fromkeys(c for c in window if 'לחיצים' not in c and len(c) < 25))
            if colors:
                specs.append({'label': 'צבעים', 'value': ', '.join(colors)})
        imgs = [copy_media(site, host, images, s) for s in product_images(p, images, shared)]
        if imgs and cat not in cat_images:
            cat_images[cat] = imgs[0]
        slug = slugify(re.sub(r'\s*(צד|מספר).*$', '', title), used)
        write_md(ROOT / 'content' / site / 'products' / f'{slug}.md', {
            'title': title, 'category': cat, 'type': typ, 'summary': '',
            'images': imgs, 'specs': specs, 'order': 100, 'old_url': p['url'],
        })
        n += 1

    for cid, title, summary, order in BATH_CATS:
        write_md(ROOT / 'content' / site / 'categories' / f'{cid}.md',
                 {'title': title, 'summary': summary, 'image': cat_images.get(cid), 'order': order})
    print('bath products', n)


# ---------------------------------------------------------------- spa
SPA_CATS = [
    ('hot-tubs', 'ג׳קוזי לבית ולגינה', 'מערכות ספא חיצוניות לחצר, למרפסת ולגג, מ-2 ועד 7 רוחצים.', 1),
    ('swim-spas', 'בריכות שחייה נגד זרם', 'בריכת זרמים ששוחים בה במקום, בדגם מחולק או משולב עם ספא.', 2),
    ('equipment', 'ציוד וחומרים', 'כיסויים, משאבות, גופי חימום, פילטרים, חלקי חילוף וחומרי תחזוקה לג׳קוזי ולבריכה.', 3),
]
SPA_TYPE = {
    "ג'קוזי 3-2 אנשים": ('hot-tubs', '2-3 אנשים'), "ג'קוזי 5-4 אנשים": ('hot-tubs', '4-5 אנשים'), "ג'קוזי 6+ אנשים": ('hot-tubs', '6 אנשים ומעלה'),
    'בריכת זרמים מחולקת': ('swim-spas', 'מחולקת'), 'בריכת זרמים משולבת': ('swim-spas', 'משולבת'),
    "כיסויים לג'קוזי": ('equipment', 'כיסויים'), "משאבות לג'קוזי": ('equipment', 'משאבות'), 'פתרונות חימום': ('equipment', 'חימום'),
    'פילטרים וסננים': ('equipment', 'פילטרים'), "סינון ג'טים": ('equipment', 'סינון וג׳טים'), "ג'יטים": ('equipment', 'סינון וג׳טים'),
    "חלקי חילוף לג'קוזי": ('equipment', 'חלקי חילוף'), 'חומרי תחזוקה': ('equipment', 'חומרי תחזוקה'),
    'אביזרי PVC': ('equipment', 'אביזרי PVC'), 'אביזרים נלווים': ('equipment', 'אביזרים נלווים'),
}
SPA_TOP = {"ג'קוזי לבית ולגינה - מערכות ספא חיצוניות": 'hot-tubs', 'בריכות זרמים': 'swim-spas', 'ציוד וחומרים': 'equipment'}
SPA_SPEC_LABELS = {
    'אורך (ס"מ)': 'אורך (ס"מ)', 'רוחב (ס"מ)': 'רוחב (ס"מ)', 'גובה (ס"מ)': 'גובה (ס"מ)',
    'ישיבה': 'מקומות ישיבה', 'שכיבה': 'מקומות שכיבה', 'סה"כ מקומות': 'סה"כ מקומות',
    'משקל ללא מים': 'משקל ללא מים', 'תכולת מים (ליטר)': 'תכולת מים', 'סה"כ משקל כולל': 'משקל כולל',
    'ג\'טים עיסוי נירוסטה אל חלד סה"כ': 'ג׳טים', 'משאבות (סה"כ כ"ס)': 'משאבות (כ"ס)', 'רמת גימור': 'רמת גימור',
}
PRICE = re.compile(r'(\d{1,3}(?:,\d{3})+|\d{3,5})\s*(?:ש["״]ח|₪)(\s*(?:\+|לפני)\s*מע["״]?)?')


def spa():
    host, site, brand = 'mtispa.co.il', 'spa', 'MTI SPA'
    pages, images = load(host)
    api = json.load(open(IMPORT / host / 'products-api.json'))
    reset(site)
    shared = shared_images(pages)
    page_by_url = {unquote(p['url']).rstrip('/'): p for p in pages}
    used, n, cat_images = set(), 0, {}
    for x in api:
        cats = [t['name'] for t in x['terms'] if t['taxonomy'] == 'product_cat']
        cat, typ = None, None
        for c in cats:
            if c in SPA_TYPE:
                cat, typ = SPA_TYPE[c]; break
        if not cat:
            cat = next((SPA_TOP[c] for c in cats if c in SPA_TOP), None)
        on_sale = 'מבצעים ועודפים' in cats
        if not cat and (on_sale or "ג'קוזי" in x['title']):
            cat = 'hot-tubs'
        if not cat:
            print('spa: no category for', x['title'], cats)
            continue
        title = x['title'].replace('’', "'").strip()
        page = page_by_url.get(unquote(x['link']).rstrip('/'))
        imgs = []
        if page:
            imgs = [copy_media(site, host, images, s) for s in product_images(page, images, shared)]
        if not imgs and x.get('image'):
            src = x['image']
            match = next((k for k in images if unquote(k) == unquote(src) and images[k]), None)
            if match:
                imgs = [copy_media(site, host, images, match)]
        if imgs and cat not in cat_images and (cat != 'equipment' or typ == 'כיסויים'):
            cat_images[cat] = imgs[0]
        specs = parse_pairs(lines(page['text']), SPA_SPEC_LABELS) if page else []
        finish = [t['name'] for t in x['terms'] if t['taxonomy'] == 'finish_level']
        if finish and not any(s['label'] == 'רמת גימור' for s in specs):
            specs.append({'label': 'רמות גימור', 'value': ', '.join(finish)})
        body = x.get('content') or ''
        m = PRICE.search(body)
        price = f"{m.group(1)} ₪{' + מע״מ' if m.group(2) else ''}" if m and 'מחיר' in body[max(0, m.start() - 40):m.start()] else None
        summary = re.split(r'(?<=[.!?])\s', x.get('excerpt') or body, 1)[0].replace('[&hellip;]', '').strip()[:200]
        slug = slugify(x['slug'] if not x['slug'].startswith('%') else title, used)
        write_md(ROOT / 'content' / site / 'products' / f'{slug}.md', {
            'title': title, 'category': cat, 'type': typ, 'summary': summary, 'images': imgs,
            'price': price, 'on_sale': on_sale, 'specs': specs, 'order': 100,
            'featured': on_sale or cat == 'hot-tubs' and 'TITANIUM' in finish, 'old_url': x['link'],
        }, '\n\n'.join(p.strip() for p in body.split('\n') if p.strip()))
        n += 1
    for cid, title, summary, order in SPA_CATS:
        write_md(ROOT / 'content' / site / 'categories' / f'{cid}.md',
                 {'title': title, 'summary': summary, 'image': cat_images.get(cid), 'order': order})
    print('spa products', n)


# ---------------------------------------------------------------- hub
def hub():
    host, site = 'mti-israel.co.il', 'hub'
    pages, images = load(host)
    (ROOT / 'content' / site / 'posts').mkdir(parents=True, exist_ok=True)
    for f in (ROOT / 'content' / site / 'posts').glob('*.md'):
        f.unlink()
    media = ROOT / 'public' / site / 'media'
    media.mkdir(parents=True, exist_ok=True)
    skip = {'/', '/about/', '/contact/', '/category/blog/'}
    shared = shared_images(pages)
    used = set()
    for p in pages:
        path = p['url'].split(host)[1]
        if path in skip:
            continue
        title = re.sub(r'\s*-\s*mti israel\s*$', '', p['title'], flags=re.I).strip()
        ls = lines(p['text'])
        if ls and ls[0] == title:
            ls = ls[1:]
        body = '\n\n'.join(l for l in ls if len(l) > 30)
        imgs = [copy_media(site, host, images, s) for s in product_images(p, images, shared, 1)]
        write_md(ROOT / 'content' / site / 'posts' / f'{slugify(path.strip("/"), used)}.md', {
            'title': title, 'date': '2025-01-01', 'summary': p.get('description', '')[:200],
            'image': imgs[0] if imgs else None, 'old_url': p['url'],
        }, body)
    print('hub posts', len(used))


if __name__ == '__main__':
    bath(); spa(); hub()
