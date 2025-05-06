import { type SupportedTask } from '$lib/types-and-schemas/tasks/data-sources';
import { z } from 'zod';
import { makeRequestToServerApi } from '.';

/**
 * Creates a new scraper task on the server, distributing its inputs across the given scrapers.
 */
export const createDistributedTask = async (task: SupportedTask, scraperIds: number[]) => {
	return await makeRequestToServerApi({
		path: `tasks`,
		method: 'POST',
		body: {
			task,
			scraperIds
		},
		responseSchema: z.object({ id: z.number() })
	});
};
