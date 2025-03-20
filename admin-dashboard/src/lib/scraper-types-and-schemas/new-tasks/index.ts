import { z } from 'zod';
import {
	spotifyApiTaskTypesSchema,
	getSpotifyTaskParamsSchema,
	getSpotifyTaskInputMeta,
	getInitialSpotifyTask,
	parseSpotifyTask,
	type SpotifyAPITask
} from './spotify-api';

export const scraperSchema = z.object({
	host: z.string(),
	port: z.number(),
	protocol: z.string()
});
export type Scraper = z.infer<typeof scraperSchema>;

export const taskSchema = z.discriminatedUnion('dataSource', [
	z.object({
		dataSource: z.literal('spotify-api'),
		taskType: spotifyApiTaskTypesSchema,
		inputs: z.array(z.unknown()),
		params: z.record(z.unknown()).optional()
	})
]);

/**
 * A task with valid `dataSource` and `taskType` fields, and inputs + (optional) params of unknown type.
 *
 * Obtained as first step in parsing task objects sent from clients.
 *
 * Individual zod schema parsers for each data source can then determine if the task is indeed valid for the given data source and task type.
 */
export type SupportedTaskCandidate = z.infer<typeof taskSchema>;
// TODO: update with types for other data sources as they are added
export type SupportedTask = SpotifyAPITask;

export const parseToTaskOrThrowError = (input: unknown): SupportedTask => {
	const result = taskSchema.parse(input);
	switch (result.dataSource) {
		case 'spotify-api':
			return parseSpotifyTask(result);
	}
};

type SupportedTaskInput = SupportedTask['inputs'][0];
export type TaskInputMeta<T extends SupportedTaskInput> = {
	inputsDescription: string;
	inputSchema: z.ZodSchema<T>;
	exampleInput: T;
	/**
	 * The name of the DuckDB table which the task inputs should temporarily be stored in before passing them to the scrapers.
	 */
	inputsTableName: string;
};

export type SupportedTaskInputMeta = TaskInputMeta<SupportedTaskInput>;
export const getTaskInputMeta = (
	input: Pick<SupportedTask, 'dataSource' | 'taskType'>
): SupportedTaskInputMeta => {
	switch (input.dataSource) {
		case 'spotify-api':
			return getSpotifyTaskInputMeta(input.taskType);
	}
};

export type ParamsUnion<T> = T extends { params: infer P } ? P : never;
export function getParamsSchema(
	input: Pick<SupportedTaskCandidate, 'dataSource' | 'taskType'>
): z.ZodSchema<ParamsUnion<SupportedTask>> | null {
	switch (input.dataSource) {
		case 'spotify-api':
			return getSpotifyTaskParamsSchema(input);
	}
}

export function getInitialTaskValue(
	dataSourceStr: string,
	taskTypeStr: string
): SupportedTask | null {
	const baseSchemaParseRes = taskSchema.safeParse({
		dataSource: dataSourceStr,
		taskType: taskTypeStr,
		inputs: []
	});
	if (!baseSchemaParseRes.success) return null;
	const base = baseSchemaParseRes.data;
	switch (base.dataSource) {
		case 'spotify-api':
			return getInitialSpotifyTask(base.taskType);
	}
}
