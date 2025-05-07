import { makeRequestToServerApi, type SvelteKitServerApiResponse } from '$lib/client-api';
import {
	deleteConfirmMessageSchema,
	taskQueueItemsPageSchema,
	type TaskQueueType
} from '$lib/types-and-schemas/tasks/common';

export type TaskQueueItemsPageResponse = SvelteKitServerApiResponse<
	typeof taskQueueItemsPageSchema
>;

export async function fetchTaskQueueItems(
	scraperId: number,
	taskId: number,
	queueType: TaskQueueType,
	cursorId?: number,
	limit: number = 10
): TaskQueueItemsPageResponse {
	return await makeRequestToServerApi({
		method: 'GET',
		path: `scrapers/${scraperId}/tasks/${taskId}/queue-items/${queueType}`,
		params: cursorId ? { cursorId, limit } : { limit },
		responseSchema: taskQueueItemsPageSchema
	});
}

export type TaskQueueItemDeleteResponse = SvelteKitServerApiResponse<
	typeof deleteConfirmMessageSchema
>;

export async function deleteTaskQueueItem(
	scraperId: number,
	taskId: number,
	queueType: TaskQueueType,
	queueItemId: number
): TaskQueueItemDeleteResponse {
	return await makeRequestToServerApi({
		method: 'DELETE',
		path: `scrapers/${scraperId}/tasks/${taskId}/queue-items/${queueType}/${queueItemId}`,
		responseSchema: deleteConfirmMessageSchema
	});
}
