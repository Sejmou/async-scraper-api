import { createTransaction, db, WorkaroundTransactionRollbackError } from '$lib/server/db';
import {
	distTaskTbl,
	subtaskTbl,
	scraperServerTbl,
	type Scraper,
	type Subtask
} from '$lib/server/db/schema';
import { inArray } from 'drizzle-orm';
import { error, json } from '@sveltejs/kit';
import {
	parseToTaskOrThrowError,
	type SupportedTask as Task
} from '$lib/types-and-schemas/tasks/data-sources';
import { indent, roundRobinSplit } from '$lib/utils';
import { z, ZodError } from 'zod';
import { sendTaskToScraper } from '$lib/server/scraper-api/tasks/create';
import { type DistributedTaskCreateResponse } from '$lib/client-server-communication/create-distributed-task';
import { safeParseRequestJSON } from '$lib/server/utils.js';
import { constructScraperBaseUrl } from '$lib/server/scraper-api/index.js';
import { getScraperServerMetadata } from '$lib/server/scraper-api/get-server-metadata.js';

export async function POST({ request }) {
	return json(await createDistributedTask(request));
}

async function createDistributedTask(request: Request): Promise<DistributedTaskCreateResponse> {
	const body = await safeParseRequestJSON(request);
	const { taskData, scraperIds } = validateRequestBody(body);
	const scrapers = await getScrapersForIds(scraperIds);

	try {
		const transaction = createTransaction(db);
		const taskId = await transaction.transaction(async ({ db, rollback }) => {
			const taskCreateRes = await db
				.insert(distTaskTbl)
				.values({
					dataSource: taskData.dataSource,
					taskType: taskData.taskType,
					params: 'params' in taskData ? taskData.params : undefined
				})
				.returning({ id: distTaskTbl.id });
			const taskId = taskCreateRes[0].id;

			try {
				await distributeAcrossScrapers(taskId, taskData, scrapers);
			} catch (e) {
				console.error('Failed to distribute task across scrapers', {
					taskData,
					error: e
				});
				if (e instanceof Error) {
					rollback(e);
				} else {
					rollback('Unknown error');
				}
			}
			return taskId;
		});
		return { id: taskId };
	} catch (e) {
		console.error('Error while creating task', e);
		if (e instanceof WorkaroundTransactionRollbackError) {
			const errorMsg = e.cause instanceof Error ? e.cause.message : e.cause || 'Unknown error';
			error(503, errorMsg);
		}
		if (e instanceof Error) {
			error(500, e.message);
		}
		error(500, 'Unknown error occurred while creating task');
	}
}

/**
 * Distributes the given task across the given scrapers by sending the task to each scraper
 * with a different chunk of the input data. The chunks are created using a round-robin split.
 *
 * This means that the order of the inputs is preserved - scraper 1 gets the first item of the provided task inputs, scraper 2 gets the second one etc.
 * So, overall, the first inputs passed to the task will also be processed first (assuming no scraper gets stuck while processing its chunk).
 *
 * @throws {SubtaskCreationError} If any of the subtasks fail to be created.
 */
async function distributeAcrossScrapers(
	taskId: number,
	taskData: Task,
	scrapers: Scraper[]
): Promise<Subtask[]> {
	const { dataSource, taskType, inputs } = taskData;
	const params = 'params' in taskData ? taskData.params : undefined;

	console.log('Distributing task across scrapers', {
		task: {
			dataSource,
			taskType,
			first10Inputs: inputs.slice(0, 10),
			last10Inputs: inputs.slice(-10),
			inputLength: inputs.length,
			params
		},
		scrapers
	});

	console.log(
		`Splitting ${inputs.length} inputs of distributed task (ID: ${taskId}) across ${scrapers.length} scrapers`
	);
	// run same task across all scrapers, but give each a different chunk of the input data
	// roundRobinSplit means that each scraper gets a chunk of the input data in a round-robin fashion
	// i.e. if data is ordered by priority, each scraper's chunk will start with the most important data
	// TODO: figure out why TS cannot infer correct type of inputChunks here and remove this ugly, completely counter-intuitive cast here
	const inputChunks: (typeof inputs)[] = roundRobinSplit(inputs as string[], scrapers.length);
	const subtaskInputs: {
		scraper: Scraper;
		taskData: Task;
	}[] = scrapers.map((scraper, i) => ({
		scraper,
		taskData: {
			dataSource,
			taskType,
			params,
			inputs: inputChunks[i]
		} as Task // TS is unable to infer that taskData should always be valid here
	}));

	const results = await Promise.allSettled(
		subtaskInputs.map(async ({ scraper, taskData }) => {
			const taskSendResult = await sendTaskToScraper(scraper, taskData);
			if (taskSendResult.status === 'success') {
				const scraperTaskId = taskSendResult.data.id;
				const subtaskInsertPayload = {
					taskId,
					scraperTaskId,
					scraperId: scraper.id
				};
				try {
					const subtaskInsertRes = await db
						.insert(subtaskTbl)
						.values(subtaskInsertPayload)
						.returning();
					const subTask = subtaskInsertRes[0];
					return subTask;
				} catch (e) {
					console.error('Failed to insert subtask into database', {
						subtaskInsertPayload,
						error: e
					});
					throw new SubtaskCreationError(
						'Failed to insert subtask into database',
						scraper,
						taskData
					);
				}
			} else {
				const errorDesc = taskSendResult.scraperApiHttpCode
					? `HTTP error (code ${taskSendResult.scraperApiHttpCode})`
					: 'unknown error';
				throw new SubtaskCreationError(
					`Task creation request produced ${errorDesc}\n${indent(taskSendResult.message)}`,
					scraper,
					taskData
				);
			}
		})
	);
	const errors: SubtaskCreationError[] = results
		.filter((result) => result.status === 'rejected')
		.map((result) => result.reason);

	if (errors.length > 0) {
		const errorDetails = errors
			.map((error) => {
				const scraper = error.scraper;
				const taskData = error.taskData;
				const scraperUrl = constructScraperBaseUrl(scraper);
				return indent(
					`${scraperUrl} (ID: ${scraper.id}, ${taskData.inputs.length} inputs): ${error.message}`
				);
			})
			.join('\n\n');
		const errorMsg = `Scraper${errors.length > 1 ? 's' : ''} for ${errors.length} subtask${errors.length > 1 ? 's' : ''} responded with an error:\n${errorDetails}`;
		console.error(errorMsg);
		throw new Error(errorMsg);
	}

	const subtasks = results.filter((result) => result.status === 'fulfilled').map((r) => r.value);
	return subtasks;
}

