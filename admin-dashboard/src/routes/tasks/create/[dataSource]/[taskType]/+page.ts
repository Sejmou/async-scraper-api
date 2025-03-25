import {
	getInitialTaskValue,
	getParamsSchema,
	getTaskInputMeta
} from '$lib/scraper-types-and-schemas/new-tasks';
import { error } from '@sveltejs/kit';

export async function load({ params, data }) {
	const { dataSource, taskType } = params;

	const initialTaskValue = getInitialTaskValue(dataSource, taskType);
	if (!initialTaskValue) {
		return error(404, {
			message: 'Not found'
		});
	}

	const paramsSchema = getParamsSchema(initialTaskValue);
	const taskInputMeta = getTaskInputMeta(initialTaskValue);

	console.log({ initialTaskValue, paramsSchema, taskInputMeta });

	return {
		scrapers: data.scrapers,
		dataSource,
		taskType,
		initialTaskValue,
		paramsSchema: paramsSchema || undefined,
		taskInputMeta
	};
}
