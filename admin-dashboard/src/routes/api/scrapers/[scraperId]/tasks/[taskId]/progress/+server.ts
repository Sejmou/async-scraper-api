import { db } from '$lib/server/db';
import { fetchScraperTaskProgress } from '$lib/server/scraper-api/tasks/get-progress';
import { json, error } from '@sveltejs/kit';

export async function GET({ params }) {
	const scraperId = Number(params.scraperId);
	if (Number.isNaN(scraperId)) {
		error(400, 'Invalid scraperId');
	}

	const scraper = await db.query.scraperServerTbl.findFirst({
		where: (scrapers, { eq }) => eq(scrapers.id, scraperId)
	});
	if (!scraper) {
		error(404, 'Scraper not found');
	}

	const taskId = Number(params.taskId);
	if (Number.isNaN(taskId)) {
		error(400, 'Invalid taskId');
	}

	const res = await fetchScraperTaskProgress(scraper, taskId);
	if (res.status === 'success') {
		return json(res.data);
	} else {
		error(res.httpCode, res.message);
	}
}
