import { db } from '$lib/server/db';
import { scraperServerTbl } from '$lib/server/db/schema';
import { constructScraperRequestUrl } from '$lib/server/scraper-api/index.js';
import { error } from '@sveltejs/kit';
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

	const url = constructScraperRequestUrl(scraper, `tasks/${taskId}/logs`);
	try {
		const upstreamRes = await fetch(url);
		if (!upstreamRes.ok) {
			error(upstreamRes.status, `Error fetching logs from scraper: ${upstreamRes.statusText}`);
		}
		return upstreamRes;
	} catch (err) {
		console.error('Error proxying log file', { scraper, taskId, err });
		error(500, 'Error fetching logs from scraper');
	}
}
