import { type ExpandRecursively } from '$lib/utils';
import { z } from 'zod';
import {
	albumsTaskSchema,
	artistAlbumsTaskSchema,
	artistsTaskSchema,
	playlistsTaskSchema,
	tracksTaskSchema,
	spotifyApiTaskTypesSchema,
	parseSpotifyTask,
	getSpotifyTaskParamsSchema,
	getSpotifyTaskInputMeta
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

export const parseToTaskOrThrowError = (input: unknown) => {
	const result = taskSchema.parse(input);
	switch (result.dataSource) {
		case 'spotify-api':
			switch (result.taskType) {
				case 'tracks':
					return tracksTaskSchema.parse(result);
				case 'artists':
					return artistsTaskSchema.parse(result);
				case 'albums':
					return albumsTaskSchema.parse(result);
				case 'artist-albums':
					return artistAlbumsTaskSchema.parse(result);
				case 'playlists':
					return playlistsTaskSchema.parse(result);
			}
	}
};

export type SupportedTask = ExpandRecursively<ReturnType<typeof parseToTaskOrThrowError>>;

type SupportedTaskInput = SupportedTask['inputs'][0];
export type TaskInputMeta<T extends SupportedTaskInput> = {
	inputDescription: string;
	inputSchema: z.ZodSchema<T>;
	exampleInput: T;
	/**
	 * The name of the DuckDB table which the task inputs should temporarily be stored in before passing them to the scrapers.
	 */
	inputsTableName: string;
};

export type SupportedTaskInputMeta = TaskInputMeta<SupportedTaskInput>;
export const getTaskInputMeta = (
	input: Pick<SupportedTaskCandidate, 'dataSource' | 'taskType'>
): SupportedTaskInputMeta | null => {
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
): SupportedTaskCandidate | null {
	const baseSchemaParseRes = taskSchema.safeParse({
		dataSource: dataSourceStr,
		taskType: taskTypeStr,
		inputs: []
	});
	if (!baseSchemaParseRes.success) return null;
	const candidate = baseSchemaParseRes.data;
	switch (candidate.dataSource) {
		case 'spotify-api':
			return parseSpotifyTask(candidate);
	}
}
