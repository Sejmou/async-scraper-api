import { type Task } from '$lib/scraper-types-and-schemas/new-tasks';
import { z } from 'zod';

// to be used on server
export type CreateTaskResponse = z.infer<typeof createTaskResponseSchema>;
export const createTaskRequestSchema = z.object({
	dataSource: z.string(),
	taskType: z.string(),
	payload: z.record(z.unknown())
});

// to be used on client
const createTaskResponseSchema = z.object({
	id: z.number()
});

/**
 * Creates a new scraper task on the server. It can later be assigned to
 */
export const createTask = async <T extends Record<string, unknown>>(task: Task<T>) => {
	const resp = await fetch(`/api/tasks`, {
		method: 'POST',
		body: JSON.stringify(task)
	});
	const data = await resp.json();
	return createTaskResponseSchema.parse(data);
};
