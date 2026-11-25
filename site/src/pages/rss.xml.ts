import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getCollection } from 'astro:content';
import { SITE, sectionLabel } from '../lib/site';

/** Every published page, newest revision first. The feed is the site's "what changed". */
export async function GET(context: APIContext) {
  const pages = await getCollection('pages');
  const items = pages
    .slice()
    .sort((a, b) => b.data.updated.localeCompare(a.data.updated))
    .map((page) => ({
      title: page.data.title,
      description: page.data.summary
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/\*\*/g, ''),
      link: `/${page.data.section}/${page.data.slug}/`,
      pubDate: new Date(`${page.data.updated}T00:00:00Z`),
      categories: [sectionLabel(page.data.section)],
    }));

  return rss({
    title: `${SITE.name} — the codex`,
    description: SITE.description,
    site: context.site ?? 'https://d13myumhho8nau.cloudfront.net',
    items,
    customData: '<language>en-gb</language>',
  });
}
