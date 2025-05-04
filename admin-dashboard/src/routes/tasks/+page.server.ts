import { db } from '$lib/server/db';
import { desc } from 'drizzle-orm';

export async function load() {
	const tasks = await db.query.distTaskTbl.findMany({
		orderBy: (t) => desc(t.createdAt),
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
