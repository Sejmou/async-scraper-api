import { db } from '$lib/server/db';
import { distTaskTbl } from '$lib/server/db/schema.js';
import { error } from '@sveltejs/kit';
import { eq } from 'drizzle-orm';
import { addScraperTaskProgressPromises } from '$lib/server/scraper-api/tasks/get-progress';

export async function load({ params }) {
	const id = parseInt(params.taskId, 10);
	if (isNaN(id)) {
		return error(400, {
			message: 'Invalid task ID'
		});
	}
	const taskWithSubTasksAndScrapers = await db.query.distTaskTbl.findFirst({
		where: eq(distTaskTbl.id, id),
		with: {
			subtasks: {
				with: {
					scraper: true
				}
			}
		}
	});

	if (!taskWithSubTasksAndScrapers) {
		return error(404, {
			message: 'Not found'
		});
	}

	return await addScraperTaskProgressPromises(taskWithSubTasksAndScrapers);
}
