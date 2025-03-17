import { db } from '$lib/server/db';
import { taskTbl } from '$lib/server/db/schema.js';
import { error } from '@sveltejs/kit';
import { eq } from 'drizzle-orm';

export async function load() {
	const task = await db.query.taskTbl.findFirst({
		where: eq(taskTbl.id, 1),
		with: {
			subtasks: {
				with: {
					scraper: true
				}
			}
		}
	});

	if (!task) {
		return error(404, {
			message: 'Not found'
		});
	}

	return {
		task
	};
}
