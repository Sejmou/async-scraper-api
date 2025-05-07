import { db } from '$lib/server/db';
import { scraperServerTbl } from '$lib/server/db/schema';
import { fetchScraperTaskQueueItems } from '$lib/server/scraper-api/tasks/queue-items.js';
import { taskQueueTypeSchema } from '$lib/types-and-schemas/tasks/common.js';
import { json, error } from '@sveltejs/kit';
import { eq } from 'drizzle-orm';

export async function GET({ params, url }) {
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

	const cursorIdInput = url.searchParams.get('cursorId');
	const cursorId = cursorIdInput ? Number(cursorIdInput) : undefined;
	if (cursorId && Number.isNaN(cursorId)) {
		error(400, 'Invalid cursorId');
	}
	const limitInput = url.searchParams.get('limit');
	const limit = limitInput ? Number(limitInput) : undefined;
	if (limit) {
		if (Number.isNaN(limit)) error(400, 'Invalid limit');
		if (limit < 1) error(400, 'Limit must be greater than 0');
	}

	const res = await fetchScraperTaskQueueItems(scraper, taskId, queueType, cursorId, limit);
	if (res.status === 'success') {
		return json(res.data);
	} else {
		error(res.httpCode, res.message);
	}
}
