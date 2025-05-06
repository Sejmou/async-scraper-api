import { db } from '$lib/server/db';
import { eq } from 'drizzle-orm';
import { scraperServerTbl, distTaskTbl } from '$lib/server/db/schema';

export const load = async ({ params }) => {
	const task = params.taskId
		? (await db.select().from(distTaskTbl).where(eq(distTaskTbl.id, +params.taskId)))[0]
		: null;

	const scraper = params.scraperId
		? (
				await db.select().from(scraperServerTbl).where(eq(scraperServerTbl.id, +params.scraperId))
			)[0]
		: null;

	const scraperTask = params.scraperTaskId
		? await db.query.subtaskTbl.findFirst({
				where: (t, { eq }) => eq(t.id, +params.scraperTaskId!)
			})
		: null;

	return {
		task,
		scraper,
		scraperTask
	};
};
