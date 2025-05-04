import { makeRequestToServerApi } from '$lib/client-server-communication';
import { taskProgressSchema } from '$lib/types-and-schemas/tasks/common';

export const fetchTaskProgress = async (scraperId: number, taskId: number) => {
	return await makeRequestToServerApi({
		method: 'GET',
		path: `scrapers/${scraperId}/tasks/${taskId}/progress`,
		responseSchema: taskProgressSchema
	});
};

export type TaskProgressFetchPromise = ReturnType<typeof fetchTaskProgress>;
