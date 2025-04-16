import { z } from 'zod';
import {
	spotifyApiTaskTypesSchema,
	getSpotifyTaskParamsSchema,
	getSpotifyTaskInputMeta,
	getInitialSpotifyTask,
	parseSpotifyTask,
	type SpotifyAPITask,
	type SupportedSpotifyAPITaskCandidate,
	type SpotifyAPITaskType
} from './spotify-api';
import {
	getInitialSpotifyInternalTask,
	getSpotifyInternalTaskInputMeta,
	getSpotifyInternalTaskParamsSchema,
	parseSpotifyInternalTask,
	spotifyInternalApiTaskTypesSchema,
	type SpotifyInternalAPITask,
	type SpotifyInternalAPITaskType,
	type SupportedSpotifyInternalAPITaskCandidate
} from './spotify-internal';
import {
	dummyApiTaskTypesSchema,
	getDummyTaskInputMeta,
	getDummyTaskParamsSchema,
	getInitialDummyTask,
	parseDummyTask,
	type DummyAPITask,
	type DummyAPITaskType,
	type SupportedDummyAPITaskCandidate
} from './dummy-api';

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
	}),
	z.object({
		dataSource: z.literal('spotify-internal'),
		taskType: spotifyInternalApiTaskTypesSchema,
		inputs: z.array(z.unknown()),
		params: z.record(z.unknown()).optional()
	}),
	z.object({
		dataSource: z.literal('dummy-api'),
		taskType: dummyApiTaskTypesSchema,
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
export type SupportedTask = SpotifyAPITask | SpotifyInternalAPITask | DummyAPITask;

export const parseToTaskOrThrowError = (input: unknown): SupportedTask => {
	const result = taskSchema.parse(input);
	switch (result.dataSource) {
		case 'spotify-api':
			return parseSpotifyTask(result);
		case 'spotify-internal':
			return parseSpotifyInternalTask(result);
		case 'dummy-api':
			return parseDummyTask(result);
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
			return getSpotifyTaskInputMeta(input.taskType as SpotifyAPITaskType);
		case 'spotify-internal':
			return getSpotifyInternalTaskInputMeta(input.taskType as SpotifyInternalAPITaskType);
		case 'dummy-api':
			return getDummyTaskInputMeta(input.taskType as DummyAPITaskType);
	}
};

export type ParamsUnion<T> = T extends { params: infer P } ? P : never;
export function getParamsSchema(
	input: Pick<SupportedTaskCandidate, 'dataSource' | 'taskType'>
): z.ZodSchema<ParamsUnion<SupportedTask>> | null {
	switch (input.dataSource) {
		case 'spotify-api':
			return getSpotifyTaskParamsSchema(input as SupportedSpotifyAPITaskCandidate);
		case 'spotify-internal':
			return getSpotifyInternalTaskParamsSchema(input as SupportedSpotifyInternalAPITaskCandidate);
		case 'dummy-api':
			return getDummyTaskParamsSchema(input as SupportedDummyAPITaskCandidate);
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
		case 'spotify-internal':
			return getInitialSpotifyInternalTask(base.taskType);
		case 'dummy-api':
			return getInitialDummyTask(base.taskType);
	}
}
