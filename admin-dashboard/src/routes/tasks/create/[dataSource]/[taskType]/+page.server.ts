import { db } from '$lib/server/db';
import { scraperServerTbl } from '$lib/server/db/schema';
import { getScraperServerInfo } from '$lib/server/scraper-api/about';

export async function load() {
	const scrapers = await getAvailableScrapers();

	return {
		scrapers
	};
}

async function getAvailableScrapers() {
	const scrapers = await db.select().from(scraperServerTbl);
	const onlineServers = (
		await Promise.allSettled(
			scrapers.map(async (s) => {
				await getScraperServerInfo(s);
				return s;
			})
		)
	)
		.filter((res) => res.status === 'fulfilled')
		.map((res) => res.value);
	return onlineServers;
}
