import { db } from '$lib/server/db';
import type { Scraper } from '$lib/server/db/schema';
import { fetchScraperTaskProgress } from '$lib/server/scraper-api/tasks/get-progress';
import type { TaskProgress } from '$lib/types-and-schemas/tasks/common';
import { desc } from 'drizzle-orm';

export async function load() {
	const tasks = await db.query.distTaskTbl.findMany({
		orderBy: (t) => desc(t.createdAt),
		with: {
			subtasks: {
				with: {
					scraper: true
				}
			}
		}
	});

	return {
		tasks: tasks.map((task) => ({
			...task,
			progress: createTaskProgressPromise(task.id, task.subtasks)
		}))
	};
}

async function createTaskProgressPromise(
	taskId: number,
	subtasks: { scraper: Scraper; scraperTaskId: number }[]
): Promise<TaskProgress> {
	const cumulative: TaskProgress = {
		success_count: 0,
		failure_count: 0,
		inputs_without_output_count: 0,
		remaining_count: 0
	};
	const results = await Promise.allSettled(
		subtasks.map(async (subtask) => {
			const { scraper, scraperTaskId } = subtask;
			return await fetchScraperTaskProgress(scraper, scraperTaskId);
		})
	);
	for (const item of results) {
		if (item.status === 'rejected') {
			throw new Error('One or more items have status "rejected".');
		}
		const value = item.value;
		if (value.status === 'error') {
			// Reject the promise by throwing
			throw new Error('One or more items have status "error".');
		}
		const data = value.data;
		cumulative.success_count += data.success_count;
		cumulative.failure_count += data.failure_count;
		cumulative.remaining_count += data.remaining_count;
		cumulative.inputs_without_output_count += data.inputs_without_output_count;
	}

	return cumulative;
}
