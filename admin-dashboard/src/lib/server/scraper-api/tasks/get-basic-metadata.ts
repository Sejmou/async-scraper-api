import { makeRequestToScraper } from '..';
import type { Scraper } from '$lib/server/db/schema';
import { tasksPageSchema, dataFetchingTaskSchema } from '$lib/types-and-schemas/tasks/common';

/**
 * Fetches a page of task metadata from the scraper.
 */
export const getScraperTaskMetadataPage = async (
	scraper: Scraper,
	page: number,
	pageSize: number
) => {
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

/**
 * Fetches metadata for a specific task from the scraper.
 */
export const getScraperTaskMetadata = async (scraper: Scraper, taskId: number) => {
	return await makeRequestToScraper({
		method: 'GET',
		scraper,
		path: `tasks/${taskId}`,
		responseSchema: dataFetchingTaskSchema
	});
};
