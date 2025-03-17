import { db } from '$lib/server/db';

export async function load() {
	const tasks = await db.query.taskTbl.findMany({
		with: {
			subtasks: {
				with: {
					scraper: true
				}
			}
		}
	});

	return {
		tasks
	};
}
