import { makeRequestToServerApi, type SvelteKitServerApiResponse } from '$lib/client-api';
import { dataFetchingTaskSchema } from '$lib/types-and-schemas/tasks/common';

export type TaskStateResponse = SvelteKitServerApiResponse<typeof dataFetchingTaskSchema>;

export async function fetchTaskMetadata(scraperId: number, taskId: number): TaskStateResponse {
	return await makeRequestToServerApi({
		method: 'GET',
		path: `scrapers/${scraperId}/tasks/${taskId}`,
		responseSchema: dataFetchingTaskSchema
	});
}
