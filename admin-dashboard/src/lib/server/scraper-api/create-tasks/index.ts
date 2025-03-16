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
	await fetch(`${protocol}://${host}:${port}/${dataSource}/${taskType}`, {
		method: 'POST',
		body: JSON.stringify(payload)
	});
};
