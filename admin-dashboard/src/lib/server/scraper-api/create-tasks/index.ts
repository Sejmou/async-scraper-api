import { dataFetchingTaskSchema } from '$lib/scraper-types-and-schemas/created-tasks';
import { type Scraper, type SupportedTask } from '$lib/scraper-types-and-schemas/new-tasks';

export type DataSourceTaskDispatchFn<T extends Record<string, unknown>> = (
	taskType: string,
	scraper: Scraper,
	payload: T
) => Promise<void>;

export const sendTaskToScraper = async (scraper: Scraper, task: SupportedTask) => {
	const { host, port, protocol } = scraper;
	const { dataSource, taskType, payload } = task;
	const scraperUrl = `${protocol}://${host}:${port}`;
	const res = await fetch(`${scraperUrl}/${dataSource}/${taskType}`, {
		method: 'POST',
		body: JSON.stringify(payload)
	});
	if (!res.ok) {
		const data = await res.json();
		console.error(`Failed to send task to ${scraperUrl}`, data);
	}
	const data = await res.json();
	return dataFetchingTaskSchema.parse(data);
};
