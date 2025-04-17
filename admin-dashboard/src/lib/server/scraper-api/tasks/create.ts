import { dataFetchingTaskSchema } from '$lib/scraper-types-and-schemas/created-tasks';
import { type Scraper } from '$lib/server/db/schema';
import { type SupportedTask } from '$lib/scraper-types-and-schemas/new-tasks';
import { makeRequestToScraper } from '..';

export const sendTaskToScraper = async (scraper: Scraper, task: SupportedTask) => {
	const { dataSource, taskType, inputs } = task;
	const params = 'params' in task ? task.params : undefined;
	return await makeRequestToScraper({
		method: 'POST',
		scraper,
		path: `${dataSource}/${taskType}`,
		body: {
			inputs,
			params
		},
		responseSchema: dataFetchingTaskSchema
	});
};
