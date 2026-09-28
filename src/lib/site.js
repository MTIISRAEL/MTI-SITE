import { getCollection } from 'astro:content';

export const SITE = import.meta.env.MTI_SITE;
const all = import.meta.glob('../../content/*/settings.json', { eager: true, import: 'default' });
export const settings = all[`../../content/${SITE}/settings.json`];

export const isSales = SITE === 'spa';
export const isBrand = SITE === 'bath';
export const isHub = SITE === 'hub';

export const wa = (number, text) => `https://wa.me/${number}${text ? `?text=${encodeURIComponent(text)}` : ''}`;
export const tel = (phone) => `tel:+972${phone.replace(/\D/g, '').replace(/^0/, '')}`;
export const price = (n) => `₪${n.toLocaleString('he-IL')}`;

export async function categories() {
  return (await getCollection('categories')).sort((a, b) => a.data.order - b.data.order);
}

export async function products(category) {
  const list = (await getCollection('products')).filter((p) => !p.data.hidden && (!category || p.data.category === category));
  return list.sort((a, b) => a.data.order - b.data.order || a.data.title.localeCompare(b.data.title, 'he'));
}

export function nav(cats) {
  const items = cats.filter((c) => !c.data.link).map((c) => ({ href: `/${c.id}/`, label: c.data.title }));
  if (isSales) items.push({ href: '/sale/', label: 'מבצעים' });
  if (isBrand) items.push({ href: '/where-to-buy/', label: 'איפה קונים' });
  if (isHub) items.push({ href: '/blog/', label: 'בלוג' });
  items.push({ href: '/about/', label: 'אודות' }, { href: '/contact/', label: 'צור קשר' });
  return items;
}
