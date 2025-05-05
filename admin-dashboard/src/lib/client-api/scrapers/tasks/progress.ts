import { makeRequestToServerApi, type SvelteKitServerApiResponse } from '$lib/client-api';
import { taskProgressSchema } from '$lib/types-and-schemas/tasks/common';

export const fetchTaskProgress = async (
	scraperId: number,
	taskId: number
): TaskProgressResponse => {
	return await makeRequestToServerApi({
		method: 'GET',
		path: `scrapers/${scraperId}/tasks/${taskId}/progress`,
		responseSchema: taskProgressSchema
	});
};

export type TaskProgressResponse = SvelteKitServerApiResponse<typeof taskProgressSchema>;
