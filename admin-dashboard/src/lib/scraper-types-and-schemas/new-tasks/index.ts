import { z } from 'zod';
import {
	albumsTaskSchema,
	artistAlbumsTaskSchema,
	artistsTaskSchema,
	isSpotifyAPITaskType,
	playlistsTaskSchema,
	spotifyApiTaskTypes,
	tracksTaskSchema
} from './spotify-api';

// TODO: update (turn into z.union([z.literal('...'), z.literal('...')])) as more sources are added
export const dataSourceSchema = z.literal('spotify-api');
export type ScraperDataSource = z.infer<typeof dataSourceSchema>;

export const scraperSchema = z.object({
	host: z.string(),
	port: z.number(),
	protocol: z.string()
});
export type Scraper = z.infer<typeof scraperSchema>;

export const taskSchema = z.object({
	dataSource: dataSourceSchema,
	taskType: z.string(),
	payload: z.record(z.unknown())
});

export type Task<T extends Record<string, unknown>> = {
	dataSource: ScraperDataSource;
	taskType: string;
	payload: T;
};

export const parseToTaskOrThrowError = (input: unknown) => {
	const result = taskSchema.parse(input);
	const dataSource = result.dataSource;
	if (dataSource === 'spotify-api') {
		const taskType = result.taskType;
		if (isSpotifyAPITaskType(taskType)) {
			switch (taskType) {
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
		} else {
			throw new Error(`Invalid task type. Must be one of ${spotifyApiTaskTypes.join(', ')}`);
		}
	}
	// TODO: update as more sources are added
	throw new Error(`Invalid data source. Must be 'spotify-api'`);
};

export type SupportedTask = ReturnType<typeof parseToTaskOrThrowError>;
