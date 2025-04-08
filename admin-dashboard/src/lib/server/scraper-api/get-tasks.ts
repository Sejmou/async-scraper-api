import { makeRequestToScraper } from '.';
import type { Scraper } from '$lib/server/db/schema';
import { tasksPageSchema } from '$lib/scraper-types-and-schemas/created-tasks';

export const fetchScraperTasks = async (scraper: Scraper, page: number, pageSize: number) => {
	const res = await makeRequestToScraper(scraper, `tasks`, undefined, {
		page,
		size: pageSize
	});
	if (res.status === 'error') {
		throw new Error(`Failed to get tasks for scraper with ID ${scraper.id}`);
	}
	return tasksPageSchema.parse(res.data);
};
