import { makeRequestToScraper } from '..';
import type { Scraper } from '$lib/server/db/schema';
import { dataFetchingTaskSchema } from '$lib/types-and-schemas/tasks/common';

export async function pauseTask(scraper: Scraper, taskId: string) {
	return await makeRequestToScraper({
		method: 'POST',
		scraper,
		path: `tasks/${taskId}/pause`,
		responseSchema: dataFetchingTaskSchema
	});
}

export async function resumeTask(scraper: Scraper, taskId: string) {
	return await makeRequestToScraper({
		method: 'POST',
		scraper,
		path: `tasks/${taskId}/resume`,
		responseSchema: dataFetchingTaskSchema
	});
}
