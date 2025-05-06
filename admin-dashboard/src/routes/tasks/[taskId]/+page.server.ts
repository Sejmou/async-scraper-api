import { db } from '$lib/server/db';
import { error } from '@sveltejs/kit';

export async function load({ params }) {
	const taskId = Number(params.taskId);
	if (Number.isNaN(taskId)) {
		error(400, 'Invalid taskId');
	}

	const task = await db.query.distTaskTbl.findFirst({
		where: (t, { eq }) => eq(t.id, taskId),
		with: {
			subtasks: {
				with: {
					scraper: true
				}
			}
		}
	});

	if (!task) {
		error(404, 'Task not found');
	}

	return {
		task
	};
}
