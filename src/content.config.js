import { defineCollection } from 'astro:content';
import { glob, file } from 'astro/loaders';
import { z } from 'astro/zod';

const SITE = process.env.SITE || 'spa';
const base = `content/${SITE}`;

const categories = defineCollection({
  loader: glob({ pattern: 'categories/*.md', base, generateId: ({ entry }) => entry.replace(/^categories\/|\.md$/g, '') }),
  schema: z.object({
    title: z.string(),
    summary: z.string().default(''),
    image: z.string().optional(),
    order: z.number().default(100),
    // Hub only: a category can point at another site instead of a local page.
    link: z.string().optional(),
  }),
});

const products = defineCollection({
  loader: glob({ pattern: 'products/*.md', base, generateId: ({ entry }) => entry.replace(/^products\/|\.md$/g, '') }),
  schema: z.object({
    title: z.string(),
    category: z.string(),
    summary: z.string().default(''),
    images: z.array(z.string()).default([]),
    // Free text so editors can write e.g. "23,990 ₪ + מע״מ".
    price: z.string().optional(),
    on_sale: z.boolean().default(false),
    // Sub-type shown as a filter on the category page, e.g. "פינתית", "4-5 אנשים".
    type: z.string().optional(),
    specs: z.array(z.object({ label: z.string(), value: z.string() })).default([]),
    order: z.number().default(100),
    featured: z.boolean().default(false),
    hidden: z.boolean().default(false),
    old_url: z.string().optional(),
  }),
});

const dealers = defineCollection({
  loader: glob({ pattern: 'dealers/*.md', base, generateId: ({ entry }) => entry.replace(/^dealers\/|\.md$/g, '') }),
  schema: z.object({
    name: z.string(),
    city: z.string(),
    region: z.enum(['צפון', 'מרכז', 'ירושלים והסביבה', 'דרום', 'שרון', 'שפלה']).default('מרכז'),
    address: z.string().default(''),
    phone: z.string().default(''),
    website: z.string().default(''),
  }),
});

const posts = defineCollection({
  loader: glob({ pattern: 'posts/*.md', base, generateId: ({ entry }) => entry.replace(/^posts\/|\.md$/g, '') }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    summary: z.string().default(''),
    image: z.string().optional(),
    old_url: z.string().optional(),
  }),
});

export const collections = { categories, products, dealers, posts };
