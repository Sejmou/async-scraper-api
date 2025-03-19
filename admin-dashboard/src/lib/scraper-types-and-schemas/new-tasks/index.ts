import { type ExpandRecursively } from '$lib/utils';
import { z } from 'zod';
import {
	albumsTaskSchema,
	artistAlbumsTaskSchema,
	artistsTaskSchema,
	playlistsTaskSchema,
	tracksTaskSchema,
	spotifyApiTaskTypesSchema,
	getInitialSpotifyTaskParams,
	tracksParamsSchema,
	artistAlbumsParamsSchema,
	albumsParamsSchema
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

export const noParamsSchema = z.object({
	params: z.undefined()
});

export type SupportedTask = ExpandRecursively<ReturnType<typeof parseToTaskOrThrowError>>;

type TaskInput = SupportedTask['inputs'][0];
export type TaskInputMeta<T extends TaskInput> = {
	inputDescription: string;
	inputSchema: z.ZodSchema<T>;
	exampleInput: T;
	/**
	 * The name of the DuckDB table which the task inputs should temporarily be stored in before passing them to the scrapers.
	 */
	inputsTableName: string;
};
export type SupportedTaskInputMeta = TaskInputMeta<TaskInput>;

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
	const { dataSource, taskType } = baseSchemaParseRes.data;
	const input = {
		dataSource,
		taskType,
		inputs: [],
		params: getInitialTaskParams(dataSource, taskType)
	};
	const task = parseToTaskSafe(input);
	if (!task) console.error('Failed to parse task (this is probably a bug):', { task });
	return task;
}

export function getParamsSchema(task: SupportedTask): z.ZodSchema | null {
	// TODO: update as more data sources and task types are added
	switch (task.dataSource) {
		case 'spotify-api':
			switch (task.taskType) {
				case 'artists':
					return null;
				case 'tracks':
					return tracksParamsSchema;
				case 'artist-albums':
					return artistAlbumsParamsSchema;
				case 'albums':
					return albumsParamsSchema;
				case 'playlists':
					return null;
			}
	}
}

function getInitialTaskParams(
	dataSource: SupportedTask['dataSource'],
	taskType: SupportedTask['taskType']
): Record<string, unknown> | null {
	switch (dataSource) {
		case 'spotify-api':
			return getInitialSpotifyTaskParams(taskType);
	}
}

function parseToTaskSafe(input: unknown): SupportedTask | null {
	try {
		return parseToTaskOrThrowError(input);
	} catch {
		console.error('Failed to parse task from input:', input);
		return null;
	}
}
