import { json } from '@sveltejs/kit';
import { taskSchema } from '$lib/scraper-types-and-schemas/new-tasks';
import {
	artistsTaskSchema,
	tracksTaskSchema
} from '$lib/scraper-types-and-schemas/new-tasks/spotify-api.js';

const parseTask = (body: unknown) => {
	const task = taskSchema.parse(body);
	if (task.dataSource === 'spotify-api') {
		if (task.taskType === 'tracks') {
			const tracksTask = tracksTaskSchema.parse(task);
			return tracksTask;
		} else if (task.taskType === 'artists') {
			const artistsTask = artistsTaskSchema.parse(task);
			return artistsTask;
		}
		throw new Error('Unsupported taskType');
	}
	throw new Error('Unsupported dataSource');
};

export async function POST({ request }) {
	const body = await request.json();
	try {
		const task = parseTask(body);
		const randomFakeTaskId = Math.random().toString(36).substring(7);
		return json({ ...task, id: randomFakeTaskId }, { status: 200 });
	} catch (e) {
		if (e instanceof Error) return json({ error: e.message }, { status: 400 });
		return json({ error: 'Unknown error' }, { status: 500 });
	}
}
