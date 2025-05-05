import { makeRequestToServerApi, type SvelteKitServerApiResponse } from '$lib/client-api';
import { dataFetchingTaskSchema } from '$lib/types-and-schemas/tasks/common';

export type TaskStateResponse = SvelteKitServerApiResponse<typeof dataFetchingTaskSchema>;

export async function pauseTask(scraperId: number, taskId: number): TaskStateResponse {
	return await makeRequestToServerApi({
		method: 'POST',
		path: `scrapers/${scraperId}/tasks/${taskId}/pause`,
		responseSchema: dataFetchingTaskSchema
	});
}

export async function resumeTask(scraperId: number, taskId: number): TaskStateResponse {
	return await makeRequestToServerApi({
		method: 'POST',
		path: `scrapers/${scraperId}/tasks/${taskId}/resume`,
		responseSchema: dataFetchingTaskSchema
	});
}