class SubtaskCreationError extends Error {
	scraper: Scraper;
	taskData: Task;

	constructor(message: string, scraper: Scraper, taskData: Task) {
		super(message);
		this.name = 'SubtaskCreationError';
		this.scraper = scraper;
		this.taskData = taskData;
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
			console.error('Zod validation for task provided by client failed', { task, error: e });

			return {
				success: false,
				errors: taskCreationZodErrorToLines(e)
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

function validateRequestBody(body: unknown) {
	if (!body || typeof body !== 'object') {
		error(400, 'Invalid request body. Should be object with "task" and "scrapers" properties');
	}
	if (!('task' in body)) {
		return error(400, 'Missing "task" property');
	}
	if (!('scraperIds' in body)) {
		return error(400, 'Missing "scraperIds" property');
	}
	const taskParseRes = parseTask(body.task);
	if (!taskParseRes.success) return error(400, taskParseRes.errors.join('\n'));

	const scraperIdParseRes = z.array(z.number()).safeParse(body.scraperIds);
	if (!scraperIdParseRes.success) return error(400, scraperIdParseRes.error.errors.join('\n'));

	const taskData = taskParseRes.data;
	const scraperIds = scraperIdParseRes.data;

	if (scraperIds.length > taskData.inputs.length) {
		return error(
			400,
			`More scrapers than inputs! (${scraperIds.length} scrapers, ${taskData.inputs.length} inputs)`
		);
	}

	return {
		taskData,
		scraperIds
	};
}

async function getScrapersForIds(scraperIds: number[]) {
	// first, verify that all scraper IDs can in fact be matched to scrapers in our database
	const scrapers = await db
		.select()
		.from(scraperServerTbl)
		.where(inArray(scraperServerTbl.id, scraperIds));

	if (scrapers.length === 0) {
		const allScraperCount = await db.$count(scraperServerTbl);
		if (allScraperCount === 0) {
			console.error('No scrapers in database');
			return error(503, 'No scrapers in database');
		} else {
			console.error('No scrapers found for IDs provided by client', { scraperIds });
			return error(400, 'Invalid scraper ID(s) provided');
		}
	}

	if (scrapers.length !== scraperIds.length) {
		console.error('Client provided at least one invalid scraper ID', {
			scraperIds,
			scrapers
		});
		return error(400, 'Invalid scraper ID(s) provided');
	}

	// finally, check if all scrapers we matched are online and return a descriptive error message if not
	const scraperMetadataResponses = await Promise.all(
		scrapers.map(async (scraper) => ({
			scraper,
			metadataRequestResponse: await getScraperServerMetadata(scraper)
		}))
	);
	const offlineScrapers = scraperMetadataResponses
		.filter((data) => data.metadataRequestResponse.status === 'error')
		.map((data) => data.scraper);
	if (offlineScrapers.length > 0) {
		const offlineScraperUrls = offlineScrapers.map((s) => constructScraperBaseUrl(s));
		const offlineCountMessage =
			offlineScrapers.length === 1
				? '1 scraper you provided is currently offline'
				: `${offlineScrapers.length} scrapers are currently offline`;
		const offlineMessage = `${offlineCountMessage}:\n${offlineScraperUrls.map((url) => ' - ' + url).join('\n')}`;
		return error(503, offlineMessage);
	}

	return scrapers;
}

function taskCreationZodErrorToLines(e: ZodError): string[] {
	const maxVisible = 7;
	const messages = e.errors.slice(0, maxVisible).map((err) => {
		const path = parseTaskCreationZodValidationErrorPath(err.path);
		return `${path}: ${err.message}`;
	});

	if (e.errors.length > maxVisible) {
		messages.push(`... (${e.errors.length - maxVisible} more)`);
	}

	return messages;
}

function parseTaskCreationZodValidationErrorPath(path: (string | number)[]) {
	if (path.length === 0) {
		return 'value';
	}
	if (path.length === 1) {
		return path[0];
	}
	const [first, second] = path;
	if (first === 'inputs' && typeof second === 'number') {
		return `input ${second + 1} is invalid`;
	}
	return path.join('.');
}
