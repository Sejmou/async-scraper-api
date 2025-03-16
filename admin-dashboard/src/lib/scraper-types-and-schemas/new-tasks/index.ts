import { z } from 'zod';

// TODO: update (turn into z.union([z.literal('...'), z.literal('...')])) as more sources are added
export const dataSourceSchema = z.literal('spotify-api');
export type ScraperDataSource = z.infer<typeof dataSourceSchema>;

export const scraperSchema = z.object({
	host: z.string(),
	port: z.number(),
	protocol: z.string()
});
export type Scraper = z.infer<typeof scraperSchema>;

export const taskSchema = z.object({
	dataSource: dataSourceSchema,
	taskType: z.string(),
	payload: z.record(z.unknown())
});

export type Task<T extends Record<string, unknown>> = {
	dataSource: ScraperDataSource;
	taskType: string;
	payload: T;
};
