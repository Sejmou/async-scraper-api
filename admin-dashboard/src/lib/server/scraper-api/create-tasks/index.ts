import {
	dataFetchingTaskSchema,
	type DataFetchingTask
} from '$lib/scraper-types-and-schemas/created-tasks';
import { type Scraper, type SupportedTask } from '$lib/scraper-types-and-schemas/new-tasks';

export type DataSourceTaskDispatchFn<T extends Record<string, unknown>> = (
	taskType: string,
	scraper: Scraper,
	payload: T
) => Promise<void>;

export const sendTaskToScraper = async (
	scraper: Scraper,
	task: SupportedTask
): Promise<
	| {
			success: true;
			data: DataFetchingTask;
	  }
	| {
			success: false;
			error: unknown;
	  }
> => {
	const { host, port, protocol } = scraper;
	const { dataSource, taskType, inputs } = task;
	const params = 'params' in task ? task.params : undefined;
	const scraperUrl = `${protocol}://${host}:${port}`;
	const res = await fetch(`${scraperUrl}/${dataSource}/${taskType}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			inputs,
			params
		})
	});
	const data = await res.json();
	if (!res.ok) {
		console.error(`Failed to send task to ${scraperUrl}`, data);
		return {
			success: false,
			error: data
		};
	}
	const schemaParseRes = dataFetchingTaskSchema.safeParse(data);
	if (!schemaParseRes.success) {
		const error = schemaParseRes.error;
		console.error(`Failed to parse schemaParseRes from ${scraperUrl}`, error);
		return {
			success: false,
			error
		};
	}
	return {
		success: true,
		data: schemaParseRes.data
	};
};
