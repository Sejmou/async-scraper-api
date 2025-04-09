import { createTransaction, db } from '$lib/server/db';
import { taskTbl, subtaskTbl, scraperServerTbl } from '$lib/server/db/schema';
import { inArray } from 'drizzle-orm';
import { json } from '@sveltejs/kit';
import {
	parseToTaskOrThrowError,
	type Scraper,
	type SupportedTask as Task
} from '$lib/scraper-types-and-schemas/new-tasks';
import { roundRobinSplit } from '$lib/utils';
import { z, ZodError } from 'zod';
import { sendTaskToScraper } from '$lib/server/scraper-api/send-new-task';
import { type CreateTaskResponseData } from '$lib/client-api/scraper-tasks';
import { TransactionRollbackError } from 'drizzle-orm';

export async function POST({ request }) {
	const body = (await request.json()) as unknown;
	if (!body || typeof body !== 'object') {
		return sendResponse(
			{
				status: 'error',
				error: 'Invalid request body. Should be object with "task" and "scrapers" properties'
			},
			400
		);
	}
	if (!('task' in body)) {
		return sendResponse({ status: 'error', error: 'Missing "task" property' }, 400);
	}
	if (!('scraperIds' in body)) {
		return sendResponse({ status: 'error', error: 'Missing "scraperIds" property' }, 400);
	}
	const taskParseRes = parseTask(body.task);
	if (!taskParseRes.success)
		return sendResponse({ status: 'error', error: taskParseRes.errors.join('\n') }, 400);

	const scraperIdParseRes = z.array(z.number()).safeParse(body.scraperIds);
	if (!scraperIdParseRes.success)
		return sendResponse({ status: 'error', error: scraperIdParseRes.error.errors.join('\n') }, 400);

	const scraperIds = scraperIdParseRes.data;

	const scrapers = await db
		.select()
		.from(scraperServerTbl)
		.where(inArray(scraperServerTbl.id, scraperIds));
	if (scrapers.length === 0) {
		console.error('No scrapers passed from client');
		return sendResponse({ status: 'error', error: 'No scrapers passed' }, 400);
	}
	if (scrapers.length !== scraperIds.length) {
		console.error('Some scrapers not found in database', {
			scraperIds,
			scrapers
		});
		return sendResponse(
			{
				status: 'error',
				error: 'Some scrapers not found in database'
			},
			400
		);
	}
	console.log('Scrapers to distribute tasks on', scrapers);

	const task = taskParseRes.data;
	const { dataSource, taskType, inputs } = task;
	const params = 'params' in task ? task.params : undefined;
	console.log('Task to send to distribute among scrapers', {
		dataSource,
		taskType,
		first10Inputs: inputs.slice(0, 10),
		last10Inputs: inputs.slice(-10),
		inputLength: inputs.length,
		params
	});

	// run same task across all scrapers, but give each a different chunk of the input data
	// roundrobinSplit means that each scraper gets a chunk of the input data in a round-robin fashion
	// i.e. if data is ordered by priority, each scraper's chunk will start with the most important data
	const inputChunks = roundRobinSplit(inputs, scrapers.length);

	const successes: { scraper: Scraper; subtaskId: number }[] = [];
	const failures: { scraper: Scraper; inputs: typeof inputs }[] = [];

	try {
		const transaction = createTransaction(db);
		const taskId = await transaction.transaction(async ({ db, rollback }) => {
			const taskCreateRes = await db
				.insert(taskTbl)
				.values({
					dataSource,
					taskType,
					params
				})
				.returning({ id: taskTbl.id });
			const taskId = taskCreateRes[0].id;

			for (const [i, scraper] of scrapers.entries()) {
				task.inputs = inputChunks[i];
				console.log('Sending task to scraper', {
					scraper,
					first10Inputs: task.inputs.slice(0, 10),
					last10Inputs: task.inputs.slice(-10),
					inputLength: task.inputs.length,
					params
				});
				const taskSendResult = await sendTaskToScraper(scraper, task);
				if (taskSendResult.status === 'success') {
					const subtaskId = taskSendResult.data.id;
					await db.insert(subtaskTbl).values({
						taskId,
						scraperTaskId: subtaskId,
						scraperId: scraper.id
					});
					successes.push({ scraper, subtaskId });
				} else {
					console.error('Failed to send task to scraper', {
						scraper,
						first10Inputs: task.inputs.slice(0, 10),
						last10Inputs: task.inputs.slice(-10),
						inputLength: task.inputs.length,
						params,
						error: taskSendResult.error
					});
					failures.push({ scraper, inputs });
				}
			}

			if (successes.length === 0) {
				rollback();
			}
			return taskId;
		});
		return sendResponse({ status: 'success', id: taskId }, 200);
	} catch (e) {
		console.error('Error while creating task', e);
		if (e instanceof TransactionRollbackError) {
			sendResponse(
				{
					status: 'error',
					error: 'Failed to send task to any scrapers. This is probably a bug.'
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
			console.warn('Failed to parse task', e.errors);
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

function sendResponse(res: CreateTaskResponseData, status: number) {
	if (res.status === 'success') {
		return json({ status: 'success', id: res.id }, { status });
	} else {
		return json({ status: 'error', error: res.error }, { status });
	}
}
