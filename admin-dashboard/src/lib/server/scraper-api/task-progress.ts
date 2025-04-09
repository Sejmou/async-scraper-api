import { makeRequestToScraper } from '.';
import type { Scraper, Subtask, DBTask } from '$lib/server/db/schema';
import { z } from 'zod';

const taskProgressSchema = z.object({
	success_count: z.number(),
	failure_count: z.number(),
	inputs_without_output_count: z.number(),
	remaining_count: z.number()
});
export type ScraperTaskProgress = z.infer<typeof taskProgressSchema>;

const fetchScraperTaskProgress = async (scraper: Scraper, subtaskId: number) => {
	return await makeRequestToScraper({
		method: 'GET',
		scraper,
		path: `tasks/${subtaskId}/progress`,
		responseSchema: taskProgressSchema
	});
};

type TaskWithSubtasksAndScrapers = DBTask & { subtasks: (Subtask & { scraper: Scraper })[] };
export type SubtaskWithScraperAndProgress = Subtask & {
	scraper: Scraper;
	progress: ReturnType<typeof fetchScraperTaskProgress>;
};

export const addScraperTaskProgressPromises = (
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
			progress: fetchScraperTaskProgress(s.scraper, s.scraperTaskId)
		}))
	};
};
