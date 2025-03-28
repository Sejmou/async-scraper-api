import { makeRequestToScraper } from '.';
import type { Scraper, Subtask, DBTask } from '$lib/server/db/schema';
import { z } from 'zod';

const taskProgressSchema = z.object({
	success_count: z.number(),
	failure_count: z.number(),
	inputs_without_output_count: z.number(),
	remaining_count: z.number()
});
export type ScraperSubtaskProgress = z.infer<typeof taskProgressSchema>;

const getSubtaskProgress = async (scraper: Scraper, subtaskId: number) => {
	const res = await makeRequestToScraper(scraper, `tasks/${subtaskId}/progress`);
	if (res.status === 'error') {
		throw new Error('Failed to get task progress');
	}
	return taskProgressSchema.parse(res.data);
};

const createSubtaskProgressPromiseSafe = async (scraper: Scraper, subTaskId: number) => {
	try {
		const data = await getSubtaskProgress(scraper, subTaskId);
		return data;
	} catch (error) {
		console.error('Failed to get progress for scraper subtask', { scraper, subTaskId, error });
		return null;
	}
};

type TaskWithSubtasksAndScrapers = DBTask & { subtasks: (Subtask & { scraper: Scraper })[] };
export type SubtaskWithScraperAndProgress = Subtask & {
	scraper: Scraper;
	progress: Promise<ScraperSubtaskProgress | null>;
};

export const addSubtaskProgressPromises = (
	data: TaskWithSubtasksAndScrapers
): {
	task: DBTask;
	subTasksWithProgress: SubtaskWithScraperAndProgress[];
} => {
	const { subtasks, ...task } = data;

	return {
		task,
		subTasksWithProgress: subtasks.map((s) => ({
			...s,
			progress: createSubtaskProgressPromiseSafe(s.scraper, s.scraperTaskId)
		}))
	};
};
