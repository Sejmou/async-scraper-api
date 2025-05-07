import { db } from '$lib/server/db';
import { scraperServerTbl } from '$lib/server/db/schema';
import { deleteScraperTaskQueueItem } from '$lib/server/scraper-api/tasks/queue-items.js';
import { taskQueueTypeSchema } from '$lib/types-and-schemas/tasks/common.js';
import { json, error } from '@sveltejs/kit';
import { eq } from 'drizzle-orm';

export async function DELETE({ params }) {
	const queueTypeInput = params.queueType;
	const queueTypeParseResult = taskQueueTypeSchema.safeParse(queueTypeInput);
	if (!queueTypeParseResult.success) {
		error(400, 'Invalid queue type');
	}
	const queueType = queueTypeParseResult.data;

	const scraperId = Number(params.scraperId);
	if (Number.isNaN(scraperId)) {
		error(400, 'Invalid scraperId');
	}
	const scraper = await db.query.scraperServerTbl.findFirst({
		where: eq(scraperServerTbl.id, scraperId)
	});
	if (!scraper) {
		error(404, 'Scraper not found');
	}
	const taskId = Number(params.taskId);
	if (Number.isNaN(taskId)) {
		error(400, 'Invalid taskId');
	}

	const queueItemIdInput = params.queueItemId;
	const queueItemId = Number(queueItemIdInput);
	if (Number.isNaN(queueItemId)) {
		error(400, 'Invalid queueItemId');
	}

	const res = await deleteScraperTaskQueueItem(scraper, taskId, queueType, queueItemId);
	if (res.status === 'success') {
		return json(res.data);
	} else {
		error(res.httpCode, res.message);
	}
}
