import { json } from '@sveltejs/kit';
import {
	parseToTaskOrThrowError,
	type Scraper,
	type SupportedTask as Task
} from '$lib/scraper-types-and-schemas/new-tasks';
import { roundRobinSplit } from '$lib/utils';
import { ZodError } from 'zod';
import { sendTaskToScraper } from '$lib/server/scraper-api/create-tasks/index.js';

// TODO: read from DB properly
async function getScrapers() {
	return [
		{
			host: 'localhost',
			port: 3000,
			protocol: 'http'
		},
		{
			host: 'localhost',
			port: 3001,
			protocol: 'http'
		},
		{
			host: 'localhost',
			port: 3002,
			protocol: 'http'
		}
	];
}

type CreateTaskPayload = {
	scraperTasks: { scraper: Scraper; taskId: number }[];
	params?: Record<string, unknown>;
};

// TODO: write to DB properly
async function createTask(payload: CreateTaskPayload) {
	console.log('Creating dummy task from payload', payload);
	return { id: 1 };
}

function parseTask(task: unknown):
	| {
			success: true;
			data: Task;
	  }
	| {
			success: false;
			errors: string[];
	  } {
	try {
		return {
			success: true,
			data: parseToTaskOrThrowError(task)
		};
	} catch (e) {
		if (e instanceof ZodError) {
			return {
				success: false,
				errors: e.errors.map((err) => err.message)
			};
		} else if (e instanceof Error) {
			return {
				success: false,
				errors: [e.message]
			};
		} else
			return {
				success: false,
				errors: ['Unknown error']
			};
	}
}

const extractInputs = (task: Task) => {
	if (task.dataSource === 'spotify-api') {
		switch (task.taskType) {
			case 'tracks':
				return task.payload.track_ids;
			case 'artists':
				return task.payload.artist_ids;
			case 'albums':
				return task.payload.album_ids;
			case 'artist-albums':
				return task.payload.artist_ids;
			case 'playlists':
				return task.payload.playlist_ids;
		}
	}
};

const extractParams = (task: Task) => {
	if (task.dataSource === 'spotify-api') {
		switch (task.taskType) {
			case 'tracks':
				return {
					region: task.payload.region
				};
			case 'albums':
				return {
					region: task.payload.region
				};
			case 'artist-albums':
				return {
					region: task.payload.region,
					release_types: task.payload.release_types
				};
		}
	}
};

export async function POST({ request }) {
	const body = await request.json();
	try {
		const res = parseTask(body);
		if (!res.success) return json({ errors: res.errors }, { status: 400 });
		const data = res.data;
		const inputs = extractInputs(data);
		const params = extractParams(data);
		const { dataSource, taskType } = data;
		console.log('Got task', { dataSource, taskType, inputs, params });

		const scrapers = await getScrapers();
		console.log('Available scrapers', scrapers);

		// run same task across all scrapers, but give each a different chunk of the input data
		// roundrobinSplit means that each scraper gets a chunk of the input data in a round-robin fashion
		// i.e. if data is ordered by priority, each scraper's chunk will start with the most important data
		const inputChunks = inputs ? roundRobinSplit(inputs, scrapers.length) : null;

		const successes: { scraper: Scraper; inputs: typeof inputs; taskId: number }[] = [];
		const failures: { scraper: Scraper; inputs: typeof inputs }[] = [];
		for (const [i, scraper] of scrapers.entries()) {
			const input = inputChunks ? inputChunks[i] : null;
			console.log('Sending task to scraper', { scraper, input, params });
			try {
				const { id: taskId } = await sendTaskToScraper(scraper, {
					dataSource,
					taskType,
					payload: { input, params }
				});
				successes.push({ scraper, inputs, taskId });
			} catch (e) {
				console.error('Failed to send task to scraper', { scraper, input, params, error: e });
				failures.push({ scraper, inputs });
			}
		}
		const scraperTasks = successes.map(({ scraper, taskId }) => ({ scraper, taskId }));
		const createTaskPayload = {
			scraperTasks,
			params
		};
		const { id } = await createTask(createTaskPayload);
		const status = successes.length === 0 ? 503 : 200;
		return json({ id, successes, failures }, { status });
	} catch (e) {
		if (e instanceof Error) return json({ error: e.message }, { status: 400 });
		return json({ error: 'Unknown error' }, { status: 500 });
	}
}
