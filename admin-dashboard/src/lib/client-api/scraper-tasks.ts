import { type SupportedTask } from '$lib/scraper-types-and-schemas/new-tasks';
import { z } from 'zod';

// to be used on server
export type CreateTaskResponseData = z.infer<typeof createTaskResponseSchema>;

// to be used on client
const createTaskResponseSchema = z.discriminatedUnion('status', [
	z.object({ status: z.literal('success'), id: z.number() }),
	z.object({ status: z.literal('error'), error: z.string() })
]);

/**
 * Creates a new scraper task on the server, distributing its inputs across the given scrapers.
 */
export const createTask = async (task: SupportedTask, scraperIds: number[]) => {
	const resp = await fetch(`/api/tasks`, {
		method: 'POST',
		body: JSON.stringify({ task, scraperIds })
	});
	const data = await resp.json();
	return createTaskResponseSchema.parse(data);
};
