import { db } from '$lib/server/db/index.js';
import { eq } from 'drizzle-orm';
import { scraperServerTbl, type Scraper } from '$lib/server/db/schema';
import { fetchScraperTaskMetadataPage } from '$lib/server/scraper-api/tasks/get-basic-metadata';
import { error } from '@sveltejs/kit';
import { fetchScraperServerMetadata } from '$lib/server/scraper-api/get-server-metadata';

const fetchScraperData = async (scraper: Scraper, tasksPage: number, pageSize = 10) => {
	// definining this as handling null/error case on client would be more annoying than just returning this 'empty' data
	const tasksFallbackData = {
		page: 1,
		items: [],
		size: pageSize,
		total: 0,
		pages: 1
	};
	try {
		const [infoRes, tasksRes] = await Promise.all([
			fetchScraperServerMetadata(scraper),
			fetchScraperTaskMetadataPage(scraper, tasksPage, pageSize)
		]);
		return {
			status: infoRes.status === 'success' ? ('online' as const) : ('offline' as const),
			version: infoRes.status === 'success' ? infoRes.data.version : 'unknown',
			tasks: tasksRes.status === 'success' ? tasksRes.data : tasksFallbackData
		};
	} catch (e) {
		console.error('Failed to get scraper data', { scraper, error: e });
		return {
			status: 'offline' as const,
			version: 'unknown',
			tasks: tasksFallbackData
		};
	}
};

export async function load({ params, url }) {
	const scraperId = params.scraperId;
	const page = Number(url.searchParams.get('page')) || 1;
	const scraper = await db.query.scraperServerTbl.findFirst({
		where: eq(scraperServerTbl.id, +scraperId)
	});
	if (!scraper) {
		return error(404, {
			message: 'Not found'
		});
	}
	const scraperData = await fetchScraperData(scraper, page);
	return { scraper, ...scraperData };
}
