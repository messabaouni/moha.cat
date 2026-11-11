import { getCollection } from 'astro:content';

type Collection = 'escrits' | 'lectures' | 'projectes' | 'miscellania';

// Keys are URL slugs; `collection` is the content collection behind each one.
export const sections = {
  escrits: {
    collection: 'escrits',
    name: 'Escrits',
    listLabel: "Llista d'escrits",
    eyebrow: 'ARXIU',
    lead: 'Anècdotes, records, costums, llocs i preguntes que no sempre tenen resposta.',
    description: 'Assajos, apunts i relats.',
    backLabel: 'Tots els escrits',
    empty: 'Encara no hi ha cap escrit publicat.',
  },
  lectures: {
    collection: 'lectures',
    name: 'Lectures',
    listLabel: "Llista de lectures",
    eyebrow: 'LLIBRES I IDEES',
    lead: 'Llibres llegits, llibres pendents i algunes notes al marge.',
    description: 'Llibres i notes de lectura.',
    backLabel: 'Totes les lectures',
    empty: 'Encara no hi ha cap nota de lectura.',
  },
  projectes: {
    collection: 'projectes',
    name: 'Projectes',
    listLabel: "Llista de projectes",
    eyebrow: 'FEINA I CURIOSITAT',
    lead: 'Projectes, experiments i coses que vaig construint.',
    description: 'Projectes personals i professionals.',
    backLabel: 'Tots els projectes',
    empty: 'Encara no hi ha cap projecte publicat.',
  },
  'miscel-lania': {
    collection: 'miscellania',
    name: 'Miscel·lània',
    listLabel: 'Llista de miscel·lània',
    eyebrow: 'DE TOT UN POC',
    feed: true,
    lead: 'Pensaments breus, fotografies, música que escolto i enllaços.',
    description: 'Fotografia i música de Moha.',
    backLabel: 'Tota la miscel·lània',
    empty: 'Aviat hi haurà coses per aquí.',
  },
} as const satisfies Record<string, { collection: Collection; [k: string]: unknown }>;

// Seccions que es mostren com un flux de notes curtes, sense pàgina per entrada.
export const isFeed = (section: string) => section === 'miscel-lania';

export type SectionKey = keyof typeof sections;
export const sectionKeys = Object.keys(sections) as SectionKey[];

export const byDateDesc = (a: { data: { date: Date } }, b: { data: { date: Date } }) =>
  b.data.date.valueOf() - a.data.date.valueOf();

export async function getPublished(section: SectionKey) {
  const posts = await getCollection(sections[section].collection, ({ data }) => !data.draft);
  return posts.sort(byDateDesc);
}

export const formatDateTime = (date: Date) =>
  date.toLocaleString('ca-ES', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Madrid',
  });

export const excerpt = (text = '', max = 70) => {
  const plain = text.replace(/!\[[^\]]*\]\([^)]*\)/g, '').replace(/[#*_>`\[\]]/g, '').replace(/\s+/g, ' ').trim();
  return plain.length > max ? `${plain.slice(0, max).trimEnd()}…` : plain || 'Nota';
};

export const formatDate = (date: Date, month: 'long' | 'short' = 'long') =>
  date.toLocaleDateString('ca-ES', { day: 'numeric', month, year: 'numeric' });
