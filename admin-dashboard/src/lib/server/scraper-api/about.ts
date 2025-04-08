import { z } from 'zod';

const scraperServerInfoSchema = z.object({
	version: z.string()
});

export type ScraperServerInfo = z.infer<typeof scraperServerInfoSchema>;

export const getScraperServerInfo = async (meta: {
	host: string;
	port: number;
	protocol: string;
}): Promise<ScraperServerInfo> => {
	const { host, port, protocol } = meta;
	const url = `${protocol}://${host}:${port}/about`;
	const response = await fetch(url);
	const data = await response.json();
	return scraperServerInfoSchema.parse(data);
};
