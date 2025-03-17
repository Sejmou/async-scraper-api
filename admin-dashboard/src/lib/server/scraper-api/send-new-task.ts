import {
	dataFetchingTaskSchema,
	type DataFetchingTask
} from '$lib/scraper-types-and-schemas/created-tasks';
import { type Scraper } from '$lib/server/db/schema';
import { type SupportedTask } from '$lib/scraper-types-and-schemas/new-tasks';
import { makeRequestToScraper } from '.';

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
	const { dataSource, taskType, inputs } = task;
	const params = 'params' in task ? task.params : undefined;
	const result = await makeRequestToScraper(scraper, `${dataSource}/${taskType}`, {
		inputs,
		params
	});
	if (result.status === 'error') {
		return {
			success: false,
			error: result.error
		};
	}

	const data = result.data;
	const schemaParseRes = dataFetchingTaskSchema.safeParse(data);
	if (!schemaParseRes.success) {
		const error = schemaParseRes.error;
		console.error(`Failed to parse return value for task creation API call`, { scraper, error });
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
