import {
	getInitialTaskValue,
	getParamsSchema,
	getTaskInputMeta
} from '$lib/scraper-types-and-schemas/new-tasks';
import { error } from '@sveltejs/kit';
export function load({ params }) {
	const dataSource = 'spotify-api';
	const { taskType } = params;

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
		dataSource,
		taskType,
		initialTaskValue,
		paramsSchema: paramsSchema || undefined,
		taskInputMeta
	};
}
