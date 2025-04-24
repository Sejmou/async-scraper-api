import { db } from '$lib/server/db';
import { addScraperTaskProgressPromises } from '$lib/server/scraper-api/tasks/get-progress';

export async function load() {
	const tasks = await db.query.distTaskTbl.findMany({
		with: {
			subtasks: {
				with: {
					scraper: true
				}
			}
		}
	});

	return {
		tasks: tasks.map(addScraperTaskProgressPromises)
	};
}
