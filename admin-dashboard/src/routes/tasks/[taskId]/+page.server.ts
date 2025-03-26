import { db } from '$lib/server/db';
import { taskTbl } from '$lib/server/db/schema.js';
import { error } from '@sveltejs/kit';
import { eq } from 'drizzle-orm';
import { addSubtaskProgressPromises } from '$lib/server/scraper-api/subtask-progress';

export async function load({ params }) {
	const id = parseInt(params.taskId, 10);
	if (isNaN(id)) {
		return error(400, {
			message: 'Invalid task ID'
		});
	}
	const taskWithSubTasksAndScrapers = await db.query.taskTbl.findFirst({
		where: eq(taskTbl.id, id),
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

	return await addSubtaskProgressPromises(taskWithSubTasksAndScrapers);
}
