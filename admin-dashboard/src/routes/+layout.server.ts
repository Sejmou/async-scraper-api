import { db } from '$lib/server/db';
import { eq } from 'drizzle-orm';
import { scraperServerTbl, taskTbl } from '$lib/server/db/schema';

export const load = async ({ params }) => {
	const task = params.taskId
		? (await db.select().from(taskTbl).where(eq(taskTbl.id, +params.taskId)))[0]
		: null;

	const scraper = params.scraperId
		? (
				await db.select().from(scraperServerTbl).where(eq(scraperServerTbl.id, +params.scraperId))
			)[0]
		: null;

	return {
		task,
		scraper
	};
};
