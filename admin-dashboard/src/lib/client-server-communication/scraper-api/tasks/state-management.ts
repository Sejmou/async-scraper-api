import { makeRequestToServerApi } from '$lib/client-server-communication';
import { dataFetchingTaskSchema } from '$lib/types-and-schemas/tasks/common';

export async function pauseTask(scraperId: number, taskId: number) {
	return await makeRequestToServerApi({
		method: 'POST',
		path: `scrapers/${scraperId}/tasks/${taskId}/pause`,
		responseSchema: dataFetchingTaskSchema
	});
}

export async function resumeTask(scraperId: number, taskId: number) {
	return await makeRequestToServerApi({
		method: 'POST',
		path: `scrapers/${scraperId}/tasks/${taskId}/resume`,
		responseSchema: dataFetchingTaskSchema
	});
}
