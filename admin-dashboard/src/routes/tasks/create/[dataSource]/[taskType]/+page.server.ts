import { db } from '$lib/server/db';
import { scraperServerTbl } from '$lib/server/db/schema';
import { getScraperServerMetadata } from '$lib/server/scraper-api/get-server-metadata';

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
				const res = await getScraperServerMetadata(s);
				if (res.status === 'error') {
					throw new Error(`Failed to get scraper info for ${s.protocol}://${s.host}:${s.port}`);
				}
				return s;
			})
		)
	)
		.filter((res) => res.status === 'fulfilled')
		.map((res) => res.value);
	return onlineServers;
}
