import { z } from 'zod';
import { makeRequestToScraper } from '.';
import type { Scraper } from '$lib/server/db/schema';

const scraperAboutResponseSchema = z.object({
	version: z.string()
});

export const getScraperInfo = async (scraper: Scraper) => {
	return await makeRequestToScraper({
		method: 'GET',
		scraper,
		path: 'about',
		responseSchema: scraperAboutResponseSchema
	});
};
