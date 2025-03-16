import { db } from '$lib/server/db';
import { server, task, subtask } from '$lib/server/db/schema';
import { getAPIServerInfo } from '$lib/server/scraper-api/about';
import { json } from '@sveltejs/kit';
import {
	parseToTaskOrThrowError,
	type Scraper,
	type SupportedTask as Task
} from '$lib/scraper-types-and-schemas/new-tasks';
import { roundRobinSplit } from '$lib/utils';
import { ZodError } from 'zod';
import { sendTaskToScraper } from '$lib/server/scraper-api/create-tasks';
import { type CreateTaskResponseData } from '$lib/client-api/scraper-tasks';
import { TransactionRollbackError } from 'drizzle-orm';

async function getAvailableScrapers() {
	const servers = await db.select().from(server);
	const onlineServers = (
		await Promise.allSettled(
			servers.map(async (s) => {
				await getAPIServerInfo(s);
				return s;
			})
		)
	)
		.filter((res) => res.status === 'fulfilled')
		.map((res) => res.value);
	return onlineServers;
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

const sendResponse = (res: CreateTaskResponseData, status: number) => {
	if (res.status === 'success') {
		return json({ status: 'success', id: res.id }, { status });
	} else {
		return json({ status: 'error', error: res.error }, { status });
	}
};

export async function POST({ request }) {
	const body = await request.json();
	const res = parseTask(body);
	if (!res.success) return sendResponse({ status: 'error', error: res.errors.join('\n') }, 400);
	const data = res.data;
	const inputs = extractInputs(data);
	const params = extractParams(data);
	const { dataSource, taskType } = data;
	console.log('Got task', { dataSource, taskType, inputs, params });

	const scrapers = await getAvailableScrapers();
	if (scrapers.length === 0) {
		console.error('No scrapers available');
		return sendResponse({ status: 'error', error: 'No scrapers available' }, 503);
	}
	console.log('Available scrapers', scrapers);

	// run same task across all scrapers, but give each a different chunk of the input data
	// roundrobinSplit means that each scraper gets a chunk of the input data in a round-robin fashion
	// i.e. if data is ordered by priority, each scraper's chunk will start with the most important data
	const inputChunks = inputs ? roundRobinSplit(inputs, scrapers.length) : null;

	const successes: { scraper: Scraper; taskId: number }[] = [];
	const failures: { scraper: Scraper; inputs: typeof inputs }[] = [];

	try {
		const taskId = await db.transaction(async (trx) => {
			const taskCreateRes = await trx
				.insert(task)
				.values({
					dataSource,
					taskType,
					params
				})
				.returning({ id: task.id });
			const taskId = taskCreateRes[0].id;

			for (const [i, scraper] of scrapers.entries()) {
				const input = inputChunks ? inputChunks[i] : null;
				console.log('Sending task to scraper', { scraper, input, params });

				let subtaskId: number | null = null;
				try {
					const { id } = await sendTaskToScraper(scraper, {
						dataSource,
						taskType,
						payload: { input, params }
					});
					subtaskId = id;
					console.log('Successfully sent task to scraper', { scraper, input, params });
					successes.push({ scraper, taskId });
				} catch (e) {
					console.error('Failed to send task to scraper', { scraper, input, params, error: e });
					failures.push({ scraper, inputs });
				}

				if (subtaskId) {
					await trx.insert(subtask).values({
						taskId,
						scraperId: scraper.id
					});
				}
			}

			if (successes.length === 0) {
				trx.rollback();
			}
			return taskId;
		});
		return sendResponse({ status: 'success', id: taskId }, 200);
	} catch (e) {
		console.error('Error while creating task', e);
		if (e instanceof TransactionRollbackError) {
			return sendResponse(
				{
					status: 'error',
					error:
						'Failed to send task to any scrapers. There has probably been an error in how the data was sent to the scrapers.'
				},
				500
			);
		}
		if (e instanceof Error) {
			return sendResponse({ status: 'error', error: e.message }, 500);
		}
		return sendResponse({ status: 'error', error: 'Error while creating task' }, 500);
	}
}
