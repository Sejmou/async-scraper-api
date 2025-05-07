import { makeRequestToScraper } from '..';
import type { Scraper } from '$lib/server/db/schema';
import {
	deleteConfirmMessageSchema,
	taskQueueItemsPageSchema,
	type TaskQueueType
} from '$lib/types-and-schemas/tasks/common';

export const fetchScraperTaskQueueItems = async (
	scraper: Scraper,
	taskId: number,
	queueType: TaskQueueType,
	cursorId?: number,
	limit: number = 10
) => {
	return await makeRequestToScraper({
		method: 'GET',
		scraper,
		path: `tasks/${taskId}/queue-items/${queueType}`,
		params: cursorId ? { cursor_id: cursorId, limit } : { limit },
		responseSchema: taskQueueItemsPageSchema
	});
};

export const deleteScraperTaskQueueItem = async (
	scraper: Scraper,
	taskId: number,
	queueType: TaskQueueType,
	id: number
) => {
	return await makeRequestToScraper({
		method: 'DELETE',
		scraper,
		path: `tasks/${taskId}/queue-items/${queueType}/${id}`,
		responseSchema: deleteConfirmMessageSchema
	});
};
