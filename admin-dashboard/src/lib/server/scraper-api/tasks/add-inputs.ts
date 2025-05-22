import { taskAddResponseSchema } from '$lib/types-and-schemas/tasks/common';
import { type Scraper } from '$lib/server/db/schema';
import { makeRequestToScraper } from '..';

export const addInputsToScraperTask = async <T>(scraper: Scraper, taskId: number, inputs: T[]) => {
	return await makeRequestToScraper({
		method: 'POST',
		scraper,
		path: `tasks/${taskId}/queue-items/inputs`,
		body: inputs,
		responseSchema: taskAddResponseSchema
	});
};
