import { db } from '$lib/server/db/index.js';
import { eq } from 'drizzle-orm';
import { scraperServerTbl, type Scraper } from '$lib/server/db/schema';
import { fetchScraperTasks } from '$lib/server/scraper-api/get-tasks';
import { error } from '@sveltejs/kit';
import { getScraperServerInfo } from '$lib/server/scraper-api/about';

const getScraperData = async (scraper: Scraper, tasksPage: number, pageSize = 10) => {
	try {
		const [info, tasks] = await Promise.all([
			getScraperServerInfo(scraper),
			fetchScraperTasks(scraper, tasksPage, pageSize)
		]);
		return {
			status: 'online' as const,
			version: info.version,
			tasks
		};
	} catch (e) {
		console.error('Failed to get scraper data', { scraper, error: e });
		return {
			status: 'offline' as const,
			version: 'unknown',
			tasks: {
				page: 1,
				items: [],
				size: pageSize,
				total: 0,
				pages: 1
			}
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
	const scraperData = await getScraperData(scraper, page);
	return { scraper, ...scraperData };
}
