import { dataFetchingTaskSchema } from '$lib/scraper-types-and-schemas/created-tasks';
import { type Scraper, type Task } from '$lib/scraper-types-and-schemas/new-tasks';

export type DataSourceTaskDispatchFn<T extends Record<string, unknown>> = (
	taskType: string,
	scraper: Scraper,
	payload: T
) => Promise<void>;

export const sendTaskToScraper = async <T extends Record<string, unknown>>(
	scraper: Scraper,
	task: Task<T>
) => {
	const { host, port, protocol } = scraper;
	const { dataSource, taskType, payload } = task;
	const res = await fetch(`${protocol}://${host}:${port}/${dataSource}/${taskType}`, {
		method: 'POST',
		body: JSON.stringify(payload)
	});
	if (!res.ok) {
		throw new Error(`Failed to send task to scraper: ${res.statusText}`);
	}
	const data = await res.json();
	return dataFetchingTaskSchema.parse(data);
};
