import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const schema = z.object({
  title: z.string(),
  date: z.coerce.date(),
  description: z.string().optional(),
  draft: z.boolean().default(false),
});

const escrits = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/escrits' }),
  schema,
});

const lectures = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/lectures' }),
  schema,
});

const projectes = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/projectes' }),
  schema,
});

const miscellania = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/miscellania' }),
  schema,
});

export const collections = { escrits, lectures, projectes, miscellania };
