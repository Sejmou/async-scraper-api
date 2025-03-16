import { type Task } from '$lib/scraper-types-and-schemas/new-tasks';
import { z } from 'zod';

// to be used on server
export type CreateTaskResponseData = z.infer<typeof createTaskResponseSchema>;
export const createTaskRequestSchema = z.object({
	dataSource: z.string(),
	taskType: z.string(),
	payload: z.record(z.unknown())
});

// to be used on client
const createTaskResponseSchema = z.discriminatedUnion('status', [
	z.object({ status: z.literal('success'), id: z.number() }),
	z.object({ status: z.literal('error'), error: z.string() })
]);

/**
 * Creates a new scraper task on the server. It can later be assigned to
 */
export const createTask = async <T extends Record<string, unknown>>(task: Task<T>) => {
	const resp = await fetch(`/api/tasks`, {
		method: 'POST',
		body: JSON.stringify(task)
	});
	const data = await resp.json();
	console.log('createTask response', data);
	return createTaskResponseSchema.parse(data);
};
