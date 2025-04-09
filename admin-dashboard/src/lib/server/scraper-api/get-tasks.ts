import { makeRequestToScraper } from '.';
import type { Scraper } from '$lib/server/db/schema';
import { tasksPageSchema } from '$lib/scraper-types-and-schemas/created-tasks';

export const fetchScraperTasks = async (scraper: Scraper, page: number, pageSize: number) => {
	return await makeRequestToScraper({
		method: 'GET',
		scraper,
		path: `tasks`,
		params: {
			page,
			size: pageSize
		},
		responseSchema: tasksPageSchema
	});
};
