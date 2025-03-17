import { db } from '$lib/server/db';
import { addSubtaskProgressPromises } from '$lib/server/scraper-api/subtask-progress';

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
		tasks: tasks.map(addSubtaskProgressPromises)
	};
}
