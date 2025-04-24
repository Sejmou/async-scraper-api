import { db } from '$lib/server/db';
import { scraperServerTbl } from '$lib/server/db/schema';
import { getScraperTaskMetadata } from '$lib/server/scraper-api/tasks/get-basic-metadata.js';
import { json, error } from '@sveltejs/kit';
import { eq } from 'drizzle-orm';

export async function GET({ params }) {
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

	const res = await getScraperTaskMetadata(scraper, taskId);
	if (res.status === 'success') {
		return json(res.data);
	} else {
		error(res.scraperApiHttpCode ?? 500, res.message);
	}
}
