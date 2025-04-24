import { type SupportedTask } from '$lib/types-and-schemas/tasks/data-sources';
import { z } from 'zod';
import { makeRequestToServerApi } from '.';

// to be used on server
export type DistributedTaskCreateResponse = z.infer<typeof createDistTaskResponseSchema>;

// to be used on client
const createDistTaskResponseSchema = z.object({ id: z.number() });

/**
 * Creates a new scraper task on the server, distributing its inputs across the given scrapers.
 */
export const createTask = async (task: SupportedTask, scraperIds: number[]) => {
	return await makeRequestToServerApi({
		path: `tasks`,
		method: 'POST',
		body: {
			task,
			scraperIds
		},
		responseSchema: createDistTaskResponseSchema
	});
};
