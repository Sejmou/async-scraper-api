import { makeRequestToScraper } from '..';
import type { Scraper } from '$lib/server/db/schema';
import { z } from 'zod';
import { taskProgressSchema } from '$lib/types-and-schemas/tasks/common';

export type ScraperTaskProgress = z.infer<typeof taskProgressSchema>;

export const fetchScraperTaskProgress = async (scraper: Scraper, taskId: number) => {
	return await makeRequestToScraper({
		method: 'GET',
		scraper,
		path: `tasks/${taskId}/progress`,
		responseSchema: taskProgressSchema
	});
};
