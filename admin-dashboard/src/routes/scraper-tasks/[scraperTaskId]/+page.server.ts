import { db } from '$lib/server/db';
import { error } from '@sveltejs/kit';

export async function load({ params }) {
	const scraperTaskId = Number(params.scraperTaskId);
	if (Number.isNaN(scraperTaskId)) {
		error(400, 'Invalid scraperTaskId');
	}

	const scraperTask = await db.query.subtaskTbl.findFirst({
		where: (t, { eq }) => eq(t.id, scraperTaskId),
		with: {
			scraper: true,
			task: true
		}
	});

	if (!scraperTask) {
		error(404, 'Task not found');
	}

	return {
		scraperTask
	};
}
